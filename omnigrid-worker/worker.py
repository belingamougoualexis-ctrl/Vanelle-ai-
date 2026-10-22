#!/usr/bin/env python3
"""Vanelle OmniGrid worker: cross-platform, allow-listed local task agent.

Python 3.10+. No shell execution. Remote binding is refused unless TLS cert/key are configured.
Set VANELLE_WORKER_TOKEN to a long random secret before starting.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import platform
import secrets
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
HOST = os.environ.get("VANELLE_WORKER_HOST", "127.0.0.1")
PORT = int(os.environ.get("VANELLE_WORKER_PORT", "8765"))
TOKEN = os.environ.get("VANELLE_WORKER_TOKEN", "")
WORKSPACE = Path(os.environ.get("VANELLE_WORKSPACE", "./workspace")).resolve()
AUDIT_PATH = Path(os.environ.get("VANELLE_AUDIT_LOG", "./vanelle-worker-audit.jsonl")).resolve()
TLS_CERT = os.environ.get("VANELLE_TLS_CERT", "")
TLS_KEY = os.environ.get("VANELLE_TLS_KEY", "")
MAX_BODY = 64 * 1024
APPROVAL_HEADER = "X-Vanelle-Approval"


class AgentError(ValueError):
    pass


def _safe_path(relative: str, workspace: Path = WORKSPACE) -> Path:
    root = workspace.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise AgentError("Chemin refusé : sortie de l'espace de travail.")
    return candidate


def _number(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _number(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
        a, b = _number(node.left), _number(node.right)
        if isinstance(node.op, ast.Add): result = a + b
        elif isinstance(node.op, ast.Sub): result = a - b
        elif isinstance(node.op, ast.Mult): result = a * b
        elif isinstance(node.op, ast.Div):
            if b == 0: raise AgentError("Division par zéro.")
            result = a / b
        elif isinstance(node.op, ast.FloorDiv):
            if b == 0: raise AgentError("Division par zéro.")
            result = a // b
        elif isinstance(node.op, ast.Mod):
            if b == 0: raise AgentError("Division par zéro.")
            result = a % b
        else:
            if abs(b) > 12 or abs(a) > 1e9: raise AgentError("Puissance hors limites.")
            result = a ** b
        if abs(result) > 1e100: raise AgentError("Résultat trop grand.")
        return result
    raise AgentError("Expression non autorisée.")


def safe_calculate(expression: str) -> float:
    if not isinstance(expression, str) or len(expression) > 200:
        raise AgentError("Expression invalide ou trop longue.")
    try:
        tree = ast.parse(expression, mode="eval")
        result = _number(tree.body)
    except (SyntaxError, OverflowError, ZeroDivisionError) as exc:
        raise AgentError("Expression arithmétique invalide.") from exc
    return result


class Worker:
    def __init__(self, workspace: Path = WORKSPACE, audit_path: Path = AUDIT_PATH):
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.audit_path = audit_path
        self.audit_lock = threading.Lock()

    def audit(self, action: str, outcome: str, detail: str = "") -> None:
        row = {"time": dt.datetime.now(dt.timezone.utc).isoformat(), "action": action,
               "outcome": outcome, "detail": detail[:300], "host": platform.node()}
        with self.audit_lock:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def execute(self, payload: dict[str, Any], approved: bool = False) -> dict[str, Any]:
        action = payload.get("action")
        if action == "system.info":
            result = {"system": platform.system(), "release": platform.release(),
                      "machine": platform.machine(), "python": platform.python_version(),
                      "workspace": str(self.workspace)}
        elif action == "workspace.list":
            rel = payload.get("path", ".")
            path = self.workspace if rel == "." else (self.workspace / str(rel)).resolve()
            if path != self.workspace and self.workspace not in path.parents:
                raise AgentError("Chemin refusé.")
            if not path.is_dir(): raise AgentError("Dossier introuvable.")
            result = {"path": str(path.relative_to(self.workspace)) if path != self.workspace else ".",
                      "entries": [{"name": p.name, "directory": p.is_dir(), "size": p.stat().st_size if p.is_file() else None}
                                  for p in sorted(path.iterdir(), key=lambda x: x.name.lower())[:200]]}
        elif action == "workspace.read":
            path = _safe_path(str(payload.get("path", "")), self.workspace)
            if not path.is_file(): raise AgentError("Fichier introuvable.")
            if path.stat().st_size > 1_000_000: raise AgentError("Fichier supérieur à 1 Mo refusé.")
            result = {"path": str(path.relative_to(self.workspace)), "text": path.read_text(encoding="utf-8")}
        elif action == "workspace.write":
            if not approved: return {"status": "approval_required", "action": action, "message": "Écriture bloquée : approbation explicite requise."}
            path = _safe_path(str(payload.get("path", "")), self.workspace)
            text = payload.get("text")
            if not isinstance(text, str) or len(text.encode("utf-8")) > 1_000_000:
                raise AgentError("Texte invalide ou supérieur à 1 Mo.")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            result = {"path": str(path.relative_to(self.workspace)), "bytes_written": len(text.encode("utf-8"))}
        elif action == "math.calculate":
            result = {"value": safe_calculate(str(payload.get("expression", "")))}
        elif action == "agent.catalog":
            result = {"agents": [
                {"id": "coordinator", "purpose": "Décomposition et ordonnancement des tâches"},
                {"id": "system", "purpose": "Informations système non sensibles"},
                {"id": "workspace", "purpose": "Lecture et liste limitées à l'espace de travail"},
                {"id": "writer", "purpose": "Écriture de fichiers avec approbation explicite"},
                {"id": "calculator", "purpose": "Calcul arithmétique sans eval ni shell"},
            ]}
        else:
            raise AgentError("Action inconnue ou non autorisée.")
        self.audit(str(action), "success")
        return {"status": "completed", "agent": self._agent_for(str(action)), "result": result}

    @staticmethod
    def _agent_for(action: str) -> str:
        if action.startswith("system."): return "system"
        if action.startswith("workspace.write"): return "writer"
        if action.startswith("workspace."): return "workspace"
        if action.startswith("math."): return "calculator"
        return "coordinator"


def make_handler(worker: Worker, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VanelleWorker/" + VERSION

        def log_message(self, fmt: str, *args: Any) -> None:
            # Request details may contain private paths; do not print them.
            return

        def _reply(self, code: int, body: dict[str, Any]) -> None:
            raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path != "/health":
                self._reply(404, {"status": "not_found"})
                return
            self._reply(200, {"status": "ok", "worker": "Vanelle OmniGrid", "version": VERSION})

        def do_POST(self) -> None:
            if self.path != "/v1/tasks":
                self._reply(404, {"status": "not_found"})
                return
            supplied = self.headers.get("Authorization", "")
            if not token or not secrets.compare_digest(supplied, "Bearer " + token):
                worker.audit("auth", "denied", self.client_address[0])
                self._reply(401, {"status": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY:
                    self._reply(413, {"status": "error", "message": "Taille de requête refusée."})
                    return
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict): raise AgentError("Le corps doit être un objet JSON.")
                approved = self.headers.get(APPROVAL_HEADER, "") == "yes"
                result = worker.execute(payload, approved=approved)
                self._reply(200, result)
            except (UnicodeDecodeError, json.JSONDecodeError, AgentError, OSError) as exc:
                worker.audit("task", "rejected", str(exc))
                self._reply(400, {"status": "error", "message": str(exc)})

    return Handler


def main() -> None:
    if len(TOKEN) < 32:
        raise SystemExit("Refus de démarrer : définis VANELLE_WORKER_TOKEN avec un secret aléatoire d'au moins 32 caractères.")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), make_handler(Worker(), TOKEN))
    if HOST not in ("127.0.0.1", "localhost", "::1"):
        if not (TLS_CERT and TLS_KEY):
            server.server_close()
            raise SystemExit("Refus de réseau distant sans TLS : définis VANELLE_TLS_CERT et VANELLE_TLS_KEY.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(TLS_CERT, TLS_KEY)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    print(f"Vanelle OmniGrid Worker {VERSION} prêt sur {HOST}:{PORT}; espace={WORKSPACE}")
    print("Actions autorisées uniquement; aucune commande shell arbitraire.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

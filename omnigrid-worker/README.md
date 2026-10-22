# Vanelle OmniGrid Worker

Cross-platform worker agent for Windows, Linux and macOS (Python 3.10+). It exposes a small authenticated JSON API and runs only explicitly allow-listed operations. It never executes shell commands.

## Start

Set a random secret of at least 32 characters, then:

```bash
# Linux/macOS
export VANELLE_WORKER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python worker.py
```

On Windows PowerShell:

```powershell
$env:VANELLE_WORKER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(48))"
python .\worker.py
```

The default listener is loopback only (127.0.0.1:8765). To use it from another computer, configure a certificate and private key with `VANELLE_TLS_CERT` and `VANELLE_TLS_KEY`, then set `VANELLE_WORKER_HOST` to the intended interface. The worker refuses remote binding without TLS. Use a trusted certificate and firewall rules; the Android app does not yet pair with or call this worker automatically.

Optional environment variables: `VANELLE_WORKER_PORT`, `VANELLE_WORKSPACE`, `VANELLE_AUDIT_LOG`.

## API

- `GET /health`: basic health check.
- `POST /v1/tasks`: JSON task, authenticated with `Authorization: Bearer <token>`.

Allow-listed actions:
- `system.info`
- `agent.catalog`
- `workspace.list` with optional relative `path`
- `workspace.read` with relative `path` (UTF-8, max 1 MB)
- `workspace.write` with relative `path` and `text`; requires explicit `X-Vanelle-Approval: yes`
- `math.calculate` with `expression`

Example local request:

```bash
curl -H "Authorization: Bearer $VANELLE_WORKER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"system.info"}' http://127.0.0.1:8765/v1/tasks
```

All file operations are confined to the configured workspace. A JSON Lines audit log is written locally. No shell, process execution, arbitrary URL fetch, or privileged OS action is exposed. The worker is a real starting agent, but it is not yet integrated into the Android task coordinator; remote multi-device orchestration must not be considered enabled until authenticated pairing, TLS certificate validation/pinning, timeouts, replay protection, and end-to-end tests are implemented.

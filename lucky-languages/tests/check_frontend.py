import re
import shutil
import subprocess
import tempfile
from pathlib import Path

html = (Path(__file__).resolve().parents[1] / "app" / "static" / "index.html").read_text(encoding="utf-8")
scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
if not scripts:
    raise SystemExit("No inline JavaScript found")
node = shutil.which("node")
if not node:
    raise SystemExit("Node.js is required to syntax-check the frontend")
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tmp:
    tmp.write("\n".join(scripts))
    path = tmp.name
result = subprocess.run([node, "--check", path], text=True, capture_output=True)
Path(path).unlink(missing_ok=True)
if result.returncode:
    print(result.stdout)
    print(result.stderr)
    raise SystemExit(result.returncode)
print("Frontend JavaScript syntax: OK")

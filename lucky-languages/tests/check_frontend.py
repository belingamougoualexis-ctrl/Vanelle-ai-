import re
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / "app" / "static" / "index.html").read_text(encoding="utf-8")
scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
if not scripts:
    raise SystemExit("No inline JavaScript found")
external_scripts = [root / "app" / "static" / "practice.js", root / "app" / "static" / "teachers-3d.js"]
node = shutil.which("node")
if not node:
    raise SystemExit("Node.js is required to syntax-check the frontend")
for index, source in enumerate(["\n".join(scripts)] + [path.read_text(encoding="utf-8") for path in external_scripts]):
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tmp:
        tmp.write(source)
        path = tmp.name
    result = subprocess.run([node, "--check", path], text=True, capture_output=True)
    Path(path).unlink(missing_ok=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
print("Inline, adaptive-practice, and 3D teacher JavaScript syntax: OK")

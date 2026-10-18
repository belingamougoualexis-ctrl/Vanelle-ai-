# Lucky Languages Academy

Isolated application folder; the existing Android app remains unchanged.

## Scope of this initial implementation
FastAPI API, SQLite development storage, authentication, role checks, server-calculated weighted bulletins, server-side exam attempt cancellation, a small truthful language catalogue, browser UI, automated tests and CI.

This is a foundation, not yet the complete school platform. Real-time messaging, class management, assignments, verified course content, PDF exports, administration, offline synchronization and lightweight local AI integration remain to be implemented and tested.

## Run locally
```bash
cd lucky-languages
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs.

## Tests
```bash
pip install -r requirements.txt
pytest -q
```

SQLite is for development. Production requires PostgreSQL, HTTPS, backups, secret management and deployment hardening. Exit detection depends on the client reporting it; browsers cannot guarantee detection of every exit or prevent tampering. A catalogue entry does not mean a complete verified course exists for that language.
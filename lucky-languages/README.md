# Lucky Languages Academy

A standalone French-first language-school web application added under `lucky-languages/`. The existing Vanelle Android app is not replaced or rewritten.

## Start locally

Requirements: Python 3.12+ and pip.

```bash
cd lucky-languages
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. API documentation is at `http://127.0.0.1:8000/docs`. The web app is installable as a PWA in compatible browsers; its shell and public course responses can be cached, but authenticated features and messaging require the API to be reachable.

## Docker — application + real local AI model

```bash
docker compose up --build
```

The first start pulls the Ollama runtime and downloads the actual `qwen2.5:1.5b` model weights into the persistent `lucky-models` volume. This requires an Internet connection for the first download and enough disk/RAM; later starts reuse the downloaded model. The app connects to that local model service and falls back to original exercises only if model generation fails. The model is provisioned automatically by the packaged Docker setup rather than committed as a huge binary in Git. SQLite is used for development and the compose example. The database is persisted in a named volume. For public multi-user production, migrate to PostgreSQL and configure HTTPS, backups, secret storage, monitoring, rate limits, and a proper deployment proxy before exposing it to the Internet.

## First administrator

Set these environment variables **before the first server start** to bootstrap the first administrator. No default admin credentials are created.

- `LUCKY_ADMIN_NAME`: display name
- `LUCKY_ADMIN_USERNAME`: username
- `LUCKY_ADMIN_PASSWORD`: unique password of at least 16 characters

PowerShell example:

```powershell
$env:LUCKY_ADMIN_NAME="Academy Admin"
$env:LUCKY_ADMIN_USERNAME="academy-admin"
$env:LUCKY_ADMIN_PASSWORD="replace-with-a-unique-long-secret"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If the administrator account already exists, changing these variables does not overwrite its password. Administrators can change roles through the administration panel.

## Modules implemented

- Registration/login, opaque bearer sessions and role-based permissions
- Catalogue metadata for 200+ language identifiers; catalogue entries are not claims that full lessons are available
- Starter A1 courses/lessons for English, French and Spanish
- Lesson progress and saved difficulty history
- Local Ollama tutor. `docker compose up --build` starts an Ollama model service and downloads `qwen2.5:1.5b` into a persistent model volume on first launch; this initial download requires Internet and substantial disk/RAM. No cloud AI API is used by the tutor
- Timed multiple-choice exams for English, French and Spanish, server-side answer checking and scoring, 20-minute deadline and exit cancellation
- Classes, join codes, assignments, student submissions, teacher grading and gradebook integration
- Private/class messages, announcements, schedule, learning-resource uploads/downloads
- Weighted bulletin, PDF export, administrator overview and audit log
- Responsive PWA interface and limited offline shell/course cache
- GitHub Actions CI: Python compilation, JavaScript syntax check and API tests

## Run tests

```bash
pip install -r requirements.txt
python -m compileall -q app tests
python tests/check_frontend.py
pytest -q -m 'not ai_integration'
```

The separate real-model integration test is `pytest -q tests/test_ai_integration.py -m ai_integration`. It requires Ollama running at `127.0.0.1:11434` and `qwen2.5:0.5b` downloaded. GitHub Actions now has a dedicated job that starts Ollama, downloads the real model weights, and sends a request through the actual app API; this test fails if the API silently falls back to the offline question bank.

## Important scope and safety notes

- The metadata catalogue is broad, but complete verified course paths currently exist only for the starter languages/content. Do not advertise every catalogue language as a complete course.
- The starter question bank is limited; exam support must be expanded with reviewed questions before use for formal certification.
- Exit detection relies on a client signal. Browsers and mobile operating systems cannot guarantee detection of every app switch, device shutdown, network loss or tampering. The server enforces status and time when requests reach it.
- Docker Compose includes a local Ollama model service and automatically pulls the Qwen 1.5B weights into a persistent volume on first start. The multi-hundred-MB/GB model weights are downloaded at installation time, not checked into the source ZIP or Git repository. This first setup needs Internet; inference thereafter is local. Mobile-browser clients still call the server and do not run the model directly on the phone.
- Uploaded files are limited to 10 MB and allowed file extensions, but production needs malware scanning, storage isolation and retention policy.
- SQLite is not a suitable final database for a high-traffic school service. The current project is a functional application foundation, not a certified or production-hardened education platform.


## Adaptive language pedagogy (added)

- **Exercises API:** `POST /api/pedagogy/generate` supports language, level (A1–C2, beginner, primary, secondary, BEPC), skill, topic, count and learner difficulties.
- **Correction API:** `POST /api/pedagogy/grade` checks a submitted answer against the question's reference answer and returns feedback/explanation.
- **Language-specific methods:** dedicated practice guidance for English, French, Spanish, Mandarin Chinese, Japanese, Korean, Arabic, Russian, German and Portuguese. Other language identifiers receive a generic safe template rather than a claim of complete curriculum.
- **Chinese practice:** original activities include character, meaning, pinyin, tones in explanations, stroke-count metadata where known, and a writing prompt. The web text field cannot judge handwriting stroke quality or spoken tones; no such capability is claimed.
- **Local AI:** Docker Compose provisions the Ollama engine and downloads `qwen2.5:1.5b` into a persistent volume; environment variables `LUCKY_OLLAMA_URL` and `LUCKY_PEDAGOGY_MODEL` remain configurable. If generation fails, the app uses original built-in questions/templates and labels that path separately. AI-generated questions are marked unverified and must be teacher-reviewed before high-stakes grading.
- **Real model test:** `.github/workflows/lucky-languages-ci.yml` includes a dedicated integration job that downloads `qwen2.5:0.5b` and tests actual model output through the FastAPI endpoint; it rejects offline fallback as a passing result.
- **Exam sources:** the UI links to official exam/resource sites for DELF/DALF/TCF, DELE, Cambridge English, HSK and Goethe. The app stores source references and reuse warnings, not copied copyrighted question papers. Each resource's specific license must be checked before importing it.
- **Testing:** `tests/test_pedagogy.py` verifies endpoint schemas, answer validation, Chinese metadata, level rejection and exam-source reuse notes.
- **Scope:** these are starter paths and not a complete, accredited curriculum for every language or official exam. The catalogue does not imply that every language has verified lessons or question banks.

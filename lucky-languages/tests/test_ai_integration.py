"""Real model integration tests. Run only in the dedicated model-enabled CI job."""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.ai_integration
@pytest.mark.parametrize("language_code", ["en", "fr", "es", "de", "pt", "zh", "ja", "ko", "ar", "ru"])
def test_real_local_model_generates_valid_language_exercise(language_code):
    endpoint = os.getenv("LUCKY_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    model = os.getenv("LUCKY_PEDAGOGY_MODEL", "qwen2.5:1.5b")
    # Require a genuine local model response; do not silently accept offline fallback.
    response = TestClient(app).post("/api/pedagogy/generate", json={
        "language_code": language_code,
        "level": "A1",
        "skill": "vocabulary",
        "topic": "daily life",
        "count": 1,
        "use_local_ai": True,
    })
    assert response.status_code == 200, f"{language_code}: {response.text}"
    result = response.json()
    assert result["generator"] == "ollama_local", (
        f"{language_code}: expected real model output; got {result.get('generator')} "
        f"using {model} at {endpoint}"
    )
    assert len(result["questions"]) >= 1
    for question in result["questions"]:
        assert question["question"].strip()
        assert question["answer"] in question["options"]
        assert question.get("explanation") is not None
        assert question["source"] == "ai_generated_unverified"

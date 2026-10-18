"""Real model integration test. Run only in the dedicated model-enabled CI job."""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.ai_integration
def test_real_local_model_generates_valid_language_exercise():
    endpoint = os.getenv("LUCKY_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    model = os.getenv("LUCKY_PEDAGOGY_MODEL", "qwen2.5:1.5b")
    # Do not silently accept the offline fallback: this test requires a genuine model response.
    response = TestClient(app).post("/api/pedagogy/generate", json={
        "language_code": "en",
        "level": "A1",
        "skill": "vocabulary",
        "topic": "school",
        "count": 1,
        "use_local_ai": True,
    })
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["generator"] == "ollama_local", (
        f"Expected real model output; got {result.get('generator')} using {model} at {endpoint}"
    )
    assert len(result["questions"]) >= 1
    for question in result["questions"]:
        assert question["question"].strip()
        assert question["answer"] in question["options"]
        assert question.get("explanation") is not None
        assert question["source"] == "ai_generated_unverified"

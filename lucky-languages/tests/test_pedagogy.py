from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pedagogy_languages_and_distinct_chinese_method():
    response = client.get("/api/pedagogy/languages")
    assert response.status_code == 200
    data = response.json()
    chinese = next(item for item in data["items"] if item["code"] == "zh")
    assert "pinyin" in chinese["skills"]
    assert "écriture" in chinese["skills"]
    assert "caractère" in chinese["method"]
    assert "zh" in data["supported_question_banks"]

def test_original_exercise_generation_is_deterministic_and_level_scoped():
    response = client.post("/api/pedagogy/generate", json={
        "language_code": "en", "level": "A1", "skill": "vocabulary",
        "count": 3, "topic": "school", "use_local_ai": False
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    assert data["generator"] == "reviewed_original_bank_or_template"
    assert all(question["answer"] in question["options"] for question in data["questions"])
    assert all(question["source"] == "original" for question in data["questions"])

def test_chinese_exercises_include_reading_meaning_pinyin_and_writing():
    response = client.post("/api/pedagogy/generate", json={
        "language_code": "zh", "level": "A1", "skill": "character",
        "count": 4, "topic": "caractères", "use_local_ai": False
    })
    assert response.status_code == 200
    questions = response.json()["questions"]
    assert len(questions) == 4
    assert any(q.get("character") for q in questions)
    for question in questions:
        assert question.get("pinyin")
        assert question.get("meaning")
        assert question.get("writing_prompt")
        assert question["answer"] in question["options"]

def test_grade_endpoint_checks_answer_and_discloses_handwriting_limit():
    question = {"answer":"人","explanation":"Personne; pinyin rén."}
    right = client.post("/api/pedagogy/grade", json={
        "language_code":"zh", "question":question, "answer":"人"
    })
    wrong = client.post("/api/pedagogy/grade", json={
        "language_code":"zh", "question":question, "answer":"水"
    })
    assert right.status_code == 200 and right.json()["correct"] is True
    assert wrong.status_code == 200 and wrong.json()["correct"] is False
    assert "tracé" in right.json()["assessment_limit"]

def test_exam_resources_are_links_and_license_notes():
    response = client.get("/api/pedagogy/exam-resources?language_code=fr")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["url"].startswith("https://")
    assert "conditions" in item["reuse"] or "autorisation" in item["reuse"]

def test_invalid_level_is_rejected():
    response = client.post("/api/pedagogy/generate", json={
        "language_code":"en", "level":"expert", "count":1
    })
    assert response.status_code == 422


def test_all_supported_language_exercise_banks_return_valid_questions():
    data = client.get("/api/pedagogy/languages")
    assert data.status_code == 200
    for item in data.json()["items"]:
        response = client.post("/api/pedagogy/generate", json={
            "language_code": item["code"], "level": "A1", "skill": "mixed",
            "count": 3, "topic": "daily life", "use_local_ai": False
        })
        assert response.status_code == 200, item["code"]
        questions = response.json()["questions"]
        assert len(questions) == 3
        assert all(q.get("question") and q.get("options") and q.get("answer") in q["options"] for q in questions)

def test_advanced_level_selection_returns_level_matched_original_questions():
    for language_code in ("en", "fr", "es"):
        for level in ("A2", "B1", "B2", "C1", "C2"):
            response = client.post("/api/pedagogy/generate", json={
                "language_code": language_code, "level": level, "skill": "mixed",
                "count": 1, "topic": "everyday life", "use_local_ai": False
            })
            assert response.status_code == 200
            question = response.json()["questions"][0]
            assert question["level"] == level, (language_code, level, question)
            assert question["answer"] in question["options"]

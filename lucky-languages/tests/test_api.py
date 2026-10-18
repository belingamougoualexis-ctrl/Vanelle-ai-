import os, tempfile
import pytest
DB_FILE=tempfile.NamedTemporaryFile(suffix=".sqlite3",delete=False); DB_FILE.close()
os.environ["LUCKY_DB_PATH"]=DB_FILE.name
from fastapi.testclient import TestClient
from app.main import app, db_session, password_hash

@pytest.fixture()
def client():
 with TestClient(app) as c:
  with db_session() as db:
   db.execute("DELETE FROM audit_log"); db.execute("DELETE FROM messages"); db.execute("DELETE FROM submissions")
   db.execute("DELETE FROM assignments"); db.execute("DELETE FROM schedule"); db.execute("DELETE FROM announcements")
   db.execute("DELETE FROM resources"); db.execute("DELETE FROM lesson_progress"); db.execute("DELETE FROM difficulties")
   db.execute("DELETE FROM exam_answers"); db.execute("DELETE FROM enrollments"); db.execute("DELETE FROM classes"); db.execute("DELETE FROM exam_attempts")
   db.execute("DELETE FROM grades"); db.execute("DELETE FROM sessions"); db.execute("DELETE FROM users")
  yield c

def register(client,username="student1",role=None):
 r=client.post("/api/auth/register",json={"full_name":"Student Example","username":username,"password":"correct-horse-battery"})
 assert r.status_code==201
 data=r.json()
 if role:
  with db_session() as db: db.execute("UPDATE users SET role=? WHERE id=?",(role,data["user"]["id"]))
 return data
def auth(token): return {"Authorization":f"Bearer {token}"}

def test_health_and_catalogue(client):
 assert client.get("/health").json()["status"]=="ok"
 catalogue=client.get("/api/languages").json()["items"]
 assert any(x["code"]=="fr" for x in catalogue)
 assert len(catalogue)>=200

def test_weighted_bulletin_and_private_access(client):
 s=register(client)
 with db_session() as db:
  db.execute("INSERT INTO grades(student_id,subject,assessment,score,coefficient) VALUES(?,?,?,?,?)",(s["user"]["id"],"Mathématiques","Devoir 1",16,2))
  db.execute("INSERT INTO grades(student_id,subject,assessment,score,coefficient) VALUES(?,?,?,?,?)",(s["user"]["id"],"Français","Devoir 1",12,1))
 result=client.get("/api/bulletin",headers=auth(s["access_token"]))
 assert result.status_code==200 and result.json()["average"]==pytest.approx(14.67)
 other=register(client,"student2")
 assert client.get(f"/api/bulletin?student_id={s['user']['id']}",headers=auth(other["access_token"])).status_code==403

def test_student_cannot_write_grades(client):
 s=register(client)
 r=client.post("/api/grades",headers=auth(s["access_token"]),json={"student_id":s["user"]["id"],"subject":"Anglais","assessment":"Test","score":20,"coefficient":1})
 assert r.status_code==403

def test_exit_cancels_exam_and_second_exit_fails(client):
 s=register(client)
 started=client.post("/api/exams/start",headers=auth(s["access_token"]),json={"language_code":"en"})
 assert started.status_code==201
 attempt=started.json()["attempt_id"]
 exited=client.post(f"/api/exams/{attempt}/exit",headers=auth(s["access_token"]))
 assert exited.status_code==200 and exited.json()["status"]=="cancelled"
 assert exited.json()["restart_required"] is True
 assert client.post(f"/api/exams/{attempt}/exit",headers=auth(s["access_token"])).status_code==409

def test_login_and_bad_password(client):
 s=register(client)
 assert client.post("/api/auth/login",json={"username":"student1","password":"correct-horse-battery"}).status_code==200
 assert client.post("/api/auth/login",json={"username":"student1","password":"wrong-password"}).status_code==401
 assert client.get("/api/me",headers=auth(s["access_token"])).status_code==200

def test_admin_role_management_and_teacher_grade_entry(client):
 student=register(client,"student_for_teacher")
 teacher=register(client,"teacher_account")
 with db_session() as db:
  db.execute("INSERT INTO users(full_name,username,password_hash,role) VALUES(?,?,?,'admin')",
             ("Admin Example","admin1",password_hash("admin-password-123456")))
 admin_login=client.post("/api/auth/login",json={"username":"admin1","password":"admin-password-123456"})
 assert admin_login.status_code==200
 admin_headers=auth(admin_login.json()["access_token"])
 promoted=client.post(f"/api/admin/users/{teacher['user']['id']}/role",headers=admin_headers,json={"role":"teacher"})
 assert promoted.status_code==200
 teacher_login=client.post("/api/auth/login",json={"username":"teacher_account","password":"correct-horse-battery"})
 assert teacher_login.status_code==200
 teacher_headers=auth(teacher_login.json()["access_token"])
 grade=client.post("/api/grades",headers=teacher_headers,json={
  "student_id":student["user"]["id"],"subject":"Français","assessment":"Évaluation 1","score":15,"coefficient":2
 })
 assert grade.status_code==201
 bulletin=client.get(f"/api/bulletin?student_id={student['user']['id']}",headers=teacher_headers)
 assert bulletin.status_code==200 and bulletin.json()["average"]==15

def test_courses_progress_and_difficulty_memory(client):
 student=register(client)
 courses=client.get("/api/courses")
 assert courses.status_code==200 and len(courses.json()["items"])>=3
 course=courses.json()["items"][0]
 detail=client.get(f"/api/courses/{course['id']}")
 assert detail.status_code==200 and len(detail.json()["lessons"])>=3
 lesson=detail.json()["lessons"][0]
 progress=client.post(f"/api/lessons/{lesson['id']}/progress",headers=auth(student["access_token"]),json={"status":"completed","score":90})
 assert progress.status_code==200
 difficulty=client.post("/api/difficulties",headers=auth(student["access_token"]),json={"lesson_id":lesson["id"],"topic":"verbes","question":"Je ne comprends pas la règle"})
 assert difficulty.status_code==201 and "étape" in difficulty.json()["explanation"]
 mine=client.get("/api/progress",headers=auth(student["access_token"]))
 assert len(mine.json()["lessons"])==1 and len(mine.json()["difficulties"])==1

def test_class_assignment_submission_and_scoped_messages(client):
 teacher=register(client,"teacher_user")
 student=register(client,"student_user")
 with db_session() as db:
  db.execute("UPDATE users SET role='teacher' WHERE id=?",(teacher["user"]["id"],))
 teacher_login=client.post("/api/auth/login",json={"username":"teacher_user","password":"correct-horse-battery"})
 th=auth(teacher_login.json()["access_token"]); sh=auth(student["access_token"])
 created=client.post("/api/classes",headers=th,json={"name":"Groupe A","language_code":"fr","level":"A1"})
 assert created.status_code==201
 cls=created.json()
 joined=client.post("/api/classes/join",headers=sh,json={"join_code":cls["join_code"]})
 assert joined.status_code==200
 assignment=client.post(f"/api/classes/{cls['id']}/assignments",headers=th,json={"title":"Devoir 1","instructions":"Écris trois phrases."})
 assert assignment.status_code==201
 assert client.get(f"/api/classes/{cls['id']}/assignments",headers=sh).status_code==200
 submitted=client.post(f"/api/assignments/{assignment.json()['id']}/submit",headers=sh,json={"answer":"Je suis élève. J'apprends. Je progresse."})
 assert submitted.status_code==201
 assert len(client.get(f"/api/classes/{cls['id']}/submissions",headers=th).json()["items"])==1
 sent=client.post("/api/messages",headers=sh,json={"class_id":cls["id"],"body":"Bonjour à tous"})
 assert sent.status_code==201
 assert len(client.get(f"/api/messages?class_id={cls['id']}",headers=th).json()["items"])==1

def test_pdf_bulletin_and_role_protected_admin(client):
 student=register(client)
 pdf=client.get("/api/bulletin.pdf",headers=auth(student["access_token"]))
 assert pdf.status_code==200 and pdf.headers["content-type"]=="application/pdf"
 assert pdf.content.startswith(b"%PDF")
 assert client.get("/api/admin/overview",headers=auth(student["access_token"])).status_code==403

def test_real_exam_questions_answers_server_grading_and_exit(client):
 student=register(client,"exam_student")
 headers=auth(student["access_token"])
 start=client.post("/api/exams/start",headers=headers,json={"language_code":"fr"})
 assert start.status_code==201
 attempt=start.json()["attempt_id"]
 qs=client.get(f"/api/exams/{attempt}/questions",headers=headers)
 assert qs.status_code==200 and len(qs.json()["questions"])>0
 q=qs.json()["questions"][0]
 assert "correct_answer" not in q
 saved=client.post(f"/api/exams/{attempt}/answer",headers=headers,json={"question_id":q["id"],"answer":q["options"][0]})
 assert saved.status_code==200
 submitted=client.post(f"/api/exams/{attempt}/submit",headers=headers)
 assert submitted.status_code==200 and submitted.json()["status"]=="submitted"
 assert client.post(f"/api/exams/{attempt}/submit",headers=headers).status_code==409
 assert len(client.get("/api/bulletin",headers=headers).json()["grades"])==1


def test_cefr_course_paths_cover_a1_to_c2_and_additional_language_starters(client):
 courses = client.get("/api/courses")
 assert courses.status_code == 200
 items = courses.json()["items"]
 for code in ("en", "fr", "es"):
  levels = {item["level"] for item in items if item["language_code"] == code}
  assert {"A1", "A2", "B1", "B2", "C1", "C2"} <= levels
  for item in items:
   if item["language_code"] == code and item["level"] in {"A2", "B1", "B2", "C1", "C2"}:
    detail = client.get(f"/api/courses/{item['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["lessons"]) >= 6
    assert all(lesson["title"] and lesson["body"] and lesson["exercise"] and lesson["answer"] and lesson["position"] for lesson in detail.json()["lessons"])
 for code in ("de", "pt", "zh", "ja", "ko", "ar", "ru"):
  starter = next((item for item in items if item["language_code"] == code and item["level"] == "A1"), None)
  assert starter is not None
  detail = client.get(f"/api/courses/{starter['id']}")
  assert detail.status_code == 200
  assert len(detail.json()["lessons"]) >= 8
  assert all(lesson.get("answer") for lesson in detail.json()["lessons"])

def test_course_lessons_expose_answer_for_interactive_self_check(client):
 courses = client.get("/api/courses").json()["items"]
 for code in ("en", "fr", "es"):
  starter = next(item for item in courses if item["language_code"] == code and item["level"] == "A1")
  detail = client.get(f"/api/courses/{starter['id']}").json()
  assert len(detail["lessons"]) >= 6
  assert all(isinstance(lesson["answer"], str) and lesson["answer"].strip() for lesson in detail["lessons"])

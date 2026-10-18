import os, tempfile
import pytest
DB_FILE=tempfile.NamedTemporaryFile(suffix=".sqlite3",delete=False); DB_FILE.close()
os.environ["LUCKY_DB_PATH"]=DB_FILE.name
from fastapi.testclient import TestClient
from app.main import app, db_session

@pytest.fixture()
def client():
 with TestClient(app) as c:
  with db_session() as db:
   db.execute("DELETE FROM audit_log"); db.execute("DELETE FROM exam_attempts")
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
 assert any(x["code"]=="fr" for x in client.get("/api/languages").json()["items"])

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

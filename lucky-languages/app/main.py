from __future__ import annotations
import hashlib, hmac, os, secrets, sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("LUCKY_DB_PATH", str(BASE / "lucky.db")))
app = FastAPI(title="Lucky Languages Academy API", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
LANGUAGES = [
 {"code":"en","name":"English","status":"catalogue"},
 {"code":"fr","name":"Français","status":"catalogue"},
 {"code":"es","name":"Español","status":"catalogue"},
 {"code":"de","name":"Deutsch","status":"catalogue"},
 {"code":"pt","name":"Português","status":"catalogue"},
 {"code":"sw","name":"Kiswahili","status":"catalogue"},
 {"code":"ha","name":"Hausa","status":"catalogue"},
 {"code":"yo","name":"Yorùbá","status":"catalogue"},
]
def connect():
 DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 db=sqlite3.connect(DB_PATH, timeout=10); db.row_factory=sqlite3.Row
 db.execute("PRAGMA foreign_keys=ON")
 return db
@contextmanager
def db_session():
 db=connect()
 try:
  yield db; db.commit()
 except Exception:
  db.rollback(); raise
 finally: db.close()
def init_db():
 with db_session() as db:
  db.executescript("""
  CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,full_name TEXT NOT NULL,username TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')));
  CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS grades(id INTEGER PRIMARY KEY,student_id INTEGER NOT NULL REFERENCES users(id),subject TEXT NOT NULL,assessment TEXT NOT NULL,score REAL NOT NULL CHECK(score>=0 AND score<=20),coefficient REAL NOT NULL CHECK(coefficient>0),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS exam_attempts(id INTEGER PRIMARY KEY,student_id INTEGER NOT NULL REFERENCES users(id),language_code TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('in_progress','cancelled','submitted')),question_seed INTEGER NOT NULL,started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY,actor_id INTEGER,action TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  """)
@app.on_event("startup")
def startup():
 init_db()
 # Optional first-admin bootstrap: configure all three variables in the deployment environment.
 # No default credentials are created.
 admin_name=os.getenv("LUCKY_ADMIN_NAME")
 admin_username=os.getenv("LUCKY_ADMIN_USERNAME")
 admin_password=os.getenv("LUCKY_ADMIN_PASSWORD")
 if admin_name and admin_username and admin_password and len(admin_password)>=16:
  with db_session() as db:
   existing=db.execute("SELECT id FROM users WHERE username=?",(admin_username.lower(),)).fetchone()
   if not existing:
    db.execute("INSERT INTO users(full_name,username,password_hash,role) VALUES(?,?,?,'admin')",
                (admin_name,admin_username.lower(),password_hash(admin_password)))
def password_hash(password):
 salt=secrets.token_bytes(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,180000)
 return salt.hex()+"$"+digest.hex()
def verify_password(password,stored):
 try:
  salt,digest=stored.split("$",1)
  actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),180000).hex()
  return hmac.compare_digest(actual,digest)
 except (ValueError,TypeError): return False
def digest_token(token): return hashlib.sha256(token.encode()).hexdigest()
class RegisterIn(BaseModel):
 full_name:str=Field(min_length=2,max_length=100)
 username:str=Field(min_length=3,max_length=40,pattern=r"^[a-zA-Z0-9_.-]+$")
 password:str=Field(min_length=10,max_length=128)
class LoginIn(BaseModel):
 username:str
 password:str
class GradeIn(BaseModel):
 student_id:int
 subject:str=Field(min_length=1,max_length=80)
 assessment:str=Field(min_length=1,max_length=120)
 score:float=Field(ge=0,le=20)
 coefficient:float=Field(gt=0,le=20)
class ExamStartIn(BaseModel):
 language_code:str=Field(min_length=2,max_length=12)
class RoleIn(BaseModel):
 role:str=Field(pattern=r"^(student|teacher|admin)$")
def current_user(authorization:Optional[str]=Header(default=None)):
 if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Authentification requise")
 token=authorization[7:].strip()
 with db_session() as db:
  row=db.execute("SELECT u.id,u.full_name,u.username,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",(digest_token(token),)).fetchone()
 if not row: raise HTTPException(401,"Session invalide")
 return dict(row)
def require_roles(*roles):
 def guard(user=Depends(current_user)):
  if user["role"] not in roles: raise HTTPException(403,"Permission insuffisante")
  return user
 return guard
@app.get("/")
def home(): return FileResponse(BASE/"static"/"index.html")
@app.get("/health")
def health(): return {"status":"ok","service":"lucky-languages-api"}
@app.get("/api/languages")
def languages(): return {"items":LANGUAGES,"note":"Catalogue initial; les langues listées ne garantissent pas un cours complet vérifié."}
@app.post("/api/auth/register",status_code=201)
def register(payload:RegisterIn):
 with db_session() as db:
  try:
   cur=db.execute("INSERT INTO users(full_name,username,password_hash,role) VALUES(?,?,?,'student')",(payload.full_name.strip(),payload.username.lower(),password_hash(payload.password)))
   uid=cur.lastrowid
  except sqlite3.IntegrityError: raise HTTPException(409,"Nom d'utilisateur déjà utilisé")
  token=secrets.token_urlsafe(32)
  db.execute("INSERT INTO sessions(token_hash,user_id) VALUES(?,?)",(digest_token(token),uid))
 return {"access_token":token,"token_type":"bearer","user":{"id":uid,"full_name":payload.full_name.strip(),"username":payload.username.lower(),"role":"student"}}
@app.post("/api/auth/login")
def login(payload:LoginIn):
 with db_session() as db:
  row=db.execute("SELECT * FROM users WHERE username=?",(payload.username.lower(),)).fetchone()
  if not row or not verify_password(payload.password,row["password_hash"]): raise HTTPException(401,"Identifiants incorrects")
  token=secrets.token_urlsafe(32); db.execute("INSERT INTO sessions(token_hash,user_id) VALUES(?,?)",(digest_token(token),row["id"]))
 return {"access_token":token,"token_type":"bearer","user":{"id":row["id"],"full_name":row["full_name"],"username":row["username"],"role":row["role"]}}
@app.post("/api/auth/logout")
def logout(user=Depends(current_user),authorization:str=Header(...)):
 token=authorization[7:].strip()
 with db_session() as db: db.execute("DELETE FROM sessions WHERE token_hash=?",(digest_token(token),))
 return {"ok":True}
@app.get("/api/me")
def me(user=Depends(current_user)): return user
@app.post("/api/admin/users/{user_id}/role")
def set_user_role(user_id:int,payload:RoleIn,user=Depends(require_roles("admin"))):
 with db_session() as db:
  target=db.execute("SELECT id FROM users WHERE id=?",(user_id,)).fetchone()
  if not target: raise HTTPException(404,"Utilisateur introuvable")
  db.execute("UPDATE users SET role=? WHERE id=?",(payload.role,user_id))
  db.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES(?,?,?)",(user["id"],"user_role_changed",f"user_id={user_id};role={payload.role}"))
 return {"user_id":user_id,"role":payload.role}
@app.post("/api/grades",status_code=201)
def add_grade(payload:GradeIn,user=Depends(require_roles("teacher","admin"))):
 with db_session() as db:
  student=db.execute("SELECT id FROM users WHERE id=? AND role='student'",(payload.student_id,)).fetchone()
  if not student: raise HTTPException(404,"Élève introuvable")
  cur=db.execute("INSERT INTO grades(student_id,subject,assessment,score,coefficient) VALUES(?,?,?,?,?)",(payload.student_id,payload.subject.strip(),payload.assessment.strip(),payload.score,payload.coefficient))
  db.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES(?,?,?)",(user["id"],"grade_created",f"grade_id={cur.lastrowid};student_id={payload.student_id}"))
 return {"id":cur.lastrowid,"created":True}
@app.get("/api/bulletin")
def bulletin(student_id:Optional[int]=None,user=Depends(current_user)):
 if user["role"]=="student":
  if student_id is not None and student_id!=user["id"]: raise HTTPException(403,"Un élève ne peut consulter que son propre bulletin")
  target=user["id"]
 elif user["role"] in ("teacher","admin"):
  if student_id is None: raise HTTPException(422,"student_id requis pour ce rôle")
  target=student_id
 with db_session() as db:
  student=db.execute("SELECT id,full_name FROM users WHERE id=? AND role='student'",(target,)).fetchone()
  if not student: raise HTTPException(404,"Élève introuvable")
  rows=db.execute("SELECT subject,assessment,score,coefficient FROM grades WHERE student_id=? ORDER BY subject,id",(target,)).fetchall()
 total=sum(r["coefficient"] for r in rows)
 average=round(sum(r["score"]*r["coefficient"] for r in rows)/total,2) if total else None
 return {"student":dict(student),"average":average,"total_coefficient":total,"grades":[dict(r) for r in rows]}
@app.post("/api/exams/start",status_code=201)
def start_exam(payload:ExamStartIn,user=Depends(require_roles("student"))):
 if not any(item["code"]==payload.language_code for item in LANGUAGES): raise HTTPException(404,"Langue absente du catalogue initial")
 with db_session() as db:
  cur=db.execute("INSERT INTO exam_attempts(student_id,language_code,status,question_seed) VALUES(?,?,'in_progress',?)",(user["id"],payload.language_code,secrets.randbelow(2**31)))
 return {"attempt_id":cur.lastrowid,"status":"in_progress","message":"La banque de questions vérifiées doit être ajoutée avant d'activer de vrais examens."}
@app.post("/api/exams/{attempt_id}/exit")
def exit_exam(attempt_id:int,user=Depends(require_roles("student"))):
 with db_session() as db:
  row=db.execute("SELECT * FROM exam_attempts WHERE id=? AND student_id=?",(attempt_id,user["id"])).fetchone()
  if not row: raise HTTPException(404,"Tentative introuvable")
  if row["status"]!="in_progress": raise HTTPException(409,"La tentative n'est plus active")
  db.execute("UPDATE exam_attempts SET status='cancelled',question_seed=? WHERE id=?",(secrets.randbelow(2**31),attempt_id))
  db.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES(?,?,?)",(user["id"],"exam_cancelled_on_exit",f"attempt_id={attempt_id}"))
 return {"attempt_id":attempt_id,"status":"cancelled","restart_required":True,"new_questions_on_restart":True}

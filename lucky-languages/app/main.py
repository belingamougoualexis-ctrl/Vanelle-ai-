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
  if not db.execute("SELECT id FROM exam_questions WHERE language_code=? LIMIT 1",(payload.language_code,)).fetchone():
   raise HTTPException(422,"Aucune banque d’examen vérifiée n’est encore disponible pour cette langue.")
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


# --- Academy modules: verified starter content, classes, assignments, messages, resources,
# timetable, progress/difficulty tracking, announcements and optional local Ollama tutor. ---
import json
import time
import urllib.request
from datetime import datetime, timezone
from fastapi import Query, UploadFile, File
from fastapi.responses import Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def init_academy_tables():
 with db_session() as db:
  db.executescript("""
  CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,language_code TEXT NOT NULL,title TEXT NOT NULL,level TEXT NOT NULL,description TEXT NOT NULL,published INTEGER NOT NULL DEFAULT 1);
  CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY,course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,title TEXT NOT NULL,body TEXT NOT NULL,exercise TEXT NOT NULL,answer TEXT NOT NULL,position INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS enrollments(id INTEGER PRIMARY KEY,class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,UNIQUE(class_id,student_id));
  CREATE TABLE IF NOT EXISTS classes(id INTEGER PRIMARY KEY,name TEXT NOT NULL,teacher_id INTEGER NOT NULL REFERENCES users(id),language_code TEXT NOT NULL,level TEXT NOT NULL,join_code TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY,class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,title TEXT NOT NULL,instructions TEXT NOT NULL,due_at TEXT,created_by INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY,assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,student_id INTEGER NOT NULL REFERENCES users(id),answer TEXT NOT NULL,score REAL,feedback TEXT,submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(assignment_id,student_id));
  CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,sender_id INTEGER NOT NULL REFERENCES users(id),recipient_id INTEGER REFERENCES users(id),class_id INTEGER REFERENCES classes(id),body TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY,owner_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL,filename TEXT NOT NULL,stored_path TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS schedule(id INTEGER PRIMARY KEY,class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),start_time TEXT NOT NULL,end_time TEXT NOT NULL,topic TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS announcements(id INTEGER PRIMARY KEY,author_id INTEGER NOT NULL REFERENCES users(id),class_id INTEGER REFERENCES classes(id),title TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS difficulties(id INTEGER PRIMARY KEY,student_id INTEGER NOT NULL REFERENCES users(id),lesson_id INTEGER REFERENCES lessons(id),topic TEXT NOT NULL,question TEXT NOT NULL,explanation TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS lesson_progress(id INTEGER PRIMARY KEY,student_id INTEGER NOT NULL REFERENCES users(id),lesson_id INTEGER NOT NULL REFERENCES lessons(id),status TEXT NOT NULL DEFAULT 'started',score REAL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(student_id,lesson_id));
  CREATE TABLE IF NOT EXISTS exam_questions(id INTEGER PRIMARY KEY,language_code TEXT NOT NULL,question TEXT NOT NULL,options_json TEXT NOT NULL,correct_answer TEXT NOT NULL,explanation TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS exam_answers(id INTEGER PRIMARY KEY,attempt_id INTEGER NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,question_id INTEGER NOT NULL REFERENCES exam_questions(id),answer TEXT NOT NULL,UNIQUE(attempt_id,question_id));
  """)
  # Carefully curated starter lessons, authored for this application. Catalogue status is not a claim of 200 complete courses.
  starters=[
   ("en","English foundations","A1","Greetings, introductions and everyday phrases.",[
    ("Greetings","Hello = bonjour. Good morning = bonjour le matin. My name is… = je m’appelle…","Translate: « My name is Amina. »","Je m’appelle Amina."),
    ("Simple sentences","English basic order: subject + verb + complement. Example: I speak French.","Complete: She ___ English. (speak/speaks)","speaks"),
    ("Questions","Use What for things, Where for places, Who for people. Example: Where are you from?","Choose: ___ are you from? (Where/Who)","Where")]),
   ("fr","Français débutant","A1","Compréhension, phrases simples et vocabulaire de base.",[
    ("Se présenter","Pour se présenter : « Bonjour, je m’appelle Amina. J’habite à Douala. » Le verbe être : je suis, tu es, il/elle est.","Complète : Je ___ élève. (suis/es)","suis"),
    ("Articles","Un/une désignent souvent un nom au singulier. Le/la sont des articles définis : le livre, la maison.","Choisis : ___ maison (le/la).","la"),
    ("Phrase simple","Une phrase simple contient généralement un sujet et un verbe : « Les élèves apprennent. »","Identifie le verbe : « Amina lit un livre. »","lit")]),
   ("es","Español inicial","A1","Saludar, presentarse y construir frases simples.",[
    ("Saludos","Hola = bonjour/salut. Buenos días = bonjour le matin. Me llamo Ana = je m’appelle Ana.","Traduce: « Me llamo Ana ».","Je m’appelle Ana."),
    ("Ser y estar","Ser décrit souvent l’identité : soy estudiante. Estar décrit souvent un état ou une localisation : estoy aquí.","Complète : Yo ___ estudiante. (soy/estoy)","soy"),
    ("Preguntas","Qué = quoi/que, dónde = où, quién = qui. Exemple : ¿Dónde vives? = Où habites-tu ?","Quel mot espagnol signifie « où » ?","dónde")])]
  starter_questions=[
   ("en","Which sentence is correct?",["She speak English.","She speaks English.","She speaking English."],"She speaks English.","With he/she/it, the present simple verb usually takes -s."),
   ("en","What does \"Where are you from?\" mean?",["Où habites-tu ?","D’où viens-tu ?","Quel âge as-tu ?"],"D’où viens-tu ?","Where are you from asks about origin."),
   ("en","Choose the correct article: ___ apple",["a","an","thee"],"an","Use an before a vowel sound."),
   ("fr","Complète : Je ___ élève.",["suis","es","est"],"suis","Avec je, le verbe être se conjugue suis."),
   ("fr","Quel article convient : ___ maison ?",["le","la","un"],"la","Maison est un nom féminin : la maison."),
   ("fr","Dans « Amina lit », quel est le verbe ?",["Amina","lit","aucun"],"lit","Le verbe exprime l’action : lit."),
   ("es","Complète : Yo ___ estudiante.",["soy","eres","es"],"soy","Avec yo, ser se conjugue soy."),
   ("es","Que signifie « hola » ?",["Au revoir","Bonjour/salut","Merci"],"Bonjour/salut","Hola est une salutation."),
   ("es","Quel mot signifie « où » ?",["quién","cuándo","dónde"],"dónde","Dónde demande un lieu.") ]
  for code,q,opts,correct,explain in starter_questions:
   if not db.execute("SELECT id FROM exam_questions WHERE language_code=? AND question=?",(code,q)).fetchone():
    db.execute("INSERT INTO exam_questions(language_code,question,options_json,correct_answer,explanation) VALUES(?,?,?,?,?)",(code,q,json.dumps(opts,ensure_ascii=False),correct,explain))
  for code,title,level,desc,lessons in starters:
   row=db.execute("SELECT id FROM courses WHERE language_code=? AND level=?",(code,level)).fetchone()
   if not row:
    cid=db.execute("INSERT INTO courses(language_code,title,level,description) VALUES(?,?,?,?)",(code,title,level,desc)).lastrowid
    for i,(lt,body,exercise,answer) in enumerate(lessons,1):
     db.execute("INSERT INTO lessons(course_id,title,body,exercise,answer,position) VALUES(?,?,?,?,?,?)",(cid,lt,body,exercise,answer,i))

@app.on_event("startup")
def startup_academy():
 init_academy_tables()

class ClassIn(BaseModel):
 name:str=Field(min_length=2,max_length=100)
 language_code:str=Field(min_length=2,max_length=12)
 level:str=Field(min_length=1,max_length=20)
class JoinClassIn(BaseModel):
 join_code:str=Field(min_length=6,max_length=20)
class AssignmentIn(BaseModel):
 title:str=Field(min_length=2,max_length=160)
 instructions:str=Field(min_length=3,max_length=5000)
 due_at:Optional[str]=None
class SubmissionIn(BaseModel):
 answer:str=Field(min_length=1,max_length=10000)
class MessageIn(BaseModel):
 body:str=Field(min_length=1,max_length=4000)
 recipient_id:Optional[int]=None
 class_id:Optional[int]=None
class AnnouncementIn(BaseModel):
 title:str=Field(min_length=2,max_length=160)
 body:str=Field(min_length=2,max_length=5000)
 class_id:Optional[int]=None
class ScheduleIn(BaseModel):
 weekday:int=Field(ge=0,le=6)
 start_time:str=Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
 end_time:str=Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
 topic:str=Field(min_length=2,max_length=160)
class ProgressIn(BaseModel):
 status:str=Field(pattern=r"^(started|completed|needs_review)$")
 score:Optional[float]=Field(default=None,ge=0,le=100)
class DifficultyIn(BaseModel):
 lesson_id:Optional[int]=None
 topic:str=Field(min_length=2,max_length=120)
 question:str=Field(min_length=2,max_length=2000)
class GradeSubmissionIn(BaseModel):
 score:float=Field(ge=0,le=20)
 feedback:str=Field(min_length=1,max_length=2000)

def is_class_member(db,class_id,user):
 row=db.execute("SELECT c.id,c.teacher_id FROM classes c LEFT JOIN enrollments e ON e.class_id=c.id WHERE c.id=? AND (c.teacher_id=? OR e.student_id=?)",(class_id,user["id"],user["id"])).fetchone()
 return row
@app.get("/api/courses")
def list_courses(language_code:Optional[str]=None,level:Optional[str]=None):
 with db_session() as db:
  sql="SELECT * FROM courses WHERE published=1"; args=[]
  if language_code: sql+=" AND language_code=?"; args.append(language_code)
  if level: sql+=" AND level=?"; args.append(level)
  rows=db.execute(sql+" ORDER BY language_code,level",args).fetchall()
 return {"items":[dict(r) for r in rows]}
@app.get("/api/courses/{course_id}")
def course_detail(course_id:int):
 with db_session() as db:
  course=db.execute("SELECT * FROM courses WHERE id=? AND published=1",(course_id,)).fetchone()
  if not course: raise HTTPException(404,"Cours introuvable")
  lessons=db.execute("SELECT id,title,body,exercise,position FROM lessons WHERE course_id=? ORDER BY position",(course_id,)).fetchall()
 return {"course":dict(course),"lessons":[dict(x) for x in lessons]}
@app.post("/api/lessons/{lesson_id}/progress")
def update_progress(lesson_id:int,payload:ProgressIn,user=Depends(require_roles("student"))):
 with db_session() as db:
  if not db.execute("SELECT id FROM lessons WHERE id=?",(lesson_id,)).fetchone(): raise HTTPException(404,"Leçon introuvable")
  db.execute("INSERT INTO lesson_progress(student_id,lesson_id,status,score,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(student_id,lesson_id) DO UPDATE SET status=excluded.status,score=excluded.score,updated_at=CURRENT_TIMESTAMP",(user["id"],lesson_id,payload.status,payload.score))
 return {"lesson_id":lesson_id,"status":payload.status,"score":payload.score}
@app.get("/api/progress")
def my_progress(user=Depends(require_roles("student"))):
 with db_session() as db:
  rows=db.execute("SELECT p.lesson_id,l.title,c.title AS course,p.status,p.score,p.updated_at FROM lesson_progress p JOIN lessons l ON l.id=p.lesson_id JOIN courses c ON c.id=l.course_id WHERE p.student_id=? ORDER BY p.updated_at DESC",(user["id"],)).fetchall()
  difficulties=db.execute("SELECT topic,question,explanation,created_at FROM difficulties WHERE student_id=? ORDER BY created_at DESC LIMIT 50",(user["id"],)).fetchall()
 return {"lessons":[dict(r) for r in rows],"difficulties":[dict(r) for r in difficulties]}
@app.post("/api/difficulties",status_code=201)
def record_difficulty(payload:DifficultyIn,user=Depends(require_roles("student"))):
 if payload.lesson_id:
  with db_session() as db:
   if not db.execute("SELECT id FROM lessons WHERE id=?",(payload.lesson_id,)).fetchone(): raise HTTPException(404,"Leçon introuvable")
 # Provide a real rule-based explanation for the curated starter lessons; never pretend this is generative AI.
 with db_session() as db:
  cur=db.execute("INSERT INTO difficulties(student_id,lesson_id,topic,question,explanation) VALUES(?,?,?,?,?)",(user["id"],payload.lesson_id,payload.topic,payload.question,"Reprenons étape par étape : identifie d’abord le mot ou la règle qui te bloque, relis l’exemple de la leçon, puis essaie de reformuler avec tes propres mots. Cette difficulté est enregistrée pour tes révisions."))
 return {"id":cur.lastrowid,"saved":True,"explanation":"Reprenons étape par étape : identifie d’abord le mot ou la règle qui te bloque, relis l’exemple de la leçon, puis essaie de reformuler avec tes propres mots. Cette difficulté est enregistrée pour tes révisions."}
@app.post("/api/tutor/explain")
def local_tutor(payload:DifficultyIn,user=Depends(require_roles("student"))):
 # Only loopback Ollama is supported; no cloud API or third-party endpoint.
 prompt=("Tu es un professeur de langue patient. Réponds en français simple. Explique autrement, donne deux exemples, puis un mini-exercice. Ne prétends pas connaître un fait incertain. Sujet: "+payload.topic+"\nQuestion: "+payload.question)
 url=os.getenv("LUCKY_OLLAMA_URL","http://127.0.0.1:11434/api/generate")
 model=os.getenv("LUCKY_OLLAMA_MODEL","qwen2.5:1.5b")
 if not url.startswith(("http://127.0.0.1:","http://localhost:")):
  raise HTTPException(503,"Pour la confidentialité, le tuteur accepte uniquement un serveur IA local.")
 try:
  req=urllib.request.Request(url,data=json.dumps({"model":model,"prompt":prompt,"stream":False}).encode(),headers={"Content-Type":"application/json"})
  with urllib.request.urlopen(req,timeout=25) as resp: data=json.loads(resp.read().decode())
  explanation=data.get("response","").strip()
  if not explanation: raise ValueError("Réponse locale vide")
 except Exception:
  raise HTTPException(503,"Le modèle local n'est pas disponible. Installez et démarrez Ollama localement, puis réessayez.")
 with db_session() as db:
  db.execute("INSERT INTO difficulties(student_id,lesson_id,topic,question,explanation) VALUES(?,?,?,?,?)",(user["id"],payload.lesson_id,payload.topic,payload.question,explanation))
 return {"model":model,"local":True,"explanation":explanation}
@app.post("/api/classes",status_code=201)
def create_class(payload:ClassIn,user=Depends(require_roles("teacher","admin"))):
 code=secrets.token_urlsafe(6).replace("-","").replace("_","")[:8].upper()
 with db_session() as db:
  cur=db.execute("INSERT INTO classes(name,teacher_id,language_code,level,join_code) VALUES(?,?,?,?,?)",(payload.name,user["id"],payload.language_code,payload.level,code))
 return {"id":cur.lastrowid,"name":payload.name,"join_code":code}
@app.get("/api/classes")
def list_classes(user=Depends(current_user)):
 with db_session() as db:
  if user["role"] in ("admin","teacher"):
   rows=db.execute("SELECT c.*,u.full_name AS teacher_name FROM classes c JOIN users u ON u.id=c.teacher_id WHERE c.teacher_id=? OR ?='admin' ORDER BY c.id DESC",(user["id"],user["role"])).fetchall()
  else:
   rows=db.execute("SELECT c.*,u.full_name AS teacher_name FROM classes c JOIN users u ON u.id=c.teacher_id JOIN enrollments e ON e.class_id=c.id WHERE e.student_id=? ORDER BY c.id DESC",(user["id"],)).fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/classes/join")
def join_class(payload:JoinClassIn,user=Depends(require_roles("student"))):
 with db_session() as db:
  row=db.execute("SELECT id,name FROM classes WHERE join_code=?",(payload.join_code.upper(),)).fetchone()
  if not row: raise HTTPException(404,"Code de classe invalide")
  db.execute("INSERT OR IGNORE INTO enrollments(class_id,student_id) VALUES(?,?)",(row["id"],user["id"]))
 return {"class_id":row["id"],"name":row["name"],"joined":True}
@app.post("/api/classes/{class_id}/assignments",status_code=201)
def create_assignment(class_id:int,payload:AssignmentIn,user=Depends(require_roles("teacher","admin"))):
 with db_session() as db:
  cls=db.execute("SELECT * FROM classes WHERE id=?",(class_id,)).fetchone()
  if not cls: raise HTTPException(404,"Classe introuvable")
  if user["role"]!="admin" and cls["teacher_id"]!=user["id"]: raise HTTPException(403,"Cette classe ne vous appartient pas")
  cur=db.execute("INSERT INTO assignments(class_id,title,instructions,due_at,created_by) VALUES(?,?,?,?,?)",(class_id,payload.title,payload.instructions,payload.due_at,user["id"]))
 return {"id":cur.lastrowid,"created":True}
@app.get("/api/classes/{class_id}/assignments")
def list_assignments(class_id:int,user=Depends(current_user)):
 with db_session() as db:
  if not is_class_member(db,class_id,user): raise HTTPException(403,"Accès réservé aux membres de la classe")
  rows=db.execute("SELECT a.*,u.full_name AS teacher_name FROM assignments a JOIN users u ON u.id=a.created_by WHERE a.class_id=? ORDER BY a.created_at DESC",(class_id,)).fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/assignments/{assignment_id}/submit",status_code=201)
def submit_assignment(assignment_id:int,payload:SubmissionIn,user=Depends(require_roles("student"))):
 with db_session() as db:
  a=db.execute("SELECT * FROM assignments WHERE id=?",(assignment_id,)).fetchone()
  if not a: raise HTTPException(404,"Devoir introuvable")
  if not db.execute("SELECT id FROM enrollments WHERE class_id=? AND student_id=?",(a["class_id"],user["id"])).fetchone(): raise HTTPException(403,"Inscription à cette classe requise")
  db.execute("INSERT INTO submissions(assignment_id,student_id,answer) VALUES(?,?,?) ON CONFLICT(assignment_id,student_id) DO UPDATE SET answer=excluded.answer,submitted_at=CURRENT_TIMESTAMP",(assignment_id,user["id"],payload.answer))
 return {"submitted":True}
@app.get("/api/classes/{class_id}/submissions")
def class_submissions(class_id:int,user=Depends(require_roles("teacher","admin"))):
 with db_session() as db:
  cls=db.execute("SELECT * FROM classes WHERE id=?",(class_id,)).fetchone()
  if not cls: raise HTTPException(404,"Classe introuvable")
  if user["role"]!="admin" and cls["teacher_id"]!=user["id"]: raise HTTPException(403,"Accès refusé")
  rows=db.execute("SELECT s.*,u.full_name,a.title AS assignment_title FROM submissions s JOIN users u ON u.id=s.student_id JOIN assignments a ON a.id=s.assignment_id WHERE a.class_id=? ORDER BY s.submitted_at DESC",(class_id,)).fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/submissions/{submission_id}/grade")
def grade_submission(submission_id:int,payload:GradeSubmissionIn,user=Depends(require_roles("teacher","admin"))):
 with db_session() as db:
  row=db.execute("SELECT s.id,c.teacher_id FROM submissions s JOIN assignments a ON a.id=s.assignment_id JOIN classes c ON c.id=a.class_id WHERE s.id=?",(submission_id,)).fetchone()
  if not row: raise HTTPException(404,"Rendu introuvable")
  if user["role"]!="admin" and row["teacher_id"]!=user["id"]: raise HTTPException(403,"Accès refusé")
  db.execute("UPDATE submissions SET score=?,feedback=? WHERE id=?",(payload.score,payload.feedback,submission_id))
  detail=db.execute("SELECT s.student_id,a.title,c.name FROM submissions s JOIN assignments a ON a.id=s.assignment_id JOIN classes c ON c.id=a.class_id WHERE s.id=?",(submission_id,)).fetchone()
  db.execute("INSERT INTO grades(student_id,subject,assessment,score,coefficient) VALUES(?,?,?,?,1)",(detail["student_id"],detail["name"],detail["title"],payload.score))
 return {"graded":True}
@app.post("/api/messages",status_code=201)
def send_message(payload:MessageIn,user=Depends(current_user)):
 if bool(payload.recipient_id)==bool(payload.class_id): raise HTTPException(422,"Choisissez un destinataire privé OU une classe")
 with db_session() as db:
  if payload.recipient_id:
   recipient=db.execute("SELECT id FROM users WHERE id=?",(payload.recipient_id,)).fetchone()
   if not recipient: raise HTTPException(404,"Destinataire introuvable")
  else:
   if not is_class_member(db,payload.class_id,user): raise HTTPException(403,"Accès réservé aux membres de la classe")
  cur=db.execute("INSERT INTO messages(sender_id,recipient_id,class_id,body) VALUES(?,?,?,?)",(user["id"],payload.recipient_id,payload.class_id,payload.body))
 return {"id":cur.lastrowid,"sent":True}
@app.get("/api/messages")
def inbox(class_id:Optional[int]=None,user=Depends(current_user)):
 with db_session() as db:
  if class_id:
   if not is_class_member(db,class_id,user): raise HTTPException(403,"Accès réservé aux membres de la classe")
   rows=db.execute("SELECT m.*,u.full_name AS sender_name FROM messages m JOIN users u ON u.id=m.sender_id WHERE m.class_id=? ORDER BY m.id DESC LIMIT 200",(class_id,)).fetchall()
  else:
   rows=db.execute("SELECT m.*,u.full_name AS sender_name FROM messages m JOIN users u ON u.id=m.sender_id WHERE m.class_id IS NULL AND (m.sender_id=? OR m.recipient_id=?) ORDER BY m.id DESC LIMIT 200",(user["id"],user["id"])).fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/classes/{class_id}/schedule",status_code=201)
def add_schedule(class_id:int,payload:ScheduleIn,user=Depends(require_roles("teacher","admin"))):
 if payload.start_time>=payload.end_time: raise HTTPException(422,"L'heure de fin doit être après l'heure de début")
 with db_session() as db:
  cls=db.execute("SELECT * FROM classes WHERE id=?",(class_id,)).fetchone()
  if not cls: raise HTTPException(404,"Classe introuvable")
  if user["role"]!="admin" and cls["teacher_id"]!=user["id"]: raise HTTPException(403,"Accès refusé")
  cur=db.execute("INSERT INTO schedule(class_id,weekday,start_time,end_time,topic) VALUES(?,?,?,?,?)",(class_id,payload.weekday,payload.start_time,payload.end_time,payload.topic))
 return {"id":cur.lastrowid,"created":True}
@app.get("/api/schedule")
def get_schedule(class_id:Optional[int]=None,user=Depends(current_user)):
 with db_session() as db:
  if class_id is not None:
   if not is_class_member(db,class_id,user): raise HTTPException(403,"Accès refusé")
   rows=db.execute("SELECT * FROM schedule WHERE class_id=? ORDER BY weekday,start_time",(class_id,)).fetchall()
  elif user["role"]=="student":
   rows=db.execute("SELECT s.* FROM schedule s JOIN enrollments e ON e.class_id=s.class_id WHERE e.student_id=? ORDER BY weekday,start_time",(user["id"],)).fetchall()
  elif user["role"]=="teacher":
   rows=db.execute("SELECT s.* FROM schedule s JOIN classes c ON c.id=s.class_id WHERE c.teacher_id=? ORDER BY weekday,start_time",(user["id"],)).fetchall()
  else: rows=db.execute("SELECT * FROM schedule ORDER BY weekday,start_time").fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/announcements",status_code=201)
def create_announcement(payload:AnnouncementIn,user=Depends(require_roles("teacher","admin"))):
 with db_session() as db:
  if payload.class_id:
   cls=db.execute("SELECT * FROM classes WHERE id=?",(payload.class_id,)).fetchone()
   if not cls: raise HTTPException(404,"Classe introuvable")
   if user["role"]!="admin" and cls["teacher_id"]!=user["id"]: raise HTTPException(403,"Accès refusé")
  cur=db.execute("INSERT INTO announcements(author_id,class_id,title,body) VALUES(?,?,?,?)",(user["id"],payload.class_id,payload.title,payload.body))
 return {"id":cur.lastrowid,"created":True}
@app.get("/api/announcements")
def get_announcements(user=Depends(current_user)):
 with db_session() as db:
  if user["role"]=="student":
   rows=db.execute("SELECT a.*,u.full_name AS author FROM announcements a JOIN users u ON u.id=a.author_id WHERE a.class_id IS NULL OR a.class_id IN (SELECT class_id FROM enrollments WHERE student_id=?) ORDER BY a.id DESC LIMIT 100",(user["id"],)).fetchall()
  else: rows=db.execute("SELECT a.*,u.full_name AS author FROM announcements a JOIN users u ON u.id=a.author_id ORDER BY a.id DESC LIMIT 100").fetchall()
 return {"items":[dict(r) for r in rows]}
@app.post("/api/resources",status_code=201)
async def upload_resource(title:str=Query(min_length=2,max_length=160),description:str=Query(default="",max_length=1000),file:UploadFile=File(...),user=Depends(require_roles("teacher","admin"))):
 allowed={".pdf",".txt",".md",".png",".jpg",".jpeg",".webp"}
 name=Path(file.filename or "file").name
 if Path(name).suffix.lower() not in allowed: raise HTTPException(415,"Format autorisé : PDF, TXT, MD, PNG, JPG, WEBP")
 content=await file.read(10*1024*1024+1)
 if len(content)>10*1024*1024: raise HTTPException(413,"Fichier limité à 10 Mo")
 folder=BASE/"uploads"; folder.mkdir(parents=True,exist_ok=True)
 stored=secrets.token_hex(16)+Path(name).suffix.lower()
 (folder/stored).write_bytes(content)
 with db_session() as db:
  cur=db.execute("INSERT INTO resources(owner_id,title,description,filename,stored_path) VALUES(?,?,?,?,?)",(user["id"],title,description,name,stored))
 return {"id":cur.lastrowid,"title":title,"filename":name}
@app.get("/api/resources")
def list_resources(user=Depends(current_user)):
 with db_session() as db:
  rows=db.execute("SELECT id,title,description,filename,created_at FROM resources ORDER BY id DESC LIMIT 100").fetchall()
 return {"items":[dict(r) for r in rows]}
@app.get("/api/resources/{resource_id}/download")
def download_resource(resource_id:int,user=Depends(current_user)):
 with db_session() as db:
  row=db.execute("SELECT * FROM resources WHERE id=?",(resource_id,)).fetchone()
  if not row: raise HTTPException(404,"Ressource introuvable")
  path=BASE/"uploads"/row["stored_path"]
  if not path.is_file(): raise HTTPException(404,"Fichier absent du stockage")
 return FileResponse(path,filename=row["filename"])
@app.get("/api/bulletin.pdf")
def bulletin_pdf(student_id:Optional[int]=None,user=Depends(current_user)):
 if user["role"]=="student":
  if student_id is not None and student_id!=user["id"]: raise HTTPException(403,"Accès refusé")
  target=user["id"]
 elif user["role"] in ("teacher","admin"):
  if student_id is None: raise HTTPException(422,"student_id requis")
  target=student_id
 with db_session() as db:
  student=db.execute("SELECT id,full_name FROM users WHERE id=? AND role='student'",(target,)).fetchone()
  if not student: raise HTTPException(404,"Élève introuvable")
  rows=db.execute("SELECT subject,assessment,score,coefficient FROM grades WHERE student_id=? ORDER BY subject,id",(target,)).fetchall()
 total=sum(r["coefficient"] for r in rows)
 average=sum(r["score"]*r["coefficient"] for r in rows)/total if total else None
 from io import BytesIO
 buff=BytesIO(); pdf=canvas.Canvas(buff,pagesize=A4); width,height=A4
 pdf.setTitle("Bulletin scolaire - Lucky Languages Academy")
 pdf.setFont("Helvetica-Bold",18); pdf.drawString(50,height-55,"LUCKY LANGUAGES ACADEMY")
 pdf.setFont("Helvetica",12); pdf.drawString(50,height-85,"Bulletin de résultats")
 pdf.drawString(50,height-110,"Élève : "+student["full_name"][:80])
 y=height-150; pdf.setFont("Helvetica-Bold",10); pdf.drawString(50,y,"Matière");pdf.drawString(230,y,"Évaluation");pdf.drawString(390,y,"Note");pdf.drawString(445,y,"Coef.")
 y-=20; pdf.setFont("Helvetica",9)
 for r in rows:
  if y<70: pdf.showPage(); y=height-60; pdf.setFont("Helvetica",9)
  pdf.drawString(50,y,str(r["subject"])[:28]);pdf.drawString(230,y,str(r["assessment"])[:28]);pdf.drawRightString(425,y,f'{r["score"]:.2f}/20');pdf.drawRightString(475,y,f'{r["coefficient"]:.2f}');y-=18
 pdf.setFont("Helvetica-Bold",12);pdf.drawString(50,max(45,y-15),"Moyenne pondérée : "+(f"{average:.2f}/20" if average is not None else "Aucune note"))
 pdf.save()
 return Response(buff.getvalue(),media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=bulletin.pdf"})
@app.get("/api/admin/overview")
def admin_overview(user=Depends(require_roles("admin"))):
 with db_session() as db:
  result={}
  for table in ("users","classes","courses","lessons","assignments","submissions","messages","resources","exam_attempts"):
   result[table]=db.execute("SELECT COUNT(*) AS n FROM "+table).fetchone()["n"]
  result["recent_audit"]=[dict(r) for r in db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 30").fetchall()]
 return result


class ExamAnswerIn(BaseModel):
 question_id:int
 answer:str=Field(min_length=1,max_length=500)
@app.get("/api/exams/{attempt_id}/questions")
def exam_questions(attempt_id:int,user=Depends(require_roles("student"))):
 with db_session() as db:
  attempt=db.execute("SELECT * FROM exam_attempts WHERE id=? AND student_id=?",(attempt_id,user["id"])).fetchone()
  if not attempt: raise HTTPException(404,"Tentative introuvable")
  if attempt["status"]!="in_progress": raise HTTPException(409,"Cet examen n'est plus actif")
  started=datetime.fromisoformat(attempt["started_at"]).replace(tzinfo=timezone.utc) if attempt["started_at"] else datetime.now(timezone.utc)
  if (datetime.now(timezone.utc)-started).total_seconds()>1200:
   db.execute("UPDATE exam_attempts SET status='cancelled' WHERE id=?",(attempt_id,))
   raise HTTPException(409,"Temps écoulé : examen annulé, recommencez avec de nouvelles questions.")
  rows=db.execute("SELECT id,question,options_json FROM exam_questions WHERE language_code=?",(attempt["language_code"],)).fetchall()
  rows=sorted(rows,key=lambda r:hashlib.sha256("{}:{}".format(attempt["question_seed"],r["id"]).encode()).hexdigest())[:5]
 return {"attempt_id":attempt_id,"duration_seconds":1200,"questions":[{"id":r["id"],"question":r["question"],"options":json.loads(r["options_json"])} for r in rows]}
@app.post("/api/exams/{attempt_id}/answer")
def answer_exam(attempt_id:int,payload:ExamAnswerIn,user=Depends(require_roles("student"))):
 with db_session() as db:
  attempt=db.execute("SELECT * FROM exam_attempts WHERE id=? AND student_id=?",(attempt_id,user["id"])).fetchone()
  if not attempt: raise HTTPException(404,"Tentative introuvable")
  if attempt["status"]!="in_progress": raise HTTPException(409,"Cet examen n'est plus actif")
  started=datetime.fromisoformat(attempt["started_at"]).replace(tzinfo=timezone.utc)
  if (datetime.now(timezone.utc)-started).total_seconds()>1200:
   db.execute("UPDATE exam_attempts SET status='cancelled' WHERE id=?",(attempt_id,))
   raise HTTPException(409,"Temps écoulé : examen annulé.")
  q=db.execute("SELECT id FROM exam_questions WHERE id=? AND language_code=?",(payload.question_id,attempt["language_code"])).fetchone()
  if not q: raise HTTPException(404,"Question invalide")
  db.execute("INSERT INTO exam_answers(attempt_id,question_id,answer) VALUES(?,?,?) ON CONFLICT(attempt_id,question_id) DO UPDATE SET answer=excluded.answer",(attempt_id,payload.question_id,payload.answer.strip()))
 return {"saved":True}
@app.post("/api/exams/{attempt_id}/submit")
def submit_exam(attempt_id:int,user=Depends(require_roles("student"))):
 with db_session() as db:
  attempt=db.execute("SELECT * FROM exam_attempts WHERE id=? AND student_id=?",(attempt_id,user["id"])).fetchone()
  if not attempt: raise HTTPException(404,"Tentative introuvable")
  if attempt["status"]!="in_progress": raise HTTPException(409,"Cet examen n'est plus actif")
  started=datetime.fromisoformat(attempt["started_at"]).replace(tzinfo=timezone.utc)
  if (datetime.now(timezone.utc)-started).total_seconds()>1200:
   db.execute("UPDATE exam_attempts SET status='cancelled' WHERE id=?",(attempt_id,))
   raise HTTPException(409,"Temps écoulé : examen annulé.")
  qs=db.execute("SELECT id,correct_answer,explanation FROM exam_questions WHERE language_code=?",(attempt["language_code"],)).fetchall()
  qs=sorted(qs,key=lambda r:hashlib.sha256("{}:{}".format(attempt["question_seed"],r["id"]).encode()).hexdigest())[:5]
  answers=db.execute("SELECT question_id,answer FROM exam_answers WHERE attempt_id=?",(attempt_id,)).fetchall()
  given={r["question_id"]:r["answer"].strip().casefold() for r in answers}
  correct=sum(1 for q in qs if given.get(q["id"])==q["correct_answer"].strip().casefold())
  count=len(qs); score=round((correct/count)*20,2) if count else 0
  db.execute("UPDATE exam_attempts SET status='submitted' WHERE id=?",(attempt_id,))
  db.execute("INSERT INTO grades(student_id,subject,assessment,score,coefficient) VALUES(?,?,?,?,1)",(user["id"],"Langue "+attempt["language_code"].upper(),"Examen "+str(attempt_id),score))
 return {"attempt_id":attempt_id,"status":"submitted","correct":correct,"total":count,"score_out_of_20":score}

@app.get("/sw.js", include_in_schema=False)
def service_worker():
 return Response((BASE/"static"/"sw.js").read_text(encoding="utf-8"),media_type="application/javascript",headers={"Service-Worker-Allowed":"/","Cache-Control":"no-cache"})

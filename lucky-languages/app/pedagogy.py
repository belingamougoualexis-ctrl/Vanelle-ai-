"""Pedagogical engine for Lucky Languages Academy.

Offline-first original practice content, language-specific activity templates, and an
optional local Ollama generator. External exam links are references only; copyrighted
exam papers are never copied into the built-in bank.
"""
from __future__ import annotations

import json
import logging
import os
import random
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/pedagogy", tags=["pedagogy"])
logger = logging.getLogger(__name__)

LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2", "beginner", "primary", "secondary", "be_pc"}
LANGUAGE_METHODS: dict[str, dict[str, Any]] = {
    "en": {"name": "English", "skills": ["vocabulary", "grammar", "reading", "listening", "writing", "speaking"], "method": "Short contextual examples, spaced vocabulary, grammar in sentences, comprehension and guided production."},
    "fr": {"name": "Français", "skills": ["vocabulaire", "grammaire", "lecture", "écoute", "orthographe", "rédaction", "oral"], "method": "Conjugaison et accords en contexte, compréhension, dictée et production écrite guidée."},
    "es": {"name": "Español", "skills": ["vocabulario", "gramática", "lectura", "escucha", "escritura", "oral"], "method": "Vocabulario contextual, conjugación, comprensión y diálogos progresivos."},
    "zh": {"name": "中文 / Mandarin", "skills": ["caractère", "signification", "pinyin", "tons", "reconnaissance", "écriture", "phrase"], "method": "Pour chaque caractère : forme, sens, pinyin, ton, exemple, reconnaissance et rappel écrit. L'écriture manuscrite est saisie ou auto-évaluée; l'application ne prétend pas reconnaître le tracé sans outil spécialisé."},
    "ja": {"name": "日本語", "skills": ["hiragana", "katakana", "kanji", "sens", "lecture", "écriture"], "method": "Distinguer kana et kanji, apprendre lecture et sens, puis pratiquer rappel et phrases."},
    "ko": {"name": "한국어", "skills": ["hangeul", "syllabes", "vocabulaire", "lecture", "écriture"], "method": "Composer les blocs syllabiques du hangeul, prononcer, lire et écrire des mots."},
    "ar": {"name": "العربية", "skills": ["alphabet", "formes liées", "voyelles", "lecture", "écriture"], "method": "Lire de droite à gauche, reconnaître les formes contextuelles et pratiquer les lettres liées."},
    "ru": {"name": "Русский", "skills": ["cyrillique", "prononciation", "vocabulaire", "grammaire", "lecture"], "method": "Apprendre l'alphabet cyrillique, les sons, puis déclinaisons et phrases graduées."},
    "pt": {"name": "Português", "skills": ["vocabulário", "gramática", "leitura", "escuta", "escrita"], "method": "Vocabulaire contextualisé, conjugaison et compréhension progressive."},
    "de": {"name": "Deutsch", "skills": ["Wortschatz", "Grammatik", "Lesen", "Hören", "Schreiben"], "method": "Vocabulaire en contexte, ordre des mots, genres et cas dans des phrases."},
}

EXAM_RESOURCES = [
    {"id":"delf-fei", "language_code":"fr", "name":"France Éducation international — DELF/DALF/TCF examples", "url":"https://www.france-education-international.fr/", "kind":"official_examples", "reuse":"Lire les conditions de chaque document; lien seulement, ne pas recopier sans autorisation.", "levels":["A1","A2","B1","B2","C1","C2"]},
    {"id":"dele-cervantes", "language_code":"es", "name":"Instituto Cervantes — DELE exam preparation", "url":"https://examenes.cervantes.es/", "kind":"official_examples", "reuse":"Vérifier la licence et les conditions par document; lien seulement par défaut.", "levels":["A1","A2","B1","B2","C1","C2"]},
    {"id":"cambridge-english", "language_code":"en", "name":"Cambridge English — preparation and sample papers", "url":"https://www.cambridgeenglish.org/exams-and-tests/", "kind":"official_examples", "reuse":"Respecter les droits et conditions d'utilisation de chaque ressource.", "levels":["A1","A2","B1","B2","C1","C2"]},
    {"id":"hsk-chinese", "language_code":"zh", "name":"Chinese Test / HSK — official information", "url":"https://www.chinesetest.cn/", "kind":"official_reference", "reuse":"Utiliser le site comme référence; les questions intégrées ci-dessous sont originales.", "levels":["A1","A2","B1","B2"]},
    {"id":"goethe", "language_code":"de", "name":"Goethe-Institut — German exam practice", "url":"https://www.goethe.de/", "kind":"official_examples", "reuse":"Vérifier les conditions du document avant toute reproduction.", "levels":["A1","A2","B1","B2","C1","C2"]},
]

# Original questions authored for this app, not copied from external exam papers.
BANK: dict[str, list[dict[str, Any]]] = {
 "en": [
  {"level":"A1","skill":"vocabulary","question":"Choose the correct meaning of 'apple'.","options":["Une pomme","Une maison","Un livre"],"answer":"Une pomme","explanation":"'Apple' signifie « pomme » en français.","source":"original"},
  {"level":"A1","skill":"grammar","question":"Complete: She ___ a student.","options":["am","is","are"],"answer":"is","explanation":"Avec « she », on utilise « is » au présent du verbe be.","source":"original"},
  {"level":"A2","skill":"grammar","question":"Yesterday, we ___ to school.","options":["go","went","gone"],"answer":"went","explanation":"« Yesterday » indique le passé; le prétérit de go est went.","source":"original"},
  {"level":"B1","skill":"grammar","question":"If I had more time, I ___ another language.","options":["learn","would learn","will learned"],"answer":"would learn","explanation":"Le second conditionnel utilise if + prétérit, puis would + base verbale.","source":"original"},
 ],
 "fr": [
  {"level":"A1","skill":"vocabulaire","question":"Que signifie « bonjour » en anglais ?","options":["Good morning / Hello","Good night","Goodbye"],"answer":"Good morning / Hello","explanation":"« Bonjour » s'emploie pour saluer pendant la journée.","source":"original"},
  {"level":"A1","skill":"grammaire","question":"Complète : Nous ___ à l'école.","options":["suis","sommes","êtes"],"answer":"sommes","explanation":"Avec « nous », le verbe être se conjugue « nous sommes ».","source":"original"},
  {"level":"A2","skill":"orthographe","question":"Choisis la phrase correctement accordée.","options":["Les filles sont arrivées.","Les filles sont arrivé.","Les filles est arrivées."],"answer":"Les filles sont arrivées.","explanation":"Avec être, le participe passé s'accorde avec le sujet féminin pluriel.","source":"original"},
  {"level":"B1","skill":"grammaire","question":"Si j'avais étudié, je ___ mieux réussi.","options":["aurais","avais","ai"],"answer":"aurais","explanation":"La phrase exprime une condition passée irréelle : si + plus-que-parfait, conditionnel passé.","source":"original"},
 ],
 "es": [
  {"level":"A1","skill":"vocabulario","question":"¿Qué significa « gracias » en francés?","options":["Merci","Bonjour","Au revoir"],"answer":"Merci","explanation":"« Gracias » significa « merci ».","source":"original"},
  {"level":"A1","skill":"gramática","question":"Completa: Yo ___ estudiante.","options":["soy","eres","son"],"answer":"soy","explanation":"Avec « yo », le verbe ser se conjugue « soy ».","source":"original"},
  {"level":"A2","skill":"gramática","question":"Ayer nosotros ___ al mercado.","options":["vamos","fuimos","iremos"],"answer":"fuimos","explanation":"« Ayer » appelle ici le passé simple de ir : fuimos.","source":"original"},
 ],
 "zh": [
  {"level":"A1","skill":"caractère et sens","question":"Que signifie le caractère 人 ?","options":["Personne / être humain","Eau","Montagne"],"answer":"Personne / être humain","explanation":"人 signifie personne ou être humain. Pinyin : rén, 2e ton. Trace les deux traits dans l'ordre appris puis écris 人 de mémoire.","character":"人","pinyin":"rén","meaning":"personne; être humain","stroke_count":2,"source":"original"},
  {"level":"A1","skill":"caractère et sens","question":"Associe 水 à son sens.","options":["Eau","Feu","Bois"],"answer":"Eau","explanation":"水 signifie eau. Pinyin : shuǐ, 3e ton. Observe la forme, prononce le mot et écris le caractère plusieurs fois.","character":"水","pinyin":"shuǐ","meaning":"eau","stroke_count":4,"source":"original"},
  {"level":"A1","skill":"vocabulaire","question":"Quel mot signifie « élève / étudiant » ?","options":["学生 (xuésheng)","老师 (lǎoshī)","朋友 (péngyou)"],"answer":"学生 (xuésheng)","explanation":"学生 signifie élève/étudiant; 老师 signifie professeur et 朋友 signifie ami.","character":"学生","pinyin":"xuésheng","meaning":"élève; étudiant","source":"original"},
  {"level":"A1","skill":"phrase","question":"Que signifie 你好 (nǐ hǎo) ?","options":["Bonjour","Merci","Au revoir"],"answer":"Bonjour","explanation":"你好 est une salutation courante : nǐ (3e ton) + hǎo (3e ton, souvent réalisé avec changement de ton en parole).","character":"你好","pinyin":"nǐ hǎo","meaning":"bonjour","source":"original"},
 ],
 "ja": [
  {"level":"A1","skill":"kana","question":"Que représente あ en hiragana ?","options":["Le son a","Le son ka","Le son mi"],"answer":"Le son a","explanation":"あ se lit « a ». Entraîne la reconnaissance puis l'écriture.","source":"original"},
 ],
 "ko": [
  {"level":"A1","skill":"hangeul","question":"Quelle syllabe représente 한 ?","options":["han","dal","min"],"answer":"han","explanation":"한 se compose de ㅎ (h), ㅏ (a) et ㄴ (n) dans un bloc syllabique.","source":"original"},
 ],
 "de": [
  {"level":"A1","skill":"Wortschatz","question":"Was bedeutet „Guten Morgen“?","options":["Bonjour le matin","Bonne nuit","Au revoir"],"answer":"Bonjour le matin","explanation":"« Guten Morgen » est une salutation utilisée le matin.","source":"original"},
 ],
 "pt": [
  {"level":"A1","skill":"vocabulário","question":"Que signifie « obrigado » en français ?","options":["Merci","Pardon","Bonsoir"],"answer":"Merci","explanation":"« Obrigado » est généralement dit par un locuteur masculin; « obrigada » par une locutrice.","source":"original"},
 ],
 "ar": [
  {"level":"A1","skill":"alphabet","question":"Dans quel sens l'arabe s'écrit-il habituellement ?","options":["De droite à gauche","De gauche à droite","De haut en bas"],"answer":"De droite à gauche","explanation":"L'arabe se lit et s'écrit de droite à gauche; les formes de lettres peuvent changer selon leur position.","source":"original"},
 ],
 "ru": [
  {"level":"A1","skill":"alphabet","question":"Quelle lettre cyrillique correspond au son « m » ?","options":["М","Р","Н"],"answer":"М","explanation":"М se prononce comme m dans beaucoup de mots russes; Р se prononce r et Н se prononce n.","source":"original"},
 ],
}

class GenerateRequest(BaseModel):
    language_code: str = Field(min_length=2, max_length=12)
    level: str = "A1"
    skill: str = "mixed"
    count: int = Field(default=5, ge=1, le=12)
    topic: str = Field(default="everyday life", max_length=160)
    learner_language: str = "fr"
    wrong_answers: list[str] = Field(default_factory=list, max_length=20)
    use_local_ai: bool = False

class GradeRequest(BaseModel):
    language_code: str
    question: dict[str, Any]
    answer: str = Field(max_length=2000)

def _level_rank(level: str) -> int:
    return {"A1":1,"A2":2,"B1":3,"B2":4,"C1":5,"C2":6,"beginner":1,"primary":1,"secondary":2,"be_pc":2}.get(level.lower(),1)

def _local_ai(req: GenerateRequest) -> list[dict[str, Any]] | None:
    endpoint = os.getenv("LUCKY_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    model = os.getenv("LUCKY_PEDAGOGY_MODEL", "qwen2.5:1.5b")
    method = LANGUAGE_METHODS.get(req.language_code, {"name":req.language_code, "method":"Progressive vocabulary and sentence practice."})
    system = ("You are Lucky Languages Academy's careful language teacher and assessment author. "
              "Generate original educational questions only; never claim they are official exam questions. "
              "Match the requested level, use valid answers, include one concise explanation, and return ONLY a JSON array. "
              "Each object must have question, options (3 or 4 strings), answer (exactly one option), explanation, skill. "
              "For Chinese use actual Chinese characters and include character, pinyin, meaning, and writing_prompt when relevant. "
              "Never invent an external citation. If uncertain, use simple reliable material.")
    prompt = {"system_role":system,"target_language":method["name"],"level":req.level,"skill":req.skill,
              "topic":req.topic,"learner_language":req.learner_language,"language_method":method["method"],
              "learner_difficulties":req.wrong_answers,"count":req.count}
    payload = json.dumps({"model":model,"prompt":json.dumps(prompt,ensure_ascii=False),"stream":False,"format":"json","options":{"num_predict":384,"temperature":0.2}},ensure_ascii=False).encode()
    request = urllib.request.Request(endpoint,data=payload,headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data=json.loads(response.read().decode())
        raw=data.get("response","[]")
        # Ollama's JSON mode can return either an array, a {"questions": [...]} object,
        # or (with smaller models) a single question object. Accept only validated items.
        if isinstance(raw, (dict, list)):
            parsed=raw
        else:
            raw=str(raw).strip()
            if raw.startswith("```"):
                raw=raw.split("\n",1)[-1]
                if raw.endswith("```"):
                    raw=raw[:-3].strip()
            parsed=json.loads(raw)
        if isinstance(parsed,dict):
            if isinstance(parsed.get("questions"),list):
                parsed=parsed["questions"]
            elif parsed.get("question"):
                parsed=[parsed]
            else:
                parsed=[]
        if not isinstance(parsed,list): return None
        valid=[]
        for item in parsed[:req.count]:
            if not isinstance(item,dict): continue
            q=str(item.get("question","")).strip()
            opts=item.get("options",[])
            ans=str(item.get("answer","")).strip()
            if isinstance(opts, str):
                opts=[part.strip() for part in opts.split("|") if part.strip()]
            if not isinstance(opts,list):
                continue
            opts=[str(option).strip() for option in opts if str(option).strip()]
            # Repair minor answer casing/whitespace mismatches, but never invent an answer.
            matching=next((option for option in opts if option.casefold()==ans.casefold()),None)
            if matching:
                ans=matching
            if q and 2 <= len(opts) <= 5 and ans in opts:
                item.update({"question":q,"options":opts,"answer":ans,
                             "explanation":str(item.get("explanation","")).strip() or "Relis la règle et explique pourquoi cette réponse convient.",
                             "skill":str(item.get("skill") or req.skill),
                             "source":"ai_generated_unverified"})
                if req.language_code=="zh" and not all(item.get(k) for k in ("pinyin","meaning")):
                    continue
                valid.append(item)
        if not valid:
            logger.warning("Local model %s returned no schema-valid questions for language=%s level=%s", model, req.language_code, req.level)
            return None
        return valid
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Local model request/parse failed (%s): %s", type(exc).__name__, exc)
        return None

def generate_questions(req: GenerateRequest) -> dict[str, Any]:
    code=req.language_code.lower()
    if req.level not in LEVELS:
        raise HTTPException(422, "Niveau invalide. Choisissez A1–C2, débutant, primaire, secondaire ou BEPC.")
    method=LANGUAGE_METHODS.get(code, {"name":code,"skills":["vocabulaire","grammaire","lecture","écriture"],"method":"Vocabulaire contextualisé, exemples courts, rappel actif et révision espacée."})
    generated=_local_ai(req) if req.use_local_ai else None
    bank=BANK.get(code, [])
    eligible=[q for q in bank if _level_rank(q.get("level","A1")) <= _level_rank(req.level)]
    # Keep at least a small valid exercise set for supported starter languages.
    if not generated:
        pool=eligible or bank
        if not pool:
            pool=[{"level":req.level,"skill":req.skill if req.skill!="mixed" else method["skills"][0],
                   "question":f"Crée une phrase simple dans la langue {method['name']} avec le thème « {req.topic} ».",
                   "options":["Je peux le faire","Je ne sais pas encore","Je veux un exemple"],"answer":"Je peux le faire",
                   "explanation":"Exercice de démarrage original : écris ensuite ta propre phrase et compare-la à un exemple fiable.",
                   "source":"original_template","writing_prompt":"Écris une phrase puis demande une correction au professeur."}]
        rng=random.Random(f"{code}|{req.level}|{req.skill}|{req.topic}|{','.join(req.wrong_answers)}")
        generated=[dict(q) for q in (pool if len(pool)>=req.count else pool* ((req.count+len(pool)-1)//len(pool)))[:req.count]]
        if code=="zh":
            for q in generated:
                q.setdefault("writing_prompt",f"Écris {q.get('character', 'le caractère étudié')} de mémoire, puis compare les traits avec le modèle.")
    return {"language_code":code,"language":method["name"],"level":req.level,"skill":req.skill,
            "teaching_method":method["method"],"questions":generated[:req.count],
            "generator":"ollama_local" if generated and generated[0].get("source")=="ai_generated_unverified" else "reviewed_original_bank_or_template",
            "ai_status":"generated_unverified" if generated and generated[0].get("source")=="ai_generated_unverified" else "fallback_offline",
            "quality_note":"Les questions IA sont vérifiées au format et à la cohérence de réponse, mais restent à réviser par un enseignant avant un examen noté.",
            "exam_resources":[x for x in EXAM_RESOURCES if x["language_code"]==code]}

@router.get("/languages")
def pedagogy_languages():
    return {"items":[{"code":code,**method,"available_in_question_bank":code in BANK} for code,method in LANGUAGE_METHODS.items()],
            "supported_question_banks":sorted(BANK.keys()),"note":"Le catalogue de langues ne signifie pas que toutes possèdent un cours complet."}

@router.get("/exam-resources")
def exam_resources(language_code: str | None = None):
    items=EXAM_RESOURCES if not language_code else [x for x in EXAM_RESOURCES if x["language_code"]==language_code.lower()]
    return {"items":items,"policy":"Liens vers des ressources officielles; aucune reproduction de sujets protégés sans autorisation."}

@router.post("/generate")
def generate(req: GenerateRequest):
    return generate_questions(req)

@router.post("/grade")
def grade(req: GradeRequest):
    question=req.question
    expected=str(question.get("answer","")).strip()
    submitted=req.answer.strip()
    if not expected:
        raise HTTPException(422,"Cette question ne contient pas de réponse de référence.")
    # For Chinese and other logographic/script exercises, normalize Unicode but do not
    # pretend to assess handwriting or pronunciation from plain text.
    normalize=lambda s:" ".join(s.casefold().split())
    correct=normalize(submitted)==normalize(expected)
    return {"correct":correct,"expected_answer":expected,"explanation":str(question.get("explanation","")),
            "feedback":"Bonne réponse !" if correct else "Pas encore. Lis l'explication puis réessaie.",
            "assessment_limit":"La saisie de texte vérifie le contenu, pas la qualité du tracé manuscrit ni la prononciation."}

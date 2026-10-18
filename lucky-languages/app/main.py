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
app = FastAPI(title="LinguaBloom Academy API", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
LANGUAGES = [
 {"code":"en","name":"English","status":"catalogue"},
 {"code":"fr","name":"Français","status":"catalogue"},
 {"code":"es","name":"Español","status":"catalogue"},
 {"code":"de","name":"Deutsch","status":"catalogue"},
 {"code":"pt","name":"Português","status":"catalogue"},
 {"code":"it","name":"Italiano","status":"catalogue"},
 {"code":"nl","name":"Nederlands","status":"catalogue"},
 {"code":"sv","name":"Svenska","status":"catalogue"},
 {"code":"no","name":"Norsk","status":"catalogue"},
 {"code":"da","name":"Dansk","status":"catalogue"},
 {"code":"fi","name":"Suomi","status":"catalogue"},
 {"code":"is","name":"Íslenska","status":"catalogue"},
 {"code":"ga","name":"Gaeilge","status":"catalogue"},
 {"code":"cy","name":"Cymraeg","status":"catalogue"},
 {"code":"gd","name":"Gàidhlig","status":"catalogue"},
 {"code":"eu","name":"Euskara","status":"catalogue"},
 {"code":"ca","name":"Català","status":"catalogue"},
 {"code":"gl","name":"Galego","status":"catalogue"},
 {"code":"ro","name":"Română","status":"catalogue"},
 {"code":"hu","name":"Magyar","status":"catalogue"},
 {"code":"pl","name":"Polski","status":"catalogue"},
 {"code":"cs","name":"Čeština","status":"catalogue"},
 {"code":"sk","name":"Slovenčina","status":"catalogue"},
 {"code":"sl","name":"Slovenščina","status":"catalogue"},
 {"code":"hr","name":"Hrvatski","status":"catalogue"},
 {"code":"sr","name":"Srpski","status":"catalogue"},
 {"code":"bs","name":"Bosanski","status":"catalogue"},
 {"code":"bg","name":"Български","status":"catalogue"},
 {"code":"mk","name":"Македонски","status":"catalogue"},
 {"code":"sq","name":"Shqip","status":"catalogue"},
 {"code":"el","name":"Ελληνικά","status":"catalogue"},
 {"code":"ru","name":"Русский","status":"catalogue"},
 {"code":"uk","name":"Українська","status":"catalogue"},
 {"code":"be","name":"Беларуская","status":"catalogue"},
 {"code":"lt","name":"Lietuvių","status":"catalogue"},
 {"code":"lv","name":"Latviešu","status":"catalogue"},
 {"code":"et","name":"Eesti","status":"catalogue"},
 {"code":"mt","name":"Malti","status":"catalogue"},
 {"code":"lb","name":"Lëtzebuergesch","status":"catalogue"},
 {"code":"yi","name":"ייִדיש","status":"catalogue"},
 {"code":"he","name":"עברית","status":"catalogue"},
 {"code":"ar","name":"العربية","status":"catalogue"},
 {"code":"fa","name":"فارسی","status":"catalogue"},
 {"code":"ur","name":"اردو","status":"catalogue"},
 {"code":"ps","name":"پښتو","status":"catalogue"},
 {"code":"ku","name":"Kurdî","status":"catalogue"},
 {"code":"ckb","name":"کوردیی ناوەندی","status":"catalogue"},
 {"code":"tr","name":"Türkçe","status":"catalogue"},
 {"code":"az","name":"Azərbaycanca","status":"catalogue"},
 {"code":"hy","name":"Հայերեն","status":"catalogue"},
 {"code":"ka","name":"ქართული","status":"catalogue"},
 {"code":"kk","name":"Қазақша","status":"catalogue"},
 {"code":"ky","name":"Кыргызча","status":"catalogue"},
 {"code":"uz","name":"Oʻzbekcha","status":"catalogue"},
 {"code":"tk","name":"Türkmençe","status":"catalogue"},
 {"code":"tg","name":"Тоҷикӣ","status":"catalogue"},
 {"code":"mn","name":"Монгол","status":"catalogue"},
 {"code":"zh","name":"中文","status":"catalogue"},
 {"code":"yue","name":"粵語","status":"catalogue"},
 {"code":"ja","name":"日本語","status":"catalogue"},
 {"code":"ko","name":"한국어","status":"catalogue"},
 {"code":"vi","name":"Tiếng Việt","status":"catalogue"},
 {"code":"th","name":"ไทย","status":"catalogue"},
 {"code":"lo","name":"ລາວ","status":"catalogue"},
 {"code":"km","name":"ខ្មែរ","status":"catalogue"},
 {"code":"my","name":"မြန်မာ","status":"catalogue"},
 {"code":"id","name":"Bahasa Indonesia","status":"catalogue"},
 {"code":"ms","name":"Bahasa Melayu","status":"catalogue"},
 {"code":"jv","name":"Basa Jawa","status":"catalogue"},
 {"code":"su","name":"Basa Sunda","status":"catalogue"},
 {"code":"tl","name":"Filipino","status":"catalogue"},
 {"code":"ceb","name":"Cebuano","status":"catalogue"},
 {"code":"ilo","name":"Ilokano","status":"catalogue"},
 {"code":"war","name":"Waray","status":"catalogue"},
 {"code":"hil","name":"Hiligaynon","status":"catalogue"},
 {"code":"bcl","name":"Bikol","status":"catalogue"},
 {"code":"pam","name":"Kapampangan","status":"catalogue"},
 {"code":"bjn","name":"Banjar","status":"catalogue"},
 {"code":"min","name":"Minangkabau","status":"catalogue"},
 {"code":"ace","name":"Acehnese","status":"catalogue"},
 {"code":"tet","name":"Tetum","status":"catalogue"},
 {"code":"mi","name":"Māori","status":"catalogue"},
 {"code":"sm","name":"Gagana Sāmoa","status":"catalogue"},
 {"code":"to","name":"Lea faka-Tonga","status":"catalogue"},
 {"code":"fj","name":"Vosa Vakaviti","status":"catalogue"},
 {"code":"ty","name":"Reo Tahiti","status":"catalogue"},
 {"code":"haw","name":"ʻŌlelo Hawaiʻi","status":"catalogue"},
 {"code":"la","name":"Latina","status":"catalogue"},
 {"code":"eo","name":"Esperanto","status":"catalogue"},
 {"code":"ia","name":"Interlingua","status":"catalogue"},
 {"code":"vo","name":"Volapük","status":"catalogue"},
 {"code":"sw","name":"Kiswahili","status":"catalogue"},
 {"code":"ha","name":"Hausa","status":"catalogue"},
 {"code":"yo","name":"Yorùbá","status":"catalogue"},
 {"code":"ig","name":"Igbo","status":"catalogue"},
 {"code":"pcm","name":"Nigerian Pidgin","status":"catalogue"},
 {"code":"ff","name":"Fulfulde","status":"catalogue"},
 {"code":"wo","name":"Wolof","status":"catalogue"},
 {"code":"bm","name":"Bamanankan","status":"catalogue"},
 {"code":"ln","name":"Lingála","status":"catalogue"},
 {"code":"kg","name":"Kikongo","status":"catalogue"},
 {"code":"rw","name":"Ikinyarwanda","status":"catalogue"},
 {"code":"rn","name":"Ikirundi","status":"catalogue"},
 {"code":"lg","name":"Luganda","status":"catalogue"},
 {"code":"ny","name":"Chichewa","status":"catalogue"},
 {"code":"sn","name":"chiShona","status":"catalogue"},
 {"code":"nd","name":"isiNdebele","status":"catalogue"},
 {"code":"zu","name":"isiZulu","status":"catalogue"},
 {"code":"xh","name":"isiXhosa","status":"catalogue"},
 {"code":"st","name":"Sesotho","status":"catalogue"},
 {"code":"tn","name":"Setswana","status":"catalogue"},
 {"code":"ts","name":"Xitsonga","status":"catalogue"},
 {"code":"ss","name":"siSwati","status":"catalogue"},
 {"code":"ve","name":"Tshivenḓa","status":"catalogue"},
 {"code":"nso","name":"Sepedi","status":"catalogue"},
 {"code":"am","name":"አማርኛ","status":"catalogue"},
 {"code":"ti","name":"ትግርኛ","status":"catalogue"},
 {"code":"om","name":"Afaan Oromoo","status":"catalogue"},
 {"code":"so","name":"Soomaali","status":"catalogue"},
 {"code":"or","name":"ଓଡ଼ିଆ","status":"catalogue"},
 {"code":"hi","name":"हिन्दी","status":"catalogue"},
 {"code":"bn","name":"বাংলা","status":"catalogue"},
 {"code":"pa","name":"ਪੰਜਾਬੀ","status":"catalogue"},
 {"code":"gu","name":"ગુજરાતી","status":"catalogue"},
 {"code":"mr","name":"मराठी","status":"catalogue"},
 {"code":"ne","name":"नेपाली","status":"catalogue"},
 {"code":"si","name":"සිංහල","status":"catalogue"},
 {"code":"ta","name":"தமிழ்","status":"catalogue"},
 {"code":"te","name":"తెలుగు","status":"catalogue"},
 {"code":"kn","name":"ಕನ್ನಡ","status":"catalogue"},
 {"code":"ml","name":"മലയാളം","status":"catalogue"},
 {"code":"as","name":"অসমীয়া","status":"catalogue"},
 {"code":"sa","name":"संस्कृतम्","status":"catalogue"},
 {"code":"sd","name":"سنڌي","status":"catalogue"},
 {"code":"ks","name":"कॉशुर","status":"catalogue"},
 {"code":"kok","name":"कोंकणी","status":"catalogue"},
 {"code":"doi","name":"डोगरी","status":"catalogue"},
 {"code":"mni","name":"মৈতৈলোন্","status":"catalogue"},
 {"code":"brx","name":"बड़ो","status":"catalogue"},
 {"code":"sat","name":"Santali","status":"catalogue"},
 {"code":"bh","name":"भोजपुरी","status":"catalogue"},
 {"code":"awa","name":"अवधी","status":"catalogue"},
 {"code":"mag","name":"मगही","status":"catalogue"},
 {"code":"mai","name":"मैथिली","status":"catalogue"},
 {"code":"raj","name":"राजस्थानी","status":"catalogue"},
 {"code":"hne","name":"छत्तीसगढ़ी","status":"catalogue"},
 {"code":"bho","name":"भोजपुरी","status":"catalogue"},
 {"code":"lmo","name":"Lombard","status":"catalogue"},
 {"code":"sc","name":"Sardu","status":"catalogue"},
 {"code":"co","name":"Corsu","status":"catalogue"},
 {"code":"fur","name":"Furlan","status":"catalogue"},
 {"code":"vec","name":"Vèneto","status":"catalogue"},
 {"code":"pms","name":"Piemontèis","status":"catalogue"},
 {"code":"nap","name":"Napoletano","status":"catalogue"},
 {"code":"scn","name":"Sicilianu","status":"catalogue"},
 {"code":"an","name":"Aragonés","status":"catalogue"},
 {"code":"ast","name":"Asturianu","status":"catalogue"},
 {"code":"oc","name":"Occitan","status":"catalogue"},
 {"code":"rm","name":"Rumantsch","status":"catalogue"},
 {"code":"wa","name":"Walon","status":"catalogue"},
 {"code":"fo","name":"Føroyskt","status":"catalogue"},
 {"code":"se","name":"Davvisámegiella","status":"catalogue"},
 {"code":"sma","name":"Åarjelsaemien","status":"catalogue"},
 {"code":"smi","name":"Sámi","status":"catalogue"},
 {"code":"qu","name":"Runa Simi","status":"catalogue"},
 {"code":"ay","name":"Aymar aru","status":"catalogue"},
 {"code":"gn","name":"Avañe'ẽ","status":"catalogue"},
 {"code":"nah","name":"Nāhuatl","status":"catalogue"},
 {"code":"yua","name":"Maaya t'aan","status":"catalogue"},
 {"code":"ht","name":"Kreyòl ayisyen","status":"catalogue"},
 {"code":"pap","name":"Papiamentu","status":"catalogue"},
 {"code":"jam","name":"Jamaican Patois","status":"catalogue"},
 {"code":"gcr","name":"Guianese Creole","status":"catalogue"},
 {"code":"kea","name":"Kriolu","status":"catalogue"},
 {"code":"crs","name":"Seselwa","status":"catalogue"},
 {"code":"mfe","name":"Kreol Morisien","status":"catalogue"},
 {"code":"sg","name":"Sängö","status":"catalogue"},
 {"code":"ady","name":"Адыгабзэ","status":"catalogue"},
 {"code":"ab","name":"Аҧсуа","status":"catalogue"},
 {"code":"os","name":"Ирон","status":"catalogue"},
 {"code":"ce","name":"Нохчийн","status":"catalogue"},
 {"code":"av","name":"МагӀарул мацӀ","status":"catalogue"},
 {"code":"lez","name":"Лезги чӀал","status":"catalogue"},
 {"code":"sah","name":"Саха тыла","status":"catalogue"},
 {"code":"tyv","name":"Тыва дыл","status":"catalogue"},
 {"code":"ba","name":"Башҡортса","status":"catalogue"},
 {"code":"tt","name":"Татарча","status":"catalogue"},
 {"code":"cv","name":"Чӑвашла","status":"catalogue"},
 {"code":"udm","name":"Удмурт кыл","status":"catalogue"},
 {"code":"mhr","name":"Олык марий","status":"catalogue"},
 {"code":"myv","name":"Эрзянь кель","status":"catalogue"},
 {"code":"koi","name":"Перем коми","status":"catalogue"},
 {"code":"kom","name":"Коми","status":"catalogue"},
 {"code":"kv","name":"Коми кыв","status":"catalogue"},
 {"code":"mdf","name":"Мокшень кяль","status":"catalogue"},
 {"code":"lbe","name":"Лакку маз","status":"catalogue"},
 {"code":"kbd","name":"Адыгэбзэ","status":"catalogue"},
 {"code":"dz","name":"རྫོང་ཁ","status":"catalogue"},
 {"code":"bo","name":"བོད་སྐད","status":"catalogue"},
 {"code":"ug","name":"ئۇيغۇرچە","status":"catalogue"},
 {"code":"dari","name":"دری","status":"catalogue"},
 {"code":"bal","name":"بلوچی","status":"catalogue"},
 {"code":"sdh","name":"کوردی","status":"catalogue"},
 {"code":"bua","name":"Буряад хэлэн","status":"catalogue"},
 {"code":"alt","name":"Алтай тил","status":"catalogue"},
 {"code":"xal","name":"Хальмг келн","status":"catalogue"},
 {"code":"krc","name":"Къарачай-малкъар тил","status":"catalogue"},
 {"code":"nog","name":"Ногай тили","status":"catalogue"},
 {"code":"kum","name":"Къумукъ тил","status":"catalogue"},
 {"code":"kaa","name":"Qaraqalpaqsha","status":"catalogue"},
 {"code":"syr","name":"ܣܘܪܝܝܐ","status":"catalogue"},
 {"code":"arc","name":"ܐܪܡܝܐ","status":"catalogue"},
 {"code":"cop","name":"ⲙⲉⲧⲛ̀ⲣⲉⲙⲛ̀ⲕⲏⲙⲉ","status":"catalogue"},
 {"code":"egy","name":"Ancient Egyptian","status":"catalogue"},
 {"code":"grc","name":"Ancient Greek","status":"catalogue"},
 {"code":"got","name":"Gothic","status":"catalogue"},
 {"code":"ang","name":"Old English","status":"catalogue"},
 {"code":"enm","name":"Middle English","status":"catalogue"},
 {"code":"fro","name":"Old French","status":"catalogue"},
 {"code":"frm","name":"Middle French","status":"catalogue"},
 {"code":"non","name":"Old Norse","status":"catalogue"},
 {"code":"peo","name":"Old Persian","status":"catalogue"},
 {"code":"pal","name":"Middle Persian","status":"catalogue"},
 {"code":"ave","name":"Avestan","status":"catalogue"},
 {"code":"sux","name":"Sumerian","status":"catalogue"},
 {"code":"akk","name":"Akkadian","status":"catalogue"},
 {"code":"hit","name":"Hittite","status":"catalogue"},
 {"code":"phn","name":"Phoenician","status":"catalogue"},
 {"code":"xcl","name":"Classical Armenian","status":"catalogue"},
 {"code":"chu","name":"Church Slavonic","status":"catalogue"},
 {"code":"cu","name":"Church Slavonic","status":"catalogue"},
 {"code":"hsb","name":"Hornjoserbšćina","status":"catalogue"},
 {"code":"dsb","name":"Dolnoserbšćina","status":"catalogue"},
 {"code":"vro","name":"Võro","status":"catalogue"},
 {"code":"liv","name":"Līvõ kēļ","status":"catalogue"},
 {"code":"vot","name":"Vađđa ceeli","status":"catalogue"},
 {"code":"izh","name":"Inari Izhorian","status":"catalogue"},
 {"code":"krl","name":"Karjalan kieli","status":"catalogue"},
 {"code":"vep","name":"Vepsän kel'","status":"catalogue"},
 {"code":"olo","name":"Livvi","status":"catalogue"},
 {"code":"kca","name":"Ханты ясаң","status":"catalogue"},
 {"code":"mns","name":"Мāньси","status":"catalogue"},
 {"code":"sel","name":"Шӧльӄумыт әты","status":"catalogue"},
 {"code":"yrk","name":"Ненэця' вада","status":"catalogue"},
 {"code":"ckt","name":"Ԓыгъоравэтԓьэн йиԓыйиԓ","status":"catalogue"},
 {"code":"abq","name":"Абазшәа","status":"catalogue"},
 {"code":"lzz","name":"Lazuri","status":"catalogue"},
 {"code":"xmf","name":"მარგალური","status":"catalogue"},
 {"code":"sva","name":"ლუშნუ ნინ","status":"catalogue"},
 {"code":"gag","name":"Gagauz","status":"catalogue"},
 {"code":"crh","name":"Qırımtatarca","status":"catalogue"},
 {"code":"sco","name":"Scots","status":"catalogue"},
 {"code":"pih","name":"Norfuk","status":"catalogue"},
 {"code":"gyn","name":"Guyanese Creole English","status":"catalogue"},
 {"code":"bzj","name":"Belizean Creole","status":"catalogue"},
 {"code":"aig","name":"Antiguan Creole","status":"catalogue"},
 {"code":"srm","name":"Saramaccan","status":"catalogue"},
 {"code":"srn","name":"Sranan Tongo","status":"catalogue"},
 {"code":"djk","name":"Ndyuka","status":"catalogue"},
 {"code":"kri","name":"Krio","status":"catalogue"},
 {"code":"tem","name":"Temne","status":"catalogue"},
 {"code":"men","name":"Mende","status":"catalogue"},
 {"code":"kpe","name":"Kpelle","status":"catalogue"},
 {"code":"vai","name":"Vai","status":"catalogue"},
 {"code":"sus","name":"Sosoxui","status":"catalogue"},
 {"code":"dyu","name":"Julakan","status":"catalogue"},
 {"code":"man","name":"Manding","status":"catalogue"},
 {"code":"mnk","name":"Mandinka","status":"catalogue"},
 {"code":"snk","name":"Soninke","status":"catalogue"},
 {"code":"son","name":"Songhay","status":"catalogue"},
 {"code":"zgh","name":"Tamazight","status":"catalogue"},
 {"code":"tzm","name":"Central Atlas Tamazight","status":"catalogue"},
 {"code":"kab","name":"Taqbaylit","status":"catalogue"},
 {"code":"shi","name":"Tashelhit","status":"catalogue"},
 {"code":"rif","name":"Tarifit","status":"catalogue"},
 {"code":"ary","name":"Moroccan Arabic","status":"catalogue"},
 {"code":"arz","name":"Egyptian Arabic","status":"catalogue"},
 {"code":"apc","name":"Levantine Arabic","status":"catalogue"},
 {"code":"acm","name":"Mesopotamian Arabic","status":"catalogue"},
 {"code":"ber","name":"Berber languages","status":"catalogue"},
 {"code":"bss","name":"Akoose","status":"catalogue"},
 {"code":"ewo","name":"Ewondo","status":"catalogue"},
 {"code":"bas","name":"Basaa","status":"catalogue"},
 {"code":"dua","name":"Duala","status":"catalogue"},
 {"code":"fan","name":"Fang","status":"catalogue"},
 {"code":"bax","name":"Bamun","status":"catalogue"},
 {"code":"bum","name":"Bulu","status":"catalogue"},
 {"code":"mua","name":"Mundang","status":"catalogue"},
 {"code":"ncu","name":"Chumburung","status":"catalogue"},
 {"code":"nnh","name":"Ngiemboon","status":"catalogue"},
 {"code":"baf","name":"Nabak","status":"catalogue"},
 {"code":"bdu","name":"Oroko","status":"catalogue"},
 {"code":"bkm","name":"Kom","status":"catalogue"},
 {"code":"byv","name":"Medumba","status":"catalogue"},
 {"code":"ken","name":"Kenyang","status":"catalogue"},
 {"code":"fmp","name":"Fe'efe'e","status":"catalogue"},
 {"code":"guz","name":"Gusii","status":"catalogue"},
 {"code":"kam","name":"Kikamba","status":"catalogue"},
 {"code":"kik","name":"Gikuyu","status":"catalogue"},
 {"code":"luo","name":"Dholuo","status":"catalogue"},
 {"code":"mas","name":"Maa","status":"catalogue"},
 {"code":"mer","name":"Kimeru","status":"catalogue"},
 {"code":"nyf","name":"Kigiryama","status":"catalogue"},
 {"code":"suk","name":"Kisukuma","status":"catalogue"},
 {"code":"yao","name":"Chiyao","status":"catalogue"},
 {"code":"mak","name":"Makassar","status":"catalogue"},
 {"code":"bug","name":"Basa Ugi","status":"catalogue"},
 {"code":"sas","name":"Sasak","status":"catalogue"},
 {"code":"ban","name":"Basa Bali","status":"catalogue"},
 {"code":"mad","name":"Madhurâ","status":"catalogue"},
 {"code":"btx","name":"Batak Karo","status":"catalogue"},
 {"code":"bbc","name":"Batak Toba","status":"catalogue"},
 {"code":"rej","name":"Rejang","status":"catalogue"},
 {"code":"kac","name":"Jingpho","status":"catalogue"},
 {"code":"lus","name":"Mizo ṭawng","status":"catalogue"},
 {"code":"brh","name":"Brahui","status":"catalogue"},
 {"code":"bpy","name":"Bishnupriya","status":"catalogue"},
 {"code":"kha","name":"Khasi","status":"catalogue"},
 {"code":"grt","name":"Garo","status":"catalogue"},
 {"code":"njo","name":"Ao Naga","status":"catalogue"},
 {"code":"kru","name":"Kurukh","status":"catalogue"},
 {"code":"ho","name":"Ho","status":"catalogue"},
 {"code":"kfq","name":"Korku","status":"catalogue"},
 {"code":"gon","name":"Gondi","status":"catalogue"},
 {"code":"kxu","name":"Kui","status":"catalogue"},
 {"code":"kpy","name":"Koryak","status":"catalogue"},
 {"code":"evn","name":"Evenki","status":"catalogue"},
 {"code":"eve","name":"Even","status":"catalogue"},
 {"code":"ikt","name":"Inuinnaqtun","status":"catalogue"},
 {"code":"iu","name":"Inuktitut","status":"catalogue"},
 {"code":"ik","name":"Inupiaq","status":"catalogue"},
 {"code":"kl","name":"Kalaallisut","status":"catalogue"},
 {"code":"cr","name":"Cree","status":"catalogue"},
 {"code":"oj","name":"Ojibwe","status":"catalogue"},
 {"code":"nv","name":"Diné bizaad","status":"catalogue"},
 {"code":"chr","name":"ᏣᎳᎩ","status":"catalogue"},
 {"code":"chy","name":"Tsėhesenėstsestotse","status":"catalogue"},
 {"code":"lkt","name":"Lakȟótiyapi","status":"catalogue"},
 {"code":"mus","name":"Mvskoke","status":"catalogue"},
 {"code":"ybb","name":"Yemba","status":"catalogue"},
 {"code":"nmg","name":"Kwasio","status":"catalogue"},
 {"code":"mcp","name":"Makaa","status":"catalogue"},
 {"code":"zom","name":"Zo","status":"catalogue"},
 {"code":"ctd","name":"Tedim Chin","status":"catalogue"},
 {"code":"hak","name":"Hakka Chinese","status":"catalogue"},
 {"code":"nan","name":"Min Nan Chinese","status":"catalogue"},
 {"code":"wuu","name":"Wu Chinese","status":"catalogue"},
 {"code":"gan","name":"Gan Chinese","status":"catalogue"},
 {"code":"hsn","name":"Xiang Chinese","status":"catalogue"},
 {"code":"cjy","name":"Jin Chinese","status":"catalogue"},
 {"code":"lzh","name":"Classical Chinese","status":"catalogue"},
 {"code":"sgh","name":"Shughni","status":"catalogue"},
 {"code":"kmr","name":"Northern Kurdish","status":"catalogue"},
 {"code":"lrc","name":"Northern Luri","status":"catalogue"},
 {"code":"bqi","name":"Bakhtiari","status":"catalogue"},
 {"code":"glk","name":"Gilaki","status":"catalogue"},
 {"code":"mzn","name":"Mazanderani","status":"catalogue"},
 {"code":"tly","name":"Talysh","status":"catalogue"},
 {"code":"abk","name":"Abkhaz","status":"catalogue"},
 {"code":"che","name":"Chechen","status":"catalogue"},
 {"code":"inh","name":"Ingush","status":"catalogue"},
 {"code":"dar","name":"Dargwa","status":"catalogue"},
 {"code":"tab","name":"Tabasaran","status":"catalogue"},
 {"code":"rut","name":"Rutul","status":"catalogue"},
 {"code":"udi","name":"Udi","status":"catalogue"},
 {"code":"ava","name":"Avar","status":"catalogue"},
 {"code":"kjh","name":"Khakas","status":"catalogue"},
 {"code":"bak","name":"Bashkir","status":"catalogue"},
 {"code":"tat","name":"Tatar","status":"catalogue"},
 {"code":"chv","name":"Chuvash","status":"catalogue"},
 {"code":"kpv","name":"Komi-Zyrian","status":"catalogue"},
 {"code":"gld","name":"Nanai","status":"catalogue"},
 {"code":"sro","name":"Sardinian","status":"catalogue"},
 {"code":"lld","name":"Ladin","status":"catalogue"},
 {"code":"lij","name":"Ligurian","status":"catalogue"},
 {"code":"rup","name":"Aromanian","status":"catalogue"},
 {"code":"roa","name":"Romance languages","status":"catalogue"},
 {"code":"ine","name":"Indo-European languages","status":"catalogue"},
 {"code":"art","name":"Artificial languages","status":"catalogue"},
 {"code":"sgn","name":"Sign languages","status":"catalogue"},
 {"code":"ase","name":"American Sign Language","status":"catalogue"},
 {"code":"bfi","name":"British Sign Language","status":"catalogue"},
 {"code":"fsl","name":"French Sign Language","status":"catalogue"},
 {"code":"dse","name":"Dutch Sign Language","status":"catalogue"},
 {"code":"gsg","name":"German Sign Language","status":"catalogue"},
 {"code":"jsl","name":"Japanese Sign Language","status":"catalogue"},
 {"code":"csl","name":"Chinese Sign Language","status":"catalogue"},
 {"code":"bzs","name":"Brazilian Sign Language","status":"catalogue"},
 {"code":"ils","name":"International Sign","status":"catalogue"}
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
  row=db.execute("SELECT u.id,u.full_name,u.username,u.role,s.created_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",(digest_token(token),)).fetchone()
 if not row: raise HTTPException(401,"Session invalide")
 created=datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
 if (datetime.now(timezone.utc)-created).total_seconds()>604800:
  with db_session() as db: db.execute("DELETE FROM sessions WHERE token_hash=?",(digest_token(token),))
  raise HTTPException(401,"Session expirée : reconnectez-vous")
 return {k:row[k] for k in ("id","full_name","username","role")}
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
 return {"access_token":token,"token_type":"bearer","expires_in":604800,"user":{"id":uid,"full_name":payload.full_name.strip(),"username":payload.username.lower(),"role":"student"}}
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

  # LinguaBloom curated learning paths. Each lesson has an explicit answer and a
  # short explanation; levels describe progression, not official certification.
  advanced_tracks = [
   ("en","English · Elementary conversations","A2","Everyday conversations, past events and future plans.",[
    ("Daily routines","Use present simple for habits: I usually study after school. Use frequency adverbs before most main verbs.","Complete: She usually ___ breakfast at seven. (have/has)","has"),
    ("Past experiences","Use the past simple for completed events: I visited my aunt yesterday. Regular verbs usually end in -ed.","Complete: We ___ a film last night. (watch/watched)","watched"),
    ("Plans and invitations","Use going to for intentions and would like to for polite requests: I’m going to practise. Would you like to join?","Choose the polite invitation: (Come now!/Would you like to join us?)","Would you like to join us?")]),
   ("en","English · Independent speaker","B1","Narration, practical conditionals and clear opinions.",[
    ("Tell a story","Use past simple for completed events and past continuous for the background: I was walking when it started to rain.","Complete: I ___ when the phone rang. (was reading/read)","was reading"),
    ("Real and imagined conditions","First conditional: if + present, will + verb. Second conditional: if + past, would + verb.","If I had more time, I ___ another language. (learn/would learn)","would learn"),
    ("Support an opinion","State your view, give a reason and add an example. Use however to introduce a contrast.","Choose the best contrast connector: (because/however)","however")]),
   ("en","English · Confident communication","B2","Complex sentences, passive voice and nuanced argument.",[
    ("Passive voice","Use be + past participle when the action matters more than the agent: The results were published yesterday.","Change to passive: They built the bridge in 1990.","The bridge was built in 1990."),
    ("Relative clauses","Use who for people, which for things and that in many defining clauses.","The book ___ I borrowed is excellent. (who/that)","that"),
    ("Balanced argument","A strong argument states a claim, supports it with evidence and acknowledges a counterpoint.","Which phrase introduces a concession? (Even though/For example)","Even though")]),
   ("en","English · Advanced expression","C1","Register, precise linking and evidence-led writing.",[
    ("Formal register","Prefer precise verbs and avoid contractions in formal academic writing: We do not agree with the proposal.","Choose the formal option: (kids/children)","children"),
    ("Concession and emphasis","Although introduces a concession; nevertheless marks a contrast with the preceding idea.","___ the evidence was limited, the team reported its findings. (Although/Despite of)","Although"),
    ("Synthesis","Combine sources by comparing claims, noting limitations and drawing a qualified conclusion.","Which conclusion is appropriately cautious? (This proves everything./The evidence suggests a likely trend.)","The evidence suggests a likely trend.")]),
   ("en","English · Mastery and nuance","C2","Idiomatic nuance, rhetorical precision and careful editing.",[
    ("Idiomatic meaning","Idioms must be interpreted as a whole; their meaning may not equal the sum of their words.","“To get the ball rolling” means to… (start an activity/stop a project)","start an activity"),
    ("Rhetorical effect","Parallel structures give related ideas a balanced rhythm: to learn, to practise, to improve.","Which sentence has parallel structure? (She likes reading, to swim and bikes./She likes reading, swimming and cycling.)","She likes reading, swimming and cycling."),
    ("Precision editing","Choose wording that matches the strength of the evidence and avoid absolute claims without proof.","Replace an unsupported absolute: (This always works./This often works in the tested cases.)","This often works in the tested cases.")]),
   ("fr","Français · Autonomie quotidienne","A2","Raconter, demander poliment et parler de projets.",[
    ("Raconter au passé","Le passé composé exprime souvent une action terminée : « Hier, j’ai étudié. » Avec être, le participe passé s’accorde généralement avec le sujet.","Complète : Hier, nous ___ un film. (avons regardé/ regardons)","avons regardé"),
    ("Demander poliment","« Pourriez-vous… ? » et « J’aimerais… » rendent une demande plus polie que l’impératif direct.","Choisis la demande la plus polie : (Donne-moi ça./Pourriez-vous m’aider ?)","Pourriez-vous m’aider ?"),
    ("Parler de projets","« Aller + infinitif » exprime un futur proche : « Je vais réviser ce soir. »","Complète : Demain, elle ___ visiter sa tante. (va/est)","va")]),
   ("fr","Français · Expression indépendante","B1","Récit, hypothèses et argumentation structurée.",[
    ("Organiser un récit","Les marqueurs « d’abord », « ensuite », « pendant que » et « finalement » rendent un récit plus clair.","Quel marqueur annonce la dernière étape ? (d’abord/finalement)","finalement"),
    ("Exprimer une hypothèse","« Si + imparfait » est suivi du conditionnel présent : « Si j’avais le temps, je voyagerais. »","Si j’étais libre, je ___ avec vous. (viens/viendrais)","viendrais"),
    ("Défendre une opinion","Présente une idée, justifie-la, donne un exemple et réponds à une objection.","Quel connecteur marque l’opposition ? (cependant/parce que)","cependant")]),
   ("fr","Français · Argumentation avancée","B2","Voix passive, subordination et argumentation nuancée.",[
    ("Voix passive","La voix passive met l’accent sur l’action ou le résultat : « Le rapport a été publié. »","Mets au passif : « Le jury a choisi le texte. »","Le texte a été choisi par le jury."),
    ("Subordination","« Bien que » est suivi du subjonctif : « Bien qu’il soit tard… »","Bien qu’elle ___ fatiguée, elle continue. (est/soit)","soit"),
    ("Construire une argumentation","Une argumentation solide relie thèse, preuves, limites et conclusion.","Quelle étape renforce un argument ? (une preuve pertinente/une répétition sans raison)","une preuve pertinente")]),
   ("fr","Français · Maîtrise du registre","C1","Registres, précision lexicale et synthèse critique.",[
    ("Adapter le registre","Le vocabulaire et la syntaxe changent selon le destinataire : conversation, courrier professionnel ou essai.","Dans un courrier formel, choisis : (Salut !/Madame, Monsieur,)","Madame, Monsieur,"),
    ("Nuancer une affirmation","« Il semble que », « dans une certaine mesure » et « les données suggèrent » évitent les certitudes excessives.","Quelle formulation est la plus nuancée ? (C’est incontestable./Les éléments disponibles suggèrent que…)","Les éléments disponibles suggèrent que…"),
    ("Synthèse critique","Une synthèse regroupe les idées communes et les divergences sans juxtaposer mécaniquement les textes.","Une bonne synthèse doit… (comparer et hiérarchiser les idées/copier chaque paragraphe)","comparer et hiérarchiser les idées")]),
   ("fr","Français · Maîtrise et finesse","C2","Figures de style, idiomes et révision stylistique.",[
    ("Sens figuré","Une expression idiomatique s’interprète dans son contexte et ne se traduit pas toujours mot à mot.","« Avoir le cœur sur la main » signifie être… (généreux/indifférent)","généreux"),
    ("Effets rhétoriques","L’anaphore répète un mot ou groupe de mots au début de plusieurs segments.","La répétition en début de phrases s’appelle… (anaphore/métaphore)","anaphore"),
    ("Réviser un texte","Une révision avancée vérifie le sens, la cohérence, le rythme et la précision des mots.","Quel choix améliore la précision ? (un terme exact/une formule vague)","un terme exact")]),
   ("es","Español · Conversación cotidiana","A2","Hablar del pasado, pedir con cortesía y expresar planes.",[
    ("Hablar del pasado","El pretérito indefinido presenta una acción terminada: « Ayer estudié ».","Ayer nosotros ___ al mercado. (vamos/fuimos)","fuimos"),
    ("Pedir con cortesía","« ¿Podría ayudarme? » es más cortés que una orden directa.","Elige la petición más cortés: (Dame eso./¿Podría ayudarme?)","¿Podría ayudarme?"),
    ("Planes futuros","« Ir a + infinitivo » expresa un plan: « Voy a estudiar esta tarde ».","Mañana ella ___ a practicar. (va/voy)","va")]),
   ("es","Español · Usuario independiente","B1","Narración, hipótesis y opinión razonada.",[
    ("Narrar experiencias","Combina conectores como primero, después, mientras y finalmente para ordenar un relato.","¿Qué conector suele cerrar una secuencia? (primero/finalmente)","finalmente"),
    ("Expresar hipótesis","La segunda condicional usa si + imperfecto de subjuntivo y condicional: « Si pudiera, viajaría ».","Si tuviera tiempo, ___ más. (estudio/estudiaría)","estudiaría"),
    ("Argumentar","Presenta una idea, justifícala con una razón y añade un ejemplo concreto.","¿Qué conector expresa contraste? (sin embargo/por eso)","sin embargo")]),
   ("es","Español · Argumentación avanzada","B2","Voz pasiva, subordinación y matices argumentativos.",[
    ("Voz pasiva","La pasiva con ser + participio destaca la acción: « El informe fue publicado ».","Completa: La carta fue ___ ayer. (escribir/escrita)","escrita"),
    ("Subjuntivo en contexto","Tras ciertas expresiones de duda, deseo o valoración se usa el subjuntivo.","Espero que ella ___ pronto. (viene/venga)","venga"),
    ("Debate equilibrado","Una buena argumentación presenta razones, reconoce objeciones y responde con evidencia.","¿Qué fortalece una tesis? (evidencia pertinente/afirmaciones sin apoyo)","evidencia pertinente")]),
   ("es","Español · Registro y precisión","C1","Registro formal, conectores complejos y síntesis.",[
    ("Registro formal","En textos profesionales, elige vocabulario preciso y evita expresiones demasiado coloquiales.","En un correo formal, ¿qué saludo conviene? (Estimado equipo/Hola, colega!)","Estimado equipo"),
    ("Matizar afirmaciones","« Los datos parecen indicar… » expresa más cautela que « Esto demuestra todo ».","Elige la afirmación prudente: (Siempre ocurre./Los datos sugieren una tendencia.)","Los datos sugieren una tendencia."),
    ("Sintetizar fuentes","Una síntesis compara ideas, destaca diferencias y formula una conclusión propia.","Una síntesis eficaz debe… (jerarquizar ideas/copiar cada texto)","jerarquizar ideas")]),
   ("es","Español · Dominio y estilo","C2","Expresiones idiomáticas, retórica y edición precisa.",[
    ("Expresiones idiomáticas","El sentido de una expresión fija depende del contexto cultural y comunicativo.","« Estar en las nubes » significa estar… (distraído/muy enfadado)","distraído"),
    ("Recursos retóricos","La anáfora repite palabras al inicio de varias frases para crear ritmo o énfasis.","¿Cómo se llama esa repetición inicial? (anáfora/hipérbole)","anáfora"),
    ("Edición de estilo","La revisión avanzada elimina ambigüedades y adapta el tono al propósito y al lector.","¿Qué mejora la precisión? (un término específico/una frase vaga)","un término específico")]),
  ]
  for code,title,level,desc,lessons in advanced_tracks:
   if not db.execute("SELECT id FROM courses WHERE language_code=? AND level=?",(code,level)).fetchone():
    cid=db.execute("INSERT INTO courses(language_code,title,level,description) VALUES(?,?,?,?)",(code,title,level,desc)).lastrowid
    for i,(lt,body,exercise,answer) in enumerate(lessons,1):
     db.execute("INSERT INTO lessons(course_id,title,body,exercise,answer,position) VALUES(?,?,?,?,?,?)",(cid,lt,body,exercise,answer,i))
  # Original introductory pathways for seven additional writing systems/languages.
  additional_tracks = [
   ("de","Deutsch · Erste Schritte","A1","Begrüßungen, einfache Sätze und Alltag.",[
    ("Begrüßungen","Hallo = salut. Guten Morgen = bonjour le matin. Ich heiße… = je m’appelle…","Complète : Ich ___ Anna. (heiße/heißt)","heiße"),
    ("Sein","Sein au présent : ich bin, du bist, er/sie ist. Exemple : Ich bin Schüler.","Ich ___ müde. (bin/bist)","bin"),
    ("Questions simples","Wer = qui, wo = où, was = quoi. Wo wohnst du? = Où habites-tu ?","Quel mot demande un lieu ? (wer/wo)","wo")]),
   ("pt","Português · Primeiros passos","A1","Saudações, apresentações et phrases simples.",[
    ("Saudações","Olá = bonjour. Bom dia = bonjour le matin. Chamo-me Ana / Meu nome é Ana = je m’appelle Ana.","« Obrigado » signifie… (merci/bonjour)","merci"),
    ("Ser","Ser : eu sou, tu és, ele/ela é. Exemple : Eu sou estudante.","Completa: Eu ___ estudante. (sou/és)","sou"),
    ("Perguntas","Onde = où, quem = qui, o que = quoi. Onde moras? = Où habites-tu ?","Quel mot signifie « où » ? (onde/quem)","onde")]),
   ("zh","中文 · Premiers caractères","A1","Caractères, pinyin, sens et premières salutations.",[
    ("人 — personne","人 signifie personne/être humain. Pinyin : rén, deuxième ton. Observe les deux traits et rappelle le sens sans regarder.","Que signifie 人 ? (personne/eau)","personne"),
    ("水 — eau","水 signifie eau. Pinyin : shuǐ, troisième ton. Le caractère compte quatre traits; prononce puis rappelle le sens.","Quel est le pinyin de 水 ? (shuǐ/rén)","shuǐ"),
    ("Saluer","你好 (nǐ hǎo) signifie bonjour. 你 = tu/vous; 好 = bien/bon.","Que signifie 你好 ? (bonjour/merci)","bonjour")]),
   ("ja","日本語 · Premiers kana","A1","Hiragana, salutations et expressions utiles.",[
    ("Hiragana あ","あ se lit a. Les kana représentent des sons; apprends d’abord à reconnaître les signes et leur lecture.","あ se lit… (a/ka)","a"),
    ("Saluer","こんにちは (konnichiwa) signifie bonjour dans la journée. ありがとう (arigatō) signifie merci.","Que signifie ありがとう ? (merci/bonjour)","merci"),
    ("Se présenter","わたしはアナです。 signifie « Je suis Ana ». は marque ici le thème et se prononce wa.","Quelle expression signifie « je suis Ana » ? (わたしはアナです。/さようなら)","わたしはアナです。")]),
   ("ko","한국어 · Premiers hangeul","A1","Hangeul, syllabes et expressions de base.",[
    ("Bloc syllabique","한 se compose de ㅎ (h), ㅏ (a) et ㄴ (n) : han. Les lettres se regroupent en blocs syllabiques.","한 se lit… (han/dal)","han"),
    ("Saluer","안녕하세요 (annyeonghaseyo) est une salutation polie courante; 감사합니다 (gamsahamnida) signifie merci.","Que signifie 감사합니다 ? (merci/bonjour)","merci"),
    ("Se présenter","저는 학생입니다 signifie « Je suis étudiant(e) ». 저는 introduit « moi, je » et 학생 signifie étudiant.","학생 signifie… (étudiant/professeur)","étudiant")]),
   ("ar","العربية · Premiers pas","A1","Alphabet, lecture de droite à gauche et salutations.",[
    ("Sens de lecture","L’arabe se lit de droite à gauche. Les lettres peuvent changer de forme selon leur position dans le mot.","Dans quel sens lit-on l’arabe ? (droite à gauche/gauche à droite)","droite à gauche"),
    ("Salutations","مرحبا (marhaban) signifie bonjour/bienvenue. شكرا (shukran) signifie merci.","Que signifie شكرا ? (merci/bonjour)","merci"),
    ("Se présenter","أنا طالب (ana talib) signifie « je suis étudiant » au masculin; أنا طالبة (ana taliba) au féminin.","أنا signifie… (je/eau)","je")]),
   ("ru","Русский · Premiers pas","A1","Cyrillique, salutations et premières phrases.",[
    ("Cyrillique","М se prononce m; Р se prononce r; Н se prononce n. Certaines lettres ressemblent au latin mais ont un autre son.","Quelle lettre se prononce m ? (М/Р)","М"),
    ("Saluer","Здравствуйте est une salutation polie; привет est plus familier. Спасибо signifie merci.","Что значит Спасибо? (merci/bonjour)","merci"),
    ("Se présenter","Я студент / Я студентка signifie « je suis étudiant / étudiante ». Я signifie je.","Я signifie… (je/tu)","je")])
  ]
  for code,title,level,desc,lessons in additional_tracks:
   if not db.execute("SELECT id FROM courses WHERE language_code=? AND level=?",(code,level)).fetchone():
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

# Adaptive language exercises and source-aware exam preparation.
from .pedagogy import router as pedagogy_router
app.include_router(pedagogy_router)

"""Idempotent multi-level curriculum expansion for LinguaBloom Academy.

Creates 250 lessons per core European language and 300 for languages with
additional writing-system/pronunciation load. Lessons are generated from
explicit language-specific phrase banks and a structured CEFR skill sequence.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

LANGUAGES = {
    "en": ("English", "English ·"),
    "fr": ("Français", "Français ·"),
    "es": ("Español", "Español ·"),
    "de": ("Allemand", "Allemand ·"),
    "pt": ("Portugais", "Portugais ·"),
    "zh": ("Mandarin chinois", "Mandarin ·"),
    "ja": ("Japonais", "Japonais ·"),
    "ko": ("Coréen", "Coréen ·"),
    "ar": ("Arabe standard moderne", "Arabe ·"),
    "ru": ("Russe", "Russe ·"),
}

# Each item is (French meaning, natural target-language phrase). These are
# intentionally short, practical phrases suitable for self-study exercises.
PHRASES = {
"en": [("Bonjour.","Hello."),("Bonsoir.","Good evening."),("Comment allez-vous ?","How are you?"),("Je vais bien, merci.","I am fine, thank you."),("Je m’appelle Lina.","My name is Lina."),("Je viens du Cameroun.","I come from Cameroon."),("J’habite à Yaoundé.","I live in Yaoundé."),("Je suis élève.","I am a student."),("J’apprends une langue.","I am learning a language."),("Je ne comprends pas.","I do not understand."),("Pouvez-vous répéter ?","Can you repeat, please?"),("Où est la gare ?","Where is the station?"),("Combien ça coûte ?","How much does it cost?"),("Je voudrais de l’eau.","I would like some water."),("J’ai besoin d’aide.","I need help."),("Aujourd’hui, il fait beau.","The weather is nice today."),("Hier, j’ai étudié.","I studied yesterday."),("Demain, je vais travailler.","Tomorrow, I am going to work."),("Si j’avais le temps, je voyagerais.","If I had time, I would travel."),("Merci beaucoup.","Thank you very much."),("Excusez-moi.","Excuse me."),("Je suis d’accord.","I agree."),("À mon avis, c’est utile.","In my opinion, it is useful."),("Pourriez-vous m’aider ?","Could you help me?"),("Je cherche une pharmacie.","I am looking for a pharmacy."),("Le rendez-vous est à neuf heures.","The appointment is at nine o’clock."),("Le rapport a été publié.","The report was published."),("Les résultats suggèrent une tendance.","The results suggest a trend."),("Il faut vérifier les sources.","The sources must be checked."),("Merci de votre patience.","Thank you for your patience.")],
"fr": [("Hello.","Bonjour."),("Good evening.","Bonsoir."),("How are you?","Comment allez-vous ?"),("I am fine, thank you.","Je vais bien, merci."),("My name is Lina.","Je m’appelle Lina."),("I come from Cameroon.","Je viens du Cameroun."),("I live in Yaoundé.","J’habite à Yaoundé."),("I am a student.","Je suis élève."),("I am learning a language.","J’apprends une langue."),("I do not understand.","Je ne comprends pas."),("Can you repeat, please?","Pouvez-vous répéter ?"),("Where is the station?","Où est la gare ?"),("How much does it cost?","Combien ça coûte ?"),("I would like some water.","Je voudrais de l’eau."),("I need help.","J’ai besoin d’aide."),("The weather is nice today.","Aujourd’hui, il fait beau."),("I studied yesterday.","Hier, j’ai étudié."),("Tomorrow, I am going to work.","Demain, je vais travailler."),("If I had time, I would travel.","Si j’avais le temps, je voyagerais."),("Thank you very much.","Merci beaucoup."),("Excuse me.","Excusez-moi."),("I agree.","Je suis d’accord."),("In my opinion, it is useful.","À mon avis, c’est utile."),("Could you help me?","Pourriez-vous m’aider ?"),("I am looking for a pharmacy.","Je cherche une pharmacie."),("The appointment is at nine o’clock.","Le rendez-vous est à neuf heures."),("The report was published.","Le rapport a été publié."),("The results suggest a trend.","Les résultats suggèrent une tendance."),("The sources must be checked.","Il faut vérifier les sources."),("Thank you for your patience.","Merci de votre patience.")],
"es": [("Bonjour.","Hola."),("Bonsoir.","Buenas noches."),("Comment allez-vous ?","¿Cómo está?"),("Je vais bien, merci.","Estoy bien, gracias."),("Je m’appelle Lina.","Me llamo Lina."),("Je viens du Cameroun.","Vengo de Camerún."),("J’habite à Yaoundé.","Vivo en Yaundé."),("Je suis élève.","Soy estudiante."),("J’apprends une langue.","Estoy aprendiendo un idioma."),("Je ne comprends pas.","No entiendo."),("Pouvez-vous répéter ?","¿Puede repetir, por favor?"),("Où est la gare ?","¿Dónde está la estación?"),("Combien ça coûte ?","¿Cuánto cuesta?"),("Je voudrais de l’eau.","Quisiera agua."),("J’ai besoin d’aide.","Necesito ayuda."),("Aujourd’hui, il fait beau.","Hoy hace buen tiempo."),("Hier, j’ai étudié.","Ayer estudié."),("Demain, je vais travailler.","Mañana voy a trabajar."),("Si j’avais le temps, je voyagerais.","Si tuviera tiempo, viajaría."),("Merci beaucoup.","Muchas gracias."),("Excusez-moi.","Disculpe."),("Je suis d’accord.","Estoy de acuerdo."),("À mon avis, c’est utile.","En mi opinión, es útil."),("Pourriez-vous m’aider ?","¿Podría ayudarme?"),("Je cherche une pharmacie.","Busco una farmacia."),("Le rendez-vous est à neuf heures.","La cita es a las nueve."),("Le rapport a été publié.","El informe fue publicado."),("Les résultats suggèrent une tendance.","Los resultados sugieren una tendencia."),("Il faut vérifier les sources.","Hay que verificar las fuentes."),("Merci de votre patience.","Gracias por su paciencia.")],
"de": [("Bonjour.","Guten Tag."),("Bonsoir.","Guten Abend."),("Comment allez-vous ?","Wie geht es Ihnen?"),("Je vais bien, merci.","Mir geht es gut, danke."),("Je m’appelle Lina.","Ich heiße Lina."),("Je viens du Cameroun.","Ich komme aus Kamerun."),("J’habite à Yaoundé.","Ich wohne in Yaoundé."),("Je suis élève.","Ich bin Schüler."),("J’apprends une langue.","Ich lerne eine Sprache."),("Je ne comprends pas.","Ich verstehe nicht."),("Pouvez-vous répéter ?","Können Sie das bitte wiederholen?"),("Où est la gare ?","Wo ist der Bahnhof?"),("Combien ça coûte ?","Wie viel kostet das?"),("Je voudrais de l’eau.","Ich hätte gern Wasser."),("J’ai besoin d’aide.","Ich brauche Hilfe."),("Aujourd’hui, il fait beau.","Heute ist das Wetter schön."),("Hier, j’ai étudié.","Gestern habe ich gelernt."),("Demain, je vais travailler.","Morgen werde ich arbeiten."),("Si j’avais le temps, je voyagerais.","Wenn ich Zeit hätte, würde ich reisen."),("Merci beaucoup.","Vielen Dank."),("Excusez-moi.","Entschuldigen Sie."),("Je suis d’accord.","Ich bin einverstanden."),("À mon avis, c’est utile.","Meiner Meinung nach ist das nützlich."),("Pourriez-vous m’aider ?","Könnten Sie mir helfen?"),("Je cherche une pharmacie.","Ich suche eine Apotheke."),("Le rendez-vous est à neuf heures.","Der Termin ist um neun Uhr."),("Le rapport a été publié.","Der Bericht wurde veröffentlicht."),("Les résultats suggèrent une tendance.","Die Ergebnisse deuten auf einen Trend hin."),("Il faut vérifier les sources.","Man muss die Quellen überprüfen."),("Merci de votre patience.","Vielen Dank für Ihre Geduld.")],
"pt": [("Bonjour.","Olá."),("Bonsoir.","Boa noite."),("Comment allez-vous ?","Como está?"),("Je vais bien, merci.","Estou bem, obrigado."),("Je m’appelle Lina.","Chamo-me Lina."),("Je viens du Cameroun.","Venho dos Camarões."),("J’habite à Yaoundé.","Moro em Yaoundé."),("Je suis élève.","Sou estudante."),("J’apprends une langue.","Estou a aprender uma língua."),("Je ne comprends pas.","Não compreendo."),("Pouvez-vous répéter ?","Pode repetir, por favor?"),("Où est la gare ?","Onde fica a estação?"),("Combien ça coûte ?","Quanto custa?"),("Je voudrais de l’eau.","Queria água, por favor."),("J’ai besoin d’aide.","Preciso de ajuda."),("Aujourd’hui, il fait beau.","Hoje está bom tempo."),("Hier, j’ai étudié.","Ontem estudei."),("Demain, je vais travailler.","Amanhã vou trabalhar."),("Si j’avais le temps, je voyagerais.","Se tivesse tempo, viajaria."),("Merci beaucoup.","Muito obrigado."),("Excusez-moi.","Com licença."),("Je suis d’accord.","Concordo."),("À mon avis, c’est utile.","Na minha opinião, é útil."),("Pourriez-vous m’aider ?","Poderia ajudar-me?"),("Je cherche une pharmacie.","Procuro uma farmácia."),("Le rendez-vous est à neuf heures.","A consulta é às nove horas."),("Le rapport a été publié.","O relatório foi publicado."),("Les résultats suggèrent une tendance.","Os resultados sugerem uma tendência."),("Il faut vérifier les sources.","É necessário verificar as fontes."),("Merci de votre patience.","Obrigado pela sua paciência.")],
"zh": [("Bonjour.","你好。"),("Bonsoir.","晚上好。"),("Comment allez-vous ?","您好吗？"),("Je vais bien, merci.","我很好，谢谢。"),("Je m’appelle Lina.","我叫莉娜。"),("Je viens du Cameroun.","我来自喀麦隆。"),("J’habite à Yaoundé.","我住在雅温得。"),("Je suis élève.","我是学生。"),("J’apprends une langue.","我在学习一门语言。"),("Je ne comprends pas.","我不明白。"),("Pouvez-vous répéter ?","请再说一遍，好吗？"),("Où est la gare ?","火车站在哪里？"),("Combien ça coûte ?","这个多少钱？"),("Je voudrais de l’eau.","我想要水。"),("J’ai besoin d’aide.","我需要帮助。"),("Aujourd’hui, il fait beau.","今天天气很好。"),("Hier, j’ai étudié.","我昨天学习了。"),("Demain, je vais travailler.","我明天要工作。"),("Si j’avais le temps, je voyagerais.","如果我有时间，我就去旅行。"),("Merci beaucoup.","非常感谢。"),("Excusez-moi.","不好意思。"),("Je suis d’accord.","我同意。"),("À mon avis, c’est utile.","我认为这很有用。"),("Pourriez-vous m’aider ?","您可以帮我吗？"),("Je cherche une pharmacie.","我在找药店。"),("Le rendez-vous est à neuf heures.","约会时间是九点。"),("Le rapport a été publié.","报告已经发布了。"),("Les résultats suggèrent une tendance.","结果显示出一种趋势。"),("Il faut vérifier les sources.","需要核实资料来源。"),("Merci de votre patience.","感谢您的耐心。")],
"ja": [("Bonjour.","こんにちは。"),("Bonsoir.","こんばんは。"),("Comment allez-vous ?","お元気ですか。"),("Je vais bien, merci.","元気です、ありがとうございます。"),("Je m’appelle Lina.","私はリナです。"),("Je viens du Cameroun.","カメルーンから来ました。"),("J’habite à Yaoundé.","ヤウンデに住んでいます。"),("Je suis élève.","私は学生です。"),("J’apprends une langue.","言語を勉強しています。"),("Je ne comprends pas.","分かりません。"),("Pouvez-vous répéter ?","もう一度言っていただけますか。"),("Où est la gare ?","駅はどこですか。"),("Combien ça coûte ?","いくらですか。"),("Je voudrais de l’eau.","水をお願いします。"),("J’ai besoin d’aide.","助けが必要です。"),("Aujourd’hui, il fait beau.","今日は天気がいいです。"),("Hier, j’ai étudié.","昨日、勉強しました。"),("Demain, je vais travailler.","明日、働く予定です。"),("Si j’avais le temps, je voyagerais.","時間があれば、旅行するのに。"),("Merci beaucoup.","どうもありがとうございます。"),("Excusez-moi.","すみません。"),("Je suis d’accord.","賛成です。"),("À mon avis, c’est utile.","私の意見では、役に立ちます。"),("Pourriez-vous m’aider ?","手伝っていただけますか。"),("Je cherche une pharmacie.","薬局を探しています。"),("Le rendez-vous est à neuf heures.","約束は九時です。"),("Le rapport a été publié.","報告書が公開されました。"),("Les résultats suggèrent une tendance.","結果は傾向を示しています。"),("Il faut vérifier les sources.","情報源を確認する必要があります。"),("Merci de votre patience.","お待ちいただきありがとうございます。")],
"ko": [("Bonjour.","안녕하세요."),("Bonsoir.","안녕하세요."),("Comment allez-vous ?","어떻게 지내세요?"),("Je vais bien, merci.","잘 지내요, 감사합니다."),("Je m’appelle Lina.","제 이름은 리나예요."),("Je viens du Cameroun.","저는 카메룬에서 왔어요."),("J’habite à Yaoundé.","저는 야운데에 살아요."),("Je suis élève.","저는 학생이에요."),("J’apprends une langue.","저는 언어를 배우고 있어요."),("Je ne comprends pas.","이해하지 못해요."),("Pouvez-vous répéter ?","다시 말씀해 주시겠어요?"),("Où est la gare ?","역이 어디예요?"),("Combien ça coûte ?","얼마예요?"),("Je voudrais de l’eau.","물을 주세요."),("J’ai besoin d’aide.","도움이 필요해요."),("Aujourd’hui, il fait beau.","오늘 날씨가 좋아요."),("Hier, j’ai étudié.","어제 공부했어요."),("Demain, je vais travailler.","내일 일할 거예요."),("Si j’avais le temps, je voyagerais.","시간이 있다면 여행할 텐데요."),("Merci beaucoup.","정말 감사합니다."),("Excusez-moi.","실례합니다."),("Je suis d’accord.","동의해요."),("À mon avis, c’est utile.","제 생각에는 유용해요."),("Pourriez-vous m’aider ?","도와주실 수 있나요?"),("Je cherche une pharmacie.","약국을 찾고 있어요."),("Le rendez-vous est à neuf heures.","약속은 아홉 시예요."),("Le rapport a été publié.","보고서가 발표되었어요."),("Les résultats suggèrent une tendance.","결과는 경향을 보여 줘요."),("Il faut vérifier les sources.","출처를 확인해야 해요."),("Merci de votre patience.","기다려 주셔서 감사합니다.")],
"ar": [("Bonjour.","مرحبًا."),("Bonsoir.","مساء الخير."),("Comment allez-vous ?","كيف حالك؟"),("Je vais bien, merci.","أنا بخير، شكرًا."),("Je m’appelle Lina.","اسمي لينا."),("Je viens du Cameroun.","أنا من الكاميرون."),("J’habite à Yaoundé.","أسكن في ياوندي."),("Je suis élève.","أنا طالب."),("J’apprends une langue.","أنا أتعلم لغة."),("Je ne comprends pas.","أنا لا أفهم."),("Pouvez-vous répéter ?","هل يمكنك أن تكرر من فضلك؟"),("Où est la gare ?","أين محطة القطار؟"),("Combien ça coûte ?","كم السعر؟"),("Je voudrais de l’eau.","أريد ماءً من فضلك."),("J’ai besoin d’aide.","أحتاج إلى مساعدة."),("Aujourd’hui, il fait beau.","الطقس جميل اليوم."),("Hier, j’ai étudié.","درست أمس."),("Demain, je vais travailler.","سأعمل غدًا."),("Si j’avais le temps, je voyagerais.","لو كان لدي وقت لسافرت."),("Merci beaucoup.","شكرًا جزيلًا."),("Excusez-moi.","عذرًا."),("Je suis d’accord.","أنا موافق."),("À mon avis, c’est utile.","في رأيي، هذا مفيد."),("Pourriez-vous m’aider ?","هل يمكنك مساعدتي؟"),("Je cherche une pharmacie.","أبحث عن صيدلية."),("Le rendez-vous est à neuf heures.","الموعد في الساعة التاسعة."),("Le rapport a été publié.","نُشر التقرير."),("Les résultats suggèrent une tendance.","تشير النتائج إلى اتجاه."),("Il faut vérifier les sources.","يجب التحقق من المصادر."),("Merci de votre patience.","شكرًا على صبرك.")],
"ru": [("Bonjour.","Здравствуйте."),("Bonsoir.","Добрый вечер."),("Comment allez-vous ?","Как поживаете?"),("Je vais bien, merci.","У меня всё хорошо, спасибо."),("Je m’appelle Lina.","Меня зовут Лина."),("Je viens du Cameroun.","Я из Камеруна."),("J’habite à Yaoundé.","Я живу в Яунде."),("Je suis élève.","Я ученик."),("J’apprends une langue.","Я изучаю язык."),("Je ne comprends pas.","Я не понимаю."),("Pouvez-vous répéter ?","Повторите, пожалуйста."),("Où est la gare ?","Где находится вокзал?"),("Combien ça coûte ?","Сколько это стоит?"),("Je voudrais de l’eau.","Я хотел бы воды."),("J’ai besoin d’aide.","Мне нужна помощь."),("Aujourd’hui, il fait beau.","Сегодня хорошая погода."),("Hier, j’ai étudié.","Вчера я занимался."),("Demain, je vais travailler.","Завтра я буду работать."),("Si j’avais le temps, je voyagerais.","Если бы у меня было время, я бы путешествовал."),("Merci beaucoup.","Большое спасибо."),("Excusez-moi.","Извините."),("Je suis d’accord.","Я согласен."),("À mon avis, c’est utile.","По моему мнению, это полезно."),("Pourriez-vous m’aider ?","Не могли бы вы мне помочь?"),("Je cherche une pharmacie.","Я ищу аптеку."),("Le rendez-vous est à neuf heures.","Встреча в девять часов."),("Le rapport a été publié.","Отчёт был опубликован."),("Les résultats suggèrent une tendance.","Результаты указывают на тенденцию."),("Il faut vérifier les sources.","Нужно проверить источники."),("Merci de votre patience.","Спасибо за терпение.")],
}

LEVELS = {
    "A1": (30, "Débutant", "sons et alphabet, salutations, nombres, identité, famille, objets usuels et phrases très courtes"),
    "A2": (35, "Élémentaire", "routines, lieux, achats, temps passé simple, projets, demandes polies et descriptions courtes"),
    "B1": (40, "Intermédiaire", "récits cohérents, opinions justifiées, hypothèses courantes, expériences et autonomie pratique"),
    "B2": (45, "Intermédiaire avancé", "argumentation, subordination, registre, nuances, compréhension de textes et reformulation"),
    "C1": (45, "Avancé", "registre professionnel, synthèse, précision lexicale, implicite, structure argumentative et esprit critique"),
    "C2": (55, "Maîtrise", "idiomes, nuances culturelles, rhétorique, style, ambiguïtés et révision fine"),
}
HARD_LEVELS = {
    "A1": (40, "Débutant", "sons ou système d’écriture, salutations, identité et phrases élémentaires"),
    "A2": (45, "Élémentaire", "phrases courantes, particules ou accords essentiels, situations quotidiennes et demandes polies"),
    "B1": (50, "Intermédiaire", "récits, expériences, intentions, compréhension contextuelle et conversation autonome"),
    "B2": (50, "Intermédiaire avancé", "structures complexes, registres, argumentation et reformulation"),
    "C1": (55, "Avancé", "textes longs, implicite, précision, argumentation structurée et contexte culturel"),
    "C2": (60, "Maîtrise", "idiomes, style, ambiguïtés, nuances culturelles et édition experte"),
}
TOPICS = [
"se présenter","salutations et politesse","nombres et quantités","dates et heures","famille et relations",
"école et apprentissage","maison et objets","ville et directions","transports et déplacements","alimentation",
"courses et prix","restaurant et commandes","santé et pharmacie","corps et sensations","vêtements et couleurs",
"météo et saisons","loisirs et préférences","routine quotidienne","travail et métiers","voyage et hébergement",
"téléphone et messages","rendez-vous et horaires","émotions et opinions","décrire une personne","décrire un lieu",
"comparer des choix","raconter hier","parler de demain","demander une information","résoudre un problème",
"règles et consignes","accord et désaccord","cause et conséquence","condition et hypothèse","possibilité et obligation",
"conseils et recommandations","expériences personnelles","événements et chronologie","études et projets","environnement",
"technologie et médias","culture et traditions","relations sociales","services publics","budget et paiements",
"travail en équipe","argumenter une idée","résumer un texte","langue formelle et informelle","réviser et corriger",
"idiomes et expressions","humour et sous-entendus","discours et présentation","courriel professionnel","entretien et négociation",
"information et fiabilité","nuance et degré de certitude","métaphores et rhétorique","synthèse de sources","édition stylistique",
]
SKILLS = [
    ("Vocabulaire en contexte", "Mémorise le groupe de mots comme une unité, puis replace-le dans une phrase personnelle."),
    ("Point de langue", "Observe l’ordre des mots et la forme grammaticale. Compare l’exemple avec une phrase que tu connais déjà."),
    ("Compréhension écrite", "Lis la phrase lentement, repère le sujet et l’information essentielle, puis reformule son sens."),
    ("Production guidée", "Construis une phrase complète, vérifie l’ordre des mots et relis-la à voix haute si possible."),
    ("Dialogue pratique", "Imagine le contexte réel. Choisis une formule adaptée au destinataire et réponds avec une phrase complète."),
    ("Révision active", "Rappelle la notion sans regarder l’explication, puis compare ta réponse au corrigé."),
]

def _level_for_position(i: int, counts: dict[str, tuple[int, str, str]]) -> tuple[str, int]:
    cursor = 0
    for level, (count, _, _) in counts.items():
        if cursor <= i < cursor + count:
            return level, i - cursor
        cursor += count
    raise IndexError(i)

def _lesson_text(language_code: str, level: str, topic: str, skill_index: int, phrase_index: int) -> tuple[str, str, str, str]:
    lang_name = LANGUAGES[language_code][0]
    meaning, phrase = PHRASES[language_code][phrase_index % len(PHRASES[language_code])]
    skill, method = SKILLS[skill_index % len(SKILLS)]
    _, level_label, objectives = (HARD_LEVELS if language_code in {"zh", "ja", "ko", "ar", "ru"} else LEVELS)[level]
    title = f"{level} · {topic.capitalize()} · {skill}"
    if language_code == "zh":
        script_note = "En mandarin, observe les caractères, la segmentation et le pinyin fourni par ton cours. Cette activité travaille le sens écrit; elle ne note pas automatiquement les tons à l’oral."
    elif language_code == "ja":
        script_note = "En japonais, repère les kana et les kanji présents. Le romaji peut aider au départ, mais entraîne-toi progressivement à lire l’écriture japonaise."
    elif language_code == "ko":
        script_note = "En coréen, repère les blocs syllabiques du hangeul et lis chaque bloc dans l’ordre. Les terminaisons dépendent du niveau de politesse."
    elif language_code == "ar":
        script_note = "En arabe standard moderne, lis de droite à gauche. Les voyelles brèves sont souvent omises dans les textes courants; observe le contexte."
    elif language_code == "ru":
        script_note = "En russe, observe l’alphabet cyrillique et les terminaisons. L’accent tonique n’est pas indiqué systématiquement dans les textes ordinaires."
    else:
        script_note = f"En {lang_name}, observe les mots clés, leur place dans la phrase et le registre utilisé."
    body = (
        f"**Objectif {level} — {level_label} : {topic}.** Cette leçon développe {objectives}. "
        f"**Exemple :** « {meaning} » → **{phrase}** "
        f"**Méthode :** {method} {script_note} "
        f"**À retenir :** réutilise l’expression dans une situation réelle et adapte-la au contexte. "
        f"Le corrigé est une réponse de référence; d’autres formulations peuvent être acceptables selon le contexte."
    )
    prompts = [
        f"Traduis en {lang_name} : « {meaning} »",
        f"Écris en {lang_name} l’expression qui signifie : « {meaning} »",
        f"Reproduis en {lang_name} une formulation naturelle de : « {meaning} »",
        f"Sans copier l’exemple, écris l’équivalent en {lang_name} de : « {meaning} »",
        f"Quelle phrase en {lang_name} exprime l’idée suivante : « {meaning} » ?",
        f"Rappelle la formulation en {lang_name} pour : « {meaning} »",
    ]
    exercise = prompts[skill_index % len(prompts)]
    answer = phrase
    return title, body, exercise, answer

def seed_expanded_curriculum(db_path: str | Path) -> dict[str, int]:
    """Add enough lessons for each active language, without deleting learner data."""
    db = sqlite3.connect(str(db_path), timeout=20)
    db.row_factory = sqlite3.Row
    totals: dict[str, int] = {}
    try:
        for code, (language_name, prefix) in LANGUAGES.items():
            level_map = HARD_LEVELS if code in {"zh", "ja", "ko", "ar", "ru"} else LEVELS
            for level, (target_count, level_label, objectives) in level_map.items():
                rows = db.execute("SELECT id FROM courses WHERE language_code=? AND level=? ORDER BY id", (code, level)).fetchall()
                if rows:
                    course_id = rows[0]["id"]
                else:
                    description = f"Parcours {level} ({level_label}) : {objectives}. Cours d'entraînement avec corrigés."
                    course_id = db.execute(
                        "INSERT INTO courses(language_code,title,level,description,published) VALUES(?,?,?,?,1)",
                        (code, f"{prefix} {level} — {level_label}", level, description),
                    ).lastrowid
                existing = db.execute("SELECT COUNT(*) AS n FROM lessons WHERE course_id=?", (course_id,)).fetchone()["n"]
                # Existing courses may have a few authored lessons. Never delete or overwrite them.
                for position in range(existing + 1, target_count + 1):
                    global_index = position - 1
                    topic = TOPICS[(global_index + list(level_map).index(level) * 7) % len(TOPICS)]
                    skill_index = (global_index + list(level_map).index(level)) % len(SKILLS)
                    phrase_index = (global_index * 3 + list(level_map).index(level) * 5) % len(PHRASES[code])
                    title, body, exercise, answer = _lesson_text(code, level, topic, skill_index, phrase_index)
                    # Position and title are deterministic, so repeated startup does not duplicate lessons.
                    duplicate = db.execute("SELECT id FROM lessons WHERE course_id=? AND position=?", (course_id, position)).fetchone()
                    if duplicate:
                        continue
                    db.execute(
                        "INSERT INTO lessons(course_id,title,body,exercise,answer,position) VALUES(?,?,?,?,?,?)",
                        (course_id, title, body, exercise, answer, position),
                    )
                # If older versions had multiple courses for a level, make the published
                # curriculum count truthful across all of them without touching progress.
                total_level = db.execute(
                    "SELECT COUNT(*) AS n FROM lessons l JOIN courses c ON c.id=l.course_id WHERE c.language_code=? AND c.level=?",
                    (code, level),
                ).fetchone()["n"]
                if total_level < target_count:
                    for position in range(total_level + 1, target_count + 1):
                        topic = TOPICS[(position + list(level_map).index(level) * 11) % len(TOPICS)]
                        skill_index = position % len(SKILLS)
                        phrase_index = (position * 7 + list(level_map).index(level)) % len(PHRASES[code])
                        title, body, exercise, answer = _lesson_text(code, level, topic, skill_index, phrase_index)
                        db.execute(
                            "INSERT INTO lessons(course_id,title,body,exercise,answer,position) VALUES(?,?,?,?,?,?)",
                            (course_id, title, body, exercise, answer, position + 1000),
                        )
            total = db.execute("SELECT COUNT(*) AS n FROM lessons l JOIN courses c ON c.id=l.course_id WHERE c.language_code=?", (code,)).fetchone()["n"]
            totals[code] = total
        db.commit()
        return totals
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

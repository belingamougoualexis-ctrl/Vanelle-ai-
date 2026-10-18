/* Lucky Languages Academy: adaptive practice UI */
let practiceQuestions = [];
async function renderPractice(container) {
  const langData = await api('/api/pedagogy/languages');
  const options = langData.items.map(function (item) {
    return '<option value="' + esc(item.code) + '">' + esc(item.name) +
      (item.available_in_question_bank ? '' : ' · modèle de base') + '</option>';
  }).join('');
  container.innerHTML =
    '<div class="panel"><h2>Atelier d’exercices adaptatifs</h2>' +
    '<p>Choisis une langue, un niveau et une compétence. Les exercices originaux sont distincts des questions générées par l’IA locale.</p>' +
    '<div class="formgrid">' +
    '<div class="field"><label>Langue</label><select id="practiceLanguage">' + options + '</select></div>' +
    '<div class="field"><label>Niveau</label><select id="practiceLevel">' +
    '<option>A1</option><option>A2</option><option>B1</option><option>B2</option><option>C1</option><option>C2</option>' +
    '<option value="beginner">Débutant</option><option value="primary">Primaire</option><option value="secondary">Secondaire</option><option value="be_pc">BEPC</option></select></div>' +
    '<div class="field"><label>Compétence</label><select id="practiceSkill"><option value="mixed">Mixte</option>' +
    '<option value="vocabulary">Vocabulaire</option><option value="grammar">Grammaire</option><option value="reading">Lecture</option>' +
    '<option value="writing">Écriture</option><option value="character">Caractères / écriture</option></select></div>' +
    '<div class="field"><label>Thème</label><input id="practiceTopic" value="vie quotidienne" maxlength="160"></div>' +
    '<div class="field"><label>Nombre de questions</label><select id="practiceCount"><option>3</option><option selected>5</option><option>8</option><option>12</option></select></div>' +
    '<div class="field"><label>Générateur IA local (Ollama installé sur le serveur)</label><select id="practiceAI">' +
    '<option value="false">Banque originale hors ligne</option><option value="true">Essayer l’IA locale puis repli hors ligne</option></select></div></div>' +
    '<button onclick="generatePractice()">Créer mes exercices</button><div id="practiceStatus" class="status"></div><div id="practiceResults"></div></div>' +
    '<div class="panel"><h2>Préparation aux examens</h2><p>Liens vers les sources officielles. Les documents restent sur les sites d’origine : leurs droits de réutilisation doivent être respectés.</p><div id="examResourceList">Chargement des ressources…</div></div>';
  await loadExamResources();
  document.getElementById('practiceLanguage').addEventListener('change', loadExamResources);
}
async function loadExamResources() {
  const select = document.getElementById('practiceLanguage');
  const list = document.getElementById('examResourceList');
  if (!list) return;
  try {
    const lang = select ? select.value : '';
    const data = await api('/api/pedagogy/exam-resources' + (lang ? '?language_code=' + encodeURIComponent(lang) : ''));
    list.innerHTML = data.items.length ? data.items.map(function (item) {
      return '<div class="listitem"><h3>' + esc(item.name) + '</h3><p>' + esc(item.reuse) +
        '</p><a href="' + esc(item.url) + '" target="_blank" rel="noopener noreferrer">Ouvrir la source officielle ↗</a></div>';
    }).join('') : 'Aucune ressource référencée pour cette langue.';
  } catch (error) { list.textContent = error.message; }
}
async function generatePractice() {
  const status = document.getElementById('practiceStatus');
  const results = document.getElementById('practiceResults');
  status.classList.remove('error');
  status.textContent = 'Préparation des exercices…';
  results.innerHTML = '';
  try {
    const data = await api('/api/pedagogy/generate', {method:'POST', body:JSON.stringify({
      language_code:document.getElementById('practiceLanguage').value,
      level:document.getElementById('practiceLevel').value,
      skill:document.getElementById('practiceSkill').value,
      count:Number(document.getElementById('practiceCount').value),
      topic:document.getElementById('practiceTopic').value || 'vie quotidienne',
      learner_language:'fr',
      use_local_ai:document.getElementById('practiceAI').value === 'true'
    })});
    practiceQuestions = data.questions || [];
    status.textContent = (data.generator === 'ollama_local' ?
      'IA locale utilisée. Les questions générées restent à vérifier par un enseignant avant un examen noté. ' :
      'Banque originale / modèle hors ligne. ') + data.quality_note;
    results.innerHTML = practiceQuestions.map(function (question, index) {
      let html = '<div class="tile" style="margin-top:12px"><span class="pill">' +
        esc(question.level || data.level) + ' · ' + esc(question.skill || data.skill) +
        '</span><h3>' + (index + 1) + '. ' + esc(question.question) + '</h3>';
      if (question.character) {
        html += '<div style="font-size:38px;margin:8px 0">' + esc(question.character) + '</div>' +
          '<p><b>Pinyin :</b> ' + esc(question.pinyin || '') + ' · <b>Sens :</b> ' + esc(question.meaning || '') +
          (question.stroke_count ? ' · Traits : ' + esc(question.stroke_count) : '') + '</p>' +
          '<p><b>Pratique d’écriture :</b> ' + esc(question.writing_prompt || ('Écris ' + question.character + ' de mémoire puis compare au modèle.')) + '</p>';
      }
      html += (question.options || []).map(function (option) {
        return '<label style="display:block;padding:8px;border-bottom:1px solid #edf1f5"><input style="width:auto" type="radio" name="practice_' +
          index + '" value="' + esc(option) + '"> ' + esc(option) + '</label>';
      }).join('') + '<div class="field"><label>Ou écris ta réponse</label><input id="practiceText_' + index +
        '" maxlength="2000" placeholder="Ta réponse…"></div><button class="smallbtn" onclick="gradePractice(' + index +
        ')">Corriger ma réponse</button><div class="status" id="practiceGrade_' + index + '"></div></div>';
      return html;
    }).join('');
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('error');
  }
}
async function gradePractice(index) {
  const question = practiceQuestions[index];
  if (!question) return;
  const radio = document.querySelector('input[name="practice_' + index + '"]:checked');
  const input = document.getElementById('practiceText_' + index);
  const answer = ((input && input.value) || (radio && radio.value) || '').trim();
  const output = document.getElementById('practiceGrade_' + index);
  if (!answer) { output.textContent = 'Choisis ou écris une réponse.'; return; }
  try {
    const data = await api('/api/pedagogy/grade', {method:'POST', body:JSON.stringify({
      language_code:document.getElementById('practiceLanguage').value, question:question, answer:answer
    })});
    output.textContent = data.feedback + ' Réponse attendue : ' + data.expected_answer + '. ' +
      data.explanation + ' ' + data.assessment_limit;
  } catch (error) { output.textContent = error.message; }
}

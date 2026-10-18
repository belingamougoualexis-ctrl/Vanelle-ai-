function renderTeacherStudio(c) {
  const html = '<div class="teacher-studio">' +
    '<div class="teacher-stage" id="teacherStage">' +
      '<model-viewer id="teacherModel" alt="Modèle 3D du professeur importé" camera-controls auto-rotate rotation-per-second="12deg" shadow-intensity="1.1" exposure="1.05" environment-image="neutral" interaction-prompt="auto"></model-viewer>' +
      '<div class="teacher-empty" id="teacherEmpty"><div class="orb">✦</div><h3>Votre professeur en 3D</h3><p>Importez un modèle humanoïde GLB pour le visualiser, le faire pivoter et examiner son rendu dans la salle de cours.</p></div>' +
    '</div><div class="teacher-controls">' +
      '<div class="teacher-feature"><strong>01 · Modèle 3D réel</strong><p>Format GLB recommandé, avec maillage, textures et matériaux. Le visualiseur ne remplace pas la création d’un modèle photoréaliste.</p></div>' +
      '<label class="model-file"><strong>Importer le modèle du professeur</strong><input id="teacherModelFile" type="file" accept=".glb,model/gltf-binary"><span class="model-note">Le fichier est chargé localement dans ce navigateur pour la prévisualisation. Il n’est pas envoyé au serveur ni sauvegardé dans le compte.</span></label>' +
      '<div id="teacherModelStatus" class="model-status" role="status" aria-live="polite">Aucun modèle chargé.</div>' +
      '<div class="row"><button type="button" onclick="resetTeacherModel()" class="secondary">Réinitialiser la vue</button><button type="button" onclick="toggleTeacherMotion()" class="secondary" id="teacherMotionBtn">Arrêter la rotation</button></div>' +
      '<div class="teacher-feature"><strong>02 · Pour un rendu ultra-réaliste</strong><p>Il faut un asset humain de haute qualité avec textures de peau, cheveux, vêtements et idéalement rig/animations. Un simple fichier 3D stylisé ne devient pas photoréaliste par le visualiseur seul.</p></div>' +
      '<p class="model-note">Le visualiseur 3D est chargé depuis un composant web externe et nécessite Internet pour son premier chargement. Le reste de l’interface garde son fonctionnement habituel.</p>' +
    '</div></div>';
  c.innerHTML = panel('Studio des professeurs 3D', 'Prévisualisez un véritable modèle humanoïde 3D dans l’espace de cours. Le réalisme dépend du fichier 3D importé : aucun avatar photoréaliste n’est fourni artificiellement avec cette version.', html);
  const script = document.createElement('script');
  script.type = 'module';
  script.src = 'https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js';
  document.head.appendChild(script);
  const file = document.getElementById('teacherModelFile');
  file.addEventListener('change', function(e) {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.glb')) { setTeacherStatus('Choisis un fichier .glb pour une prévisualisation fiable.', true); return; }
    const model = document.getElementById('teacherModel');
    const stage = document.getElementById('teacherStage');
    if (window.teacherModelObjectUrl) URL.revokeObjectURL(window.teacherModelObjectUrl);
    window.teacherModelObjectUrl = URL.createObjectURL(f);
    model.src = window.teacherModelObjectUrl;
    stage.classList.add('has-model');
    model.addEventListener('load', function() { setTeacherStatus('Modèle chargé : ' + f.name + ' · ' + (f.size / 1024 / 1024).toFixed(1) + ' Mo'); }, { once: true });
    model.addEventListener('error', function() { setTeacherStatus('Impossible de lire ce GLB. Vérifie le fichier et ses textures intégrées.', true); }, { once: true });
    setTeacherStatus('Chargement de ' + f.name + '…');
  });
}
function setTeacherStatus(message, isError) {
  const el = document.getElementById('teacherModelStatus');
  if (el) { el.textContent = message; el.style.color = isError ? '#c74757' : '#0b8a72'; }
}
function resetTeacherModel() {
  const model = document.getElementById('teacherModel');
  if (!model) return;
  model.removeAttribute('src');
  document.getElementById('teacherStage').classList.remove('has-model');
  document.getElementById('teacherModelFile').value = '';
  if (window.teacherModelObjectUrl) { URL.revokeObjectURL(window.teacherModelObjectUrl); window.teacherModelObjectUrl = null; }
  setTeacherStatus('Aucun modèle chargé.');
}
function toggleTeacherMotion() {
  const model = document.getElementById('teacherModel');
  const btn = document.getElementById('teacherMotionBtn');
  if (!model || !btn) return;
  if (model.hasAttribute('auto-rotate')) { model.removeAttribute('auto-rotate'); btn.textContent = 'Reprendre la rotation'; }
  else { model.setAttribute('auto-rotate', ''); btn.textContent = 'Arrêter la rotation'; }
}

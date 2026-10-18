function renderTeacherStudio(c) {
  const html = '<div class="teacher-studio">' +
    '<div class="teacher-stage" id="teacherStage">' +
      '<iframe id="teacherViewerFrame" title="Visualiseur isolé du professeur 3D" sandbox="allow-scripts" referrerpolicy="no-referrer" style="width:100%;height:100%;min-height:320px;border:0;background:transparent;z-index:1"></iframe>' +
      '<div class="teacher-empty" id="teacherEmpty"><div class="orb">✦</div><h3>Votre professeur en 3D</h3><p>Importez un modèle humanoïde GLB pour le visualiser, le faire pivoter et examiner son rendu dans la salle de cours.</p></div>' +
    '</div><div class="teacher-controls">' +
      '<div class="teacher-feature"><strong>01 · Modèle 3D réel</strong><p>Format GLB recommandé, avec maillage, textures et matériaux. Le visualiseur ne remplace pas la création d’un modèle photoréaliste.</p></div>' +
      '<label class="model-file"><strong>Importer le modèle du professeur</strong><input id="teacherModelFile" type="file" accept=".glb,model/gltf-binary"><span class="model-note">Le fichier reste dans le navigateur et n’est pas envoyé à l’API de l’application. Le visualiseur s’exécute dans un cadre isolé sans accès au stockage de session de l’application.</span></label>' +
      '<div id="teacherModelStatus" class="model-status" role="status" aria-live="polite">Initialisation du visualiseur…</div>' +
      '<div class="row"><button type="button" onclick="resetTeacherModel()" class="secondary">Réinitialiser la vue</button><button type="button" onclick="toggleTeacherMotion()" class="secondary" id="teacherMotionBtn">Arrêter la rotation</button></div>' +
      '<div class="teacher-feature"><strong>02 · Pour un rendu ultra-réaliste</strong><p>Il faut un asset humain de haute qualité avec textures de peau, cheveux, vêtements et idéalement rig/animations. Un simple fichier 3D stylisé ne devient pas photoréaliste par le visualiseur seul.</p></div>' +
      '<p class="model-note">Le visualiseur 3D est téléchargé depuis Google CDN et nécessite Internet. Il s’exécute dans une iframe sandboxée, séparée de la session de l’application.</p>' +
    '</div></div>';
  cleanupTeacherStudio();
  c.innerHTML = panel('Studio des professeurs 3D', 'Prévisualisez un véritable modèle humanoïde 3D dans l’espace de cours. Le réalisme dépend du fichier 3D importé : aucun avatar photoréaliste n’est fourni artificiellement avec cette version.', html);
  const frame = document.getElementById('teacherViewerFrame');
  const file = document.getElementById('teacherModelFile');
  window.teacherViewerReady = false;
  window.teacherViewerPendingFile = null;
  window.teacherViewerMessageHandler = function(event) {
    if (!frame || event.source !== frame.contentWindow || !event.data || typeof event.data.type !== 'string') return;
    if (event.data.type === 'viewer-ready') {
      window.teacherViewerReady = true;
      setTeacherStatus('Visualiseur prêt. Sélectionne un modèle GLB.');
      if (window.teacherViewerPendingFile) sendTeacherModel(window.teacherViewerPendingFile);
    } else if (event.data.type === 'viewer-status') {
      setTeacherStatus(String(event.data.message || 'Visualiseur prêt.'), Boolean(event.data.error));
      if (event.data.loaded) document.getElementById('teacherStage')?.classList.add('has-model');
    }
  };
  window.addEventListener('message', window.teacherViewerMessageHandler);
  frame.srcdoc = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}model-viewer{display:block;width:100%;height:100%;min-height:320px;background:transparent;--poster-color:transparent}</style></head><body><model-viewer id="mv" alt="Modèle 3D du professeur" camera-controls auto-rotate rotation-per-second="12deg" shadow-intensity="1.1" exposure="1.05" environment-image="neutral" interaction-prompt="auto"></model-viewer><script type="module">import "https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js";const mv=document.getElementById("mv");let objectUrl=null;window.addEventListener("message",async e=>{if(e.source!==parent||!e.data||e.data.type!=="model-file"||!(e.data.buffer instanceof ArrayBuffer))return;if(objectUrl)URL.revokeObjectURL(objectUrl);objectUrl=URL.createObjectURL(new Blob([e.data.buffer],{type:"model/gltf-binary"}));mv.src=objectUrl;parent.postMessage({type:"viewer-status",message:"Chargement de "+String(e.data.name||"modèle")+"…"},"*")});mv.addEventListener("load",()=>parent.postMessage({type:"viewer-status",message:"Modèle 3D chargé avec succès.",loaded:true},"*"));mv.addEventListener("error",()=>parent.postMessage({type:"viewer-status",message:"Impossible de lire ce GLB. Vérifie son intégrité et ses textures.",error:true},"*"));parent.postMessage({type:"viewer-ready"},"*");window.addEventListener("pagehide",()=>{if(objectUrl)URL.revokeObjectURL(objectUrl)});</script></body></html>';
  file.addEventListener('change', async function(e) {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.glb')) { setTeacherStatus('Choisis un fichier .glb pour une prévisualisation fiable.', true); return; }
    if (f.size > 500 * 1024 * 1024) { setTeacherStatus('Le fichier dépasse la limite de prévisualisation de 500 Mo.', true); return; }
    window.teacherViewerPendingFile = f;
    if (window.teacherViewerReady) await sendTeacherModel(f);
    setTeacherStatus('Préparation de ' + f.name + '…');
  });
}
async function sendTeacherModel(file) {
  const frame = document.getElementById('teacherViewerFrame');
  if (!frame || !file) return;
  try {
    const buffer = await file.arrayBuffer();
    if (!document.getElementById('teacherViewerFrame')) return;
    frame.contentWindow.postMessage({type:'model-file', name:file.name, buffer}, '*', [buffer]);
    document.getElementById('teacherStage')?.classList.add('has-model');
    setTeacherStatus('Modèle transmis au visualiseur isolé : ' + file.name + ' · ' + (file.size / 1024 / 1024).toFixed(1) + ' Mo');
  } catch (err) {
    setTeacherStatus('Impossible de lire ce fichier : ' + String(err && err.message || err), true);
  }
}
function setTeacherStatus(message, isError) {
  const el = document.getElementById('teacherModelStatus');
  if (el) { el.textContent = message; el.style.color = isError ? '#c74757' : '#0b8a72'; }
}
function resetTeacherModel() {
  const frame = document.getElementById('teacherViewerFrame');
  if (frame && frame.contentWindow) frame.contentWindow.postMessage({type:'reset-model'}, '*');
  window.teacherViewerPendingFile = null;
  const stage = document.getElementById('teacherStage');
  if (stage) stage.classList.remove('has-model');
  const input = document.getElementById('teacherModelFile');
  if (input) input.value = '';
  setTeacherStatus('Aucun modèle chargé.');
}
function toggleTeacherMotion() {
  const frame = document.getElementById('teacherViewerFrame');
  const btn = document.getElementById('teacherMotionBtn');
  if (!frame || !btn) return;
  frame.contentWindow.postMessage({type:'toggle-motion'}, '*');
  btn.textContent = btn.textContent.includes('Arrêter') ? 'Reprendre la rotation' : 'Arrêter la rotation';
}
function cleanupTeacherStudio() {
  if (window.teacherViewerMessageHandler) {
    window.removeEventListener('message', window.teacherViewerMessageHandler);
    window.teacherViewerMessageHandler = null;
  }
  const frame = document.getElementById('teacherViewerFrame');
  if (frame) frame.srcdoc = '';
  window.teacherViewerReady = false;
  window.teacherViewerPendingFile = null;
}

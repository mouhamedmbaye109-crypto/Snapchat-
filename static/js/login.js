const form = document.getElementById('form');
const msg = document.getElementById('msg');
const btn = form.querySelector('button');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const identifiant = form.identifiant.value.trim();
  const mot_de_passe = form.mot_de_passe.value;

  msg.className = 'msg';
  msg.textContent = '';

  if (!identifiant || !mot_de_passe) {
    msg.className = 'msg err';
    msg.textContent = 'Renseigne les deux champs.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Connexion…';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifiant, mot_de_passe })
    });
    const data = await res.json();

    if (res.ok && data.ok) {
      btn.textContent = 'Connecté ✓';
      location.href = data.redirect;
      return;
    }
    throw new Error(data.erreur || 'Connexion impossible.');
  } catch (err) {
    msg.className = 'msg err';
    msg.textContent = err.message;
    btn.disabled = false;
    btn.textContent = 'Se connecter';
  }
});
const token = document.body.dataset.token;
const objectif = Number(document.querySelector('.point')?.parentElement.children.length || 5);

const barre = document.getElementById('barre');
const compte = document.getElementById('compte');
const points = document.getElementById('points');
const bouton = document.getElementById('debloquer');

const TEXTE = "J'ai débloqué Snapchat+ 🎉";

function lien() {
  return `${location.origin}/r/${token}`;
}

function dessiner(n) {
  compte.textContent = n;
  barre.style.width = `${Math.min(100, (n / objectif) * 100)}%`;
  [...points.children].forEach((p, i) => p.classList.toggle('actif', i < n));

  if (n >= objectif) {
    document.body.classList.add('debloque');
    bouton.disabled = false;
    bouton.textContent = 'Débloquer Snapchat+';
    document.getElementById('zone').querySelector('.verrou').textContent = 'Accès débloqué';
  }
}

async function enregistrer(reseau) {
  try {
    const res = await fetch(`/api/partage/${token}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reseau })
    });
    const data = await res.json();
    if (data.ok) dessiner(data.partages);
  } catch (_) { /* silencieux : le partage a déjà eu lieu */ }
}

function ouvrir(reseau) {
  const u = encodeURIComponent(lien());
  const t = encodeURIComponent(TEXTE);
  const urls = {
    whatsapp: `https://wa.me/?text=${t}%20${u}`,
    x: `https://twitter.com/intent/tweet?text=${t}&url=${u}`,
    telegram: `https://t.me/share/url?url=${u}&text=${t}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${u}`
  };
  if (urls[reseau]) window.open(urls[reseau], '_blank', 'noopener,width=620,height=640');
}

document.querySelectorAll('.reseau').forEach((b) => {
  b.addEventListener('click', async () => {
    const reseau = b.dataset.reseau;

    if (reseau === 'copie') {
      try {
        await navigator.clipboard.writeText(lien());
        b.textContent = 'Lien copié ✓';
        setTimeout(() => (b.textContent = 'Copier le lien'), 1600);
      } catch (_) {
        b.textContent = lien();
      }
    } else {
      ouvrir(reseau);
    }

    await enregistrer(reseau);
  });
});

bouton.addEventListener('click', () => {
  bouton.textContent = 'Activation en cours…';
  bouton.disabled = true;
  setTimeout(() => {
    bouton.textContent = 'Snapchat+ activé ✓';
  }, 1400);
});

dessiner(Number(compte.textContent));
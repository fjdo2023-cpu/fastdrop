import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .models import User

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates"   # <-- ESSA LINHA RESOLVE
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///fastdrop.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"

    # Register blueprints
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .vendor.routes import vendor_bp
    from .bling.routes import bling_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(vendor_bp, url_prefix="/vendor")
    app.register_blueprint(bling_bp, url_prefix="/bling")

    @app.route("/")
    def index():
        from flask_login import current_user
        from flask import redirect, url_for, render_template
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("vendor.dashboard"))
        # ------------------------------------------------------------------
        # Criar tabelas e usuário admin padrão (somente se ainda não existirem)
        # ------------------------------------------------------------------
        from werkzeug.security import generate_password_hash
        from .models import User, Vendor

        with app.app_context():
            # cria todas as tabelas se não existirem
            from .extensions import db
            db.create_all()

            # cria usuário admin padrão, se ainda não existir
            admin_email = "admin@fastdrop.com"
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    name="Administrador",
                    email=admin_email,
                    password_hash=generate_password_hash("123456"),  # senha padrão
                    role="admin",
                )
                db.session.add(admin)
                db.session.commit()
    return app

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User, Vendor
from werkzeug.security import generate_password_hash

auth_bp = Blueprint("auth", __name__)
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Credenciais inválidas", "danger")
            return redirect(url_for("auth.login"))
        if not user.active:
            flash("Usuário inativo", "warning")
            return redirect(url_for("auth.login"))
        login_user(user)
        flash("Login realizado com sucesso", "success")
        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("vendor.dashboard"))
    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/register-vendor", methods=["GET", "POST"])
def register_vendor():
    # opcional: você pode fechar esse endpoint e cadastrar vendedores só via admin
    if request.method == "POST":
        name = request.form.get("name")
        company_name = request.form.get("company_name")
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "warning")
            return redirect(url_for("auth.register_vendor"))
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="vendor",
        )
        db.session.add(user)
        db.session.commit()

        vendor = Vendor(
            user_id=user.id,
            company_name=company_name,
        )
        db.session.add(vendor)
        db.session.commit()

        flash("Cadastro realizado. Faça login.", "success")
        return redirect(url_for("auth.login"))
        @auth_bp.route("/init-admin")
def init_admin():
    from .models import User
    from .extensions import db
    from werkzeug.security import generate_password_hash

    db.create_all()

    admin_email = "admin@fastdrop.com"
    admin = User.query.filter_by(email=admin_email).first()

    if not admin:
        admin = User(
            name="Administrador",
            email=admin_email,
            password_hash=generate_password_hash("123456"),
            role="admin",
            active=True
        )
        db.session.add(admin)
        db.session.commit()
        return "Admin criado: admin@fastdrop.com /
    return render_template("auth/register_vendor.html")

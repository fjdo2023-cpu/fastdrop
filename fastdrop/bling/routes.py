import os
from datetime import datetime, timedelta
import requests
from flask import Blueprint, redirect, request, url_for, flash, render_template
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Vendor, BlingAccount

bling_bp = Blueprint("bling", __name__, template_folder="../../templates/bling")

BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"

def get_bling_client_credentials():
    client_id = os.environ.get("BLING_CLIENT_ID")
    client_secret = os.environ.get("BLING_CLIENT_SECRET")
    redirect_uri = os.environ.get("BLING_REDIRECT_URI")
    return client_id, client_secret, redirect_uri

@bling_bp.route("/connect")
@login_required
def connect():
    # Apenas vendedores conectam seu Bling
    if current_user.role != "vendor":
        flash("Apenas vendedores podem conectar o Bling.", "warning")
        return redirect(url_for("admin.dashboard"))
    vendor = current_user.vendor
    client_id, _, redirect_uri = get_bling_client_credentials()
    if not client_id or not redirect_uri:
        flash("Credenciais do Bling não configuradas.", "danger")
        return redirect(url_for("vendor.dashboard"))
    state = str(vendor.id)
    auth_url = (
        f"{BLING_AUTH_URL}?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&state={state}"
    )
    return redirect(auth_url)

@bling_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")  # vendor_id
    error = request.args.get("error")
    if error:
        flash(f"Erro ao conectar com o Bling: {error}", "danger")
        return redirect(url_for("auth.login"))

    client_id, client_secret, redirect_uri = get_bling_client_credentials()
    if not all([client_id, client_secret, redirect_uri]):
        flash("Credenciais do Bling não configuradas.", "danger")
        return redirect(url_for("auth.login"))

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(BLING_TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        flash("Erro ao obter token do Bling.", "danger")
        return redirect(url_for("auth.login"))
    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    vendor = Vendor.query.get(int(state))
    if not vendor:
        flash("Vendedor não encontrado.", "danger")
        return redirect(url_for("auth.login"))

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    if vendor.bling_account:
        vendor.bling_account.access_token = access_token
        vendor.bling_account.refresh_token = refresh_token
        vendor.bling_account.token_expires_at = expires_at
    else:
        ba = BlingAccount(
            vendor_id=vendor.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
        )
        db.session.add(ba)
    vendor.bling_connected = True
    db.session.commit()
    flash("Bling conectado com sucesso!", "success")
    return redirect(url_for("vendor.dashboard"))

@bling_bp.route("/status")
@login_required
def status():
    if current_user.role != "vendor":
        flash("Apenas vendedores possuem status de Bling.", "warning")
        return redirect(url_for("admin.dashboard"))
    vendor = current_user.vendor
    return render_template("bling/status.html", vendor=vendor)

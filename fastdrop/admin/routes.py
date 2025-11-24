import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import boto3

from ..extensions import db
from ..models import Product, Vendor, User

admin_bp = Blueprint("admin", __name__)


# ---------- Helpers S3 ----------


def _get_s3_client():
    """Retorna o client do S3 usando as variáveis de ambiente."""
    region = os.getenv("AWS_S3_REGION") or os.getenv("AWS_REGION") or "us-east-2"

    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
    )


def upload_image_to_s3(file_obj, folder="products"):
    """Faz upload do arquivo para o S3 e devolve a URL pública."""
    if not file_obj or file_obj.filename == "":
        return None

    bucket = (
        os.getenv("AWS_BUCKET_NAME")
        or os.getenv("S3_BUCKET_NAME")
        or os.getenv("AWS_S3_BUCKET")
    )
    if not bucket:
        return None

    filename = secure_filename(file_obj.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    key = f"{folder}/{uuid.uuid4().hex}.{ext}"

    s3 = _get_s3_client()
    s3.upload_fileobj(
        file_obj,
        bucket,
        key,
        ExtraArgs={"ACL": "public-read", "ContentType": file_obj.mimetype},
    )

    region = os.getenv("AWS_S3_REGION") or os.getenv("AWS_REGION") or "us-east-2"
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return url


# ---------- Rotas Admin ----------


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return "Acesso negado", 403

    products_count = Product.query.count()
    vendors_count = Vendor.query.count()
    pending_orders_count = 0  # ainda não temos pedidos

    return render_template(
        "admin/dashboard.html",
        products_count=products_count,
        vendors_count=vendors_count,
        pending_orders_count=pending_orders_count,
    )


@admin_bp.route("/products")
@login_required
def list_products():
    """Endpoint: admin.list_products"""
    if current_user.role != "admin":
        return "Acesso negado", 403

    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
def add_product():
    if current_user.role != "admin":
        return "Acesso negado", 403

    if request.method == "POST":
        name = request.form.get("name")
        sku = request.form.get("sku")
        price = request.form.get("price")
        stock = request.form.get("stock")
        description = request.form.get("description")
        image_file = request.files.get("image")

        image_url = upload_image_to_s3(image_file)

        product = Product(
            name=name,
            sku=sku,
            price=price,
            stock=stock,
            description=description,
            image_url=image_url,
            active=True,
        )
        db.session.add(product)
        db.session.commit()

        flash("Produto criado com sucesso!", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/product_form.html", product=None)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    if current_user.role != "admin":
        return "Acesso negado", 403

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name")
        product.sku = request.form.get("sku")
        product.price = request.form.get("price")
        product.stock = request.form.get("stock")
        product.description = request.form.get("description")

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            image_url = upload_image_to_s3(image_file)
            if image_url:
                product.image_url = image_url

        db.session.commit()
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("admin.list_products"))

    return render_template("admin/product_form.html", product=product)


@admin_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@login_required
def toggle_product(product_id):
    if current_user.role != "admin":
        return "Acesso negado", 403

    product = Product.query.get_or_404(product_id)
    product.active = not product.active
    db.session.commit()

    flash("Status do produto atualizado.", "info")
    return redirect(url_for("admin.list_products"))


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    if current_user.role != "admin":
        return "Acesso negado", 403

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash("Produto removido.", "warning")
    return redirect(url_for("admin.list_products"))

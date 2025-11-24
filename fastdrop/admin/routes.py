from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models import Product, Order, Vendor

admin_bp = Blueprint("admin", __name__)

def admin_required(func):
    from functools import wraps
    from flask import abort
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    product_count = Product.query.count()
    vendor_count = Vendor.query.count()
    pending_orders = Order.query.filter_by(status="pendente").count()
    return render_template(
        "admin/dashboard.html",
        product_count=product_count,
        vendor_count=vendor_count,
        pending_orders=pending_orders,
    )

@admin_bp.route("/products")
@login_required
@admin_required
def products():
    products = Product.query.all()
    return render_template("admin/products.html", products=products)

@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=orders)

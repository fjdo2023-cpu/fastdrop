from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import Vendor, Product, Order

vendor_bp = Blueprint("vendor", __name__)
def vendor_required(func):
    from functools import wraps
    from flask import abort
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "vendor":
            abort(403)
        return func(*args, **kwargs)
    return wrapper

@vendor_bp.route("/dashboard")
@login_required
@vendor_required
def dashboard():
    vendor = current_user.vendor
    order_count = Order.query.filter_by(vendor_id=vendor.id).count() if vendor else 0
    return render_template("vendor/dashboard.html", order_count=order_count)

@vendor_bp.route("/catalog")
@login_required
@vendor_required
def catalog():
    products = Product.query.filter_by(active=True).all()
    return render_template("vendor/catalog.html", products=products)

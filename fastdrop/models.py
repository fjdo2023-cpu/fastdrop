from datetime import datetime
from flask_login import UserMixin
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="vendor")  # 'admin' or 'vendor'
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship("Vendor", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    document = db.Column(db.String(50))  # CPF/CNPJ
    phone = db.Column(db.String(50))
    bling_connected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="vendor")
    bling_account = db.relationship("BlingAccount", back_populates="vendor", uselist=False)
    orders = db.relationship("Order", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor {self.company_name}>"

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    wholesale_price = db.Column(db.Numeric(10, 2), nullable=False)
    suggested_price = db.Column(db.Numeric(10, 2))
    weight = db.Column(db.Numeric(10, 3))  # kg
    width = db.Column(db.Numeric(10, 2))   # cm
    height = db.Column(db.Numeric(10, 2))
    length = db.Column(db.Numeric(10, 2))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stock = db.relationship("ProductStock", back_populates="product", uselist=False)
    order_items = db.relationship("OrderItem", back_populates="product")

    def __repr__(self):
        return f"<Product {self.sku}>"

class ProductStock(db.Model):
    __tablename__ = "product_stock"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    location = db.Column(db.String(50), default="CD-DEFAULT")
    estoque_total = db.Column(db.Integer, default=0)
    estoque_reservado = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship("Product", back_populates="stock")

    @property
    def estoque_disponivel(self):
        return max(0, (self.estoque_total or 0) - (self.estoque_reservado or 0))

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    origin = db.Column(db.String(50), default="bling")  # bling, manual, api
    external_order_id = db.Column(db.String(100))      # ID no Bling
    external_number = db.Column(db.String(100))        # número do pedido no Bling
    customer_name = db.Column(db.String(200))
    customer_document = db.Column(db.String(50))
    customer_phone = db.Column(db.String(50))
    customer_email = db.Column(db.String(120))
    shipping_address = db.Column(db.Text)
    status = db.Column(db.String(30), default="pendente")  # pendente, em_separacao, enviado, entregue, cancelado
    total_cost = db.Column(db.Numeric(10, 2), default=0)
    total_vendor_price = db.Column(db.Numeric(10, 2), default=0)
    tracking_code = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = db.relationship("Vendor", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="order")

    def __repr__(self):
        return f"<Order {self.id} vendor={self.vendor_id}>"

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    sku = db.Column(db.String(100))
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    unit_vendor_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_cost = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_vendor_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

class BlingAccount(db.Model):
    __tablename__ = "bling_accounts"

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    access_token = db.Column(db.String(500), nullable=False)
    refresh_token = db.Column(db.String(500), nullable=False)
    token_expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = db.relationship("Vendor", back_populates="bling_account")

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    provider = db.Column(db.String(50), default="mercadopago")
    external_payment_id = db.Column(db.String(100))
    status = db.Column(db.String(50))  # created, pending, approved, rejected, refunded
    amount = db.Column(db.Numeric(10, 2))
    raw_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = db.relationship("Order", back_populates="payments")

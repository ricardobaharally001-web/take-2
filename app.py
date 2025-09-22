"""
Professional Shopify-Style E-commerce Flask App

Ready for GitHub and Render deployment with Supabase Storage integration.
"""

from __future__ import annotations

import os
import json
from decimal import Decimal
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, login_required, current_user
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from supabase_helpers import upload_image_to_supabase


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "admin.login"
csrf = CSRFProtect()


# ================================ MODELS ================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    products = db.relationship("Product", backref="category", lazy=True)

    def __str__(self) -> str:
        return self.name


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    image_filename = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items_json = db.Column(db.Text, default="[]")
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(50), default="pending")
    customer_name = db.Column(db.String(200))
    customer_email = db.Column(db.String(200))
    customer_phone = db.Column(db.String(50))
    customer_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1)
    store_name = db.Column(db.String(200), default="Professional Store")
    tagline = db.Column(db.String(250), default="Discover Amazing Products")
    contact_email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    theme_color = db.Column(db.String(50), default="blue")
    logo_filename = db.Column(db.String(500), nullable=True)
    paypal_client_id = db.Column(db.String(200), default="YOUR_PAYPAL_CLIENT_ID")
    mmg_instructions = db.Column(db.Text, default="")


# ================================ FORMS ================================
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login")


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save")


class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    price = DecimalField("Price", places=2, rounding=None, validators=[DataRequired(), NumberRange(min=0)])
    stock_quantity = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    image = FileField("Image", validators=[Optional()])
    submit = SubmitField("Save")


class SettingsForm(FlaskForm):
    store_name = StringField("Store Name", validators=[DataRequired(), Length(min=2, max=200)])
    tagline = StringField("Tagline", validators=[Optional(), Length(max=250)])
    contact_email = StringField("Email", validators=[Optional(), Email()])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    address = TextAreaField("Address", validators=[Optional()])
    theme_color = SelectField("Theme", choices=[("blue", "Blue"), ("green", "Green"), ("red", "Red"), ("purple", "Purple"), ("teal", "Teal")])
    paypal_client_id = StringField("PayPal Client ID", validators=[Optional()])
    mmg_instructions = TextAreaField("MMG Instructions", validators=[Optional()])
    logo = FileField("Logo", validators=[Optional()])
    submit = SubmitField("Save Settings")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Change Password")


# ================================ UTILITIES ================================
def get_settings() -> Settings:
    s = Settings.query.get(1)
    if not s:
        s = Settings(id=1)
        db.session.add(s)
        db.session.commit()
    return s


def save_uploaded(file_storage):
    if not file_storage:
        return None
    # Prefer Supabase storage
    try:
        return upload_image_to_supabase(file_storage)
    except Exception as e:
        print(f"Supabase upload failed: {e}")
        return None


def format_gyd(value):
    try:
        val = Decimal(value)
        return f"GY${val:,.2f}"
    except Exception:
        return str(value)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================================ APP FACTORY ================================
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
    # Render provides DATABASE_URL that may start with postgres://, fix for SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Create tables and seed defaults
    with app.app_context():
        db.create_all()
        # Seed admin
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com").lower()
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        if not User.query.filter_by(email=admin_email).first():
            u = User(email=admin_email)
            u.set_password(admin_password)
            db.session.add(u)
            db.session.commit()
        get_settings()

    # Filters
    app.add_template_filter(format_gyd, name="gyd")

    # Context processor
    @app.context_processor
    def inject_globals():
        s = get_settings()
        cart = session.get("cart", {})
        cart_count = sum(item.get("qty", 0) for item in cart.values())
        return dict(settings=s, cart_count=cart_count)

    # Static uploaded file compatibility (if path is URL just redirect)
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        # This is kept for backward compatibility; Supabase images use public URLs
        return redirect(url_for("static", filename=filename))

    # ================================ BLUEPRINTS ================================
    from flask import Blueprint

    admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
    store_bp = Blueprint("store", __name__)

    # ---------------- Admin Routes ----------------
    @admin_bp.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.strip().lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Logged in successfully.", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Invalid email or password.", "danger")
        return render_template("admin_login.html", form=form)

    @admin_bp.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "success")
        return redirect(url_for("admin.login"))

    @admin_bp.route("/")
    @login_required
    def dashboard():
        try:
            product_count = Product.query.count()
            category_count = Category.query.count()
            order_count = Order.query.count()
            low_stock_products = Product.query.filter(Product.stock_quantity <= 5, Product.stock_quantity > 0).count()
            recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
            return render_template(
                "admin_dashboard.html",
                product_count=product_count,
                category_count=category_count,
                order_count=order_count,
                low_stock_products=low_stock_products,
                recent_orders=recent_orders,
            )
        except Exception as e:
            print(f"Error in dashboard: {e}")
            flash("Error loading dashboard data.", "warning")
            return render_template(
                "admin_dashboard.html",
                product_count=0,
                category_count=0,
                order_count=0,
                low_stock_products=0,
                recent_orders=[],
            )

    @admin_bp.route("/categories", methods=["GET"]) 
    @login_required
    def admin_categories():
        categories = Category.query.order_by(Category.name).all()
        return render_template("admin_categories.html", categories=categories)

    @admin_bp.route("/categories/new", methods=["GET", "POST"]) 
    @login_required
    def admin_categories_new():
        form = CategoryForm()
        if form.validate_on_submit():
            if Category.query.filter_by(name=form.name.data.strip()).first():
                flash("Category name already exists.", "danger")
            else:
                c = Category(name=form.name.data.strip(), description=form.description.data or "")
                db.session.add(c)
                db.session.commit()
                flash("Category created successfully.", "success")
                return redirect(url_for("admin.admin_categories"))
        return render_template("admin_categories.html", form=form, create_view=True)

    @admin_bp.route("/categories/<int:cid>/delete", methods=["POST"]) 
    @login_required
    def admin_categories_delete(cid):
        category = Category.query.get_or_404(cid)
        if category.products:
            flash("Cannot delete category with products.", "danger")
        else:
            db.session.delete(category)
            db.session.commit()
            flash("Category deleted.", "success")
        return redirect(url_for("admin.admin_categories"))

    @admin_bp.route("/products") 
    @login_required
    def admin_products():
        category_id = request.args.get("category", type=int)
        if category_id:
            products = Product.query.filter_by(category_id=category_id).order_by(Product.created_at.desc()).all()
            current_category = Category.query.get(category_id)
        else:
            products = Product.query.order_by(Product.created_at.desc()).all()
            current_category = None
        categories = Category.query.order_by(Category.name).all()
        return render_template("admin_products.html", products=products, categories=categories, current_category=current_category)

    @admin_bp.route("/products/new", methods=["GET", "POST"]) 
    @login_required
    def admin_products_new():
        form = ProductForm()
        form.category_id.choices = [(0, "No Category")] + [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        if form.validate_on_submit():
            img_url = save_uploaded(form.image.data) if form.image.data else None
            p = Product(
                name=form.name.data.strip(),
                description=form.description.data or "",
                price=Decimal(str(form.price.data)),
                stock_quantity=form.stock_quantity.data,
                category_id=form.category_id.data if form.category_id.data != 0 else None,
                is_active=form.is_active.data or False,
                image_filename=img_url,
            )
            db.session.add(p)
            db.session.commit()
            flash("Product created successfully.", "success")
            return redirect(url_for("admin.admin_products"))
        return render_template("admin_products.html", form=form, create_view=True)

    @admin_bp.route("/products/<int:pid>/edit", methods=["GET", "POST"]) 
    @login_required
    def admin_products_edit(pid):
        product = Product.query.get_or_404(pid)
        form = ProductForm(
            name=product.name,
            description=product.description,
            price=float(product.price or 0),
            stock_quantity=product.stock_quantity,
            category_id=product.category_id or 0,
            is_active=product.is_active,
        )
        form.category_id.choices = [(0, "No Category")] + [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        if form.validate_on_submit():
            product.name = form.name.data.strip()
            product.description = form.description.data or ""
            product.price = Decimal(str(form.price.data))
            product.stock_quantity = form.stock_quantity.data
            product.category_id = form.category_id.data if form.category_id.data != 0 else None
            product.is_active = form.is_active.data or False
            if form.image.data:
                img_url = save_uploaded(form.image.data)
                if img_url:
                    product.image_filename = img_url
            db.session.commit()
            flash("Product updated successfully.", "success")
            return redirect(url_for("admin.admin_products"))
        return render_template("admin_products.html", form=form, edit_view=True, product=product)

    @admin_bp.route("/products/<int:pid>/delete", methods=["POST"]) 
    @login_required
    def admin_products_delete(pid):
        product = Product.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "info")
        return redirect(url_for("admin.admin_products"))

    @admin_bp.route("/orders") 
    @login_required
    def admin_orders():
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("admin_orders.html", orders=orders)

    @admin_bp.route("/settings", methods=["GET", "POST"]) 
    @login_required
    def settings_view():
        s = get_settings()
        form = SettingsForm(
            store_name=s.store_name,
            tagline=s.tagline,
            contact_email=s.contact_email,
            phone=s.phone,
            address=s.address,
            theme_color=s.theme_color,
            paypal_client_id=s.paypal_client_id,
            mmg_instructions=s.mmg_instructions,
        )
        if form.validate_on_submit():
            s.store_name = form.store_name.data.strip()
            s.tagline = form.tagline.data.strip() if form.tagline.data else ""
            s.contact_email = form.contact_email.data.strip() if form.contact_email.data else ""
            s.phone = form.phone.data.strip() if form.phone.data else ""
            s.address = form.address.data.strip() if form.address.data else ""
            s.theme_color = form.theme_color.data
            s.paypal_client_id = form.paypal_client_id.data.strip() if form.paypal_client_id.data else s.paypal_client_id
            s.mmg_instructions = form.mmg_instructions.data or ""
            if form.logo.data:
                logo_url = save_uploaded(form.logo.data)
                if logo_url:
                    s.logo_filename = logo_url
            db.session.commit()
            flash("Settings saved successfully.", "success")
            return redirect(url_for("admin.settings_view"))
        return render_template("admin_settings.html", form=form, settings=s)

    @admin_bp.route("/change-password", methods=["GET", "POST"]) 
    @login_required
    def change_password():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash("Password updated successfully.", "success")
                return redirect(url_for("admin.dashboard"))
            else:
                flash("Current password is incorrect.", "danger")
        return render_template("admin_change_password.html", form=form)

    # ---------------- Store Routes ----------------
    @store_bp.route("/")
    def index():
        products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
        return render_template("index.html", products=products)

    @store_bp.route("/products")
    def products_view():
        category_id = request.args.get("category", type=int)
        q = Product.query.filter_by(is_active=True)
        if category_id:
            q = q.filter_by(category_id=category_id)
        products = q.order_by(Product.created_at.desc()).all()
        return render_template("products.html", products=products)

    @store_bp.route("/product/<int:product_id>")
    def product_detail(product_id):
        p = Product.query.get_or_404(product_id)
        return render_template("product_detail.html", product=p)

    # ---- Cart Helpers ----
    def _get_cart():
        return session.setdefault("cart", {})

    def _save_cart(cart):
        session["cart"] = cart
        session.modified = True

    @store_bp.route("/cart")
    def cart_view():
        cart = _get_cart()
        items = []
        total = Decimal("0.00")
        for pid, data in cart.items():
            product = Product.query.get(int(pid))
            if not product:
                continue
            qty = int(data.get("qty", 1))
            price = Decimal(str(product.price))
            subtotal = price * qty
            total += subtotal
            items.append({
                "product": product,
                "qty": qty,
                "subtotal": subtotal,
            })
        return render_template("cart.html", items=items, total=total)

    @store_bp.route("/cart/add", methods=["POST"]) 
    def cart_add():
        pid = request.form.get("product_id") or request.json.get("product_id")
        qty = int(request.form.get("qty", 1) if request.form else request.json.get("qty", 1))
        product = Product.query.get_or_404(int(pid))
        if product.stock_quantity <= 0:
            return jsonify({"ok": False, "message": "Out of stock"}), 400
        cart = _get_cart()
        item = cart.get(str(pid), {"qty": 0})
        item["qty"] = int(item.get("qty", 0)) + qty
        cart[str(pid)] = item
        _save_cart(cart)
        return jsonify({"ok": True, "cart_count": sum(i.get("qty", 0) for i in cart.values())})

    @store_bp.route("/cart/update", methods=["POST"]) 
    def cart_update():
        pid = str(request.form.get("product_id") or request.json.get("product_id"))
        qty = int(request.form.get("qty", 1) if request.form else request.json.get("qty", 1))
        cart = _get_cart()
        if pid in cart:
            if qty <= 0:
                cart.pop(pid, None)
            else:
                cart[pid]["qty"] = qty
            _save_cart(cart)
        # compute cart_count and optional subtotal for this item
        cart_count = sum(i.get("qty", 0) for i in cart.values())
        subtotal = None
        if pid in cart:
            product = Product.query.get(int(pid))
            if product:
                subtotal = float(Decimal(str(product.price)) * int(cart[pid]["qty"]))
        return jsonify({"ok": True, "cart_count": cart_count, "subtotal": subtotal})

    @store_bp.route("/cart/remove", methods=["POST"]) 
    def cart_remove():
        pid = str(request.form.get("product_id") or request.json.get("product_id"))
        cart = _get_cart()
        cart.pop(pid, None)
        _save_cart(cart)
        return jsonify({"ok": True, "cart_count": sum(i.get("qty", 0) for i in cart.values())})

    @store_bp.route("/checkout", methods=["GET", "POST"]) 
    def checkout():
        cart = _get_cart()
        if request.method == "POST":
            data = request.form
            # compute total
            total = Decimal("0.00")
            items = []
            for pid, item in cart.items():
                product = Product.query.get(int(pid))
                if not product:
                    continue
                qty = int(item.get("qty", 1))
                price = Decimal(str(product.price))
                total += price * qty
                items.append({"id": product.id, "name": product.name, "qty": qty, "price": str(price)})

            order = Order(
                items_json=json.dumps(items),
                total_amount=total,
                status="pending",
                customer_name=data.get("name"),
                customer_email=data.get("email"),
                customer_phone=data.get("phone"),
                customer_address=data.get("address"),
            )
            db.session.add(order)
            db.session.commit()
            session["cart"] = {}
            flash("Order placed successfully.", "success")
            return redirect(url_for("store.index"))

        # GET
        items = []
        total = Decimal("0.00")
        for pid, item in cart.items():
            product = Product.query.get(int(pid))
            if not product:
                continue
            qty = int(item.get("qty", 1))
            price = Decimal(str(product.price))
            subtotal = price * qty
            total += subtotal
            items.append({"product": product, "qty": qty, "subtotal": subtotal})
        return render_template("checkout.html", items=items, total=total)

    # ---- API Aliases for JS compatibility ----
    @store_bp.route("/api/cart/add", methods=["POST"])
    def api_cart_add():
        return cart_add()

    @store_bp.route("/api/cart/update", methods=["POST"])
    def api_cart_update():
        return cart_update()

    @store_bp.route("/api/cart/remove", methods=["POST"])
    def api_cart_remove():
        return cart_remove()

    @store_bp.route("/api/order/cash", methods=["POST"])
    def api_order_cash():
        data = request.get_json(silent=True) or {}
        cart = _get_cart()
        total = Decimal("0.00")
        items = []
        for pid, item in cart.items():
            product = Product.query.get(int(pid))
            if not product:
                continue
            qty = int(item.get("qty", 1))
            price = Decimal(str(product.price))
            total += price * qty
            items.append({"id": product.id, "name": product.name, "qty": qty, "price": str(price)})
        if not items:
            return jsonify({"ok": False, "error": "Cart is empty"}), 400
        order = Order(
            items_json=json.dumps(items),
            total_amount=total,
            status="pending",
            customer_name=data.get("name"),
            customer_email=data.get("email"),
            customer_phone=data.get("phone"),
            customer_address=data.get("address"),
        )
        db.session.add(order)
        db.session.commit()
        session["cart"] = {}
        return jsonify({"ok": True, "order_id": order.id, "wa_url": None})

    @store_bp.route("/api/order/paypal", methods=["POST"])
    def api_order_paypal():
        # For demo, treat same as cash and return success JSON. Integrate PayPal SDK here if needed.
        return api_order_cash()

    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(store_bp)

    return app


# For local development convenience
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)

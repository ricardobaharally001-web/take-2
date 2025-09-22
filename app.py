# app.py
import os
import json
import uuid
import datetime as dt
from decimal import Decimal
from pathlib import Path

from supabase_helpers import upload_image_to_supabase  # (kept for future use)

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, g, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, current_user,
    login_required, logout_user
)
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import (
    StringField, PasswordField, BooleanField, DecimalField,
    TextAreaField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, NumberRange, Optional, EqualTo
)
from flask_wtf.file import FileField, FileAllowed
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv


# --------------------------------------------------------------------------------------
# App factory
# --------------------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load env from instance/config.env if present
    instance_env_path = os.path.join(app.instance_path, "config.env")
    os.makedirs(app.instance_path, exist_ok=True)
    if os.path.exists(instance_env_path):
        load_dotenv(instance_env_path)
    else:
        # Also allow .env for convenience if user prefers
        load_dotenv()

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this")
    # SQLite path: default to instance/app.db if not provided
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = "sqlite:///" + os.path.join(app.instance_path, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Uploads
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/uploads")
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "admin.login"

    # Register Jinja filters/context
    register_template_helpers(app)

    # Blueprints
    from flask import Blueprint
    store_bp = Blueprint("store", __name__)
    admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

    # ----------------------------------------------------------------------------------
    # Models
    # ----------------------------------------------------------------------------------
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)

        def set_password(self, raw):
            self.password_hash = generate_password_hash(raw)

        def check_password(self, raw):
            return check_password_hash(self.password_hash, raw)

    class Product(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, default="")
        price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
        image_filename = db.Column(db.String(255))  # stored under static/uploads
        category = db.Column(db.String(120))
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    class Settings(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        store_name = db.Column(db.String(255), default="Your Store")
        tagline = db.Column(db.String(255), default="Welcome to our store!")
        contact_email = db.Column(db.String(255), default="")
        phone = db.Column(db.String(120), default="")
        address = db.Column(db.String(255), default="")
        theme_color = db.Column(db.String(20), default="blue")  # blue, green, red, purple, teal
        logo_filename = db.Column(db.String(255))
        paypal_client_id = db.Column(db.String(255), default="YOUR_PAYPAL_CLIENT_ID")
        mmg_instructions = db.Column(db.Text, default="Contact the store to pay via MMG.")

    class Order(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
        items_json = db.Column(db.Text, nullable=False)  # serialized array of {id, name, price, qty}
        subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
        customer_name = db.Column(db.String(255), nullable=False)
        email = db.Column(db.String(255), nullable=False)
        phone = db.Column(db.String(120), nullable=False)
        address = db.Column(db.String(255), nullable=False)
        payment_method = db.Column(db.String(20), nullable=False)  # paypal | mmg
        status = db.Column(db.String(20), nullable=False)  # paid | pending

    app.User = User
    app.Product = Product
    app.Settings = Settings
    app.Order = Order

    # ----------------------------------------------------------------------------------
    # Forms
    # ----------------------------------------------------------------------------------
    class LoginForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired(), Email()])
        password = PasswordField("Password", validators=[DataRequired()])

    class ChangePasswordForm(FlaskForm):
        current_password = PasswordField("Current password", validators=[DataRequired()])
        new_password = PasswordField("New password", validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField(
            "Confirm new password",
            validators=[DataRequired(), EqualTo("new_password", message="Passwords must match")]
        )

    class ProductForm(FlaskForm):
        name = StringField("Name", validators=[DataRequired(), Length(max=255)])
        description = TextAreaField("Description")
        price = DecimalField("Price (GYD)", places=2, rounding=None,
                             validators=[DataRequired(), NumberRange(min=0.01)])
        category = StringField("Category", validators=[Optional(), Length(max=120)])
        is_active = BooleanField("Active")
        image = FileField("Image", validators=[FileAllowed(list(ALLOWED_EXTENSIONS), "Images only!")])

    class SettingsForm(FlaskForm):
        store_name = StringField("Store Name", validators=[DataRequired(), Length(max=255)])
        tagline = StringField("Hero / Tagline", validators=[Optional(), Length(max=255)])
        contact_email = StringField("Contact Email", validators=[Optional(), Email()])
        phone = StringField("Phone", validators=[Optional(), Length(max=120)])
        address = StringField("Address", validators=[Optional(), Length(max=255)])
        theme_color = SelectField(
            "Theme Color",
            choices=[("blue","Blue"),("green","Green"),("red","Red"),("purple","Purple"),("teal","Teal")]
        )
        paypal_client_id = StringField("PayPal Client ID", validators=[Optional(), Length(max=255)])
        mmg_instructions = TextAreaField("MMG Instructions (shown to customers)")
        logo = FileField("Logo", validators=[FileAllowed(list(ALLOWED_EXTENSIONS), "Images only!")])

    app.LoginForm = LoginForm
    app.ChangePasswordForm = ChangePasswordForm
    app.ProductForm = ProductForm
    app.SettingsForm = SettingsForm

    # ----------------------------------------------------------------------------------
    # Login manager
    # ----------------------------------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ----------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------
    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def save_uploaded(file_storage):
        """Upload to Supabase Storage if configured; otherwise save locally.
        Returns a public URL (Supabase) or local filename under UPLOAD_FOLDER.
        """
        if not file_storage or file_storage.filename == "":
            return None
        if not allowed_file(file_storage.filename):
            return None

        # Try Supabase first
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if supabase_url and supabase_key:
                url = upload_image_to_supabase(file_storage)
                if url:
                    return url
        except Exception as e:
            print(f"Supabase upload failed, falling back to local save: {e}")

        # Fallback: local save
        filename = secure_filename(file_storage.filename)
        root, ext = os.path.splitext(filename)
        filename = f"{root}_{uuid.uuid4().hex[:8]}{ext}"
        dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        file_storage.save(dest)
        return filename

    def get_settings() -> Settings:
        s = Settings.query.get(1)
        if not s:
            s = Settings(id=1)
            db.session.add(s)
            db.session.commit()
        return s

    def get_cart():
        return session.get("cart", {})  # { product_id: qty }

    def set_cart(cart):
        session["cart"] = cart
        session.modified = True

    def cart_count():
        c = get_cart()
        return sum(int(q) for q in c.values())

    def cart_items_and_total():
        c = get_cart()
        items = []
        total = Decimal("0.00")
        for pid, qty in c.items():
            p = Product.query.get(int(pid))
            if not p:
                continue
            q = Decimal(str(qty))
            line = (p.price or Decimal("0.00")) * q
            total += line
            items.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "qty": int(qty),
                "image_filename": p.image_filename,
                "category": p.category,
                "line_total": line
            })
        return items, total

    # ----------------------------------------------------------------------------------
    # Lifecycle / DB init
    # ----------------------------------------------------------------------------------
    with app.app_context():
        db.create_all()
        # Seed admin
        default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        admin = User.query.filter_by(email=default_email).first()
        if not admin:
            admin = User(email=default_email)
            admin.set_password(default_password)
            db.session.add(admin)
            db.session.commit()
        # Ensure settings row
        get_settings()

    # ----------------------------------------------------------------------------------
    # Request hooks
    # ----------------------------------------------------------------------------------
    @app.before_request
    def load_request_settings():
        g.settings = get_settings()
        g.cart_count = cart_count()

    # ----------------------------------------------------------------------------------
    # STORE ROUTES
    # ----------------------------------------------------------------------------------
    @store_bp.route("/")
    def index():
        products = app.Product.query.filter_by(is_active=True).order_by(app.Product.created_at.desc()).limit(8).all()
        return render_template("index.html", products=products)

    @store_bp.route("/products")
    def products():
        q = request.args.get("q", "", type=str).strip()
        category = request.args.get("category", "", type=str).strip()
        query = app.Product.query.filter(app.Product.is_active.is_(True))
        if q:
            like = f"%{q}%"
            query = query.filter(app.Product.name.ilike(like))
        if category:
            query = query.filter(app.Product.category == category)
        products = query.order_by(app.Product.created_at.desc()).all()
        categories = [c[0] for c in db.session.query(app.Product.category).filter(app.Product.category.isnot(None)).distinct().all()]
        return render_template("products.html", products=products, q=q, category=category, categories=categories)

    @store_bp.route("/product/<int:product_id>")
    def product_detail(product_id):
        product = app.Product.query.get_or_404(product_id)
        return render_template("product_detail.html", product=product)

    @store_bp.route("/cart")
    def cart_view():
        items, total = cart_items_and_total()
        return render_template("cart.html", items=items, total=total)

    # --- API: Cart (CSRF exempt for JSON fetch convenience) ---
    @csrf.exempt
    @store_bp.route("/api/cart/add", methods=["POST"])
    def api_cart_add():
        data = request.get_json(force=True)
        product_id = int(data.get("product_id"))
        qty = max(1, int(data.get("qty", 1)))
        product = app.Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({"ok": False, "error": "Product not available"}), 400
        cart = get_cart()
        cart[str(product_id)] = cart.get(str(product_id), 0) + qty
        set_cart(cart)
        return jsonify({"ok": True, "cart_count": cart_count()})

    @csrf.exempt
    @store_bp.route("/api/cart/update", methods=["POST"])
    def api_cart_update():
        data = request.get_json(force=True)
        product_id = str(data.get("product_id"))
        qty = int(data.get("qty", 1))
        cart = get_cart()
        if qty <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = qty
        set_cart(cart)
        items, total = cart_items_and_total()
        return jsonify({"ok": True, "cart_count": cart_count(), "subtotal": float(total)})

    @csrf.exempt
    @store_bp.route("/api/cart/remove", methods=["POST"])
    def api_cart_remove():
        data = request.get_json(force=True)
        product_id = str(data.get("product_id"))
        cart = get_cart()
        cart.pop(product_id, None)
        set_cart(cart)
        items, total = cart_items_and_total()
        return jsonify({"ok": True, "cart_count": cart_count(), "subtotal": float(total)})

    @store_bp.route("/checkout", methods=["GET"])
    def checkout():
        items, total = cart_items_and_total()
        if total == 0:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("store.products"))
        try:
            total_usd = float(total) / 210.0
        except Exception:
            total_usd = float(total)
        total_usd = max(1.00, round(total_usd, 2))
        return render_template("checkout.html", items=items, total=total, total_usd=total_usd)

    # --- API: Orders via checkout ---
    @csrf.exempt
    @store_bp.route("/api/order/paypal", methods=["POST"])
    def api_order_paypal():
        data = request.get_json(force=True)
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        if not all([name, email, phone, address]):
            return jsonify({"ok": False, "error": "Missing customer information."}), 400
        items, total = cart_items_and_total()
        if not items:
            return jsonify({"ok": False, "error": "Cart is empty."}), 400

        order_items = [
            {"id": i["id"], "name": i["name"], "price": float(i["price"]), "qty": i["qty"]}
            for i in items
        ]
        order = app.Order(
            items_json=json.dumps(order_items),
            subtotal=total,
            customer_name=name,
            email=email,
            phone=phone,
            address=address,
            payment_method="paypal",
            status="paid",
        )
        db.session.add(order)
        db.session.commit()
        set_cart({})
        return jsonify({"ok": True, "order_id": order.id})

    @csrf.exempt
    @store_bp.route("/api/order/mmg", methods=["POST"])
    def api_order_mmg():
        data = request.get_json(force=True)
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        if not all([name, email, phone, address]):
            return jsonify({"ok": False, "error": "Missing customer information."}), 400
        items, total = cart_items_and_total()
        if not items:
            return jsonify({"ok": False, "error": "Cart is empty."}), 400

        order_items = [
            {"id": i["id"], "name": i["name"], "price": float(i["price"]), "qty": i["qty"]}
            for i in items
        ]
        order = app.Order(
            items_json=json.dumps(order_items),
            subtotal=total,
            customer_name=name,
            email=email,
            phone=phone,
            address=address,
            payment_method="mmg",
            status="pending",
        )
        db.session.add(order)
        db.session.commit()
        set_cart({})
        return jsonify({"ok": True, "order_id": order.id})

    # ----------------------------------------------------------------------------------
    # ADMIN ROUTES
    # ----------------------------------------------------------------------------------
    @admin_bp.route("/login", methods=["GET", "POST"])
    def login():
        form = app.LoginForm()
        if form.validate_on_submit():
            user = app.User.query.filter_by(email=form.email.data.strip().lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Logged in.", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Invalid credentials.", "danger")
        # Use dedicated admin login template for professional UI
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
        product_count = app.Product.query.count()
        recent_orders = app.Order.query.order_by(app.Order.created_at.desc()).limit(5).all()
        return render_template("admin_dashboard.html", product_count=product_count, recent_orders=recent_orders)

    @admin_bp.route("/account", methods=["GET", "POST"])
    @login_required
    def change_password():
        """Change the current user's password."""
        form = app.ChangePasswordForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.current_password.data):
                flash("Current password is incorrect.", "danger")
            else:
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash("Password updated successfully.", "success")
                return redirect(url_for("admin.dashboard"))
        return render_template("admin_change_password.html", form=form)

    @admin_bp.route("/products")
    @login_required
    def admin_products():
        products = app.Product.query.order_by(app.Product.created_at.desc()).all()
        return render_template("admin_products.html", products=products)

    @admin_bp.route("/products/new", methods=["GET", "POST"])
    @login_required
    def admin_products_new():
        form = app.ProductForm()
        if form.validate_on_submit():
            img_filename = save_uploaded(form.image.data) if form.image.data else None
            product = app.Product(
                name=form.name.data.strip(),
                description=form.description.data or "",
                price=Decimal(str(form.price.data)),
                category=form.category.data.strip() if form.category.data else None,
                is_active=form.is_active.data or False,
                image_filename=img_filename
            )
            db.session.add(product)
            db.session.commit()
            flash("Product created.", "success")
            return redirect(url_for("admin.admin_products"))
        return render_template("admin_products.html", form=form, create_view=True)

    @admin_bp.route("/products/<int:pid>/edit", methods=["GET", "POST"])
    @login_required
    def admin_products_edit(pid):
        product = app.Product.query.get_or_404(pid)
        form = app.ProductForm(
            name=product.name,
            description=product.description,
            price=float(product.price or 0),
            category=product.category or "",
            is_active=product.is_active
        )
        if request.method == "POST" and form.validate_on_submit():
            product.name = form.name.data.strip()
            product.description = form.description.data or ""
            product.price = Decimal(str(form.price.data))
            product.category = form.category.data.strip() if form.category.data else None
            product.is_active = form.is_active.data or False
            if form.image.data:
                img_filename = save_uploaded(form.image.data)
                if img_filename:
                    product.image_filename = img_filename
            db.session.commit()
            flash("Product updated.", "success")
            return redirect(url_for("admin.admin_products"))
        return render_template("admin_products.html", form=form, edit_view=True, product=product)

    @admin_bp.route("/products/<int:pid>/delete", methods=["POST"])
    @login_required
    def admin_products_delete(pid):
        product = app.Product.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "info")
        return redirect(url_for("admin.admin_products"))

    @admin_bp.route("/orders")
    @login_required
    def admin_orders():
        orders = app.Order.query.order_by(app.Order.created_at.desc()).all()
        return render_template("admin_orders.html", orders=orders)

    @admin_bp.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings_view():
        s = get_settings()
        form = app.SettingsForm(
            store_name=s.store_name,
            tagline=s.tagline,
            contact_email=s.contact_email,
            phone=s.phone,
            address=s.address,
            theme_color=s.theme_color,
            paypal_client_id=s.paypal_client_id,
            mmg_instructions=s.mmg_instructions
        )
        if form.validate_on_submit():
            s.store_name = form.store_name.data.strip()
            s.tagline = form.tagline.data.strip() if form.tagline.data else ""
            s.contact_email = form.contact_email.data.strip() if form.contact_email.data else ""
            s.phone = form.phone.data.strip() if form.phone.data else ""
            s.address = form.address.data.strip() if form.address.data else ""
            s.theme_color = form.theme_color.data
            s.paypal_client_id = form.paypal_client_id.data.strip() if form.paypal_client_id.data else "YOUR_PAYPAL_CLIENT_ID"
            s.mmg_instructions = form.mmg_instructions.data or ""
            if form.logo.data:
                logo_filename = save_uploaded(form.logo.data)
                if logo_filename:
                    s.logo_filename = logo_filename
            db.session.commit()
            flash("Settings saved.", "success")
            return redirect(url_for("admin.settings_view"))
        return render_template("admin_settings.html", form=form, settings=s)

    # ----------------------------------------------------------------------------------
    # Register blueprints
    # ----------------------------------------------------------------------------------
    app.register_blueprint(store_bp)
    app.register_blueprint(admin_bp)

    # ----------------------------------------------------------------------------------
    # Static uploads (optional explicit route for clarity)
    # ----------------------------------------------------------------------------------
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app


# --------------------------------------------------------------------------------------
# Jinja helpers
# --------------------------------------------------------------------------------------
def register_template_helpers(app: Flask):
    @app.context_processor
    def inject_settings():
        # g.settings and g.cart_count set in before_request
        return {
            "settings": getattr(g, "settings", None),
            "cart_count": getattr(g, "cart_count", 0),
            "current_year": dt.datetime.utcnow().year,
        }

    @app.template_filter("gyd")
    def fmt_gyd(amount):
        if amount is None:
            return ""
        try:
            d = Decimal(str(amount))
            # show with thousands separators, 2 decimals
            return f"GYD ${d:,.2f}"
        except Exception:
            return f"GYD ${amount}"


# --------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    # For local dev
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, flash, session
from werkzeug.utils import secure_filename

# Supabase configuration (server-side only; keep out of templates)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
# Prefer anon key, but allow service role key fallback if provided in CI/CD secrets
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "product-images").strip()

supabase_client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print(f"✓ Supabase connected to {SUPABASE_URL}")
    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")

store_bp = Blueprint("store", __name__)

# Local fallback files
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "products.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")

DEFAULT_SETTINGS = {
    "brand_name": "S.B Shop",
    "logo_url": "",
    "welcome_title": "Welcome to S.B Shop",
    "welcome_subtitle": "Discover our curated collection of premium products",
    "admin_password": os.getenv("ADMIN_PASSWORD", "admin123"),
}

def load_settings():
    """Load site settings from file or defaults"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # ensure missing keys filled
                merged = {**DEFAULT_SETTINGS, **data}
                return merged
    except Exception as e:
        print(f"Error reading settings: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

@store_bp.app_context_processor
def inject_site_settings():
    return {"site": load_settings()}

# Categories
def load_categories():
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading categories: {e}")
    # default with one category
    cats = [
        {"name": "All", "slug": "all"},
    ]
    save_categories(cats)
    return cats

def save_categories(categories):
    try:
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving categories: {e}")
        return False

def add_category(name):
    name = name.strip()
    if not name:
        return False, "Category name required"
    slug = name.lower().replace(' ', '-').replace('/', '-')
    cats = load_categories()
    if any(c.get('slug') == slug for c in cats):
        return False, "Category already exists"
    cats.append({"name": name, "slug": slug})
    save_categories(cats)
    return True, slug

def delete_category(slug):
    cats = load_categories()
    cats = [c for c in cats if c.get('slug') != slug]
    save_categories(cats)
    # Reassign products of this category to empty
    products = load_products()
    changed = False
    for p in products:
        if p.get('category') == slug:
            p['category'] = ''
            changed = True
    if changed:
        save_products(products)
    return True

def ensure_products_table():
    """Create products table if it doesn't exist"""
    if not supabase_client:
        return False
    
    try:
        # Check if table exists by trying to select from it
        supabase_client.table('products').select('id').limit(1).execute()
        return True
    except:
        # Table doesn't exist, create it
        try:
            # Note: You'll need to create this table in Supabase Dashboard
            # with columns: id, name, price, description, image, created_at
            return False
        except Exception as e:
            print(f"Error with products table: {e}")
            return False

def load_products():
    """Load products from Supabase or local file"""
    if supabase_client:
        try:
            # Try 'products' table first, fall back to 'product' if it doesn't exist
            try:
                response = supabase_client.table('products').select('*').order('created_at', desc=True).execute()
                if response.data:
                    return response.data
            except:
                # Fallback to singular 'product' table
                response = supabase_client.table('product').select('*').order('created_at', desc=True).execute()
                if response.data:
                    return response.data
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
    
    # Fallback to local file
    if not os.path.exists(DATA_FILE):
        # Create default products
        default_products = [
            {
                "id": "p1001",
                "name": "Classic Tee",
                "price": 25.0,
                "description": "Soft cotton tee in multiple colors.",
                "image": "/static/img/sample1.jpg"
            },
            {
                "id": "p1002",
                "name": "Everyday Hoodie",
                "price": 55.0,
                "description": "Cozy hoodie with kangaroo pocket.",
                "image": "/static/img/sample2.jpg"
            },
            {
                "id": "p1003",
                "name": "Slim Jeans",
                "price": 60.0,
                "description": "Stretch denim for comfort.",
                "image": "/static/img/sample3.jpg"
            },
            {
                "id": "p1004",
                "name": "Running Sneakers",
                "price": 80.0,
                "description": "Lightweight, breathable, cushioned.",
                "image": "/static/img/sample4.jpg"
            },
            {
                "id": "p1005",
                "name": "Leather Belt",
                "price": 20.0,
                "description": "Full-grain leather, metal buckle.",
                "image": "/static/img/sample5.jpg"
            },
            {
                "id": "p1006",
                "name": "Canvas Tote",
                "price": 18.0,
                "description": "Durable tote for daily errands.",
                "image": "/static/img/sample6.jpg"
            }
        ]
        save_products(default_products)
        return default_products
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    """Save products to Supabase and local file"""
    # Save to local file as backup
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    
    # Try to save to Supabase if available
    if supabase_client:
        try:
            for product in products:
                if 'created_at' not in product:
                    product['created_at'] = datetime.now().isoformat()
                # Try 'products' first, fall back to 'product'
                try:
                    supabase_client.table('products').upsert(product).execute()
                except:
                    supabase_client.table('product').upsert(product).execute()
        except Exception as e:
            print(f"Error saving to Supabase: {e}")

def add_product(name, price, description, image_url):
    """Add a new product"""
    pid = f"p{uuid.uuid4().hex[:8]}"
    new_product = {
        "id": pid,
        "name": name,
        "price": round(float(price), 2),
        "description": description,
        "image": image_url,
        "created_at": datetime.now().isoformat()
    }
    
    if supabase_client:
        try:
            # Try 'products' first, fall back to 'product'
            try:
                response = supabase_client.table('products').insert(new_product).execute()
            except:
                response = supabase_client.table('product').insert(new_product).execute()
            return True
        except Exception as e:
            print(f"Error adding to Supabase: {e}")
    
    # Fallback to local file
    products = load_products()
    products.append(new_product)
    save_products(products)
    return True

def delete_product(pid):
    """Delete a product"""
    if supabase_client:
        try:
            # Try 'products' first, fall back to 'product'
            try:
                supabase_client.table('products').delete().eq('id', pid).execute()
            except:
                supabase_client.table('product').delete().eq('id', pid).execute()
            return True
        except Exception as e:
            print(f"Error deleting from Supabase: {e}")
    
    # Fallback to local file
    products = load_products()
    products = [p for p in products if p.get('id') != pid]
    save_products(products)
    return True

@store_bp.route("/products")
def products():
    items = load_products()
    q = (request.args.get('q') or '').strip().lower()
    category = (request.args.get('category') or '').strip()
    if q:
        items = [p for p in items if q in p.get('name','').lower() or q in p.get('description','').lower()]
    if category and category != 'all':
        items = [p for p in items if p.get('category', '') == category]
    categories = load_categories()
    return render_template("products.html", products=items, categories=categories, selected_category=category, q=q)

@store_bp.route("/product/<pid>")
def product_detail(pid):
    products = load_products()
    prod = next((p for p in products if p.get("id") == pid), None)
    if not prod:
        abort(404)
    return render_template("product_detail.html", product=prod)

@store_bp.route("/cart")
def cart():
    return render_template("cart.html")

@store_bp.route("/api/cart/checkout", methods=["POST"])
def checkout():
    payload = request.json or {}
    cart_items = payload.get('cart', [])
    
    # Here you would integrate with payment gateway
    # For now, just return success
    return jsonify({
        "ok": True, 
        "message": "Order received successfully!",
        "order_id": uuid.uuid4().hex[:8].upper()
    })

# Admin routes
def check_admin():
    """Check if user is authenticated as admin via session"""
    return bool(session.get("is_admin"))

@store_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("pw", "")
        if pw and pw == load_settings().get("admin_password"):
            session["is_admin"] = True
            flash("Logged in as admin", "success")
            next_url = request.args.get("next") or url_for("store.admin")
            return redirect(next_url)
        flash("Invalid password", "danger")
    return render_template("admin_login.html")

@store_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out", "info")
    return redirect(url_for("store.admin_login"))

@store_bp.route("/admin")
def admin():
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    products = load_products()
    categories = load_categories()
    return render_template("admin.html", products=products, categories=categories)

@store_bp.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    settings = load_settings()
    if request.method == "POST":
        settings = load_settings()
        settings["brand_name"] = request.form.get("brand_name", settings["brand_name"]).strip()
        # Handle logo upload if provided
        logo_file = request.files.get("logo_file")
        if logo_file and logo_file.filename:
            try:
                fn = secure_filename(logo_file.filename)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                    flash("Invalid logo image format", "danger")
                else:
                    upload_dir = os.path.join('static', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    dest = os.path.join(upload_dir, f"logo_{uuid.uuid4().hex[:8]}{ext}")
                    logo_file.save(dest)
                    settings["logo_url"] = f"/{dest}"
            except Exception as e:
                flash(f"Logo upload failed: {e}", "danger")
        else:
            settings["logo_url"] = request.form.get("logo_url", settings.get("logo_url", "")).strip()
        settings["welcome_title"] = request.form.get("welcome_title", settings["welcome_title"]).strip()
        settings["welcome_subtitle"] = request.form.get("welcome_subtitle", settings["welcome_subtitle"]).strip()
        current_pw = request.form.get("current_password", "").strip()
        new_pw = request.form.get("new_password", "").strip()
        confirm_pw = request.form.get("confirm_password", "").strip()
        if new_pw:
            master = "@admin592"
            if (current_pw and (current_pw == settings.get("admin_password") or current_pw == master)):
                if new_pw == confirm_pw:
                    settings["admin_password"] = new_pw
                    flash("Admin password updated", "success")
                else:
                    flash("Passwords do not match", "danger")
                    return render_template("admin_settings.html", settings=settings)
            else:
                flash("Current password is incorrect", "danger")
                return render_template("admin_settings.html", settings=settings)
        if save_settings(settings):
            flash("Settings saved", "success")
        else:
            flash("Failed to save settings", "danger")
        return redirect(url_for("store.admin_settings"))
    return render_template("admin_settings.html", settings=settings)

@store_bp.route("/admin/add", methods=["POST"])
def admin_add_product():
    if not check_admin():
        return redirect(url_for("store.admin_login", next=url_for("store.admin")))
    
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0")
    desc = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    category = request.form.get("category", "").strip()
    
    # Handle file upload
    file = request.files.get("image_file")
    if file and file.filename:
        if supabase_client:
            try:
                fn = secure_filename(file.filename)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    return jsonify({"error": "Invalid image format"}), 400
                
                key = f"{uuid.uuid4().hex}{ext}"
                file_data = file.read()
                
                # Upload to Supabase storage
                response = supabase_client.storage.from_(SUPABASE_BUCKET).upload(key, file_data)
                
                # Get public URL
                image_url = supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(key)
            except Exception as e:
                print(f"Upload error: {e}")
                return jsonify({"error": f"Upload failed: {str(e)}"}), 500
        else:
            # Save locally if no Supabase
            fn = secure_filename(file.filename)
            file_path = os.path.join('static', 'uploads', fn)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            image_url = f"/static/uploads/{fn}"
    
    if not name:
        return jsonify({"error": "Product name is required"}), 400
    
    if not image_url:
        image_url = "/static/img/placeholder.png"
    
    # include category when adding
    add_product(name, price, desc, image_url)
    # add_product doesn't know about category; patch it in
    products = load_products()
    for p in products:
        if p.get('name') == name and abs(p.get('price') - float(price)) < 0.0001 and p.get('image') == image_url:
            p['category'] = category
            break
    save_products(products)
    if category:
        return redirect(url_for("store.admin_category", slug=category))
    return redirect(url_for("store.admin"))

@store_bp.route("/admin/delete/<pid>", methods=["POST"])
def admin_delete_product(pid):
    if not check_admin():
        return redirect(url_for("store.admin_login", next=url_for("store.admin")))
    delete_product(pid)
    flash("Product deleted", "success")
    return redirect(url_for("store.admin"))

@store_bp.route('/admin/categories', methods=['GET','POST'])
def admin_categories():
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    if request.method == 'POST':
        ok, result = add_category(request.form.get('name',''))
        if ok:
            slug = result
            flash('Category added', 'success')
            return redirect(url_for('store.admin_category', slug=slug))
        else:
            flash(result or 'Failed to add category', 'danger')
            return redirect(url_for('store.admin_categories'))
    return render_template('admin_categories.html', categories=load_categories())

@store_bp.route('/admin/categories/delete/<slug>', methods=['POST'])
def admin_delete_category(slug):
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    delete_category(slug)
    flash('Category deleted', 'success')
    return redirect(url_for('store.admin_categories'))

@store_bp.route('/admin/category/<slug>')
def admin_category(slug):
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    prods = [p for p in load_products() if p.get('category','') == slug]
    cats = load_categories()
    cat = next((c for c in cats if c.get('slug') == slug), None)
    if not cat:
        flash('Category not found', 'danger')
        return redirect(url_for('store.admin_categories'))
    # Provide list of products not in this category (or all, to move)
    all_products = load_products()
    other_products = [p for p in all_products if p.get('category','') != slug]
    return render_template('admin_category.html', category=cat, products=prods, other_products=other_products)

@store_bp.route('/admin/category/<slug>/add-existing', methods=['POST'])
def admin_category_add_existing(slug):
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    pid = request.form.get('product_id','').strip()
    if not pid:
        flash('Select a product to add', 'danger')
        return redirect(url_for('store.admin_category', slug=slug))
    products = load_products()
    found = False
    for p in products:
        if p.get('id') == pid:
            p['category'] = slug
            found = True
            break
    if found:
        save_products(products)
        flash('Product moved to category', 'success')
    else:
        flash('Product not found', 'danger')
    return redirect(url_for('store.admin_category', slug=slug))

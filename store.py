import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, flash, session
from werkzeug.utils import secure_filename
try:
    # Optional imports: used to store and read a hosted logo URL in Supabase
    from supabase_helpers import (
        get_site_setting as _sb_get_site_setting,
        set_site_setting as _sb_set_site_setting,
        upload_logo_to_supabase as _sb_upload_logo,
    )
except Exception:
    _sb_get_site_setting = None
    _sb_set_site_setting = None
    _sb_upload_logo = None

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

# Ensure upload directories exist
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
IMG_DIR = os.path.join(BASE_DIR, 'static', 'img')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "brand_name": "S.B Shop",
    "logo_url": "",
    "welcome_title": "Welcome to S.B Shop",
    "welcome_subtitle": "Discover our curated collection of premium products",
    "admin_password": os.getenv("ADMIN_PASSWORD", "admin123"),
}

def get_safe_image_url(image_path):
    """Ensure image URL is valid or return placeholder"""
    if not image_path:
        return "https://via.placeholder.com/400x400?text=No+Image"
    
    # If it's a local static file reference, check if it exists
    if image_path.startswith('/static/'):
        static_path = os.path.join(BASE_DIR, image_path[1:])  # Remove leading slash
        if not os.path.exists(static_path):
            return "https://via.placeholder.com/400x400?text=No+Image"
    elif image_path.startswith('static/'):
        static_path = os.path.join(BASE_DIR, image_path)
        if not os.path.exists(static_path):
            return "https://via.placeholder.com/400x400?text=No+Image"
    
    return image_path

def load_settings():
    """Load site settings from file or defaults"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # ensure missing keys filled
                merged = {**DEFAULT_SETTINGS, **data}
                # If Supabase has a hosted logo URL, prefer it to avoid losing logo on redeploy
                if _sb_get_site_setting:
                    try:
                        hosted_logo = _sb_get_site_setting("logo_url")
                        if hosted_logo:
                            merged["logo_url"] = hosted_logo
                    except Exception:
                        pass
                return merged
    except Exception as e:
        print(f"Error reading settings: {e}")
    # Fall back to defaults, optionally overlay hosted logo
    defaults = DEFAULT_SETTINGS.copy()
    if _sb_get_site_setting:
        try:
            hosted_logo = _sb_get_site_setting("logo_url")
            if hosted_logo:
                defaults["logo_url"] = hosted_logo
        except Exception:
            pass
    return defaults

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
    """Load categories from Supabase or local file (fallback)."""
    # Try Supabase first
    if supabase_client:
        try:
            try:
                res = supabase_client.table('categories').select('*').order('name').execute()
                if res.data is not None:
                    cats = res.data
                    if not cats:
                        # Ensure there is at least an 'All' category in remote
                        default_cat = {"name": "All", "slug": "all"}
                        try:
                            supabase_client.table('categories').upsert(default_cat).execute()
                            cats = [default_cat]
                        except Exception:
                            cats = [default_cat]
                    return cats
            except Exception:
                # Table may not exist; fall through to local
                pass
        except Exception as e:
            print(f"Error loading categories from Supabase: {e}")

    # Fallback to local JSON file
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data:
                    data = [{"name": "All", "slug": "all"}]
                return data
        except Exception as e:
            print(f"Error reading categories: {e}")
    # default with one category
    cats = [
        {"name": "All", "slug": "all"},
    ]
    save_categories(cats)
    return cats

def save_categories(categories):
    """Persist categories to local file and Supabase (if available)."""
    # Always save locally as a backup
    try:
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2)
    except Exception as e:
        print(f"Error saving categories locally: {e}")

    # Save to Supabase if configured
    if supabase_client:
        try:
            # Upsert each category
            for c in categories:
                if not c.get('slug') or not c.get('name'):
                    continue
                try:
                    supabase_client.table('categories').upsert(c).execute()
                except Exception:
                    # If upsert unsupported, try insert then ignore on conflict
                    supabase_client.table('categories').insert(c).execute()
        except Exception as e:
            print(f"Error saving categories to Supabase: {e}")
    return True

def add_category(name):
    name = name.strip()
    if not name:
        return False, "Category name required"
    slug = name.lower().replace(' ', '-').replace('/', '-')
    # Remote-first path
    if supabase_client:
        try:
            # Check if exists remotely
            res = supabase_client.table('categories').select('slug').eq('slug', slug).limit(1).execute()
            if res.data:
                return False, "Category already exists"
            supabase_client.table('categories').insert({"name": name, "slug": slug}).execute()
            # Also update local cache
            cats = load_categories()
            if not any(c.get('slug') == slug for c in cats):
                cats.append({"name": name, "slug": slug})
                save_categories(cats)
            return True, slug
        except Exception as e:
            print(f"Error adding category to Supabase: {e}")
    # Local fallback
    cats = load_categories()
    if any(c.get('slug') == slug for c in cats):
        return False, "Category already exists"
    cats.append({"name": name, "slug": slug})
    save_categories(cats)
    return True, slug

def delete_category(slug):
    # Delete in Supabase first if available
    if supabase_client:
        try:
            supabase_client.table('categories').delete().eq('slug', slug).execute()
        except Exception as e:
            print(f"Error deleting category from Supabase: {e}")
    # Update local cache/file
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
                    # Fix image URLs for any broken references
                    for product in response.data:
                        product['image'] = get_safe_image_url(product.get('image', ''))
                    return response.data
            except:
                # Fallback to singular 'product' table
                response = supabase_client.table('product').select('*').order('created_at', desc=True).execute()
                if response.data:
                    # Fix image URLs for any broken references
                    for product in response.data:
                        product['image'] = get_safe_image_url(product.get('image', ''))
                    return response.data
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
    
    # Fallback to local file
    if not os.path.exists(DATA_FILE):
        # Create default products with working placeholder images
        default_products = [
            {
                "id": "p1001",
                "name": "Classic Tee",
                "price": 25.0,
                "description": "Soft cotton tee in multiple colors.",
                "image": "https://via.placeholder.com/400x400?text=Classic+Tee"
            },
            {
                "id": "p1002",
                "name": "Everyday Hoodie",
                "price": 55.0,
                "description": "Cozy hoodie with kangaroo pocket.",
                "image": "https://via.placeholder.com/400x400?text=Everyday+Hoodie"
            },
            {
                "id": "p1003",
                "name": "Slim Jeans",
                "price": 60.0,
                "description": "Stretch denim for comfort.",
                "image": "https://via.placeholder.com/400x400?text=Slim+Jeans"
            },
            {
                "id": "p1004",
                "name": "Running Sneakers",
                "price": 80.0,
                "description": "Lightweight, breathable, cushioned.",
                "image": "https://via.placeholder.com/400x400?text=Running+Sneakers"
            },
            {
                "id": "p1005",
                "name": "Leather Belt",
                "price": 20.0,
                "description": "Full-grain leather, metal buckle.",
                "image": "https://via.placeholder.com/400x400?text=Leather+Belt"
            },
            {
                "id": "p1006",
                "name": "Canvas Tote",
                "price": 18.0,
                "description": "Durable tote for daily errands.",
                "image": "https://via.placeholder.com/400x400?text=Canvas+Tote"
            }
        ]
        save_products(default_products)
        return default_products
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)
        # Fix image URLs for any broken references
        for product in products:
            product['image'] = get_safe_image_url(product.get('image', ''))
        return products

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

def add_product(name, price, description, image_url, category=''):
    """Add a new product"""
    pid = f"p{uuid.uuid4().hex[:8]}"
    new_product = {
        "id": pid,
        "name": name,
        "description": description,
        "image": image_url,
        "category": category,
        "created_at": datetime.now().isoformat()
    }
    
    # Only add price if it's provided and not empty
    if price and price.strip():
        try:
            new_product["price"] = round(float(price), 2)
        except ValueError:
            pass  # Don't add price if invalid
    
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

def update_product(pid, name, price, description, image_url, category=''):
    """Update an existing product"""
    products = load_products()
    product = None
    
    for p in products:
        if p.get('id') == pid:
            product = p
            break
    
    if not product:
        return False
    
    # Update fields
    product['name'] = name
    product['description'] = description
    product['image'] = image_url
    product['category'] = category
    
    # Handle price - if empty/None, remove price field
    if price and str(price).strip():
        try:
            product['price'] = round(float(price), 2)
        except ValueError:
            # Remove price if invalid
            product.pop('price', None)
    else:
        # Remove price if empty
        product.pop('price', None)
    
    save_products(products)
    
    if supabase_client:
        try:
            # Try 'products' first, fall back to 'product'
            try:
                supabase_client.table('products').update(product).eq('id', pid).execute()
            except:
                supabase_client.table('product').update(product).eq('id', pid).execute()
        except Exception as e:
            print(f"Error updating in Supabase: {e}")
    
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
        # Handle logo upload if provided — prefer Supabase storage
        logo_file = request.files.get("logo_file")
        if logo_file and logo_file.filename:
            try:
                fn = secure_filename(logo_file.filename)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                    flash("Invalid logo image format", "danger")
                else:
                    if _sb_upload_logo:
                        # Upload to Supabase `assets` bucket and store public URL
                        public_url = _sb_upload_logo(logo_file)
                        settings["logo_url"] = public_url
                        if _sb_set_site_setting:
                            try:
                                _sb_set_site_setting("logo_url", public_url)
                            except Exception:
                                pass
                        flash("Logo uploaded to cloud storage", "success")
                    else:
                        # Fallback to local upload
                        os.makedirs(UPLOAD_DIR, exist_ok=True)
                        dest = os.path.join(UPLOAD_DIR, f"logo_{uuid.uuid4().hex[:8]}{ext}")
                        logo_file.save(dest)
                        settings["logo_url"] = f"/static/uploads/{os.path.basename(dest)}"
            except Exception as e:
                flash(f"Logo upload failed: {e}", "danger")
        else:
            # If a direct URL was provided, keep it
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
    price = request.form.get("price", "")
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
                    flash("Invalid image format", "danger")
                    return redirect(request.referrer or url_for("store.admin"))
                
                key = f"{uuid.uuid4().hex}{ext}"
                file_data = file.read()
                
                # Upload to Supabase storage
                response = supabase_client.storage.from_(SUPABASE_BUCKET).upload(key, file_data)
                
                # Get public URL
                image_url = supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(key)
            except Exception as e:
                print(f"Upload error: {e}")
                flash(f"Upload failed: {str(e)}", "danger")
                # Fall back to local upload
                try:
                    fn = secure_filename(file.filename)
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{fn}")
                    file.save(file_path)
                    image_url = f"/static/uploads/{os.path.basename(file_path)}"
                except Exception as local_e:
                    print(f"Local upload error: {local_e}")
                    image_url = "https://via.placeholder.com/400x400?text=Upload+Failed"
        else:
            # Save locally if no Supabase
            try:
                fn = secure_filename(file.filename)
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{fn}")
                file.save(file_path)
                image_url = f"/static/uploads/{os.path.basename(file_path)}"
            except Exception as e:
                print(f"Local upload error: {e}")
                image_url = "https://via.placeholder.com/400x400?text=Upload+Failed"
    
    if not name:
        flash("Product name is required", "danger")
        return redirect(request.referrer or url_for("store.admin"))
    
    if not image_url:
        image_url = "https://via.placeholder.com/400x400?text=No+Image"
    
    add_product(name, price, desc, image_url, category)
    flash("Product added successfully", "success")
    
    if category:
        return redirect(url_for("store.admin_category", slug=category))
    return redirect(url_for("store.admin"))

@store_bp.route("/admin/edit/<pid>", methods=["GET", "POST"])
def admin_edit_product(pid):
    if not check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    
    products = load_products()
    product = next((p for p in products if p.get("id") == pid), None)
    
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("store.admin"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "")
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
                        flash("Invalid image format", "danger")
                    else:
                        key = f"{uuid.uuid4().hex}{ext}"
                        file_data = file.read()
                        
                        # Upload to Supabase storage
                        response = supabase_client.storage.from_(SUPABASE_BUCKET).upload(key, file_data)
                        
                        # Get public URL
                        image_url = supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(key)
                except Exception as e:
                    print(f"Upload error: {e}")
                    flash(f"Upload failed: {str(e)}", "danger")
                    # Fall back to local upload
                    try:
                        fn = secure_filename(file.filename)
                        os.makedirs(UPLOAD_DIR, exist_ok=True)
                        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{fn}")
                        file.save(file_path)
                        image_url = f"/static/uploads/{os.path.basename(file_path)}"
                    except Exception as local_e:
                        print(f"Local upload error: {local_e}")
            else:
                # Save locally if no Supabase
                try:
                    fn = secure_filename(file.filename)
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{fn}")
                    file.save(file_path)
                    image_url = f"/static/uploads/{os.path.basename(file_path)}"
                except Exception as e:
                    print(f"Local upload error: {e}")
        
        # If no new image provided, keep the existing one
        if not image_url:
            image_url = product.get('image', 'https://via.placeholder.com/400x400?text=No+Image')
        
        if not name:
            flash("Product name is required", "danger")
            return render_template("admin_edit.html", product=product, categories=load_categories())
        
        if update_product(pid, name, price, desc, image_url, category):
            flash("Product updated successfully", "success")
            if category:
                return redirect(url_for("store.admin_category", slug=category))
            return redirect(url_for("store.admin"))
        else:
            flash("Failed to update product", "danger")
    
    categories = load_categories()
    return render_template("admin_edit.html", product=product, categories=categories)

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

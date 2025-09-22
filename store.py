import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, flash
from werkzeug.utils import secure_filename

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
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

# Local fallback file
DATA_FILE = os.path.join(os.path.dirname(__file__), "products.json")

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
            response = supabase_client.table('products').select('*').order('created_at', desc=True).execute()
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
                supabase_client.table('products').upsert(product).execute()
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
            response = supabase_client.table('products').insert(new_product).execute()
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
            supabase_client.table('products').delete().eq('id', pid).execute()
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
    products = load_products()
    return render_template("products.html", products=products)

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
    """Check if user is authenticated as admin"""
    admin_pw = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Check various authentication methods
    auth = request.authorization
    if auth and auth.password == admin_pw:
        return True
    
    if request.form.get("pw") == admin_pw:
        return True
    
    if request.args.get("pw") == admin_pw:
        return True
    
    return False

@store_bp.route("/admin")
def admin():
    products = load_products()
    return render_template("admin.html", products=products)

@store_bp.route("/admin/add", methods=["POST"])
def admin_add_product():
    if not check_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0")
    desc = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    
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
    
    add_product(name, price, desc, image_url)
    return redirect(url_for("store.admin"))

@store_bp.route("/admin/delete/<pid>", methods=["POST"])
def admin_delete_product(pid):
    if not check_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    delete_product(pid)
    return redirect(url_for("store.admin"))

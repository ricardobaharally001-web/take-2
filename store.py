import os, json, uuid, time
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from werkzeug.utils import secure_filename

# Optional Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "product-images").strip()

supabase_client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print("Supabase client not available:", e)

store_bp = Blueprint("store", __name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "products.json")

def load_products():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)

@store_bp.route("/products")
def products():
    products = load_products()
    return render_template("products.html", products=products)

@store_bp.route("/product/<pid>")
def product_detail(pid):
    products = load_products()
    prod = next((p for p in products if p.get("id")==pid), None)
    if not prod:
        abort(404)
    return render_template("product_detail.html", product=prod)

@store_bp.route("/cart")
def cart():
    return render_template("cart.html")

@store_bp.route("/api/cart/checkout", methods=["POST"])
def checkout():
    # No payment gateway wired here; integrate PayPal/MMG later.
    payload = request.json or {}
    return jsonify({"ok": True, "message": "Order received. You can connect PayPal/MMG later."})

# --- Simple Admin (password via ENV) ---
def is_admin(req):
    admin_pw = os.getenv("ADMIN_PASSWORD", "changeme")
    return req.args.get("pw") == admin_pw or req.form.get("pw") == admin_pw

@store_bp.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "GET":
        return render_template("admin.html")
    # POST - create product
    if not is_admin(request):
        abort(403)

    name = request.form.get("name","").strip()
    price = float(request.form.get("price","0") or 0)
    desc = request.form.get("description","").strip()
    image_url = request.form.get("image_url","").strip()

    # If a file is uploaded, push to Supabase (if configured)
    file = request.files.get("image_file")
    if file and file.filename:
        if not supabase_client:
            return "Supabase is not configured, but a file was uploaded. Set SUPABASE_* envs.", 400
        fn = secure_filename(file.filename)
        ext = os.path.splitext(fn)[1].lower()
        key = f"{uuid.uuid4().hex}{ext}"
        # Upload to bucket (public)
        res = supabase_client.storage.from_(SUPABASE_BUCKET).upload(key, file.read())
        if res and getattr(res, "status_code", 200) >= 400:
            return f"Supabase upload error: {getattr(res, 'text', 'unknown')}", 400
        # Get a public URL (assumes public bucket)
        public_url = supabase_client.storage.from_(SUPABASE_BUCKET).get_public_url(key)
        image_url = public_url

    if not name:
        return "Name is required", 400

    products = load_products()
    pid = uuid.uuid4().hex[:8]
    products.append({
        "id": pid,
        "name": name,
        "price": round(price,2),
        "description": desc,
        "image": image_url or url_for('static', filename='img/placeholder.png', _external=False)
    })
    save_products(products)
    return redirect(url_for("store.products"))

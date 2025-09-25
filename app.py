import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase_helpers import upload_logo_to_supabase, get_site_setting, set_site_setting
# Import the existing store blueprint and helpers
import store as store_mod

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# Register existing store blueprint so all your original routes work
app.register_blueprint(store_mod.store_bp, url_prefix="")

def _site_settings():
    """Load settings (now automatically includes Supabase data)."""
    try:
        site = store_mod.load_settings() or {}
    except Exception:
        site = {}
    
    # Ensure fallback values
    site.setdefault("brand_name", "S.B Shop")
    site.setdefault("welcome_title", "Welcome")
    site.setdefault("welcome_subtitle", "")
    site.setdefault("whatsapp_phone", "")
    site.setdefault("logo_url", "")
    return site

@app.route("/")
def index():
    # Use the store module to fetch products; pass `site` for base_store.html
    try:
        products = store_mod.load_products() or []
    except Exception:
        products = []
    site = _site_settings()
    return render_template("index.html", products=products, site=site, title=site.get("brand_name"))

# Simple branding endpoint to upload/replace the logo in Supabase (assets bucket)
@app.route("/admin/branding", methods=["GET", "POST"])
def admin_branding():
    site = _site_settings()
    if request.method == "POST":
        file = request.files.get("logo")
        if not file or not file.filename.strip():
            flash("Please choose an image file.", "danger")
            return redirect(url_for("admin_branding"))
        try:
            url = upload_logo_to_supabase(file)
            set_site_setting("logo_url", url)
            flash("Logo updated!", "success")
            site["logo_url"] = url
        except Exception as e:
            flash(f"Upload failed: {e}", "danger")
        return redirect(url_for("admin_branding"))
    current_logo = site.get("logo_url")
    return render_template("admin_branding.html", current_logo=current_logo, site=site, title="Branding")

# Admin-only Supabase diagnostics (temporary)
@app.route("/admin/debug/supabase")
def admin_debug_supabase():
    if not store_mod.check_admin():
        return redirect(url_for("store.admin_login", next=request.path))
    info = {
        "connected": bool(store_mod.supabase_client),
        "url_set": bool(os.environ.get("SUPABASE_URL")),
        "anon_key_set": bool(os.environ.get("SUPABASE_ANON_KEY")),
        "service_key_set": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        "buckets": {
            "products_bucket": os.environ.get("SUPABASE_BUCKET", "product-images"),
            "assets_bucket": os.environ.get("SUPABASE_ASSETS_BUCKET", "assets"),
        },
        "checks": {},
    }
    # Try reading products
    try:
        prods = store_mod.load_products()
        info["checks"]["products_count"] = len(prods or [])
        info["checks"]["products_example"] = (prods or [None])[0]
    except Exception as e:
        info["checks"]["products_error"] = str(e)
    # Try reading categories
    try:
        cats = store_mod.load_categories()
        info["checks"]["categories_count"] = len(cats or [])
        info["checks"]["categories_example"] = (cats or [None])[0]
    except Exception as e:
        info["checks"]["categories_error"] = str(e)
    # Try reading site setting logo_url
    try:
        logo = get_site_setting("logo_url")
        info["checks"]["site_logo_url"] = logo
    except Exception as e:
        info["checks"]["site_logo_error"] = str(e)
    
    # Try reading WhatsApp phone number
    try:
        whatsapp_phone = get_site_setting("whatsapp_phone")
        info["checks"]["whatsapp_phone"] = whatsapp_phone or "Not set"
        info["checks"]["whatsapp_enabled"] = bool(whatsapp_phone)
    except Exception as e:
        info["checks"]["whatsapp_error"] = str(e)
    # Render as simple preformatted page
    return render_template(
        "admin_settings.html",
        settings=store_mod.load_settings(),
        debug_info=info,
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

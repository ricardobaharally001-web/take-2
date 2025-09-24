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
    """Load your local settings and merge a Supabase-hosted logo if present."""
    site = {}
    try:
        site = store_mod.load_settings() or {}
    except Exception:
        site = {}
    # If a hosted logo was saved in Supabase site_settings, prefer it
    try:
        logo_url = get_site_setting("logo_url")
        if logo_url:
            site["logo_url"] = logo_url
    except Exception:
        pass
    # Fallback brand name
    site.setdefault("brand_name", "S.B Shop")
    site.setdefault("welcome_title", "Welcome")
    site.setdefault("welcome_subtitle", "")
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

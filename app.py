import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase_helpers import upload_logo, get_logo_url, set_logo_url, get_products

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","dev")

@app.context_processor
def inject_brand():
    return {"SITE_LOGO_URL": get_logo_url(), "site_title":"S.B Shop"}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products():
    items = get_products()
    return render_template("products.html", products=items)

@app.route("/cart")
def cart():
    return render_template("base.html", title="Cart")

@app.route("/admin/branding", methods=["GET","POST"])
def admin_branding():
    if request.method == "POST":
        f = request.files.get("logo")
        if not f or not f.filename:
            flash("Please choose an image file.","danger")
            return redirect(url_for("admin_branding"))
        try:
            url = upload_logo(f)
            set_logo_url(url)
            flash("Logo updated!","success")
        except Exception as e:
            flash(f"Upload failed: {e}", "danger")
        return redirect(url_for("admin_branding"))
    return render_template("admin_branding.html", current_logo=get_logo_url())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","5000")), debug=True)

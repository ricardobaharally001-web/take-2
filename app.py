import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase_helpers import upload_logo_to_supabase, get_site_setting, set_site_setting

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev")

@app.context_processor
def inject_site_logo():
    return {"SITE_LOGO_URL": get_site_setting("logo_url")}

@app.route("/")
def index():
    return render_template("base.html", title="Home")

@app.route("/admin/branding", methods=["GET", "POST"])
def admin_branding():
    if request.method == "POST":
        file = request.files.get("logo")
        if not file or not file.filename:
            flash("Please choose an image file.", "danger")
            return redirect(url_for("admin_branding"))
        url = upload_logo_to_supabase(file)
        set_site_setting("logo_url", url)
        flash("Logo updated!", "success")
        return redirect(url_for("admin_branding"))
    current_logo = get_site_setting("logo_url")
    return render_template("admin_branding.html", current_logo=current_logo)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
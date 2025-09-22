import os
from flask import Flask, render_template, url_for, send_from_directory
from dotenv import load_dotenv

# Load env in local dev; on Render, env is injected
load_dotenv()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Register blueprints
    from store import store_bp
    app.register_blueprint(store_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    # Index route (landing)
    @app.route("/")
    def index():
        # A simple curated selection on home (reads from products.json via store module utility)
        from store import load_products
        products = load_products()[:6]
        return render_template("index.html", products=products)

    # Favicon (optional)
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

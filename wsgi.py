import os
app = None
try:
    from app import create_app as factory
    app = factory()
except Exception:
    try:
        from app import app as flask_app
        app = flask_app
    except Exception:
        try:
            from main import app as flask_app
            app = flask_app
        except Exception:
            raise RuntimeError("Could not locate Flask app.")

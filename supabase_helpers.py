import os
from supabase import create_client
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_ASSETS_BUCKET = os.environ.get("SUPABASE_ASSETS_BUCKET", "assets")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def _public_url(bucket: str, path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"

def upload_logo_to_supabase(file_storage) -> str:
    """
    Upload a new logo to the assets bucket and return its public URL.
    file_storage: Werkzeug FileStorage (e.g., request.files['logo'])
    """
    filename = file_storage.filename or "logo.png"
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "png").lower()
    key = f"branding/logo_{stamp}.{ext}"

    data = file_storage.read()
    file_storage.seek(0)

    supabase.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
        key,
        data,
        {"content-type": f"image/{ext}", "upsert": True},
    )
    return _public_url(SUPABASE_ASSETS_BUCKET, key)

def get_site_setting(key: str) -> str | None:
    res = supabase.table("site_settings").select("value").eq("key", key).limit(1).execute()
    if res.data:
        return res.data[0]["value"]
    return None

def set_site_setting(key: str, value: str):
    supabase.table("site_settings").upsert({"key": key, "value": value}).execute()
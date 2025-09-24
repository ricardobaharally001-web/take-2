import os
from supabase import create_client
from datetime import datetime

SUPABASE_ASSETS_BUCKET = os.environ.get("SUPABASE_ASSETS_BUCKET", "assets")

def _get_env():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return url, key

_supabase_client = None

def _get_client():
    """
    Lazily create the Supabase client so the app doesn't crash at import time
    if env vars are temporarily missing. We only raise when the helper is used.
    """
    global _supabase_client
    if _supabase_client is None:
        url, key = _get_env()
        if not url or not key:
            raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY.")
        _supabase_client = create_client(url, key)
    return _supabase_client

def _public_url(bucket: str, path: str) -> str:
    url, _ = _get_env()
    return f"{url}/storage/v1/object/public/{bucket}/{path}"

def upload_logo_to_supabase(file_storage) -> str:
    filename = file_storage.filename or "logo.png"
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "png").lower()
    key = f"branding/logo_{stamp}.{ext}"

    data = file_storage.read()
    file_storage.seek(0)

    client = _get_client()
    client.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
        key,
        data,
        {"content-type": f"image/{ext}", "upsert": True},
    )
    return _public_url(SUPABASE_ASSETS_BUCKET, key)

def get_site_setting(key: str) -> str | None:
    client = _get_client()
    res = client.table("site_settings").select("value").eq("key", key).limit(1).execute()
    if res.data:
        return res.data[0]["value"]
    return None

def set_site_setting(key: str, value: str):
    client = _get_client()
    client.table("site_settings").upsert({"key": key, "value": value}).execute()
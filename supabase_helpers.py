import os
import io
from supabase import create_client
from datetime import datetime

SUPABASE_ASSETS_BUCKET = os.environ.get("SUPABASE_ASSETS_BUCKET", "assets")

def _get_env():
    url = os.environ.get("SUPABASE_URL")
    # accept either ANON or SERVICE ROLE (whichever you already use elsewhere)
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return url, key

_supabase_client = None

def _get_client():
    """Create the Supabase client lazily so imports don't crash when env is missing."""
    global _supabase_client
    if _supabase_client is None:
        url, key = _get_env()
        if not url or not key:
            raise RuntimeError("Supabase not configured. Set SUPABASE_URL and either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY.")
        _supabase_client = create_client(url, key)
    return _supabase_client

def _public_url(bucket: str, path: str) -> str:
    url, _ = _get_env()
    return f"{url}/storage/v1/object/public/{bucket}/{path}"

def upload_logo_to_supabase(file_storage) -> str:
    """Upload a new logo to the assets bucket and return its public URL."""
    filename = file_storage.filename or "logo.png"
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "png").lower()
    key = f"branding/logo_{stamp}.{ext}"
    data = file_storage.read()
    file_storage.seek(0)
    client = _get_client()
    # Use correct option names expected by supabase-py storage client
    # Choose correct MIME type
    mime = (
        "image/svg+xml" if ext in ("svg",) else
        f"image/{ext}"
    )
    # Try multiple call signatures for compatibility across supabase-py versions
    result = None
    last_err = None
    try:
        # Variant A: upsert inside file_options (older clients)
        result = client.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
            path=key,
            file=data,
            file_options={"contentType": mime, "cacheControl": "3600", "upsert": True},
        )
    except Exception as e_a:
        last_err = e_a
        try:
            # Variant B: upsert separate kwarg (newer clients)
            result = client.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
                path=key,
                file=data,
                file_options={"contentType": mime, "cacheControl": "3600"},
                upsert=True,
            )
        except Exception as e_b:
            last_err = e_b
            try:
                # Variant C: minimal call without options
                result = client.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
                    path=key,
                    file=data,
                )
            except Exception as e_c:
                last_err = e_c
                try:
                    # Variant D: use file-like object (BytesIO)
                    bio = io.BytesIO(data)
                    result = client.storage.from_(SUPABASE_ASSETS_BUCKET).upload(
                        path=key,
                        file=bio,
                        file_options={"contentType": mime, "cacheControl": "3600"},
                        upsert=True,
                    )
                except Exception as e_d:
                    last_err = e_d
                    raise RuntimeError(f"Supabase upload failed: {last_err}")

    # Some client versions return dict/bool; detect errors gracefully
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(f"Supabase upload error: {result['error']}")
    if result is False:
        raise RuntimeError("Supabase upload failed (returned False)")
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

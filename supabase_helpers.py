import os
import io
from supabase import create_client
from datetime import datetime

SUPABASE_ASSETS_BUCKET = os.environ.get("SUPABASE_ASSETS_BUCKET", "assets")

def _get_env():
    url = os.environ.get("SUPABASE_URL")
    # Prefer SERVICE ROLE for server-side writes; fall back to ANON if needed
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
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
    """Return a site setting value, supporting multiple schema variants.

    We support:
    1) Key/Value table: site_settings(key text primary key, value text)
    2) Single-row config table: site_settings has a dedicated column, e.g. site_settings.logo_url
    3) Legacy table name: settings
    """
    client = _get_client()
    # Variant 1: key/value
    try:
        res = client.table("site_settings").select("value").eq("key", key).limit(1).execute()
        if res.data:
            return res.data[0].get("value")
    except Exception:
        pass

    # Variant 2: dedicated column on site_settings
    try:
        res = client.table("site_settings").select(key).limit(1).execute()
        if res.data and res.data[0].get(key):
            return res.data[0].get(key)
    except Exception:
        pass

    # Variant 3: dedicated column on settings
    try:
        res = client.table("settings").select(key).limit(1).execute()
        if res.data and res.data[0].get(key):
            return res.data[0].get(key)
    except Exception:
        pass
    return None

def set_site_setting(key: str, value: str):
    """Persist a site setting, supporting multiple schema variants.

    Attempts in order:
    1) Upsert into key/value table site_settings(key,value)
    2) Update first row in site_settings setting a dedicated column; create row if none
    3) Update first row in settings table similarly
    """
    client = _get_client()
    # Variant 1: key/value table
    try:
        client.table("site_settings").upsert({"key": key, "value": value}).execute()
        return
    except Exception:
        pass

    # Variant 2: dedicated column on site_settings
    try:
        # Try update existing row
        res = client.table("site_settings").select("id").limit(1).execute()
        if res.data:
            row_id = res.data[0].get("id")
            if row_id is not None:
                client.table("site_settings").update({key: value}).eq("id", row_id).execute()
            else:
                # No id column; do an update without filter (affects all rows)
                client.table("site_settings").update({key: value}).execute()
        else:
            # Insert a new row with the column
            client.table("site_settings").insert({key: value}).execute()
        return
    except Exception:
        pass

    # Variant 3: dedicated column on settings
    try:
        res = client.table("settings").select("id").limit(1).execute()
        if res.data:
            row_id = res.data[0].get("id")
            if row_id is not None:
                client.table("settings").update({key: value}).eq("id", row_id).execute()
            else:
                client.table("settings").update({key: value}).execute()
        else:
            client.table("settings").insert({key: value}).execute()
    except Exception:
        pass

# supabase_helpers.py
import os
import uuid
import mimetypes

from supabase import create_client


def _client():
    url = os.getenv("https://shvwrlwzqsgnwwapqfga.supabase.co)
    key = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNodndybHd6cXNnbnd3YXBxZmdhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODU1ODIxMSwiZXhwIjoyMDc0MTM0MjExfQ.AXq4WHp0a8fdiz5KW4kDV9JrNNy3MjgmJSNoYXRzhpY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
    return create_client(url, key)


def upload_image_to_supabase(file_storage, *, bucket=None, folder="products"):
    """
    Uploads an image to Supabase Storage and returns a public URL.
    If any error occurs, raises and lets caller decide how to handle.
    """
    if not file_storage or file_storage.filename == "":
        return None

    bucket = bucket or os.getenv("SUPABASE_BUCKET", "products")
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Only .jpg, .jpeg, .png are allowed")

    path = f"{folder}/{uuid.uuid4().hex}{ext}"
    content_type = mimetypes.guess_type(file_storage.filename)[0] or "application/octet-stream"

    sb = _client()
    # IMPORTANT: pass a binary stream and set content-type
    file_storage.stream.seek(0)
    sb.storage.from_(bucket).upload(
        path=path,
        file=file_storage.stream,
        file_options={"content-type": content_type, "upsert": True},
    )
    public_url = sb.storage.from_(bucket).get_public_url(path)
    return public_url

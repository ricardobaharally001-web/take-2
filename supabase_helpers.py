import os
from datetime import datetime
from supabase import create_client

ASSETS_BUCKET = os.environ.get("SUPABASE_ASSETS_BUCKET", "assets")

def _get_env():
  url = os.environ.get("SUPABASE_URL")
  key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
  return url, key

_client = None
def client():
  global _client
  if _client is None:
    url, key = _get_env()
    if not url or not key:
      raise RuntimeError("Set SUPABASE_URL and either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY.")
    _client = create_client(url, key)
  return _client

def public_url(bucket: str, path: str) -> str:
  url, _ = _get_env()
  return f"{url}/storage/v1/object/public/{bucket}/{path}"

def upload_logo(file_storage) -> str:
  name = file_storage.filename or "logo.png"
  stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
  ext = (name.rsplit('.',1)[-1] if '.' in name else 'png').lower()
  key = f"branding/logo_{stamp}.{ext}"
  data = file_storage.read()
  file_storage.seek(0)
  client().storage.from_(ASSETS_BUCKET).upload(key, data, {"content-type": f"image/{ext}", "upsert": True})
  return public_url(ASSETS_BUCKET, key)

def get_products():
  try:
    res = client().table("products").select("*").limit(50).execute()
    items = res.data or []
  except Exception:
    items = []
  # Normalize
  out = []
  url, _ = _get_env()
  default_bucket = os.environ.get("SUPABASE_BUCKET","product-images")
  for r in items:
    img = r.get("image_url") or r.get("image") or r.get("image_path")
    if img and not str(img).startswith("http"):
      # Assume it's a path in the default bucket
      img = f"{url}/storage/v1/object/public/{default_bucket}/{img}"
    out.append({
      "name": r.get("name") or r.get("title") or "Item",
      "description": r.get("description"),
      "price": r.get("price") or r.get("amount") or 0,
      "image_url": img,
    })
  return out

def get_logo_url():
  try:
    res = client().table("site_settings").select("value").eq("key","logo_url").limit(1).execute()
    if res.data:
      return res.data[0]["value"]
  except Exception:
    pass
  return None

def set_logo_url(u: str):
  client().table("site_settings").upsert({"key":"logo_url","value":u}).execute()

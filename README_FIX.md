
# Quick Deploy Notes (Clean Image Uploads)

This trimmed build removes sample images and defaults to storing **all new product images in Supabase Storage**.

## What changed
- Removed `static/img/sample*.jpg`
- `static/products.json` is now `[]`
- Server already supports file uploads to Supabase via the `image_file` field on the admin add/edit forms.
- No other demo-image paths remain. If Supabase is configured, uploads are stored in the `product-images` bucket and the public URL is saved on the product.

## Required Render environment variables
- `SECRET_KEY` = any random string
- `SUPABASE_URL` = from your Supabase project settings
- `SUPABASE_ANON_KEY` = from your Supabase API settings
- (optional) `SUPABASE_BUCKET` = `product-images` (auto-created in code path if present in dashboard)

## How to use (Admin)
1. Go **Admin → Category → Add New Product** (or Edit Product)
2. Fill in fields. Either paste an **Image URL** or **Upload Image** (`image_file`).
3. Submit. The product will display using the public URL from Supabase Storage.
4. If Supabase is NOT configured, the app will fall back to saving in `static/uploads/` and use that path.

## Minimal files you need to replace on GitHub
- `static/products.json` (now empty `[]` to remove demo items)
- `static/img/sample*.jpg` (delete them)
- (optional) add `static/img/placeholder.png` (provided in this zip)

Everything else remains as-is.

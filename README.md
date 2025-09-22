# S.B Shop — Flask + Supabase + Render (Shopify‑style)

A minimal, clean storefront you can deploy to **Render**, store images in **Supabase Storage**, and host code on **GitHub**.

## Features
- Light gray navbar (black in dark mode)
- Desktop: **left** controls (dark mode, Shop, Orders), **center** cart, **right** logo + brand
- Mobile: **left** logo + brand, **center** cart, **right** hamburger menu (off‑canvas)
- Shopify‑like product grid, responsive and tidy “center‑outward” layout
- Dark mode toggle (persisted via `localStorage`)
- Simple cart (client‑side), checkout stub
- **Admin upload** (optional): add products and upload images to Supabase public bucket

## Quickstart (Local)
```bash
cp .env.example .env  # fill values
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## Deploy to Render
- Push this repo to GitHub.
- Create a **Web Service** on Render; it will auto-detect `render.yaml`.
- Set environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_BUCKET` (created as **public** in Supabase, default: `product-images`)
  - `ADMIN_PASSWORD` (for `/admin`)
- Render uses Gunicorn per `render.yaml`.

## Supabase Setup
- In Supabase Storage, create a **public** bucket named `product-images` (or match `SUPABASE_BUCKET`).
- Copy your Project URL and `anon` key into Render ENV.
- The Admin page `/admin` lets you upload an image to the bucket and creates the product entry.

## Fix for your previous error
Your template referenced `url_for('store.products_view')` which **doesn't exist**.
This starter uses `url_for('store.products')`, matching the blueprint endpoint, preventing the `BuildError`.

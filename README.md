# Mini Flask E-Commerce (Resell-Ready)

A simple Shopify-style store you can deploy for many small businesses with the same codebase. Each buyer gets their own deployment and can update branding, colors, hero text, contact info, MMG instructions, PayPal Client ID, and products (with images) from an admin dashboard.

## Features

- **Storefront**: Home, Products, Product Detail, Cart, Checkout
- **Admin**: Login/Logout, Dashboard, Product CRUD, Settings (branding, colors, logo, PayPal Client ID, MMG text)
- **Cart**: Session-based, add/update/remove items
- **Orders**: Created on successful PayPal (simulated) or MMG (pending)
- **Branding**: All text/logo/colors come from DB Settings (no code edits needed)
- **Uploads**: Product images + logo saved under `static/uploads/` with safe filenames
- **Currency Display**: `GYD $` with thousands separators

## Tech

- Python 3.10+, Flask, Flask-Login, Flask-WTF, Flask-SQLAlchemy, python-dotenv
- SQLite (file-based)
- Bootstrap 5 (CDN), small jQuery, vanilla JS
- No Flask-Admin — custom admin views
- PayPal Smart Buttons (placeholder Client ID)
- MMG button shows modal with customizable instructions

---

## Quick Start (Local)

1. **Create project folders**
   ```
   your-project/
     app.py
     requirements.txt
     templates/
     static/
     instance/
   ```

2. **Create virtual env & install**
   ```bash
   python -m venv .venv
   . .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create env file**
   - Copy `instance/config.example.env` to `instance/config.env`.
   - Edit as needed (SECRET_KEY, etc). The defaults work for local dev.

4. **Run**
   ```bash
   python app.py
   ```
   Visit http://127.0.0.1:5000

5. **Login to Admin**
   - URL: `http://127.0.0.1:5000/admin/login`
   - Default: `admin@example.com / admin123` (change in `instance/config.env`)

> On first run, the app auto-creates tables and seeds the admin user + settings.

---

## How Buyers Customize Their Store (No Code)

1. **Login** → `/admin/login`
2. **Settings** → `/admin/settings`
   - Upload **Logo**
   - Set **Store Name**, **Tagline**, **Contact Email/Phone/Address**
   - Choose **Theme Color** (Blue/Green/Red/Purple/Teal)
   - Paste **PayPal Client ID** (or leave placeholder)
   - Write **MMG Instructions** (shown on Checkout modal)
   - Save

3. **Products** → `/admin/products`
   - **New Product**: name, description, price (GYD), category, image, active
   - Edit/Delete anytime

---

## Checkout & Payments

- **PayPal**: Uses Smart Buttons with `client-id` from Settings. For demo, the PayPal amount is a placeholder derived from GYD total (simple /210). Replace this logic with a real conversion or switch your store currency.
- **MMG**: Customers click **“Pay with MMG”** → modal shows your instructions. Clicking **“I paid via MMG”** creates a **Pending** order. You verify manually and fulfill.

> Where to send confirmation emails? In `app.py` search for `EMAIL STUB`. Hook your SMTP there.

---

## Security & Validations

- CSRF protection on all HTML forms (admin/product/settings/login)
- File uploads restricted to `jpg/jpeg/png`, ~2MB
- Safe filenames via `secure_filename`
- All `/admin/*` routes require login
- Cart kept in user session (server-side cookie)

---

## Deploy Cheaply

### Render
1. Push your repo to GitHub.
2. Create a **Render Web Service** (Python).
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `python app.py`
5. Add env vars (from `instance/config.env`) to Render dashboard.
6. Optional: Use a **persistent disk** if you want uploads to persist (otherwise use S3 or similar later).

### Railway
1. New Project → Deploy from GitHub.
2. Add Python plugin / set buildpacks.
3. Set variables (SECRET_KEY, etc).
4. Start command: `python app.py`.

### PythonAnywhere (Free tier workable)
1. Upload code via Git or zip.
2. Create a **Flask Web App**.
3. Point **WSGI file** to your `create_app()` by using:
   ```python
   from app import create_app
   application = create_app()
   ```
4. Set environment in **Environment Variables** or read from `instance/config.env` (ensure file exists on server).
5. Add a directory for `static/uploads` and make it writable.

> **Uploads & SQLite**: On ephemeral platforms, files reset on deploy. For production, consider attaching a persistent volume or switching uploads to an object store. SQLite is fine for small shops; for larger traffic, move to a managed DB.

---

## Project Structure

```
app.py
templates/
  base_store.html
  index.html
  products.html
  product_detail.html
  cart.html
  checkout.html
  base_admin.html
  admin_dashboard.html
  admin_products.html
  admin_settings.html
static/
  style.css
  script.js
  uploads/        # created automatically on first upload
instance/
  config.example.env
  config.env      # your local copy (not committed)
```

---

## Reuse / Resell Tips

- Keep this repo as your **base package**.
- For each new client: duplicate/deploy, set their logo/name/colors/PayPal/MMG in the **Settings** page.
- You can export/import the SQLite DB for backup. For a clean start, delete `instance/app.db` before first run to create fresh tables.

---

## Admin Defaults

- Email: `admin@example.com`
- Password: `admin123`
- Change these in `instance/config.env` to auto-seed a different admin on first run.

---

## License & Attribution

- Bootstrap 5 via CDN
- PayPal Smart Buttons via official SDK
- This starter is provided “as-is.” Customize and extend for your clients.

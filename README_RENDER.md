# Flask Mini Store — Render + Supabase Setup

## Steps

### 1) Supabase
- Create project at supabase.com
- Storage → Create bucket `products` → Make public
- Settings → API: copy `Project URL` and `service_role` key
- Database → Connection strings → copy Session Pooler (port 6543) as `DATABASE_URL`

### 2) GitHub
- Create new repo
- Upload all files from this folder
- Do not add real `.env`, use `.env.example` only

### 3) Render
- New → Web Service → connect repo
- Render reads `render.yaml`
- Add environment variables: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_BUCKET, SECRET_KEY
- Deploy

### 4) Usage
- Use `save_uploaded(request.files['file'])` in your routes to upload to Supabase Storage.

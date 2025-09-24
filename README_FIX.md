# Fix applied: standardize to `products` table

This build uses a single Supabase table: **public.products**.

## Required schema (run in Supabase SQL editor)

```sql
ALTER TABLE public.products
  ALTER COLUMN id TYPE text USING id::text;
ALTER TABLE public.products
  ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz,
  ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE public.products
  ADD COLUMN IF NOT EXISTS name        text,
  ADD COLUMN IF NOT EXISTS price       numeric(10,2),
  ADD COLUMN IF NOT EXISTS description text,
  ADD COLUMN IF NOT EXISTS image       text,
  ADD COLUMN IF NOT EXISTS category    text;

DO $$
BEGIN
  ALTER TABLE public.products ADD CONSTRAINT products_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

NOTIFY pgrst, 'reload schema';
```

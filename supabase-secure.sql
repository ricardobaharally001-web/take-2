-- Secure Supabase Setup for cook-shop
-- Run this entire script in Supabase SQL Editor

-- 1. Enable UUID extension
create extension if not exists "uuid-ossp";

-- 2. Create categories table
create table if not exists public.categories (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  slug text,
  description text,
  image_url text,
  created_at timestamp with time zone default now()
);

-- 3. Create products table
create table if not exists public.products (
  id uuid primary key default uuid_generate_v4(),
  category_id uuid references public.categories(id) on delete set null,
  name text not null,
  description text,
  price_cents integer not null default 0,
  stock integer not null default 0,
  image_url text,
  is_active boolean not null default true,
  created_at timestamp with time zone default now()
);

-- 4. Create site_settings table
create table if not exists public.site_settings (
  id uuid primary key default uuid_generate_v4(),
  key text unique not null,
  value jsonb not null default '{}'::jsonb
);

-- 5. Create admin_users table for proper authentication
create table if not exists public.admin_users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  role text not null default 'admin',
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 6. Enable Row Level Security
alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.site_settings enable row level security;
alter table public.admin_users enable row level security;

-- 7. Create RLS Policies for Categories
-- Anyone can read categories
create policy "Public can read categories" 
  on public.categories for select 
  using (true);

-- Only authenticated users can modify categories
create policy "Authenticated users can insert categories" 
  on public.categories for insert 
  with check (auth.role() = 'authenticated');

create policy "Authenticated users can update categories" 
  on public.categories for update 
  using (auth.role() = 'authenticated');

create policy "Authenticated users can delete categories" 
  on public.categories for delete 
  using (auth.role() = 'authenticated');

-- 8. Create RLS Policies for Products
-- Anyone can read active products
create policy "Public can read active products" 
  on public.products for select 
  using (is_active = true);

-- Authenticated users can read all products
create policy "Authenticated users can read all products" 
  on public.products for select 
  using (auth.role() = 'authenticated');

-- Only authenticated users can modify products
create policy "Authenticated users can insert products" 
  on public.products for insert 
  with check (auth.role() = 'authenticated');

create policy "Authenticated users can update products" 
  on public.products for update 
  using (auth.role() = 'authenticated');

create policy "Authenticated users can delete products" 
  on public.products for delete 
  using (auth.role() = 'authenticated');

-- 9. Create RLS Policies for Site Settings
-- Anyone can read site settings
create policy "Public can read settings" 
  on public.site_settings for select 
  using (true);

-- Only authenticated users can modify settings
create policy "Authenticated users can insert settings" 
  on public.site_settings for insert 
  with check (auth.role() = 'authenticated');

create policy "Authenticated users can update settings" 
  on public.site_settings for update 
  using (auth.role() = 'authenticated');

create policy "Authenticated users can delete settings" 
  on public.site_settings for delete 
  using (auth.role() = 'authenticated');

-- 10. Create RLS Policies for Admin Users
-- Only authenticated users can read admin users
create policy "Authenticated users can read admin users" 
  on public.admin_users for select 
  using (auth.role() = 'authenticated');

-- Only service role can insert admin users
create policy "Service role can insert admin users" 
  on public.admin_users for insert 
  with check (auth.role() = 'service_role');

-- Only service role can update admin users
create policy "Service role can update admin users" 
  on public.admin_users for update 
  using (auth.role() = 'service_role');

-- Only service role can delete admin users
create policy "Service role can delete admin users" 
  on public.admin_users for delete 
  using (auth.role() = 'service_role');

-- 11. Insert sample categories
insert into public.categories (name, description, image_url) values
  ('🍝 Main Dishes', 'Hearty meals and entrees', 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500'),
  ('🍰 Desserts', 'Sweet treats and desserts', 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500'),
  ('🥤 Drinks', 'Refreshing beverages', 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500'),
  ('🍿 Snacks', 'Quick bites and appetizers', 'https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=500')
on conflict do nothing;

-- 12. Insert sample products
insert into public.products (name, description, price_cents, stock, category_id, image_url) values
  ('Special Fried Rice', 'Aromatic fried rice with mixed vegetables, egg, and secret spices', 1500, 25, 
    (select id from public.categories where name like '%Main Dishes%' limit 1), 
    'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500'),
  
  ('Grilled Chicken Bowl', 'Tender grilled chicken with quinoa and roasted vegetables', 2200, 15, 
    (select id from public.categories where name like '%Main Dishes%' limit 1), 
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500'),
  
  ('Classic Cheesecake', 'Creamy New York style cheesecake with berry topping', 900, 20, 
    (select id from public.categories where name like '%Desserts%' limit 1), 
    'https://images.unsplash.com/photo-1533134486753-c833f0ed4866?w=500'),
  
  ('Chocolate Lava Cake', 'Warm chocolate cake with molten center', 1100, 12, 
    (select id from public.categories where name like '%Desserts%' limit 1), 
    'https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=500'),
  
  ('Fresh Lime Juice', 'Freshly squeezed lime with mint', 500, 30, 
    (select id from public.categories where name like '%Drinks%' limit 1), 
    'https://images.unsplash.com/photo-1523371054106-bbf80586c38c?w=500'),
  
  ('Mango Smoothie', 'Creamy mango blend with yogurt', 700, 18, 
    (select id from public.categories where name like '%Drinks%' limit 1), 
    'https://images.unsplash.com/photo-1546173159-315724a31696?w=500'),
  
  ('Crispy Spring Rolls', 'Golden fried vegetable spring rolls with sweet chili sauce', 800, 22, 
    (select id from public.categories where name like '%Snacks%' limit 1), 
    'https://images.unsplash.com/photo-1609501676725-7186f017a4b7?w=500'),
  
  ('Loaded Nachos', 'Tortilla chips with cheese, jalapeños, and salsa', 1200, 15, 
    (select id from public.categories where name like '%Snacks%' limit 1), 
    'https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=500')
on conflict do nothing;

-- 13. Insert default site settings
insert into public.site_settings (key, value) values
  ('business_name', '"Cook Shop Delights"'),
  ('theme', '"light"'),
  ('whatsapp_number', '"15551234567"'),  -- Update this with your actual WhatsApp number
  ('logo_url', '"https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=100"'),
  ('stock_display', 'false')
on conflict (key) do nothing;

-- 14. Create function to handle admin user creation
create or replace function public.create_admin_user(email text)
returns uuid
language plpgsql
security definer
as $$
declare
  user_id uuid;
begin
  -- Insert admin user
  insert into public.admin_users (email, role)
  values (email, 'admin')
  returning id into user_id;
  
  return user_id;
end;
$$;

-- 15. Create function to check if user is admin
create or replace function public.is_admin()
returns boolean
language plpgsql
security definer
as $$
begin
  return exists (
    select 1 from public.admin_users 
    where email = auth.jwt() ->> 'email'
  );
end;
$$;

-- 16. Update RLS policies to use admin check
drop policy if exists "Authenticated users can insert categories" on public.categories;
drop policy if exists "Authenticated users can update categories" on public.categories;
drop policy if exists "Authenticated users can delete categories" on public.categories;

create policy "Admin users can insert categories" 
  on public.categories for insert 
  with check (public.is_admin());

create policy "Admin users can update categories" 
  on public.categories for update 
  using (public.is_admin());

create policy "Admin users can delete categories" 
  on public.categories for delete 
  using (public.is_admin());

drop policy if exists "Authenticated users can read all products" on public.products;
drop policy if exists "Authenticated users can insert products" on public.products;
drop policy if exists "Authenticated users can update products" on public.products;
drop policy if exists "Authenticated users can delete products" on public.products;

create policy "Admin users can read all products" 
  on public.products for select 
  using (public.is_admin());

create policy "Admin users can insert products" 
  on public.products for insert 
  with check (public.is_admin());

create policy "Admin users can update products" 
  on public.products for update 
  using (public.is_admin());

create policy "Admin users can delete products" 
  on public.products for delete 
  using (public.is_admin());

drop policy if exists "Authenticated users can insert settings" on public.site_settings;
drop policy if exists "Authenticated users can update settings" on public.site_settings;
drop policy if exists "Authenticated users can delete settings" on public.site_settings;

create policy "Admin users can insert settings" 
  on public.site_settings for insert 
  with check (public.is_admin());

create policy "Admin users can update settings" 
  on public.site_settings for update 
  using (public.is_admin());

create policy "Admin users can delete settings" 
  on public.site_settings for delete 
  using (public.is_admin());

-- 17. Storage buckets and policies
-- NOTE: You need to create storage buckets manually in Supabase Dashboard first:
-- 1. Go to Storage in your Supabase dashboard
-- 2. Create two buckets: "product-images" and "brand-assets"
-- 3. Make both buckets PUBLIC
-- 4. Then run these storage policies:

-- For product-images bucket (allow public read, admin write)
CREATE POLICY "Public can read product-images" ON storage.objects FOR SELECT USING (bucket_id = 'product-images');
CREATE POLICY "Admin users can upload product-images" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'product-images' AND public.is_admin());
CREATE POLICY "Admin users can update product-images" ON storage.objects FOR UPDATE USING (bucket_id = 'product-images' AND public.is_admin());
CREATE POLICY "Admin users can delete product-images" ON storage.objects FOR DELETE USING (bucket_id = 'product-images' AND public.is_admin());

-- For brand-assets bucket (allow public read, admin write)
CREATE POLICY "Public can read brand-assets" ON storage.objects FOR SELECT USING (bucket_id = 'brand-assets');
CREATE POLICY "Admin users can upload brand-assets" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'brand-assets' AND public.is_admin());
CREATE POLICY "Admin users can update brand-assets" ON storage.objects FOR UPDATE USING (bucket_id = 'brand-assets' AND public.is_admin());
CREATE POLICY "Admin users can delete brand-assets" ON storage.objects FOR DELETE USING (bucket_id = 'brand-assets' AND public.is_admin());

-- 18. Create admin user (replace with your email)
-- IMPORTANT: Replace 'admin@example.com' with your actual email address
-- This will be used to create the first admin user
-- You can create additional admin users through the Supabase dashboard or API

-- Uncomment and modify the line below with your email:
-- SELECT public.create_admin_user('admin@example.com');

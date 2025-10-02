import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  { auth: { persistSession: true, autoRefreshToken: true } }
);

export type Category = {
  id: string;
  name: string;
  slug?: string | null;
  description?: string | null;
  image_url?: string | null;
  created_at?: string | null;
};

export type Product = {
  id: string;
  category_id: string;
  name: string;
  description?: string | null;
  price_cents: number;
  stock: number;
  image_url?: string | null;
  is_active: boolean;
  created_at?: string | null;
};

export type SiteSetting = {
  id: string;
  key: string;
  value: any;
};

export async function getSettings() {
  const { data, error } = await supabase.from("site_settings").select("*");
  if (error) return {};
  const map: Record<string, any> = {};
  (data || []).forEach((row: any) => (map[row.key] = row.value));
  return map as {
    business_name?: string;
    logo_url?: string;
    theme?: string;
    whatsapp_number?: string;
  };
}

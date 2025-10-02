"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import ProductCard from "@/components/ProductCard";
import { Search, Sparkles } from "lucide-react";

export default function Storefront() {
  const [categories, setCategories] = useState<any[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<any>({});

  useEffect(() => {
    supabase.from("categories").select("*").then(({ data }) => {
      setCategories(data || []);
    });
    
    // Load settings
    supabase.from("site_settings").select("*").then(({ data }) => {
      const settingsMap: any = {};
      (data || []).forEach((row: any) => {
        settingsMap[row.key] = row.value;
      });
      setSettings(settingsMap);
    });
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      let req = supabase.from("products").select("*").eq("is_active", true);
      if (active) req = req.eq("category_id", active);
      const { data } = await req;
      const filteredProducts = (data || []).filter(p => p.name.toLowerCase().includes(q.toLowerCase()));
      
      // Add stock display setting to each product
      const productsWithStockSetting = filteredProducts.map(product => ({
        ...product,
        showStock: settings.stock_display === true
      }));
      
      setProducts(productsWithStockSetting);
      setLoading(false);
    })();
  }, [active, q, settings]);

  return (
    <>
      {/* Hero Section */}
      <div className="relative -mt-6 mb-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 opacity-90" />
        <div className="absolute inset-0 bg-black/20" />
        <div className="relative px-6 py-24 text-center text-white">
          <div className="mx-auto max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 backdrop-blur">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-medium">Fresh & Delicious</span>
            </div>
            <h1 className="mb-6 text-5xl font-bold tracking-tight md:text-6xl">
              Welcome to <span className="text-yellow-300">Cook Shop</span>
            </h1>
            <p className="mb-8 text-lg opacity-95 md:text-xl">
              Discover amazing dishes, desserts, and drinks made with love
            </p>
            <div className="relative mx-auto max-w-xl">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input 
                className="w-full rounded-2xl border-0 bg-white/95 px-12 py-4 text-gray-900 placeholder-gray-500 shadow-xl backdrop-blur focus:outline-none focus:ring-4 focus:ring-white/50"
                placeholder="Search for your favorite dish..." 
                value={q} 
                onChange={e => setQ(e.target.value)} 
              />
            </div>
          </div>
        </div>
      </div>

      {/* Categories */}
      <div className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Categories</h2>
          <span className="text-sm text-gray-500">{products.length} items</span>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-2">
          <button 
            className={`whitespace-nowrap rounded-full px-6 py-3 font-medium transition-all ${
              !active 
                ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg" 
                : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300"
            }`} 
            onClick={() => setActive(null)}
          >
            ✨ All Items
          </button>
          {categories.map(c => (
            <button 
              key={c.id} 
              className={`whitespace-nowrap rounded-full px-6 py-3 font-medium transition-all ${
                active === c.id 
                  ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg" 
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300"
              }`} 
              onClick={() => setActive(c.id)}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="aspect-square rounded-2xl bg-gray-200 dark:bg-gray-800" />
              <div className="mt-3 h-4 rounded bg-gray-200 dark:bg-gray-800" />
              <div className="mt-2 h-4 w-2/3 rounded bg-gray-200 dark:bg-gray-800" />
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-gray-500">No products found. Try adjusting your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {products.map(p => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
    </>
  );
}

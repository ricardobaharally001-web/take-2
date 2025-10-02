"use client";
import { supabase } from "@/lib/supabase";
import { useEffect, useState } from "react";
import ImageUpload from "@/components/ImageUpload";
import { Edit2, Trash2, Save, X, ArrowLeft } from "lucide-react";
import Link from "next/link";
import AdminLayout from "@/components/AdminLayout";

export default function ProductsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [cats, setCats] = useState<any[]>([]);
  const [form, setForm] = useState<any>({ 
    name: "", 
    description: "", 
    price_cents: 0, 
    stock: 0, 
    image_url: "", 
    category_id: "", 
    is_active: true 
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const [productsResponse, categoriesResponse] = await Promise.all([
        fetch('/api/admin/products'),
        fetch('/api/admin/categories')
      ]);

      if (!productsResponse.ok) {
        throw new Error('Failed to load products');
      }
      if (!categoriesResponse.ok) {
        throw new Error('Failed to load categories');
      }

      const productsData = await productsResponse.json();
      const categoriesData = await categoriesResponse.json();
      
      setRows(productsData.data || []);
      setCats(categoriesData.data || []);
    } catch (err) {
      console.error("Load error:", err);
      alert("Error loading data: " + (err as Error).message);
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.name || form.price_cents < 0) {
      alert("Please enter product name and valid price");
      return;
    }
    
    setLoading(true);
    try {
      const dataToSave = {
        name: form.name.trim(),
        description: form.description?.trim() || null,
        price_cents: Math.max(0, form.price_cents),
        stock: Math.max(0, form.stock),
        image_url: form.image_url?.trim() || null,
        category_id: form.category_id || null,
        is_active: Boolean(form.is_active)
      };

      const url = editingId ? '/api/admin/products' : '/api/admin/products';
      const method = editingId ? 'PUT' : 'POST';
      const body = editingId ? { id: editingId, ...dataToSave } : dataToSave;

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save product');
      }

      setEditingId(null);
      setForm({ 
        name: "", 
        description: "", 
        price_cents: 0, 
        stock: 0, 
        image_url: "", 
        category_id: "", 
        is_active: true 
      });
      await load();
    } catch (err) {
      console.error("Save error:", err);
      alert("Error saving product: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (product: any) => {
    setEditingId(product.id);
    setForm({
      name: product.name,
      description: product.description || "",
      price_cents: product.price_cents,
      stock: product.stock,
      image_url: product.image_url || "",
      category_id: product.category_id || "",
      is_active: product.is_active
    });
    window.scrollTo(0, 0);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm({ 
      name: "", 
      description: "", 
      price_cents: 0, 
      stock: 0, 
      image_url: "", 
      category_id: "", 
      is_active: true 
    });
  };

  const remove = async (id: string) => {
    if (!confirm("Delete this product?")) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/admin/products?id=${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete product');
      }

      await load();
    } catch (err) {
      console.error("Delete error:", err);
      alert("Error deleting product: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/admin" className="btn btn-ghost">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Link>
        <h1 className="text-2xl font-bold">Manage Products</h1>
      </div>
      
      <div className="card p-6 space-y-4">
        <h2 className="font-semibold">
          {editingId ? "Edit Product" : "Add New Product"}
        </h2>
        
        <div className="grid gap-4 md:grid-cols-2">
          <input 
            className="input" 
            placeholder="Product Name *" 
            value={form.name} 
            onChange={e => setForm({...form, name: e.target.value})} 
          />
          <input 
            className="input" 
            placeholder="Description" 
            value={form.description} 
            onChange={e => setForm({...form, description: e.target.value})} 
          />
          <div>
            <label className="label text-xs mb-1">PRICE ($)</label>
            <input 
              type="number" 
              className="input" 
              placeholder="Price" 
              value={(form.price_cents / 100).toFixed(2)} 
              onChange={e => setForm({...form, price_cents: Math.round(parseFloat(e.target.value || '0') * 100)})} 
              step="0.01"
              min="0"
            />
          </div>
          <div>
            <label className="label text-xs mb-1">STOCK QUANTITY</label>
            <input 
              type="number" 
              className="input" 
              placeholder="Stock" 
              value={form.stock} 
              onChange={e => setForm({...form, stock: parseInt(e.target.value || '0')})} 
              min="0"
            />
          </div>
          <div className="md:col-span-2">
            <label className="label text-xs mb-1">CATEGORY</label>
            <select 
              className="input" 
              value={form.category_id} 
              onChange={e => setForm({...form, category_id: e.target.value})}
            >
              <option value="">Select category</option>
              {cats.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="flex items-center gap-2">
              <input 
                type="checkbox" 
                checked={form.is_active} 
                onChange={e => setForm({...form, is_active: e.target.checked})} 
              />
              <span>Active (visible in store)</span>
            </label>
          </div>
        </div>
        
        <ImageUpload
          value={form.image_url}
          onChange={(url) => setForm({...form, image_url: url})}
          bucket="product-images"
          label="Product Image"
        />
        
        <div className="flex gap-2">
          <button 
            className="btn btn-primary" 
            onClick={save} 
            disabled={loading || !form.name}
          >
            {loading ? "Saving..." : editingId ? "Update Product" : "Add Product"}
          </button>
          {editingId && (
            <button 
              className="btn btn-ghost" 
              onClick={cancelEdit}
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-3">
        {rows.map(r => (
          <div key={r.id} className="card p-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center gap-4 flex-1">
                {r.image_url && r.image_url !== '/placeholder.svg' && (
                  <img 
                    src={r.image_url} 
                    alt={r.name} 
                    className="h-16 w-16 rounded object-cover flex-shrink-0" 
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{r.name}</div>
                  <div className="text-sm text-slate-600 dark:text-slate-300">
                    ${(r.price_cents / 100).toFixed(2)} · Stock: {r.stock}
                    {!r.is_active && <span className="ml-2 text-red-500">(Inactive)</span>}
                  </div>
                  <div className="text-xs text-slate-500">
                    {cats.find(c => c.id === r.category_id)?.name || "No category"}
                  </div>
                </div>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button 
                  className="btn btn-ghost" 
                  onClick={() => startEdit(r)}
                >
                  <Edit2 className="h-4 w-4" />
                </button>
                <button 
                  className="btn btn-danger" 
                  onClick={() => remove(r.id)}
                  disabled={loading}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      </div>
    </AdminLayout>
  );
}

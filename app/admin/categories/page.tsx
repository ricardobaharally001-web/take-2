"use client";
import { supabase } from "@/lib/supabase";
import { useEffect, useState } from "react";
import ImageUpload from "@/components/ImageUpload";
import { Edit2, Trash2, Save, X, ArrowLeft } from "lucide-react";
import Link from "next/link";
import AdminLayout from "@/components/AdminLayout";

export default function CategoriesPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [image_url, setImageUrl] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const response = await fetch('/api/admin/categories');
      
      if (!response.ok) {
        throw new Error('Failed to load categories');
      }

      const data = await response.json();
      setRows(data.data || []);
    } catch (err) {
      console.error("Load error:", err);
      alert("Error loading categories: " + (err as Error).message);
    }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!name.trim()) {
      alert("Please enter a category name");
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/admin/categories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          image_url: image_url.trim() || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to add category');
      }

      setName(""); 
      setDescription(""); 
      setImageUrl("");
      await load();
    } catch (err) {
      console.error("Add error:", err);
      alert("Error adding category: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (row: any) => {
    setEditingId(row.id);
    setEditForm({
      name: row.name,
      description: row.description || "",
      image_url: row.image_url || ""
    });
  };

  const saveEdit = async () => {
    if (!editForm.name?.trim()) {
      alert("Please enter a category name");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/admin/categories', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: editingId,
          name: editForm.name.trim(),
          description: editForm.description?.trim() || null,
          image_url: editForm.image_url?.trim() || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update category');
      }

      setEditingId(null);
      await load();
    } catch (err) {
      console.error("Save error:", err);
      alert("Error saving category: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Delete this category? Products in this category will have no category.")) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/admin/categories?id=${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete category');
      }

      await load();
    } catch (err) {
      console.error("Delete error:", err);
      alert("Error deleting category: " + (err as Error).message);
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
        <h1 className="text-2xl font-bold">Manage Categories</h1>
      </div>
      
      <div className="card p-6 space-y-4">
        <h2 className="font-semibold">Add New Category</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <input 
            className="input" 
            placeholder="Category Name *" 
            value={name} 
            onChange={e => setName(e.target.value)} 
          />
          <input 
            className="input" 
            placeholder="Description" 
            value={description} 
            onChange={e => setDescription(e.target.value)} 
          />
        </div>
        <ImageUpload
          value={image_url}
          onChange={setImageUrl}
          bucket="brand-assets"
          label="Category Image"
        />
        <button 
          className="btn btn-primary" 
          onClick={add} 
          disabled={loading || !name}
        >
          {loading ? "Adding..." : "Add Category"}
        </button>
      </div>

      <div className="space-y-2">
        {rows.map(r => (
          <div key={r.id} className="card p-4">
            {editingId === r.id ? (
              <div className="space-y-3">
                <div className="grid gap-2 md:grid-cols-2">
                  <input
                    className="input"
                    value={editForm.name}
                    onChange={e => setEditForm({...editForm, name: e.target.value})}
                  />
                  <input
                    className="input"
                    value={editForm.description || ""}
                    onChange={e => setEditForm({...editForm, description: e.target.value})}
                  />
                </div>
                <ImageUpload
                  value={editForm.image_url || ""}
                  onChange={(url) => setEditForm({...editForm, image_url: url})}
                  bucket="brand-assets"
                  label="Category Image"
                />
                <div className="flex gap-2">
                  <button 
                    className="btn btn-primary flex items-center gap-2" 
                    onClick={saveEdit}
                    disabled={loading}
                  >
                    <Save className="h-4 w-4" />
                    {loading ? "Saving..." : "Save"}
                  </button>
                  <button 
                    className="btn btn-ghost flex items-center gap-2" 
                    onClick={() => setEditingId(null)}
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex items-center gap-4 flex-1">
                  {r.image_url && r.image_url !== '/placeholder.svg' && (
                    <img src={r.image_url} alt={r.name} className="h-12 w-12 rounded object-cover flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{r.name}</div>
                    <div className="text-sm text-slate-600 dark:text-slate-300 truncate">{r.description}</div>
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
            )}
          </div>
        ))}
      </div>
      </div>
    </AdminLayout>
  );
}

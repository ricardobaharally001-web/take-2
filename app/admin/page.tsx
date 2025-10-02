"use client";
import Link from "next/link";
import AdminLayout from "@/components/AdminLayout";
import { useSimpleAdminAuth } from "@/lib/simple-admin-auth";
import { LogOut } from "lucide-react";

export default function AdminIndex() {
  const { logout } = useSimpleAdminAuth();

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <button 
            onClick={logout}
            className="btn btn-ghost flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Link href="/admin/settings" className="card p-6 hover:shadow-lg transition text-center">
            <div className="text-3xl mb-2">⚙️</div>
            <h2 className="font-semibold">Settings</h2>
            <p className="text-sm text-gray-500 mt-1">Manage site settings</p>
          </Link>
          <Link href="/admin/categories" className="card p-6 hover:shadow-lg transition text-center">
            <div className="text-3xl mb-2">📁</div>
            <h2 className="font-semibold">Categories</h2>
            <p className="text-sm text-gray-500 mt-1">Manage product categories</p>
          </Link>
          <Link href="/admin/products" className="card p-6 hover:shadow-lg transition text-center">
            <div className="text-3xl mb-2">📦</div>
            <h2 className="font-semibold">Products</h2>
            <p className="text-sm text-gray-500 mt-1">Manage products</p>
          </Link>
        </div>
      </div>
    </AdminLayout>
  );
}

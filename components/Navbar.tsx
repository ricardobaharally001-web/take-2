"use client";
import Image from "next/image";
import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import { ShoppingCart, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { getSettings } from "@/lib/supabase";
import { useCart } from "@/lib/cart-store";

export default function Navbar() {
  const [name, setName] = useState("cook-shop");
  const [logo, setLogo] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const items = useCart(s => s.items);
  const itemCount = items.reduce((sum, item) => sum + item.qty, 0);

  useEffect(() => {
    getSettings().then((s: any) => {
      if (s.business_name) setName(s.business_name);
      if (s.logo_url) setLogo(s.logo_url);
    });
  }, []);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 sticky top-0 bg-white dark:bg-gray-900 z-50">
      <nav className="container h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2" onClick={closeMobileMenu}>
            {logo ? (
              <div className="w-7 h-7 rounded-md overflow-hidden">
                <img src={logo} alt="Logo" className="w-full h-full object-cover" />
              </div>
            ) : (
              <div className="w-7 h-7 rounded-md bg-slate-200 dark:bg-slate-700" />
            )}
            <span className="hidden md:inline font-semibold">{name}</span>
          </Link>
        </div>
        
        <div className="md:hidden">
          <Link href="/cart" className="btn btn-ghost relative" aria-label="Cart" onClick={closeMobileMenu}>
            <ShoppingCart />
            {itemCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {itemCount}
              </span>
            )}
          </Link>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-4">
            <Link className="nav-link" href="/">Store</Link>
            <Link className="nav-link relative" href="/cart">
              Cart
              {itemCount > 0 && (
                <span className="absolute -top-2 -right-4 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {itemCount}
                </span>
              )}
            </Link>
            <Link className="nav-link" href="/admin">Admin</Link>
          </div>
          <ThemeToggle />
          <button 
            className="md:hidden btn btn-ghost" 
            aria-label="Menu"
            onClick={toggleMobileMenu}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-white dark:bg-gray-900 border-b border-slate-200 dark:border-slate-800 shadow-lg z-40">
          <div className="container py-4 space-y-4">
            <Link 
              href="/" 
              className="block px-4 py-2 text-lg font-medium text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
              onClick={closeMobileMenu}
            >
              Store
            </Link>
            <Link 
              href="/cart" 
              className="block px-4 py-2 text-lg font-medium text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
              onClick={closeMobileMenu}
            >
              Cart {itemCount > 0 && `(${itemCount})`}
            </Link>
            <Link 
              href="/admin" 
              className="block px-4 py-2 text-lg font-medium text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
              onClick={closeMobileMenu}
            >
              Admin
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

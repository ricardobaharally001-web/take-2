"use client";
import { useEffect, useState, ReactNode } from "react";
import { useCart } from "@/lib/cart-store";
import { useAdminAuth } from "@/lib/admin-auth";

interface HydrationWrapperProps {
  children: ReactNode;
}

export default function HydrationWrapper({ children }: HydrationWrapperProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Hydrate Zustand stores
    useCart.persist.rehydrate();
    useAdminAuth.persist.rehydrate();
    
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return <>{children}</>;
}

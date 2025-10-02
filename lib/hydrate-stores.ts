"use client";
import { useEffect } from "react";
import { useCart } from "./cart-store";
import { useAdminAuth } from "./admin-auth";

export function useHydrateStores() {
  useEffect(() => {
    // Hydrate cart store
    useCart.persist.rehydrate();
    
    // Hydrate admin auth store
    useAdminAuth.persist.rehydrate();
  }, []);
}

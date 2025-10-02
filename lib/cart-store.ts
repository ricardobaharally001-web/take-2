import { create } from "zustand";
import { persist } from "zustand/middleware";

export type CartItem = {
  id: string;
  name: string;
  price_cents: number;
  qty: number;
};

type CartState = {
  items: CartItem[];
  add: (item: CartItem) => void;
  remove: (id: string) => void;
  updateQty: (id: string, qty: number) => void;
  clear: () => void;
  subtotal: () => number;
};

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      add: (item) => {
        const exists = get().items.find(i => i.id === item.id);
        if (exists) {
          set({ items: get().items.map(i => i.id === item.id ? { ...i, qty: i.qty + item.qty } : i) });
        } else {
          set({ items: [...get().items, item] });
        }
      },
      remove: (id) => set({ items: get().items.filter(i => i.id !== id) }),
      updateQty: (id, qty) => set({ items: get().items.map(i => i.id === id ? { ...i, qty } : i) }),
      clear: () => set({ items: [] }),
      subtotal: () => get().items.reduce((sum, i) => sum + i.price_cents * i.qty, 0)
    }),
    { 
      name: "cook-shop-cart",
      skipHydration: true 
    }
  )
);

"use client";
import Image from "next/image";
import { useCart } from "@/lib/cart-store";
import { ShoppingBag, Check } from "lucide-react";
import { useState } from "react";

export default function ProductCard({ product }: { product: any }) {
  const add = useCart(s => s.add);
  const price = (product.price_cents ?? 0) / 100;
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = () => {
    setIsAdding(true);
    add({ id: product.id, name: product.name, price_cents: product.price_cents, qty: 1 });
    
    // Show toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 flex items-center gap-2 animate-slide-up';
    toast.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Added to cart!`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.remove();
    }, 3000);
    
    setTimeout(() => setIsAdding(false), 600);
  };

  return (
    <div className="group relative overflow-hidden rounded-2xl bg-white shadow-lg transition-all hover:shadow-2xl hover:-translate-y-1 dark:bg-gray-900">
      {product.stock < 5 && product.stock > 0 && (
        <div className="absolute left-2 top-2 z-10 rounded-full bg-orange-500 px-2 py-1 text-xs font-bold text-white">
          Only {product.stock} left!
        </div>
      )}
      
      <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900">
        {product.image_url && product.image_url !== '/placeholder.svg' ? (
          <img 
            src={product.image_url} 
            alt={product.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <ShoppingBag className="h-12 w-12 text-gray-400" />
          </div>
        )}
      </div>

      <div className="p-4">
        <div className="mb-2">
          <h3 className="font-bold text-gray-900 dark:text-white">{product.name}</h3>
        </div>
        
        <p className="mb-3 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
          {product.description || "Delicious and fresh"}
        </p>
        
        <div className="flex items-center justify-between">
          <div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              ${price.toFixed(2)}
            </span>
            {product.stock === 0 && (
              <p className="text-xs text-red-500">Out of stock</p>
            )}
            {product.showStock && product.stock > 0 && (
              <p className="text-xs text-gray-500">Stock: {product.stock}</p>
            )}
          </div>
          
          <button 
            className={`rounded-xl px-4 py-2 font-medium transition-all flex items-center gap-1 ${
              isAdding 
                ? "bg-green-500 text-white" 
                : (product.showStock && product.stock === 0)
                ? "cursor-not-allowed bg-gray-200 text-gray-400"
                : "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg"
            }`}
            onClick={handleAdd}
            disabled={product.showStock && product.stock === 0}
          >
            {isAdding ? <><Check className="h-4 w-4" /> Added</> : (product.showStock && product.stock === 0) ? "Sold Out" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}

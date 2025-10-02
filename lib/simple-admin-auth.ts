import { create } from "zustand";
import { persist } from "zustand/middleware";

type SimpleAdminAuthState = {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
};

// Simple hardcoded admin credentials for testing
const ADMIN_EMAIL = "admin@restaurant.com";
const ADMIN_PASSWORD = "admin123";

export const useSimpleAdminAuth = create<SimpleAdminAuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      
      login: async (email: string, password: string) => {
        // Simple email/password check
        if (email.trim().toLowerCase() === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
          set({ isAuthenticated: true });
          return { success: true };
        }
        
        return { success: false, error: "Invalid email or password" };
      },
      
      logout: () => {
        set({ isAuthenticated: false });
      }
    }),
    { 
      name: "simple-admin-auth",
      skipHydration: true 
    }
  )
);

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { supabase } from "./supabase";
import type { User, Session } from "@supabase/supabase-js";

type AdminAuthState = {
  user: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  changePassword: (newPassword: string) => Promise<{ success: boolean; error?: string }>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  initialize: () => Promise<void>;
};

export const useAdminAuth = create<AdminAuthState>()(
  persist(
    (set, get) => ({
      user: null,
      session: null,
      isAuthenticated: false,
      isLoading: true,
      
      initialize: async () => {
        try {
          set({ isLoading: true });
          
          // Get initial session
          const { data: { session }, error } = await supabase.auth.getSession();
          
          if (error) {
            console.error("Session error:", error);
            set({ isLoading: false });
            return;
          }
          
          if (session) {
            set({ 
              user: session.user, 
              session, 
              isAuthenticated: true,
              isLoading: false 
            });
          } else {
            set({ 
              user: null, 
              session: null, 
              isAuthenticated: false,
              isLoading: false 
            });
          }
          
          // Listen for auth changes
          supabase.auth.onAuthStateChange((event, session) => {
            if (event === 'SIGNED_IN' && session) {
              set({ 
                user: session.user, 
                session, 
                isAuthenticated: true 
              });
            } else if (event === 'SIGNED_OUT') {
              set({ 
                user: null, 
                session: null, 
                isAuthenticated: false 
              });
            }
          });
        } catch (error) {
          console.error("Auth initialization error:", error);
          set({ isLoading: false });
        }
      },
      
      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true });
          
          const { data, error } = await supabase.auth.signInWithPassword({
            email: email.trim().toLowerCase(),
            password: password
          });
          
          if (error) {
            set({ isLoading: false });
            return { success: false, error: error.message };
          }
          
          if (data.user && data.session) {
            set({ 
              user: data.user, 
              session: data.session, 
              isAuthenticated: true,
              isLoading: false 
            });
            return { success: true };
          }
          
          set({ isLoading: false });
          return { success: false, error: "Login failed" };
        } catch (error) {
          console.error("Login error:", error);
          set({ isLoading: false });
          return { success: false, error: "An unexpected error occurred" };
        }
      },
      
      logout: async () => {
        try {
          const { error } = await supabase.auth.signOut();
          if (error) {
            console.error("Logout error:", error);
          }
          
          set({ 
            user: null, 
            session: null, 
            isAuthenticated: false 
          });
        } catch (error) {
          console.error("Logout error:", error);
        }
      },
      
      changePassword: async (newPassword: string) => {
        try {
          const { error } = await supabase.auth.updateUser({
            password: newPassword
          });
          
          if (error) {
            return { success: false, error: error.message };
          }
          
          return { success: true };
        } catch (error) {
          console.error("Password change error:", error);
          return { success: false, error: "An unexpected error occurred" };
        }
      },
      
      resetPassword: async (email: string) => {
        try {
          const { error } = await supabase.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
            redirectTo: `${window.location.origin}/admin/reset-password`
          });
          
          if (error) {
            return { success: false, error: error.message };
          }
          
          return { success: true };
        } catch (error) {
          console.error("Password reset error:", error);
          return { success: false, error: "An unexpected error occurred" };
        }
      }
    }),
    { 
      name: "admin-auth",
      skipHydration: true,
      partialize: (state) => ({ 
        user: state.user, 
        session: state.session, 
        isAuthenticated: state.isAuthenticated 
      })
    }
  )
);

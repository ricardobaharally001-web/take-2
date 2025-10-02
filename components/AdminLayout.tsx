"use client";
import { useSimpleAdminAuth } from "@/lib/simple-admin-auth";
import SimpleAdminLogin from "./SimpleAdminLogin";
import { ReactNode } from "react";

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { isAuthenticated } = useSimpleAdminAuth();

  if (!isAuthenticated) {
    return <SimpleAdminLogin />;
  }

  return <>{children}</>;
}

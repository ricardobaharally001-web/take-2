import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { ThemeProvider } from "next-themes";
import HydrationWrapper from "@/components/HydrationWrapper";

export const metadata: Metadata = {
  title: "cook-shop",
  description: "Fast modern storefront powered by Supabase",
  openGraph: { title: "cook-shop", description: "Fast modern storefront", type: "website" }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider 
          attribute="class" 
          defaultTheme="system" 
          enableSystem
          disableTransitionOnChange={false}
        >
          <HydrationWrapper>
            <Navbar />
            <main className="container py-6">{children}</main>
          </HydrationWrapper>
        </ThemeProvider>
      </body>
    </html>
  );
}

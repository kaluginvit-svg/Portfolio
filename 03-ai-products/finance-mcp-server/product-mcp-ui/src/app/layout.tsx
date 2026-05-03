import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "@/components/layout/app-shell";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME || "product-mcp-ui",
  description: "Internal finance UI for product-mcp",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="min-h-screen font-sans">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Table2,
  LineChart,
  Scale,
  Droplets,
  CalendarDays,
  FileText,
  TrendingUp,
  FileDown,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/import", label: "Data import", icon: Upload },
  { href: "/records", label: "Financial records", icon: Table2 },
  { href: "/kpis", label: "KPIs", icon: LineChart },
  { href: "/plan-vs-fact", label: "Plan vs fact", icon: Scale },
  { href: "/liquidity", label: "Liquidity", icon: Droplets },
  { href: "/payments", label: "Payments", icon: CalendarDays },
  { href: "/contracts", label: "Contracts", icon: FileText },
  { href: "/investments", label: "Investments", icon: TrendingUp },
  { href: "/reports", label: "Reports", icon: FileDown },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex w-60 flex-col border-r border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Finance</div>
        <div className="text-lg font-bold text-foreground">{process.env.NEXT_PUBLIC_APP_NAME || "product-mcp-ui"}</div>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

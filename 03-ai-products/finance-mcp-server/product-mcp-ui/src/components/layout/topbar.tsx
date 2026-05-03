"use client";

import { Badge } from "@/components/ui/badge";

export function Topbar({ title, badge }: { title: string; badge?: string }) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card/80 px-6 backdrop-blur">
      <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
      {badge ? <Badge variant="secondary">{badge}</Badge> : null}
    </header>
  );
}

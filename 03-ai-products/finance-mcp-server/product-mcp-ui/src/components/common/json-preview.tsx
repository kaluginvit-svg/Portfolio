"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function JsonPreview({ data, title = "Raw JSON" }: { data: unknown; title?: string }) {
  const [open, setOpen] = useState(false);
  const text = JSON.stringify(data, null, 2);
  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-sm font-medium">{title}</span>
        <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(!open)}>
          {open ? "Hide" : "Show"}
        </Button>
      </div>
      {open ? <pre className="max-h-96 overflow-auto p-3 text-xs">{text}</pre> : null}
    </div>
  );
}

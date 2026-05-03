"use client";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function ErrorState({
  title,
  message,
  technical,
}: {
  title: string;
  message: string;
  technical?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Alert variant="destructive">
      <div className="font-semibold">{title}</div>
      <p className="mt-1 text-sm opacity-90">{message}</p>
      {technical ? (
        <div className="mt-3">
          <Button type="button" variant="outline" size="sm" className="border-destructive/40" onClick={() => setOpen(!open)}>
            {open ? "Hide" : "Show"} technical details
          </Button>
          {open ? (
            <pre className="mt-2 max-h-48 overflow-auto rounded bg-black/5 p-2 text-xs dark:bg-white/10">{technical}</pre>
          ) : null}
        </div>
      ) : null}
    </Alert>
  );
}

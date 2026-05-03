"use client";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

export function ToolRunPanel({
  tool,
  loading,
  error,
  mock,
  children,
}: {
  tool?: string;
  loading?: boolean;
  error?: string | null;
  mock?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {tool ? <Badge variant="outline">Tool: {tool}</Badge> : null}
        {mock ? <Badge variant="secondary">Mock / offline</Badge> : null}
        {loading ? <Badge>Running…</Badge> : null}
      </div>
      {error ? (
        <Alert variant="destructive">
          <strong>Execution error</strong>
          <p className="mt-1 text-sm">{error}</p>
        </Alert>
      ) : null}
      {children}
    </div>
  );
}

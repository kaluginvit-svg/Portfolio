"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

export function ReportDownloadCard({ fileName }: { fileName: string | null | undefined }) {
  if (!fileName) return null;
  const base = fileName.split(/[/\\]/).pop() || fileName;
  const href = `/api/export?file=${encodeURIComponent(base)}`;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Download</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap items-center gap-3">
        <code className="rounded bg-muted px-2 py-1 text-xs">{base}</code>
        <Button asChild size="sm">
          <a href={href} download>
            <Download className="mr-2 h-4 w-4" />
            Download file
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}

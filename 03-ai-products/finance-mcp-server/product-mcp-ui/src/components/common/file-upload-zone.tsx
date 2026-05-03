"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

export function FileUploadZone({
  accept,
  file,
  onFile,
  disabled,
}: {
  accept: string;
  file: File | null;
  onFile: (f: File | null) => void;
  disabled?: boolean;
}) {
  const [drag, setDrag] = useState(false);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDrag(false);
      if (disabled) return;
      const f = e.dataTransfer.files[0];
      if (f) onFile(f);
    },
    [disabled, onFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
        drag ? "border-primary bg-primary/5" : "border-border bg-muted/20",
        disabled && "pointer-events-none opacity-50"
      )}
    >
      <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
      <p className="text-sm font-medium">Drag & drop or choose file</p>
      <p className="mt-1 text-xs text-muted-foreground">{accept}</p>
      <input
        type="file"
        accept={accept}
        className="mt-4 block w-full max-w-xs text-sm"
        disabled={disabled}
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
      {file ? <p className="mt-3 text-sm text-foreground">Selected: {file.name}</p> : null}
    </div>
  );
}

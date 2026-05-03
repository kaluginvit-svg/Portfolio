import * as React from "react";
import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "destructive" }) {
  return (
    <div
      role="alert"
      className={cn(
        "relative w-full rounded-lg border p-4 text-sm",
        variant === "default" && "border-border bg-card",
        variant === "destructive" && "border-destructive/40 bg-destructive/5 text-destructive",
        className
      )}
      {...props}
    />
  );
}

import * as React from "react";
import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        "flex min-h-[132px] w-full rounded-xl border border-[var(--input)] bg-card px-4 py-3.5 text-base text-[var(--text-primary)] shadow-sm transition-[border-color,box-shadow] placeholder:text-[color-mix(in_srgb,var(--text-secondary)_75%,white)] focus-visible:border-[var(--deep-blue)] focus-visible:outline-none focus-visible:ring-[0_0_0_4px_rgba(22,58,99,0.08)] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export { Textarea };

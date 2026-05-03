import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-14 min-h-14 w-full rounded-xl border border-[var(--input)] bg-card px-4 py-2 text-base text-[var(--text-primary)] shadow-sm transition-[border-color,box-shadow] placeholder:text-[color-mix(in_srgb,var(--text-secondary)_75%,white)] focus-visible:border-[var(--deep-blue)] focus-visible:outline-none focus-visible:ring-[0_0_0_4px_rgba(22,58,99,0.08)] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };

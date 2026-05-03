import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold tracking-tight transition-[color,box-shadow,transform,background-color,border-color] duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_35%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--main-bg)] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-45 disabled:active:scale-100 [&_svg]:pointer-events-none [&_svg]:size-[1.125rem] [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--deep-blue)] text-white shadow-[0_1px_0_rgb(255_255_255/0.08)_inset,0_6px_24px_-10px_rgb(22_58_99/0.55)] hover:bg-[color-mix(in_srgb,var(--deep-blue)_88%,black)]",
        cta:
          "bg-[var(--accent-red)] text-white shadow-[0_1px_0_rgb(255_255_255/0.1)_inset,0_8px_28px_-10px_rgb(179_38_46/0.5)] hover:bg-[color-mix(in_srgb,var(--accent-red)_88%,black)]",
        secondary:
          "border border-[var(--cool-border)] bg-[var(--neutral-surface)] text-[var(--text-primary)] shadow-sm hover:bg-[color-mix(in_srgb,var(--section-bg)_65%,white)]",
        outline:
          "border-2 border-[var(--deep-blue)] bg-transparent text-[var(--deep-blue)] shadow-sm hover:bg-[color-mix(in_srgb,var(--soft-blue-bg)_55%,white)]",
        ghost:
          "text-[var(--text-primary)] hover:bg-[color-mix(in_srgb,var(--section-bg)_55%,white)]",
        link: "text-[var(--deep-blue)] underline-offset-4 hover:underline shadow-none active:scale-100",
      },
      size: {
        default: "h-11 min-h-11 px-5 py-2",
        sm: "h-9 min-h-9 rounded-lg px-3.5 text-xs font-medium",
        lg: "h-12 min-h-12 rounded-xl px-7 text-base sm:h-14 sm:min-h-14 sm:px-8",
        touch:
          "min-h-14 h-14 w-full rounded-xl px-6 text-base sm:min-h-12 sm:h-12 sm:w-auto",
        icon: "h-11 w-11 min-h-11 rounded-xl p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };

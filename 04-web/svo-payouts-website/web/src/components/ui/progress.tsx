"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "ds-quiz-progress-track relative w-full overflow-hidden ring-1 ring-[color-mix(in_srgb,var(--cool-border)_80%,transparent)]",
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 rounded-full transition-[transform] duration-700 ease-[cubic-bezier(0.33,1,0.68,1)]"
      style={{
        transform: `translateX(-${100 - (value ?? 0)}%)`,
        background: "linear-gradient(90deg, #163A63 0%, #B3262E 100%)",
        boxShadow: "inset 0 1px 0 rgb(255 255 255 / 0.12)",
      }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };

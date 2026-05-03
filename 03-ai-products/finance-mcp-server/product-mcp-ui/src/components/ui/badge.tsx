import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "secondary" | "destructive" | "outline" }) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        variant === "default" && "border-transparent bg-primary/10 text-primary",
        variant === "secondary" && "border-transparent bg-muted text-muted-foreground",
        variant === "destructive" && "border-transparent bg-destructive/10 text-destructive",
        variant === "outline" && "text-foreground",
        className
      )}
      {...props}
    />
  );
}

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Slot } from "radix-ui"

// SGDS tag: 24px tall, 4px radius, 14px/600 label.
const badgeVariants = cva(
  "inline-flex h-6 w-fit shrink-0 items-center justify-center gap-1 rounded-sm px-2 text-sm font-semibold whitespace-nowrap [&>svg]:pointer-events-none [&>svg]:size-4",
  {
    variants: {
      variant: {
        default: "bg-muted text-foreground",
        muted: "bg-muted text-muted-foreground",
        warning: "bg-warning-subtle text-warning-foreground",
        success: "bg-success-subtle text-success",
        info: "bg-muted text-secondary",
        destructive: "bg-destructive text-destructive-foreground",
        outline: "border border-border bg-card text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }

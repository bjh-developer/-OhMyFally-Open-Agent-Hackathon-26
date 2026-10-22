import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Slot } from "radix-ui"

// SGDS md button: 48px tall, 16px/600 label, 8px radius. Primary is used once per view.
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-lg text-base font-semibold whitespace-nowrap transition-colors duration-200 outline-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-5",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-card text-foreground hover:bg-muted",
        secondary: "border border-input bg-card text-foreground hover:bg-muted",
        ghost: "text-foreground hover:bg-muted",
        link: "min-h-11 text-secondary underline underline-offset-4 hover:no-underline",
      },
      size: {
        default: "h-12 min-w-24 px-5",
        sm: "h-11 min-w-20 px-4",
        lg: "h-12 min-w-24 px-6",
        icon: "size-11",
        "icon-sm": "size-11",
        "icon-lg": "size-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }

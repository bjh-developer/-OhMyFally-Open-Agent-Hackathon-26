import { Badge } from "@/components/ui/badge";
import { STATUS_COPY, type StatusKey } from "@/lib/copy";
import { STATUS_ICON } from "@/lib/icons";

export function StatusBadge({ status }: { status: StatusKey }) {
  const { label, tone } = STATUS_COPY[status];
  const Icon = STATUS_ICON[status];
  return (
    <Badge variant={tone}>
      <Icon aria-hidden strokeWidth={1.75} className={tone === "warning" ? "text-warning" : undefined} />
      {label}
    </Badge>
  );
}

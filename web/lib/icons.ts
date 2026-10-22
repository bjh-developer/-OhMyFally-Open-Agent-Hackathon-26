import { CalendarClock, ChartPie, CircleAlert, CircleCheck, CircleMinus, CircleOff, CircleX, ClipboardX, Flag, History, MapPin, Shapes, SearchX, Split, type LucideIcon } from "lucide-react";
import type { StatusKey } from "./copy";

export const FLAG_ICON: Record<string, LucideIcon> = {
  R1: CalendarClock,
  R2: CircleOff,
  R3: MapPin,
  R4: Split,
  R5: Shapes,
  R6: ChartPie,
  R8: SearchX,
  R9: ClipboardX,
  R7: History,
};
export const flagIcon = (id: string): LucideIcon => FLAG_ICON[id] ?? Flag;

export const STATUS_ICON: Record<StatusKey, LucideIcon> = {
  escalated: CircleAlert,
  accepted: Flag,
  suppressed: History,
  rejected: CircleMinus,
  confirmed: CircleCheck,
  dismissed: CircleX,
};

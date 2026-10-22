"use client";

import { useState } from "react";
import { Check, ChevronDown, ChevronsUpDown, LoaderCircle, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AGENCIES, CHECK_IDS, FLAG_COPY, formatPeriod } from "@/lib/copy";
import { flagIcon } from "@/lib/icons";
import { cn } from "@/lib/utils";
import { useRunCtx } from "@/components/run-provider";

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

// Singapore financial year runs 1 Apr to 31 Mar.
const FY = { from: "2024-04-01", to: "2025-03-31" };
function last12() {
  const to = new Date();
  const from = new Date(to);
  from.setFullYear(from.getFullYear() - 1);
  from.setDate(from.getDate() + 1);
  return { from: iso(from), to: iso(to) };
}

function AgencyCombobox({ value, onChange, invalid }: { value: string; onChange: (v: string) => void; invalid: boolean }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const typed = q.trim();
  const showTyped = typed && !AGENCIES.some((a) => a.toLowerCase() === typed.toLowerCase());
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id="agency"
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-invalid={invalid}
          aria-describedby="agency-help"
          className={cn("w-full justify-between font-normal", invalid && "border-destructive", !value && "text-muted-foreground")}
        >
          <span className="truncate">{value || "Choose or type an agency"}</span>
          <ChevronsUpDown aria-hidden strokeWidth={1.75} className="text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput placeholder="Search or type an agency name" value={q} onValueChange={setQ} className="h-12 text-base" />
          <CommandList>
            <CommandEmpty>No match. Keep typing the full name.</CommandEmpty>
            <CommandGroup>
              {AGENCIES.filter((a) => a.toLowerCase().includes(typed.toLowerCase())).map((a) => (
                <CommandItem
                  key={a}
                  value={a}
                  onSelect={() => {
                    onChange(a);
                    setOpen(false);
                    setQ("");
                  }}
                >
                  <Check aria-hidden className={cn("size-5", value === a ? "opacity-100" : "opacity-0")} />
                  {a}
                </CommandItem>
              ))}
              {showTyped && (
                <CommandItem
                  value={`use-${typed}`}
                  onSelect={() => {
                    onChange(typed);
                    setOpen(false);
                    setQ("");
                  }}
                >
                  <Check aria-hidden className="size-5 opacity-0" />
                  Use “{typed}”
                </CommandItem>
              )}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export function RequestCard() {
  const { form, setForm, checks, setChecks, begin, beginMock, state, runId, isMock } = useRunCtx();
  const [custom, setCustom] = useState(false);
  const [tried, setTried] = useState(false);
  const starting = state === "running" && !runId && !isMock;

  const preset = custom ? "custom" : form.date_from === FY.from && form.date_to === FY.to ? "fy" : (() => {
    const l = last12();
    return form.date_from === l.from && form.date_to === l.to ? "last12" : "custom";
  })();

  const agencyMissing = !form.agency.trim();
  const datesBad = !form.date_from || !form.date_to || form.date_from > form.date_to;
  const selected = checks.length ? checks : CHECK_IDS;

  const pickPreset = (v: string) => {
    if (!v) return;
    if (v === "fy") {
      setCustom(false);
      setForm({ ...form, date_from: FY.from, date_to: FY.to });
    } else if (v === "last12") {
      setCustom(false);
      const l = last12();
      setForm({ ...form, date_from: l.from, date_to: l.to });
    } else setCustom(true);
  };

  const toggleCheck = (id: string, on: boolean) => {
    const next = on ? [...new Set([...selected, id])] : selected.filter((x) => x !== id);
    if (next.length === 0) return; // at least one check must run
    setChecks(next.length === CHECK_IDS.length ? [] : CHECK_IDS.filter((c) => next.includes(c)));
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTried(true);
    if (agencyMissing || datesBad || starting) return;
    begin({ ...form, agency: form.agency.trim() });
  };

  return (
    <Card>
      <CardContent>
        <form onSubmit={submit} noValidate className="grid gap-5" aria-label="Review request">
          <div className="grid gap-2">
            <Label htmlFor="agency">Agency</Label>
            <AgencyCombobox value={form.agency} onChange={(v) => setForm({ ...form, agency: v })} invalid={tried && agencyMissing} />
            {tried && agencyMissing ? (
              <p role="alert" className="text-sm font-semibold text-destructive">Choose an agency to review.</p>
            ) : (
              <p id="agency-help" className="text-sm text-muted-foreground">Type the name exactly as it appears in GeBIZ if it isn't in the list.</p>
            )}
          </div>

          <div className="grid gap-2">
            <Label id="period-label">Period</Label>
            <ToggleGroup type="single" value={preset} onValueChange={pickPreset} aria-labelledby="period-label" variant="outline" spacing={2} className="flex-wrap">
              <ToggleGroupItem value="fy" className="h-12 px-4 text-base font-semibold">FY2024/25</ToggleGroupItem>
              <ToggleGroupItem value="last12" className="h-12 px-4 text-base font-semibold">Last 12 months</ToggleGroupItem>
              <ToggleGroupItem value="custom" className="h-12 px-4 text-base font-semibold">Custom</ToggleGroupItem>
            </ToggleGroup>
            {preset !== "custom" && form.date_from && form.date_to && <p className="text-sm text-muted-foreground">{formatPeriod(form.date_from, form.date_to)}</p>}
            {preset === "custom" && (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label htmlFor="from">From</Label>
                  <Input id="from" type="date" value={form.date_from} max={form.date_to || undefined} onChange={(e) => setForm({ ...form, date_from: e.target.value })} aria-invalid={tried && datesBad} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="to">To</Label>
                  <Input id="to" type="date" value={form.date_to} min={form.date_from || undefined} onChange={(e) => setForm({ ...form, date_to: e.target.value })} aria-invalid={tried && datesBad} />
                </div>
              </div>
            )}
            {tried && datesBad && <p role="alert" className="text-sm font-semibold text-destructive">Pick a start date that is on or before the end date.</p>}
          </div>

          <Collapsible>
            <CollapsibleTrigger className="group flex min-h-11 items-center gap-2 rounded-lg text-left text-base font-semibold text-secondary underline-offset-4 hover:underline">
              <ChevronDown aria-hidden strokeWidth={1.75} className="size-5 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
              Choose which checks to run
            </CollapsibleTrigger>
            <p className="pl-7 text-sm text-muted-foreground">{checks.length ? `${checks.length} of ${CHECK_IDS.length} checks selected` : "All checks run by default"}</p>
            <CollapsibleContent>
              <fieldset className="mt-2 grid gap-1">
                <legend className="sr-only">Checks to run</legend>
                {CHECK_IDS.map((id) => {
                  const Icon = flagIcon(id);
                  return (
                    <label key={id} className="flex min-h-11 cursor-pointer items-start gap-3 rounded-lg px-1 py-2 hover:bg-muted">
                      <Checkbox checked={selected.includes(id)} onCheckedChange={(c) => toggleCheck(id, c === true)} className="mt-0.5" />
                      <Icon aria-hidden size={20} strokeWidth={1.75} className="mt-0.5 shrink-0 text-muted-foreground" />
                      <span className="grid">
                        <span className="text-base font-semibold">{FLAG_COPY[id].check}</span>
                        <span className="text-sm text-muted-foreground">{FLAG_COPY[id].hint}</span>
                      </span>
                    </label>
                  );
                })}
              </fieldset>
            </CollapsibleContent>
          </Collapsible>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
            <Button type="submit" disabled={starting} aria-disabled={starting}>
              {starting ? <LoaderCircle aria-hidden className="animate-spin" /> : <ScanSearch aria-hidden strokeWidth={1.75} />}
              {starting ? "Starting…" : "Start review"}
            </Button>
            <Button type="button" variant="link" onClick={beginMock} disabled={starting}>
              Try a sample review
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

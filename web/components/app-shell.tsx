"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { CircleHelp, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { DISCLAIMER, PROTOTYPE_NOTE } from "@/lib/copy";
import { useRunCtx } from "@/components/run-provider";

const HOW_IT_WORKS = [
  "You choose an agency and a period.",
  "ProcureLens reads that agency's awards and matches each supplier to the company registry.",
  "It runs checks for patterns that often deserve a closer look, such as a company registered just before it won.",
  "It double-checks every result against the records before showing it to you.",
  "You decide what to follow up. ProcureLens remembers your decisions for next time.",
];

function HowItWorks() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="min-w-0 px-3">
          <CircleHelp aria-hidden strokeWidth={1.75} />
          <span className="hidden sm:inline">How it works</span>
          <span className="sr-only sm:hidden">How it works</span>
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader className="p-6 pr-16">
          <SheetTitle className="text-xl leading-7 font-semibold tracking-[-0.4px]">How it works</SheetTitle>
          <SheetDescription>Five steps, in plain words.</SheetDescription>
        </SheetHeader>
        <ol className="grid gap-4 px-6 pb-6 text-base">
          {HOW_IT_WORKS.map((t, i) => (
            <li key={t} className="flex gap-3">
              <span aria-hidden className="flex size-7 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">
                {i + 1}
              </span>
              <span>{t}</span>
            </li>
          ))}
        </ol>
      </SheetContent>
    </Sheet>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { runId } = useRunCtx();
  const tab = pathname.startsWith("/technical") ? "technical" : "review";
  const q = runId ? `?run=${encodeURIComponent(runId)}` : "";
  const go = (v: string) => router.push(`${v === "technical" ? "/technical" : "/"}${q}`);

  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-5 focus:top-2 focus:z-[1600] focus:rounded-lg focus:bg-card focus:px-4 focus:py-3">
        Skip to content
      </a>
      <header className="sticky top-0 z-[100] bg-card shadow-sticky">
        <div className="mx-auto flex max-w-[1168px] flex-wrap items-center gap-x-4 px-5 md:px-7 xl:max-w-[1168px] 2xl:max-w-[1312px]">
          <Link href={`/${q}`} className="flex min-h-14 items-center gap-2 rounded-lg" aria-label="ProcureLens home">
            <ScanSearch size={24} strokeWidth={1.75} className="text-primary" aria-hidden />
            <span className="text-xl font-semibold">ProcureLens</span>
          </Link>
          <div className="ml-auto md:order-3">
            <HowItWorks />
          </div>
          <Tabs value={tab} onValueChange={go} className="w-full gap-0 md:w-auto md:order-2 md:ml-6">
            <TabsList aria-label="Sections" className="-mx-1 w-full md:w-auto">
              <TabsTrigger value="review">Review</TabsTrigger>
              <TabsTrigger value="technical">Technical view</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-[1168px] flex-1 px-5 py-6 md:px-7 md:py-8 2xl:max-w-[1312px]">
        {children}
      </main>
      <footer className="border-t border-border bg-card">
        <div className="mx-auto grid max-w-[1168px] gap-1 px-5 py-5 text-sm text-muted-foreground md:px-7 2xl:max-w-[1312px]">
          <p>{DISCLAIMER}</p>
          <p>{PROTOTYPE_NOTE}</p>
        </div>
      </footer>
    </div>
  );
}

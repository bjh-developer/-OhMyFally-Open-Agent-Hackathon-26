import { ArrowLeftRight, ArrowRight, Brain, Compass, Database, FileText, Link2, Microscope, Scale, ShieldCheck, type LucideIcon } from "lucide-react";

function Node({ icon: Icon, name, note }: { icon: LucideIcon; name: string; note: string }) {
  return (
    <li className="flex min-w-36 flex-1 items-start gap-3 rounded-lg border border-border bg-card p-4">
      <Icon aria-hidden size={24} strokeWidth={1.75} className="mt-0.5 shrink-0 text-primary" />
      <span className="grid">
        <span className="text-base font-semibold">{name}</span>
        <span className="text-sm text-muted-foreground">{note}</span>
      </span>
    </li>
  );
}

const Join = ({ both = false }: { both?: boolean }) => (
  <li aria-hidden className="flex items-center justify-center text-muted-foreground">
    {both ? <ArrowLeftRight size={20} strokeWidth={1.75} /> : <ArrowRight size={20} strokeWidth={1.75} />}
  </li>
);

export function AgentDiagram() {
  return (
    <section aria-labelledby="diagram" className="grid gap-4">
      <h2 id="diagram" className="text-xl leading-7 font-semibold tracking-[-0.4px]">How the agents work together</h2>
      <ol className="flex flex-col gap-2 md:flex-row md:flex-wrap" aria-label="Agent order">
        <Node icon={Compass} name="Planner" note="Chooses the checks" />
        <Join />
        <Node icon={Link2} name="Resolver" note="Matches suppliers to the registry" />
        <Join />
        <Node icon={Microscope} name="Analyst" note="Runs each check" />
        <Join both />
        <Node icon={ShieldCheck} name="Critic" note="Re-runs queries to verify" />
        <Join />
        <Node icon={Scale} name="Risk" note="Wording and escalation" />
        <Join />
        <Node icon={FileText} name="Reporter" note="Writes the summary" />
      </ol>
      <ul className="flex flex-wrap gap-2" aria-label="Services used">
        <li className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 text-base"><Database aria-hidden size={20} strokeWidth={1.75} /> Zetaris: queries across GeBIZ and the company registry</li>
        <li className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 text-base"><Brain aria-hidden size={20} strokeWidth={1.75} /> H-MEM: remembers your decisions</li>
      </ul>
    </section>
  );
}

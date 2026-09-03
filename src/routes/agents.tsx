import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AGENTS } from "@/lib/meteo";
import { useRecords } from "@/lib/store";
import {
  agentMonthStats,
  monthLabel,
  recordsOfMonth,
  serviceHours,
} from "@/lib/agentStats";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Tableau de bord par agent — Messages météo" },
      {
        name: "description",
        content:
          "Suivi mensuel par agent : messages par type, heures de prise de service et de descente, écarts par rapport aux volumes attendus.",
      },
      { property: "og:title", content: "Tableau de bord par agent — Messages météo" },
      {
        property: "og:description",
        content: "Messages par type, horaires de service et écarts vs attendus pour chaque agent.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AgentsPage,
});

const MONTHS = Array.from({ length: 12 }, (_, i) =>
  new Date(2024, i, 1).toLocaleDateString("fr-FR", { month: "long" }),
);

function AgentsPage() {
  const [records] = useRecords();
  const today = new Date();
  const [agent, setAgent] = useState<string>(AGENTS[0]);
  const [month, setMonth] = useState<string>(String(today.getMonth()));
  const [year, setYear] = useState<string>(String(today.getFullYear()));

  const y = Number(year);
  const m = Number(month);

  const stats = useMemo(
    () => agentMonthStats(records, agent, y, m, today),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [records, agent, y, m],
  );

  const agentMonthRecords = useMemo(
    () => recordsOfMonth(records, y, m).filter((r) => r.agent === agent),
    [records, agent, y, m],
  );
  const services = useMemo(() => serviceHours(agentMonthRecords), [agentMonthRecords]);

  const years = Array.from({ length: 5 }, (_, i) => today.getFullYear() - 2 + i);

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Tableau de bord par agent
          </h1>
          <p className="text-sm text-muted-foreground">
            Messages par type, horaires de service et écarts par rapport aux attendus.
          </p>
        </header>

        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-2">
            <Label>Agent</Label>
            <Select value={agent} onValueChange={setAgent}>
              <SelectTrigger className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AGENTS.map((a) => (
                  <SelectItem key={a} value={a}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Mois</Label>
            <Select value={month} onValueChange={setMonth}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MONTHS.map((label, i) => (
                  <SelectItem key={label} value={String(i)}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Année</Label>
            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {years.map((yr) => (
                  <SelectItem key={yr} value={String(yr)}>
                    {yr}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {stats.totalMissing > 0 && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm">
            <p className="flex items-center gap-2 font-semibold text-destructive">
              <AlertTriangle className="size-4" />
              Alerte : {agent} a transmis {stats.totalMissing} message
              {stats.totalMissing > 1 ? "s" : ""} de moins que l'attendu de{" "}
              {monthLabel(y, m)}.
            </p>
            <div className="mt-3 space-y-2">
              {stats.rows
                .filter((r) => (r.missing ?? 0) > 0)
                .map((r) => (
                  <div key={r.type}>
                    <p className="font-medium">
                      {r.type} — {r.missing} manquant{(r.missing ?? 0) > 1 ? "s" : ""}
                    </p>
                    <p className="font-mono text-xs text-muted-foreground">
                      {r.missingSlots.slice(0, 40).join(" · ")}
                      {r.missingSlots.length > 40
                        ? ` … +${r.missingSlots.length - 40} créneaux`
                        : ""}
                    </p>
                  </div>
                ))}
            </div>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Messages par type — {monthLabel(y, m)}
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Attendus</TableHead>
                  <TableHead>Transmis</TableHead>
                  <TableHead>Dans le délai</TableHead>
                  <TableHead>Hors délai</TableHead>
                  <TableHead>Non transmis</TableHead>
                  <TableHead>Écart</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.rows.map((r) => (
                  <TableRow key={r.type}>
                    <TableCell className="font-medium">{r.type}</TableCell>
                    <TableCell className="font-mono">{r.expected ?? "—"}</TableCell>
                    <TableCell className="font-mono">{r.transmitted}</TableCell>
                    <TableCell className="font-mono text-success">{r.onTime}</TableCell>
                    <TableCell className="font-mono text-destructive">{r.late}</TableCell>
                    <TableCell className="font-mono">{r.missing ?? "—"}</TableCell>
                    <TableCell
                      className={`font-mono ${
                        (r.gap ?? 0) < 0 ? "text-destructive" : "text-success"
                      }`}
                    >
                      {r.gap === null ? "—" : r.gap > 0 ? `+${r.gap}` : r.gap}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Heures de prise de service et de descente</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Prise de service</TableHead>
                  <TableHead>Descente</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="py-8 text-center text-muted-foreground">
                      Aucune donnée pour cette période.
                    </TableCell>
                  </TableRow>
                ) : (
                  services.map((s) => (
                    <TableRow key={s.date}>
                      <TableCell>{s.date}</TableCell>
                      <TableCell className="font-mono">{s.start || "—"}</TableCell>
                      <TableCell className="font-mono">{s.end || "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
import { AGENTS, formatHM } from "@/lib/meteo";
import { useRecords } from "@/lib/store";
import { monthLabel, recordsOfMonth } from "@/lib/agentStats";

export const Route = createFileRoute("/historique")({
  head: () => ({
    meta: [
      { title: "Historique mensuel des messages météo" },
      {
        name: "description",
        content:
          "Historique mois par mois de tous les messages transmis, avec statut H+5, heures de prise de service et de descente.",
      },
      { property: "og:title", content: "Historique mensuel des messages météo" },
      {
        property: "og:description",
        content: "Tous les messages du mois avec statut H+5 et horaires de service.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HistoriquePage,
});

const MONTHS = Array.from({ length: 12 }, (_, i) =>
  new Date(2024, i, 1).toLocaleDateString("fr-FR", { month: "long" }),
);

function HistoriquePage() {
  const [records] = useRecords();
  const today = new Date();
  const [month, setMonth] = useState(String(today.getMonth()));
  const [year, setYear] = useState(String(today.getFullYear()));
  const [agent, setAgent] = useState("all");

  const y = Number(year);
  const m = Number(month);

  const list = useMemo(() => {
    const scoped = recordsOfMonth(records, y, m);
    return agent === "all" ? scoped : scoped.filter((r) => r.agent === agent);
  }, [records, y, m, agent]);

  const onTime = list.filter((r) => r.status === "Dans le délai").length;
  const years = Array.from({ length: 5 }, (_, i) => today.getFullYear() - 2 + i);

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Historique mensuel
          </h1>
          <p className="text-sm text-muted-foreground">
            Tous les messages transmis avec leur statut H+5 et les horaires de service.
          </p>
        </header>

        <div className="flex flex-wrap items-end gap-3">
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
          <div className="space-y-2">
            <Label>Agent</Label>
            <Select value={agent} onValueChange={setAgent}>
              <SelectTrigger className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les agents</SelectItem>
                {AGENTS.map((a) => (
                  <SelectItem key={a} value={a}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {monthLabel(y, m)} — {list.length} message(s), {onTime} dans le délai
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Heure message</TableHead>
                  <TableHead>Limite (H+5)</TableHead>
                  <TableHead>Transmis à</TableHead>
                  <TableHead>Prise de service</TableHead>
                  <TableHead>Descente</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">
                      Aucun message pour cette période.
                    </TableCell>
                  </TableRow>
                ) : (
                  list.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="text-muted-foreground">{r.date}</TableCell>
                      <TableCell className="font-medium">{r.agent}</TableCell>
                      <TableCell>{r.type}</TableCell>
                      <TableCell className="font-mono">{formatHM(r.hour, r.minute)}</TableCell>
                      <TableCell className="font-mono">{r.deadline}</TableCell>
                      <TableCell className="font-mono">{r.transmittedAt}</TableCell>
                      <TableCell className="font-mono">{r.serviceStart ?? "—"}</TableCell>
                      <TableCell className="font-mono">{r.serviceEnd ?? "—"}</TableCell>
                      <TableCell>
                        <Badge
                          variant={r.status === "Dans le délai" ? "secondary" : "destructive"}
                          className={
                            r.status === "Dans le délai" ? "bg-success/15 text-success" : undefined
                          }
                        >
                          {r.status === "Dans le délai" ? (
                            <CheckCircle2 className="mr-1 size-3" />
                          ) : (
                            <AlertTriangle className="mr-1 size-3" />
                          )}
                          {r.status}
                        </Badge>
                      </TableCell>
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

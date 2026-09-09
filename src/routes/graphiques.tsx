import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AGENTS, computeBreakdown, periodLabel, type Period } from "@/lib/meteo";
import { useRecords } from "@/lib/store";

export const Route = createFileRoute("/graphiques")({
  head: () => ({
    meta: [
      { title: "Graphiques des transmissions météo" },
      {
        name: "description",
        content:
          "Visualisation graphique des messages météo transmis dans le délai, hors délai et non transmis par type et par agent.",
      },
      { property: "og:title", content: "Graphiques des transmissions météo" },
      {
        property: "og:description",
        content: "Répartition des messages par type, par statut H+5 et par agent.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: GraphiquesPage,
});

function GraphiquesPage() {
  const [records] = useRecords();
  const [period, setPeriod] = useState<Period>("month");
  const [agent, setAgent] = useState("all");
  const today = new Date();

  const scoped = useMemo(
    () => (agent === "all" ? records : records.filter((r) => r.agent === agent)),
    [records, agent],
  );

  const breakdown = useMemo(
    () => computeBreakdown(scoped, period, today, today),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [scoped, period],
  );

  const byType = breakdown.rows.map((r) => ({
    type: r.type,
    "Dans le délai": r.onTime,
    "Hors délai": r.late,
    "Non transmis": r.missing ?? 0,
  }));

  const statusData = [
    { name: "Dans le délai", value: breakdown.totals.onTime },
    { name: "Hors délai", value: breakdown.totals.late },
    { name: "Non transmis", value: breakdown.totals.missing ?? 0 },
  ].filter((d) => d.value > 0);

  const byAgent = AGENTS.map((a) => {
    const list = records.filter((r) => r.agent === a);
    const onTime = list.filter((r) => r.status === "Dans le délai").length;
    return { agent: a.split(" ")[0], "Dans le délai": onTime, "Hors délai": list.length - onTime };
  });

  const STATUS_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)"];
  const AGENT_COLORS = ["var(--chart-4)", "var(--chart-5)"];

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Graphiques</h1>
          <p className="text-sm text-muted-foreground">
            Répartition des transmissions — {periodLabel(period, today)}
          </p>
        </header>

        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-2">
            <Label>Période</Label>
            <Select value={period} onValueChange={(v) => setPeriod(v as Period)}>
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="day">Journalier</SelectItem>
                <SelectItem value="month">Mensuel</SelectItem>
                <SelectItem value="year">Annuel</SelectItem>
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
            <CardTitle className="text-base">Messages par type</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byType}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="type" fontSize={11} interval={0} />
                <YAxis fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                  }}
                />
                <Legend />
                <Bar dataKey="Dans le délai" fill={STATUS_COLORS[0]} radius={[4, 4, 0, 0]} />
                <Bar dataKey="Hors délai" fill={STATUS_COLORS[1]} radius={[4, 4, 0, 0]} />
                <Bar dataKey="Non transmis" fill={STATUS_COLORS[2]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Répartition des statuts</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              {statusData.length === 0 ? (
                <p className="py-20 text-center text-sm text-muted-foreground">
                  Aucune donnée pour cette période.
                </p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={statusData} dataKey="value" nameKey="name" outerRadius={100} label>
                      {statusData.map((d, i) => (
                        <Cell key={d.name} fill={STATUS_COLORS[i % STATUS_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Messages transmis par agent (total)</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byAgent}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="agent" fontSize={11} interval={0} />
                  <YAxis fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Dans le délai" stackId="a" fill={AGENT_COLORS[0]} />
                  <Bar dataKey="Hors délai" stackId="a" fill={AGENT_COLORS[1]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}

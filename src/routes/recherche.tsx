import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import { Badge } from "@/components/ui/badge";
import {
  AGENTS,
  MESSAGE_TYPES,
  formatHM,
  parseFrDate,
  pad,
  type Record as MeteoRecord,
} from "@/lib/meteo";
import { useRecords } from "@/lib/store";

export const Route = createFileRoute("/recherche")({
  head: () => ({
    meta: [
      { title: "Recherche des messages météo par type et période" },
      {
        name: "description",
        content:
          "Recherchez les messages météo par type, agent ou contenu et obtenez le nombre de messages par jour, par mois ou par an.",
      },
      { property: "og:title", content: "Recherche des messages météo" },
      {
        property: "og:description",
        content: "Recherche par type de message et décompte journalier, mensuel ou annuel.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RecherchePage,
});

type Granularity = "day" | "month" | "year";

function bucketKey(r: MeteoRecord, g: Granularity): string {
  const d = parseFrDate(r.date);
  if (!d) return r.date;
  if (g === "day") return r.date;
  if (g === "month") return `${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
  return String(d.getFullYear());
}

function RecherchePage() {
  const [records] = useRecords();
  const [type, setType] = useState("all");
  const [agent, setAgent] = useState("all");
  const [granularity, setGranularity] = useState<Granularity>("day");
  const [query, setQuery] = useState("");

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return records.filter((r) => {
      if (type !== "all" && r.type !== type) return false;
      if (agent !== "all" && r.agent !== agent) return false;
      if (
        q &&
        !`${r.body ?? ""} ${r.type} ${r.agent} ${r.date}`.toLowerCase().includes(q)
      )
        return false;
      return true;
    });
  }, [records, type, agent, query]);

  const buckets = useMemo(() => {
    const map = new Map<string, { key: string; total: number; onTime: number }>();
    for (const r of results) {
      const key = bucketKey(r, granularity);
      const cur = map.get(key) ?? { key, total: 0, onTime: 0 };
      cur.total += 1;
      if (r.status === "Dans le délai") cur.onTime += 1;
      map.set(key, cur);
    }
    return [...map.values()].sort((a, b) => (a.key < b.key ? 1 : -1));
  }, [results, granularity]);

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Recherche de messages
          </h1>
          <p className="text-sm text-muted-foreground">
            Filtrez par type de message et obtenez le décompte par jour, mois ou année.
          </p>
        </header>

        <div className="grid gap-3 md:grid-cols-4">
          <div className="space-y-2">
            <Label>Type de message</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les types</SelectItem>
                {MESSAGE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Agent</Label>
            <Select value={agent} onValueChange={setAgent}>
              <SelectTrigger>
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
          <div className="space-y-2">
            <Label>Décompte</Label>
            <Select
              value={granularity}
              onValueChange={(v) => setGranularity(v as Granularity)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="day">Par jour</SelectItem>
                <SelectItem value="month">Par mois</SelectItem>
                <SelectItem value="year">Par an</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="q">Recherche libre</Label>
            <Input
              id="q"
              value={query}
              maxLength={100}
              placeholder="Texte du message, date…"
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Search className="size-4 text-primary" />
              Décompte — {results.length} message(s) trouvé(s)
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Période</TableHead>
                  <TableHead>Nombre de messages</TableHead>
                  <TableHead>Dans le délai</TableHead>
                  <TableHead>Hors délai</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {buckets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">
                      Aucun résultat.
                    </TableCell>
                  </TableRow>
                ) : (
                  buckets.map((b) => (
                    <TableRow key={b.key}>
                      <TableCell className="font-medium">{b.key}</TableCell>
                      <TableCell className="font-mono">{b.total}</TableCell>
                      <TableCell className="font-mono text-success">{b.onTime}</TableCell>
                      <TableCell className="font-mono text-destructive">
                        {b.total - b.onTime}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Messages correspondants</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Heure</TableHead>
                  <TableHead>Corps du message</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                      Aucun message.
                    </TableCell>
                  </TableRow>
                ) : (
                  results.slice(0, 200).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="text-muted-foreground">{r.date}</TableCell>
                      <TableCell className="font-medium">{r.agent}</TableCell>
                      <TableCell>{r.type}</TableCell>
                      <TableCell className="font-mono">{formatHM(r.hour, r.minute)}</TableCell>
                      <TableCell className="max-w-72 truncate font-mono text-xs">
                        {r.body || "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={r.status === "Dans le délai" ? "secondary" : "destructive"}
                          className={
                            r.status === "Dans le délai" ? "bg-success/15 text-success" : undefined
                          }
                        >
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

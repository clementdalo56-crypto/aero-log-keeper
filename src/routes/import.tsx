import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import {
  AGENTS,
  MESSAGE_TYPES,
  computeStatus,
  deadlineFrom,
  formatHM,
  type Agent,
  type MessageType,
  type Record as MeteoRecord,
} from "@/lib/meteo";
import { useRecords } from "@/lib/store";

export const Route = createFileRoute("/import")({
  head: () => ({
    meta: [
      { title: "Import CSV des messages météo" },
      {
        name: "description",
        content:
          "Chargez un fichier CSV ou Excel exporté en CSV contenant agent, type de message, heure et heure de transmission.",
      },
      { property: "og:title", content: "Import CSV des messages météo" },
      {
        property: "og:description",
        content: "Import en masse des messages météo depuis un fichier CSV.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ImportPage,
});

function splitLine(line: string): string[] {
  const sep = line.includes(";") && !line.includes(",") ? ";" : line.includes(";") ? ";" : ",";
  return line.split(sep).map((c) => c.trim().replace(/^"|"$/g, ""));
}

function norm(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function matchAgent(v: string): Agent | null {
  const n = norm(v);
  return (AGENTS.find((a) => norm(a) === n) as Agent | undefined) ?? null;
}

function matchType(v: string): MessageType | null {
  const n = norm(v);
  return (
    MESSAGE_TYPES.find((t) => norm(t) === n) ??
    MESSAGE_TYPES.find((t) => norm(t).startsWith(n) && n.length > 3) ??
    null
  );
}

function parseTime(v: string): { h: number; m: number } | null {
  const mt = /^(\d{1,2})\s*[:hH]?\s*(\d{2})?$/.exec(v.trim());
  if (!mt) return null;
  const h = Number(mt[1]);
  const m = Number(mt[2] ?? 0);
  if (h > 23 || m > 59) return null;
  return { h, m };
}

function ImportPage() {
  const [, setRecords] = useRecords();
  const [report, setReport] = useState<{ ok: number; errors: string[] } | null>(null);

  async function onFile(file: File) {
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter((l) => l.trim().length);
    if (!lines.length) {
      toast.error("Fichier vide.");
      return;
    }
    const header = splitLine(lines[0]!).map(norm);
    const idx = (...names: string[]) =>
      header.findIndex((h) => names.some((n) => h.includes(n)));
    const iAgent = idx("agent");
    const iType = idx("type", "message");
    const iHour = idx("heure du message", "heure message", "heure");
    const iTx = idx("transmission", "transmis");
    const iDate = idx("date");
    const iStart = idx("prise de service", "prise");
    const iEnd = idx("descente");

    if (iAgent < 0 || iType < 0 || iHour < 0 || iTx < 0) {
      toast.error(
        "En-têtes requis : agent, type, heure du message, heure de transmission.",
      );
      return;
    }

    const errors: string[] = [];
    const parsed: MeteoRecord[] = [];
    const todayStr = new Date().toLocaleDateString("fr-FR");

    lines.slice(1).forEach((line, i) => {
      const cells = splitLine(line);
      const agent = matchAgent(cells[iAgent] ?? "");
      const type = matchType(cells[iType] ?? "");
      const msg = parseTime(cells[iHour] ?? "");
      const tx = parseTime(cells[iTx] ?? "");
      if (!agent) return errors.push(`Ligne ${i + 2} : agent inconnu.`);
      if (!type) return errors.push(`Ligne ${i + 2} : type de message inconnu.`);
      if (!msg) return errors.push(`Ligne ${i + 2} : heure du message invalide.`);
      if (!tx) return errors.push(`Ligne ${i + 2} : heure de transmission invalide.`);

      const { status } = computeStatus(msg.h, msg.m, tx.h, tx.m);
      const d = deadlineFrom(msg.h, msg.m);
      parsed.push({
        id: crypto.randomUUID(),
        agent,
        type,
        hour: msg.h,
        minute: msg.m,
        deadline: formatHM(d.h, d.m),
        transmittedAt: formatHM(tx.h, tx.m),
        status,
        date: (iDate >= 0 ? cells[iDate] : "") || todayStr,
        serviceStart: (iStart >= 0 ? cells[iStart] : "") || "—",
        serviceEnd: (iEnd >= 0 ? cells[iEnd] : "") || "—",
      });
    });

    if (parsed.length) setRecords((prev) => [...parsed, ...prev]);
    setReport({ ok: parsed.length, errors });
    if (parsed.length) toast.success(`${parsed.length} message(s) importé(s).`);
    else toast.error("Aucune ligne valide importée.");
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <Toaster />
      <div className="mx-auto max-w-3xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Import CSV des messages
          </h1>
          <p className="text-sm text-muted-foreground">
            Depuis Excel, enregistrez la feuille au format CSV puis chargez-la ici.
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Fichier à importer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file">Fichier CSV</Label>
              <Input
                id="file"
                type="file"
                accept=".csv,text/csv,text/plain"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void onFile(f);
                }}
              />
            </div>
            <div className="rounded-lg border border-border bg-secondary/40 p-3 text-xs text-muted-foreground">
              <p className="flex items-center gap-2 font-medium text-foreground">
                <Upload className="size-4" /> Colonnes attendues
              </p>
              <p className="mt-2 font-mono">
                agent;type;heure du message;heure de transmission;date;prise de service;descente
              </p>
              <p className="mt-2">
                Les colonnes date, prise de service et descente sont facultatives. Séparateur
                virgule ou point-virgule.
              </p>
            </div>
            <Button variant="secondary" asChild>
              <a
                href={
                  "data:text/csv;charset=utf-8," +
                  encodeURIComponent(
                    "agent;type;heure du message;heure de transmission;date;prise de service;descente\nDALO CLEMENT;METAR;07:00;07:03;01/09/2026;06:00;18:00\n",
                  )
                }
                download="modele-messages-meteo.csv"
              >
                Télécharger un modèle CSV
              </a>
            </Button>
          </CardContent>
        </Card>

        {report && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Résultat de l'import</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p className="text-success">{report.ok} ligne(s) importée(s).</p>
              {report.errors.length > 0 && (
                <ul className="list-inside list-disc space-y-1 text-destructive">
                  {report.errors.slice(0, 20).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}

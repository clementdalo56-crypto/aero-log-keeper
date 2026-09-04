import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { AGENTS } from "@/lib/meteo";
import { useObservations, type Observation } from "@/lib/store";

export const Route = createFileRoute("/observations")({
  head: () => ({
    meta: [
      { title: "Observations sur la qualité des messages — Agents météo" },
      {
        name: "description",
        content:
          "Consignez les observations sur la qualité de rédaction et de transmission des messages météo de chaque agent.",
      },
      {
        property: "og:title",
        content: "Observations sur la qualité des messages — Agents météo",
      },
      {
        property: "og:description",
        content: "Suivi qualitatif du travail des agents : rédaction et transmission.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ObservationsPage,
});

const QUALITIES: Observation["quality"][] = [
  "Excellente",
  "Bonne",
  "Moyenne",
  "Insuffisante",
];

function ObservationsPage() {
  const [observations, setObservations] = useObservations();
  const [agent, setAgent] = useState<string>("");
  const [quality, setQuality] = useState<Observation["quality"] | "">("");
  const [subject, setSubject] = useState("");
  const [comment, setComment] = useState("");
  const [filter, setFilter] = useState("all");

  const list = useMemo(
    () => (filter === "all" ? observations : observations.filter((o) => o.agent === filter)),
    [observations, filter],
  );

  function save() {
    if (!agent || !quality || !comment.trim()) {
      toast.error("Agent, appréciation et observation sont obligatoires.");
      return;
    }
    const obs: Observation = {
      id: crypto.randomUUID(),
      date: new Date().toLocaleDateString("fr-FR"),
      agent,
      quality,
      subject: subject.trim() || "Qualité des messages",
      comment: comment.trim(),
    };
    setObservations((prev) => [obs, ...prev]);
    setSubject("");
    setComment("");
    setQuality("");
    toast.success("Observation enregistrée.");
  }

  function remove(id: string) {
    setObservations((prev) => prev.filter((o) => o.id !== id));
  }

  const tone = (q: Observation["quality"]) =>
    q === "Insuffisante"
      ? "bg-destructive/15 text-destructive"
      : q === "Moyenne"
        ? "bg-warning/15 text-warning"
        : "bg-success/15 text-success";

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <Toaster />
      <div className="mx-auto max-w-4xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Observations sur le travail des agents
          </h1>
          <p className="text-sm text-muted-foreground">
            Qualité des messages rédigés et transmis.
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Nouvelle observation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Agent</Label>
                <Select value={agent} onValueChange={setAgent}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choisir un agent" />
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
                <Label>Appréciation</Label>
                <Select
                  value={quality}
                  onValueChange={(v) => setQuality(v as Observation["quality"])}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Qualité" />
                  </SelectTrigger>
                  <SelectContent>
                    {QUALITIES.map((q) => (
                      <SelectItem key={q} value={q}>
                        {q}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Objet</Label>
                <Input
                  id="subject"
                  value={subject}
                  placeholder="Ex : rédaction du METAR de 12h"
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="comment">Observation</Label>
              <Textarea
                id="comment"
                rows={4}
                value={comment}
                placeholder="Qualité de la rédaction, exactitude des groupes, respect du délai de transmission…"
                onChange={(e) => setComment(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={save}>Enregistrer l'observation</Button>
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-wrap items-center gap-3">
          <Label className="text-muted-foreground">Filtrer par agent</Label>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-64">
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

        <div className="space-y-3">
          {list.length === 0 ? (
            <p className="rounded-lg border border-border p-8 text-center text-sm text-muted-foreground">
              Aucune observation enregistrée.
            </p>
          ) : (
            list.map((o) => (
              <Card key={o.id}>
                <CardContent className="flex items-start justify-between gap-4 pt-6">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{o.agent}</span>
                      <Badge variant="secondary" className={tone(o.quality)}>
                        {o.quality}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{o.date}</span>
                    </div>
                    <p className="text-sm font-medium">{o.subject}</p>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                      {o.comment}
                    </p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => remove(o.id)}>
                    <Trash2 className="size-4" />
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </main>
  );
}

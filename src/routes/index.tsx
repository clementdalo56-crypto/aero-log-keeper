import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, CloudSun, Clock, Timer } from "lucide-react";

import { Button } from "@/components/ui/button";
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
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

import {
  AGENTS,
  MESSAGE_TYPES,
  computeStatus,
  deadlineFrom,
  formatHM,
  hourRuleLabel,
  isHourValid,
  pad,
  type Agent,
  type MessageType,
  type Record as MeteoRecord,
} from "@/lib/meteo";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Décompte des messages météo — Suivi H+5" },
      {
        name: "description",
        content:
          "Saisie et suivi des messages METAR, METREPORT, SPECI et SYNOP par agent, avec contrôle automatique du délai de transmission H+5.",
      },
      { property: "og:title", content: "Décompte des messages météo — Suivi H+5" },
      {
        property: "og:description",
        content:
          "Suivi des transmissions météo par agent : heures théoriques, délai H+5 et statistiques filtrables.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const STORAGE_KEY = "meteo-records-v1";
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function Index() {
  const [records, setRecords] = useState<MeteoRecord[]>([]);
  const [agent, setAgent] = useState<Agent | "">("");
  const [type, setType] = useState<MessageType | "">("");
  const [hour, setHour] = useState<string>("");
  const [minute, setMinute] = useState<string>("00");
  const [transmitTime, setTransmitTime] = useState<string>("");
  const [serviceStart, setServiceStart] = useState<string>("");
  const [serviceEnd, setServiceEnd] = useState<string>("");
  const [filter, setFilter] = useState<string>("all");
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setRecords(JSON.parse(raw));
    } catch {
      /* ignore */
    }
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (records.length) localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  }, [records]);

  const hourNum = hour === "" ? null : Number(hour);
  const minuteNum = Number(minute || 0);
  const hourInvalid =
    type !== "" && hourNum !== null && !isHourValid(type, hourNum);
  const deadline =
    hourNum !== null ? deadlineFrom(hourNum, minuteNum) : null;

  const filtered = useMemo(
    () => (filter === "all" ? records : records.filter((r) => r.agent === filter)),
    [records, filter],
  );

  const stats = useMemo(() => {
    const total = filtered.length;
    const onTime = filtered.filter((r) => r.status === "Dans le délai").length;
    return {
      total,
      onTime,
      late: total - onTime,
      rate: total ? Math.round((onTime / total) * 100) : 0,
    };
  }, [filtered]);

  function transmettre() {
    if (!agent || !type || hourNum === null) {
      toast.error("Veuillez renseigner l'agent, le type de message et l'heure.");
      return;
    }
    if (hourInvalid) {
      toast.error("Heure non valide pour ce type de message.");
      return;
    }
    if (!/^\d{2}:\d{2}$/.test(transmitTime)) {
      toast.error("Veuillez saisir l'heure réelle de transmission.");
      return;
    }
    const [th, tm] = transmitTime.split(":").map(Number);
    const { status, delayMinutes } = computeStatus(hourNum, minuteNum, th, tm);
    const d = deadlineFrom(hourNum, minuteNum);
    const rec: MeteoRecord = {
      id: crypto.randomUUID(),
      agent,
      type,
      hour: hourNum,
      minute: minuteNum,
      deadline: formatHM(d.h, d.m),
      transmittedAt: formatHM(th, tm),
      status,
      date: new Date().toLocaleDateString("fr-FR"),
      serviceStart: serviceStart || "—",
      serviceEnd: serviceEnd || "—",
    };
    setRecords((prev) => [rec, ...prev]);
    if (status === "Dans le délai") {
      toast.success(`Transmis dans le délai (limite ${rec.deadline}).`);
    } else {
      toast.error(`Hors délai de ${delayMinutes} min (limite ${rec.deadline}).`);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8 md:px-8">
      <Toaster />
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
          <div className="flex items-center gap-3">
            <span className="flex size-11 items-center justify-center rounded-lg bg-primary/15 text-primary">
              <CloudSun className="size-6" />
            </span>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
                Décompte des messages météo
              </h1>
              <p className="text-sm text-muted-foreground">
                Contrôle du délai de transmission H+5 par agent
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 font-mono text-sm text-muted-foreground">
            <Clock className="size-4 text-primary" />
            {now
              ? `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
              : "--:--:--"}
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Saisie d'un message</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Agent</Label>
                <Select value={agent} onValueChange={(v) => setAgent(v as Agent)}>
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
                <Label>Type de message</Label>
                <Select value={type} onValueChange={(v) => setType(v as MessageType)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choisir un type" />
                  </SelectTrigger>
                  <SelectContent>
                    {MESSAGE_TYPES.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Heure du message</Label>
                <Select value={hour} onValueChange={setHour}>
                  <SelectTrigger aria-invalid={hourInvalid}>
                    <SelectValue placeholder="Heure" />
                  </SelectTrigger>
                  <SelectContent>
                    {HOURS.map((h) => (
                      <SelectItem key={h} value={String(h)}>
                        {pad(h)}h
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Minute</Label>
                <Select value={minute} onValueChange={setMinute}>
                  <SelectTrigger>
                    <SelectValue placeholder="Minute" />
                  </SelectTrigger>
                  <SelectContent>
                    {["00", "15", "30", "45"].map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="transmit">Heure réelle de transmission</Label>
                <Input
                  id="transmit"
                  type="time"
                  value={transmitTime}
                  onChange={(e) => setTransmitTime(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="service-start">Heure de prise de service</Label>
                <Input
                  id="service-start"
                  type="time"
                  value={serviceStart}
                  onChange={(e) => setServiceStart(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="service-end">Heure de descente</Label>
                <Input
                  id="service-end"
                  type="time"
                  value={serviceEnd}
                  onChange={(e) => setServiceEnd(e.target.value)}
                />
              </div>
            </div>

            {type && (
              <p className="text-xs text-muted-foreground">{hourRuleLabel(type)}</p>
            )}

            {hourInvalid && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>
                  Heure non valide pour un message {type} : {hourRuleLabel(type as MessageType)}.
                </span>
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-secondary/40 p-3">
              <div className="flex items-center gap-2 text-sm">
                <Timer className="size-4 text-primary" />
                <span className="text-muted-foreground">Heure limite (H+5) :</span>
                <span className="font-mono font-semibold text-primary">
                  {deadline ? formatHM(deadline.h, deadline.m) : "--h--"}
                </span>
              </div>
              <Button onClick={transmettre} disabled={hourInvalid}>
                Transmettre
              </Button>
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

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Messages transmis" value={stats.total} />
          <StatCard label="Dans le délai" value={stats.onTime} tone="success" />
          <StatCard label="Hors délai" value={stats.late} tone="destructive" />
          <StatCard label="Taux de ponctualité" value={`${stats.rate}%`} tone="primary" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tableau récapitulatif</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Type de message</TableHead>
                  <TableHead>Heure message</TableHead>
                  <TableHead>Limite (H+5)</TableHead>
                  <TableHead>Transmis à</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                      Aucun message enregistré pour ce filtre.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="text-muted-foreground">{r.date}</TableCell>
                      <TableCell className="font-medium">{r.agent}</TableCell>
                      <TableCell>{r.type}</TableCell>
                      <TableCell className="font-mono">{formatHM(r.hour, r.minute)}</TableCell>
                      <TableCell className="font-mono">{r.deadline}</TableCell>
                      <TableCell className="font-mono">{r.transmittedAt}</TableCell>
                      <TableCell>
                        <Badge
                          variant={r.status === "Dans le délai" ? "secondary" : "destructive"}
                          className={
                            r.status === "Dans le délai"
                              ? "bg-success/15 text-success"
                              : undefined
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

function StatCard({
  label,
  value,
  tone = "muted",
}: {
  label: string;
  value: string | number;
  tone?: "muted" | "success" | "destructive" | "primary";
}) {
  const toneClass = {
    muted: "text-foreground",
    success: "text-success",
    destructive: "text-destructive",
    primary: "text-primary",
  }[tone];
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className={`mt-2 text-3xl font-semibold ${toneClass}`}>{value}</p>
      </CardContent>
    </Card>
  );
}

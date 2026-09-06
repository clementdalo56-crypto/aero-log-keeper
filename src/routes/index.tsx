import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CloudSun,
  Clock,
  Pencil,
  Timer,
  Trash2,
  X,
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

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
  computeBreakdown,
  computeStatus,
  daysInPeriod,
  periodLabel,
  type Period,
  deadlineFrom,
  formatHM,
  hourRuleLabel,
  isHourValid,
  pad,
  findDuplicate,
  frToIso,
  isoToFr,
  todayIso,
  type Agent,
  type MessageType,
  type Record as MeteoRecord,
} from "@/lib/meteo";
import { useRecords } from "@/lib/store";

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


const HOURS = Array.from({ length: 24 }, (_, i) => i);

function Index() {
  const [records, setRecords] = useRecords();
  const [agent, setAgent] = useState<Agent | "">("");
  const [type, setType] = useState<MessageType | "">("");
  const [hour, setHour] = useState<string>("");
  const [minute, setMinute] = useState<string>("00");
  const [transmitTime, setTransmitTime] = useState<string>("");
  const [serviceStart, setServiceStart] = useState<string>("");
  const [serviceEnd, setServiceEnd] = useState<string>("");
  const [dateIso, setDateIso] = useState<string>("");
  const [body, setBody] = useState<string>("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [period, setPeriod] = useState<Period>("day");
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const hourNum = hour === "" ? null : Number(hour);
  const minuteNum = Number(minute || 0);
  const hourInvalid =
    type !== "" && hourNum !== null && !isHourValid(type, hourNum);
  const deadline =
    hourNum !== null ? deadlineFrom(hourNum, minuteNum) : null;

  const maxDate = todayIso(now ?? new Date());
  const effectiveDateIso = dateIso || maxDate;
  const dateInFuture = effectiveDateIso > maxDate;

  const duplicate =
    agent && type && hourNum !== null
      ? findDuplicate(
          records,
          {
            agent,
            type,
            hour: hourNum,
            minute: minuteNum,
            date: isoToFr(effectiveDateIso),
          },
          editingId ?? undefined,
        )
      : undefined;

  const filtered = useMemo(
    () => (filter === "all" ? records : records.filter((r) => r.agent === filter)),
    [records, filter],
  );

  const refDate = now ?? new Date();
  const periodDays = daysInPeriod(period, refDate, refDate);
  const breakdown = useMemo(
    () => computeBreakdown(filtered, period, refDate, refDate),
    [filtered, period, refDate],
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

  function resetForm() {
    setEditingId(null);
    setAgent("");
    setType("");
    setHour("");
    setMinute("00");
    setTransmitTime("");
    setServiceStart("");
    setServiceEnd("");
    setDateIso("");
    setBody("");
  }

  function startEdit(r: MeteoRecord) {
    setEditingId(r.id);
    setAgent(r.agent);
    setType(r.type);
    setHour(String(r.hour));
    setMinute(pad(r.minute));
    setTransmitTime(r.transmittedAt.replace("h", ":"));
    setServiceStart(r.serviceStart === "—" ? "" : r.serviceStart);
    setServiceEnd(r.serviceEnd === "—" ? "" : r.serviceEnd);
    setDateIso(frToIso(r.date));
    setBody(r.body ?? "");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function supprimer(r: MeteoRecord) {
    if (!window.confirm(`Supprimer le message ${r.type} de ${formatHM(r.hour, r.minute)} ?`)) return;
    setRecords((prev) => prev.filter((x) => x.id !== r.id));
    if (editingId === r.id) resetForm();
    toast.success("Message supprimé.");
  }

  function transmettre() {
    if (!agent || !type || hourNum === null) {
      toast.error("Veuillez renseigner l'agent, le type de message et l'heure.");
      return;
    }
    if (hourInvalid) {
      toast.error("Heure non valide pour ce type de message.");
      return;
    }
    if (dateInFuture) {
      toast.error("La date du message ne peut pas être dans le futur.");
      return;
    }
    if (!/^\d{2}:\d{2}$/.test(transmitTime)) {
      toast.error("Veuillez saisir l'heure réelle de transmission.");
      return;
    }
    if (duplicate) {
      toast.error(
        `Doublon : un message ${type} de ${formatHM(hourNum, minuteNum)} existe déjà pour ${agent} ce jour-là.`,
      );
      return;
    }
    const parts = transmitTime.split(":").map(Number);
    const th = parts[0] ?? 0;
    const tm = parts[1] ?? 0;
    const { status, delayMinutes } = computeStatus(hourNum, minuteNum, th, tm);
    const d = deadlineFrom(hourNum, minuteNum);
    const rec: MeteoRecord = {
      id: editingId ?? crypto.randomUUID(),
      agent,
      type,
      hour: hourNum,
      minute: minuteNum,
      deadline: formatHM(d.h, d.m),
      transmittedAt: formatHM(th, tm),
      status,
      date: isoToFr(effectiveDateIso),
      serviceStart: serviceStart || "—",
      serviceEnd: serviceEnd || "—",
      body: body.trim(),
      verified: false,
    };
    if (editingId) {
      setRecords((prev) => prev.map((x) => (x.id === editingId ? rec : x)));
      toast.success("Message modifié.");
    } else {
      setRecords((prev) => [rec, ...prev]);
      if (status === "Dans le délai") {
        toast.success(`Transmis dans le délai (limite ${rec.deadline}).`);
      } else {
        toast.error(`Hors délai de ${delayMinutes} min (limite ${rec.deadline}).`);
      }
    }
    resetForm();
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
          <CardHeader className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="text-base">
              {editingId ? "Modification d'un message" : "Saisie d'un message"}
            </CardTitle>
            {editingId && (
              <Button variant="ghost" size="sm" onClick={resetForm}>
                <X className="mr-1 size-4" /> Annuler la modification
              </Button>
            )}
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

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="date">Date du message</Label>
                <Input
                  id="date"
                  type="date"
                  max={maxDate}
                  value={effectiveDateIso}
                  aria-invalid={dateInFuture}
                  onChange={(e) => setDateIso(e.target.value)}
                />
              </div>
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

            <div className="space-y-2">
              <Label htmlFor="body">Corps du message</Label>
              <Textarea
                id="body"
                rows={3}
                maxLength={1000}
                placeholder="Ex. METAR DIAP 041000Z 9999 SCT013 25/23 Q1013"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Le chef de station pourra vérifier et corriger ce texte depuis l'historique.
              </p>
            </div>

            {dateInFuture && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>Les dates futures ne sont pas autorisées.</span>
              </div>
            )}

            {duplicate && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>
                  Doublon : un message {type} de {hourNum !== null ? formatHM(hourNum, minuteNum) : ""}{" "}
                  a déjà été saisi pour {agent} le {duplicate.date}.
                </span>
              </div>
            )}


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
              <Button
                onClick={transmettre}
                disabled={hourInvalid || dateInFuture || !!duplicate}
              >
                {editingId ? "Enregistrer les modifications" : "Transmettre"}
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
          <CardHeader className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base">
                Décompte par type de message — {periodLabel(period, refDate)}
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Période de {periodDays} jour{periodDays > 1 ? "s" : ""} pris en compte
              </p>
            </div>
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
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type de message</TableHead>
                  <TableHead>Attendus</TableHead>
                  <TableHead>Dans le délai</TableHead>
                  <TableHead>Hors délai</TableHead>
                  <TableHead>Non transmis</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {breakdown.rows.map((r) => (
                  <TableRow key={r.type}>
                    <TableCell className="font-medium">{r.type}</TableCell>
                    <TableCell className="font-mono">{r.expected ?? "—"}</TableCell>
                    <TableCell className="font-mono text-success">
                      {r.onTime}
                      {r.onTimePct !== null && (
                        <span className="ml-1 text-muted-foreground">({r.onTimePct}%)</span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-destructive">
                      {r.late}
                      {r.latePct !== null && (
                        <span className="ml-1 text-muted-foreground">({r.latePct}%)</span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono">
                      {r.missing ?? "—"}
                      {r.missingPct !== null && (
                        <span className="ml-1 text-muted-foreground">({r.missingPct}%)</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow className="border-t-2 font-semibold">
                  <TableCell>Total</TableCell>
                  <TableCell className="font-mono">{breakdown.totals.expected}</TableCell>
                  <TableCell className="font-mono text-success">
                    {breakdown.totals.onTime}
                    {breakdown.totals.onTimePct !== null && (
                      <span className="ml-1 font-normal text-muted-foreground">
                        ({breakdown.totals.onTimePct}%)
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-destructive">
                    {breakdown.totals.late}
                    {breakdown.totals.latePct !== null && (
                      <span className="ml-1 font-normal text-muted-foreground">
                        ({breakdown.totals.latePct}%)
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono">
                    {breakdown.totals.missing}
                    {breakdown.totals.missingPct !== null && (
                      <span className="ml-1 font-normal text-muted-foreground">
                        ({breakdown.totals.missingPct}%)
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <p className="mt-3 text-xs text-muted-foreground">
              Les SPECI étant déclenchés à la demande, aucun décompte théorique ni « non transmis »
              n'est calculé pour ce type.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tableau récapitulatif</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Type de message</TableHead>
                  <TableHead>Heure message</TableHead>
                  <TableHead>Limite (H+5)</TableHead>
                  <TableHead>Transmis à</TableHead>
                  <TableHead>Prise de service</TableHead>
                  <TableHead>Descente</TableHead>
                  <TableHead>Corps du message</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={11} className="py-10 text-center text-muted-foreground">
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
                      <TableCell className="font-mono">{r.serviceStart ?? "—"}</TableCell>
                      <TableCell className="font-mono">{r.serviceEnd ?? "—"}</TableCell>
                      <TableCell className="max-w-64 truncate font-mono text-xs" title={r.body}>
                        {r.body || "—"}
                      </TableCell>
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
                      <TableCell className="text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Modifier"
                          onClick={() => startEdit(r)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Supprimer"
                          className="text-destructive"
                          onClick={() => supprimer(r)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
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

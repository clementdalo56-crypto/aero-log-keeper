export const AGENTS = [
  "DALO CLEMENT",
  "DAO LEA",
  "OTE ARMANDE",
  "KOFFI GISELE",
  "ADOH BOUET",
  "DJAGBA BIENVENU",
] as const;

export type Agent = (typeof AGENTS)[number];

export type MessageType =
  | "METAR"
  | "METREPORT"
  | "SPECI"
  | "SYNOP Horaire"
  | "SYNOP Principal";

export const MESSAGE_TYPES: MessageType[] = [
  "METAR",
  "METREPORT",
  "SPECI",
  "SYNOP Horaire",
  "SYNOP Principal",
];

export const TRI_HORAIRE = [0, 3, 6, 9, 12, 15, 18, 21];

/** Heures théoriques valides pour un type de message. */
export function validHours(type: MessageType): number[] {
  switch (type) {
    case "METAR":
    case "METREPORT":
      return Array.from({ length: 14 }, (_, i) => i + 7); // 07h -> 20h
    case "SYNOP Principal":
      return TRI_HORAIRE;
    case "SPECI":
    case "SYNOP Horaire":
    default:
      return Array.from({ length: 24 }, (_, i) => i);
  }
}

export function isHourValid(type: MessageType, hour: number): boolean {
  return validHours(type).includes(hour);
}

export function hourRuleLabel(type: MessageType): string {
  switch (type) {
    case "METAR":
    case "METREPORT":
      return "Valide uniquement de 07h à 20h";
    case "SYNOP Principal":
      return "Valide uniquement aux heures tri-horaires (00, 03, 06, 09, 12, 15, 18, 21)";
    case "SPECI":
      return "Valide à toutes les heures (déclenché à la demande)";
    case "SYNOP Horaire":
      return "Valide à toutes les heures";
  }
}

export const pad = (n: number) => String(n).padStart(2, "0");

/** Heure limite = heure du message + 5 minutes. */
export function deadlineFrom(hour: number, minute: number): { h: number; m: number } {
  const total = (hour * 60 + minute + 5) % (24 * 60);
  return { h: Math.floor(total / 60), m: total % 60 };
}

export function formatHM(h: number, m: number) {
  return `${pad(h)}h${pad(m)}`;
}

export type Status = "Dans le délai" | "Hors délai";

export interface Record {
  id: string;
  agent: Agent;
  type: MessageType;
  hour: number;
  minute: number;
  deadline: string;
  transmittedAt: string;
  status: Status;
  date: string;
  serviceStart: string;
  serviceEnd: string;
}

/**
 * Compare l'heure de transmission saisie par l'agent à l'heure limite (H+5).
 * Gère le passage de minuit sur une fenêtre courte.
 */
export function computeStatus(
  hour: number,
  minute: number,
  transmitHour: number,
  transmitMinute: number,
): { status: Status; delayMinutes: number } {
  const limit = hour * 60 + minute + 5;
  let actual = transmitHour * 60 + transmitMinute;
  if (actual + 12 * 60 < limit) actual += 24 * 60; // transmission après minuit
  const delayMinutes = actual - limit;
  return { status: delayMinutes <= 0 ? "Dans le délai" : "Hors délai", delayMinutes };
}

/** Nombre de messages théoriquement attendus par jour pour un type. */
export function expectedPerDay(type: MessageType): number | null {
  // SPECI est déclenché à la demande : aucun décompte théorique.
  if (type === "SPECI") return null;
  return validHours(type).length;
}

/** Convertit une date "jj/mm/aaaa" en objet Date local. */
export function parseFrDate(d: string): Date | null {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(d);
  if (!m) return null;
  return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
}

export type Period = "day" | "month" | "year";

export function periodLabel(period: Period, ref: Date): string {
  if (period === "day") return ref.toLocaleDateString("fr-FR");
  if (period === "month")
    return ref.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
  return String(ref.getFullYear());
}

export function inPeriod(d: Date, period: Period, ref: Date): boolean {
  if (d.getFullYear() !== ref.getFullYear()) return false;
  if (period === "year") return true;
  if (d.getMonth() !== ref.getMonth()) return false;
  if (period === "month") return true;
  return d.getDate() === ref.getDate();
}

/** Nombre de jours couverts par la période (jusqu'à aujourd'hui inclus). */
export function daysInPeriod(period: Period, ref: Date, today: Date): number {
  if (period === "day") return 1;
  if (period === "month") {
    const sameMonth =
      ref.getFullYear() === today.getFullYear() && ref.getMonth() === today.getMonth();
    if (sameMonth) return today.getDate();
    return new Date(ref.getFullYear(), ref.getMonth() + 1, 0).getDate();
  }
  if (ref.getFullYear() === today.getFullYear()) {
    const start = new Date(today.getFullYear(), 0, 1);
    return Math.floor((today.getTime() - start.getTime()) / 86400000) + 1;
  }
  return (ref.getFullYear() % 4 === 0 && ref.getFullYear() % 100 !== 0) ||
    ref.getFullYear() % 400 === 0
    ? 366
    : 365;
}

export interface TypeBreakdown {
  type: MessageType;
  expected: number | null;
  onTime: number;
  late: number;
  missing: number | null;
  onTimePct: number | null;
  latePct: number | null;
  missingPct: number | null;
}

export function computeBreakdown(
  records: Record[],
  period: Period,
  ref: Date,
  today: Date,
): { rows: TypeBreakdown[]; totals: TypeBreakdown } {
  const days = daysInPeriod(period, ref, today);
  const scoped = records.filter((r) => {
    const d = parseFrDate(r.date);
    return d ? inPeriod(d, period, ref) : false;
  });

  const pct = (n: number, base: number | null) =>
    base && base > 0 ? Math.round((n / base) * 1000) / 10 : null;

  const rows = MESSAGE_TYPES.map<TypeBreakdown>((type) => {
    const list = scoped.filter((r) => r.type === type);
    const onTime = list.filter((r) => r.status === "Dans le délai").length;
    const late = list.length - onTime;
    const perDay = expectedPerDay(type);
    const expected = perDay === null ? null : perDay * days;
    const missing = expected === null ? null : Math.max(0, expected - list.length);
    const base = expected ?? list.length;
    return {
      type,
      expected,
      onTime,
      late,
      missing,
      onTimePct: pct(onTime, base),
      latePct: pct(late, base),
      missingPct: missing === null ? null : pct(missing, base),
    };
  });

  const sum = (fn: (r: TypeBreakdown) => number | null) =>
    rows.reduce((acc, r) => acc + (fn(r) ?? 0), 0);
  const tExpected = sum((r) => r.expected);
  const tOnTime = sum((r) => r.onTime);
  const tLate = sum((r) => r.late);
  const tMissing = sum((r) => r.missing);
  const tBase = tExpected + rows.reduce((a, r) => a + (r.expected === null ? r.onTime + r.late : 0), 0);

  return {
    rows,
    totals: {
      type: "METAR",
      expected: tExpected,
      onTime: tOnTime,
      late: tLate,
      missing: tMissing,
      onTimePct: pct(tOnTime, tBase),
      latePct: pct(tLate, tBase),
      missingPct: pct(tMissing, tBase),
    },
  };
}

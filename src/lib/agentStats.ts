import {
  MESSAGE_TYPES,
  parseFrDate,
  pad,
  validHours,
  type MessageType,
  type Record as MeteoRecord,
} from "./meteo";

export interface AgentTypeStat {
  type: MessageType;
  expected: number | null;
  transmitted: number;
  onTime: number;
  late: number;
  missing: number | null;
  gap: number | null;
  missingSlots: string[];
}

export function monthLabel(year: number, month: number) {
  return new Date(year, month, 1).toLocaleDateString("fr-FR", {
    month: "long",
    year: "numeric",
  });
}

export function daysCovered(year: number, month: number, today: Date) {
  const sameMonth = today.getFullYear() === year && today.getMonth() === month;
  if (sameMonth) return today.getDate();
  const past =
    year < today.getFullYear() ||
    (year === today.getFullYear() && month < today.getMonth());
  if (!past) return 0;
  return new Date(year, month + 1, 0).getDate();
}

export function recordsOfMonth(
  records: MeteoRecord[],
  year: number,
  month: number,
): MeteoRecord[] {
  return records.filter((r) => {
    const d = parseFrDate(r.date);
    return !!d && d.getFullYear() === year && d.getMonth() === month;
  });
}

/** Statistiques mensuelles d'un agent, avec la liste des créneaux manquants. */
export function agentMonthStats(
  records: MeteoRecord[],
  agent: string,
  year: number,
  month: number,
  today: Date,
): { rows: AgentTypeStat[]; totalMissing: number } {
  const days = daysCovered(year, month, today);
  const scoped = recordsOfMonth(records, year, month).filter((r) => r.agent === agent);

  const rows = MESSAGE_TYPES.map<AgentTypeStat>((type) => {
    const list = scoped.filter((r) => r.type === type);
    const onTime = list.filter((r) => r.status === "Dans le délai").length;
    const late = list.length - onTime;

    if (type === "SPECI") {
      return {
        type,
        expected: null,
        transmitted: list.length,
        onTime,
        late,
        missing: null,
        gap: null,
        missingSlots: [],
      };
    }

    const hours = validHours(type);
    const expected = hours.length * days;
    const done = new Set(list.map((r) => `${r.date}|${r.hour}`));
    const missingSlots: string[] = [];
    for (let day = 1; day <= days; day++) {
      const dateStr = `${pad(day)}/${pad(month + 1)}/${year}`;
      for (const h of hours) {
        if (!done.has(`${dateStr}|${h}`)) missingSlots.push(`${dateStr} ${pad(h)}h`);
      }
    }
    const missing = Math.max(0, expected - list.length);
    return {
      type,
      expected,
      transmitted: list.length,
      onTime,
      late,
      missing,
      gap: list.length - expected,
      missingSlots,
    };
  });

  return {
    rows,
    totalMissing: rows.reduce((a, r) => a + (r.missing ?? 0), 0),
  };
}

export function serviceHours(records: MeteoRecord[]): { date: string; start: string; end: string }[] {
  const map = new globalThis.Map<string, { date: string; start: string; end: string }>();
  for (const r of records) {
    const cur = map.get(r.date);
    if (!cur) map.set(r.date, { date: r.date, start: r.serviceStart, end: r.serviceEnd });
    else {
      if ((!cur.start || cur.start === "—") && r.serviceStart) cur.start = r.serviceStart;
      if ((!cur.end || cur.end === "—") && r.serviceEnd) cur.end = r.serviceEnd;
    }
  }
  return [...map.values()].sort((a, b) => (a.date < b.date ? 1 : -1));
}

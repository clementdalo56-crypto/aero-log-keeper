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

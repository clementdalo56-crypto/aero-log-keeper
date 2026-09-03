import { useCallback, useEffect, useState } from "react";
import type { Record as MeteoRecord } from "./meteo";

export const STORAGE_KEY = "meteo-records-v1";
export const OBS_KEY = "meteo-observations-v1";

const EVENT = "meteo-store-change";

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function useStore<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(fallback);

  useEffect(() => {
    setValue(read<T>(key, fallback));
    const sync = () => setValue(read<T>(key, fallback));
    window.addEventListener(EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener("storage", sync);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const update = useCallback(
    (updater: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const next =
          typeof updater === "function" ? (updater as (p: T) => T)(prev) : updater;
        try {
          localStorage.setItem(key, JSON.stringify(next));
          window.dispatchEvent(new Event(EVENT));
        } catch {
          /* ignore */
        }
        return next;
      });
    },
    [key],
  );

  return [value, update] as const;
}

export function useRecords() {
  return useStore<MeteoRecord[]>(STORAGE_KEY, []);
}

export interface Observation {
  id: string;
  date: string;
  agent: string;
  quality: "Excellente" | "Bonne" | "Moyenne" | "Insuffisante";
  subject: string;
  comment: string;
}

export function useObservations() {
  return useStore<Observation[]>(OBS_KEY, []);
}

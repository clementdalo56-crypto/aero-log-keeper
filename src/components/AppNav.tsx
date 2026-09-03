import { Link } from "@tanstack/react-router";
import { CloudSun } from "lucide-react";

const LINKS = [
  { to: "/", label: "Saisie" },
  { to: "/agents", label: "Tableau de bord agents" },
  { to: "/import", label: "Import CSV" },
  { to: "/historique", label: "Historique" },
  { to: "/observations", label: "Observations" },
] as const;

export function AppNav() {
  return (
    <nav className="sticky top-0 z-40 border-b border-border bg-card/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 md:px-8">
        <span className="flex items-center gap-2 font-semibold">
          <CloudSun className="size-5 text-primary" />
          Messages météo
        </span>
        <div className="flex flex-wrap items-center gap-1">
          {LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              activeOptions={{ exact: l.to === "/" }}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              activeProps={{ className: "bg-secondary text-foreground font-medium" }}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

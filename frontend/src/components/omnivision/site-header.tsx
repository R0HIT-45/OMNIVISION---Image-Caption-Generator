import { Activity, Github, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/omnivision/api";

export function SiteHeader() {
  const { data, isPending } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 60_000,
  });

  return (
    <header className="sticky top-0 z-50 border-b border-border/80 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-[110rem] items-center gap-4 px-6 lg:px-10 xl:px-16">
        <a href="/" className="flex min-w-0 items-center gap-3" aria-label="OmniVision home">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary">
            <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
              <path
                d="M12 4.5c-4.2 0-7.6 3-9 7.5 1.4 4.5 4.8 7.5 9 7.5s7.6-3 9-7.5c-1.4-4.5-4.8-7.5-9-7.5Z"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                className="text-primary-foreground"
              />
              <circle cx="12" cy="12" r="2.6" className="fill-primary-foreground" />
            </svg>
          </span>
          <span className="truncate text-[15px] font-semibold tracking-tight">OmniVision</span>
          <span className="hidden rounded-md border border-border px-2 py-0.5 text-[13px] font-medium text-muted-foreground sm:inline">
            Enterprise
          </span>
        </a>

        <nav className="ml-6 hidden items-center gap-6 text-[15px] text-muted-foreground lg:flex">
          <a className="transition-colors hover:text-foreground" href="#pipeline">
            Pipeline
          </a>
          <a className="transition-colors hover:text-foreground" href="#metrics">
            Performance
          </a>
          <a className="transition-colors hover:text-foreground" href="#diagnostics">
            Diagnostics
          </a>
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-lg border border-border bg-elevated px-3 py-1.5 text-[13px] sm:flex">
            <span
              className={
                "size-1.5 rounded-full " +
                (isPending ? "bg-warning" : data?.online ? "bg-success" : "bg-destructive")
              }
              aria-hidden="true"
            />
            <span className="text-muted-foreground">
              {isPending ? "Checking API" : data?.online ? "All systems operational" : "Degraded"}
            </span>
          </div>
          <span className="hidden items-center gap-1.5 text-[13px] text-subtle md:flex">
            <ShieldCheck className="size-4" aria-hidden="true" /> SOC 2
          </span>
          <span className="hidden items-center gap-1.5 text-[13px] text-subtle md:flex">
            <Activity className="size-4" aria-hidden="true" /> v1.0
          </span>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            aria-label="Open documentation repository"
            className="grid size-9 place-items-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-elevated hover:text-foreground"
          >
            <Github className="size-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </header>
  );
}

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/omnivision/api";

export function Diagnostics() {
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  const rows = [
    { label: "API endpoint", value: "Configured" },
    { label: "Health check", value: isPending ? "Checking…" : isError ? "Failed" : "200 OK" },
    { label: "Round trip", value: data ? `${data.latencyMs} ms` : "—" },
    { label: "Profile", value: data?.profile ?? "—" },
    { label: "Build", value: `v${data?.version ?? "1.0.0"}` },
  ];

  return (
    <section id="diagnostics" aria-labelledby="diagnostics-title" className="border-b border-border">
      <div className="py-14">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,560px)]">
          <div className="max-w-2xl">
            <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
              Diagnostics
            </p>
            <h2 id="diagnostics-title" className="mt-2 text-[28px] font-bold tracking-tight">
              Runtime status
            </h2>
            <p className="mt-3 text-[17px] leading-relaxed text-muted-foreground">
              OmniVision talks to the inference service over{" "}
              <code className="font-mono text-[15px] text-foreground">/health</code> and{" "}
              <code className="font-mono text-[15px] text-foreground">/process-image</code>{" "}
              endpoints. The backend runs BLIP-base captioning, CLIP embedding, NLLB translation
              and XTTS-v2 speech synthesis.
            </p>
            <button
              onClick={() => refetch()}
              className="mt-6 inline-flex min-h-11 items-center rounded-lg border border-border bg-elevated px-4 text-[15px] transition-colors hover:bg-secondary"
            >
              Re-run health check
            </button>
          </div>

          <dl className="panel divide-y divide-border">
            {rows.map((r) => (
              <div key={r.label} className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 px-5 py-4">
                <dt className="truncate text-[15px] text-muted-foreground">{r.label}</dt>
                <dd className="shrink-0 font-mono text-[13px]">{r.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}

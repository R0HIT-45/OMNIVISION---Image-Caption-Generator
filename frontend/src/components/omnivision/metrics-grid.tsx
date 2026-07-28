import type { BackendResponse } from "@/lib/omnivision/types";

interface MetricsProps {
  result: BackendResponse | null;
}

export function MetricsGrid({ result }: MetricsProps) {
  const times = result?.metadata.processing_times ?? {};
  const totalMs = result?.metadata.processing_time_ms ?? 0;

  const cards = [
    { label: "Total latency", value: Math.round(totalMs), hint: "end to end" },
    ...[
      { key: "caption_ms", label: "Vision Captioning" },
      { key: "embedding_ms", label: "Embedding" },
      { key: "retrieval_ms", label: "FAISS Retrieval" },
      { key: "grounding_ms", label: "Grounding" },
      { key: "translation_ms", label: "Translation" },
      { key: "audio_ms", label: "Speech Synthesis" },
    ].map((s) => ({
      label: s.label,
      value: Math.round(times[s.key] ?? 0),
      hint: `${Math.round(times[s.key] ?? 0)} ms`,
    })),
  ];

  return (
    <section id="metrics" aria-labelledby="metrics-title" className="border-b border-border">
      <div className="py-14">
        <div className="max-w-2xl">
          <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
            Performance
          </p>
          <h2 id="metrics-title" className="mt-2 text-[28px] font-bold tracking-tight">
            Latency breakdown
          </h2>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((c) => (
            <div key={c.label} className="panel flex h-full flex-col justify-between p-6">
              <p className="truncate text-[13px] font-medium uppercase tracking-[0.12em] text-subtle">
                {c.label}
              </p>
              <p className="mt-6 text-[36px] font-bold leading-none tracking-tight">
                {c.value}
                <span className="ml-1 text-[15px] font-medium text-muted-foreground">ms</span>
              </p>
              <p className="mt-3 truncate font-mono text-[13px] text-subtle">{c.hint}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

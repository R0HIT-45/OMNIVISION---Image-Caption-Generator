import { motion } from "motion/react";
import { Check, Loader2, Minus } from "lucide-react";
import type { BackendResponse } from "@/lib/omnivision/types";

interface PipelineViewProps {
  result: BackendResponse | null;
}

const STAGE_LABELS: Record<string, { label: string; model: string; description: string }> = {
  caption_ms: {
    label: "Vision Captioning",
    model: "BLIP-base",
    description: "Generates a base caption from the input image using the vision-language model.",
  },
  embedding_ms: {
    label: "Embedding",
    model: "CLIP",
    description: "Projects image features into the multimodal vector space for retrieval.",
  },
  retrieval_ms: {
    label: "FAISS Retrieval",
    model: "FAISS",
    description: "Searches knowledge base for relevant passages using vector similarity.",
  },
  grounding_ms: {
    label: "Grounding",
    model: "Similarity Scorer",
    description: "Evaluates retrieved context against the caption and decides whether to ground.",
  },
  translation_ms: {
    label: "Translation",
    model: "NLLB-200",
    description: "Translates the final caption into Hindi and Telugu.",
  },
  audio_ms: {
    label: "Speech Synthesis",
    model: "XTTS-v2",
    description: "Generates audio narration from the caption text.",
  },
};

export function PipelineView({ result }: PipelineViewProps) {
  const times = result?.metadata.processing_times ?? {};
  const stages = Object.entries(STAGE_LABELS).map(([key, info]) => {
    const ms = times[key];
    const hasValue = typeof ms === "number";
    return {
      id: key,
      ...info,
      latencyMs: hasValue ? Math.round(ms) : 0,
      status: hasValue ? "complete" : ("pending" as const),
    };
  });

  return (
    <section id="pipeline" aria-labelledby="pipeline-title" className="border-b border-border">
      <div className="py-14">
        <div className="max-w-4xl">
          <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
            Explainability
          </p>
          <h2 id="pipeline-title" className="mt-2 text-[28px] font-bold tracking-tight">
            AI pipeline trace
          </h2>
          <p className="mt-3 text-[17px] leading-relaxed text-muted-foreground">
            Each stage reports its model, status and measured latency so results can be audited
            end to end.
          </p>
        </div>

        <ol className="mt-10 grid gap-0">
          {stages.map((stage, i) => (
            <motion.li
              key={stage.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.04, ease: "easeOut" }}
              className="relative grid grid-cols-[auto_minmax(0,1fr)] gap-5 pb-8 last:pb-0"
            >
              {i < stages.length - 1 && (
                <span
                  aria-hidden="true"
                  className={
                    "absolute left-[15px] top-9 h-[calc(100%-1.5rem)] w-px " +
                    (stage.status === "complete" ? "bg-success/50" : "bg-border")
                  }
                />
              )}
              <span
                className={
                  "z-10 grid size-8 shrink-0 place-items-center rounded-full border " +
                  (stage.status === "complete"
                    ? "border-success/50 bg-success/15 text-success"
                    : stage.status === "running"
                      ? "border-primary/60 bg-primary/15 text-primary"
                      : stage.status === "failed"
                        ? "border-destructive/60 bg-destructive/15 text-destructive"
                        : "border-border bg-elevated text-subtle")
                }
              >
                {stage.status === "complete" ? (
                  <Check className="size-4" aria-hidden="true" />
                ) : stage.status === "running" ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : stage.status === "failed" ? (
                  <Minus className="size-4 text-destructive" aria-hidden="true" />
                ) : (
                  <Minus className="size-4" aria-hidden="true" />
                )}
              </span>

              <div className="panel min-w-0 p-6">
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
                  <p className="truncate text-[22px] font-semibold tracking-tight">{stage.label}</p>
                  <span className="shrink-0 font-mono text-[13px] text-muted-foreground">
                    {stage.status === "complete" ? `${stage.latencyMs} ms` : "—"}
                  </span>
                </div>
                <p className="mt-1 font-mono text-[13px] text-subtle">{stage.model}</p>
                <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
                  {stage.description}
                </p>
                <p
                  className={
                    "mt-4 inline-flex items-center gap-2 rounded-md border px-2 py-1 text-[13px] " +
                    (stage.status === "complete"
                      ? "border-success/40 text-success"
                      : stage.status === "running"
                        ? "border-primary/40 text-primary"
                        : stage.status === "failed"
                          ? "border-destructive/40 text-destructive"
                          : "border-border text-subtle")
                  }
                >
                  {stage.status === "complete"
                    ? "Completed"
                    : stage.status === "running"
                      ? "Running"
                      : stage.status === "failed"
                        ? "Failed"
                        : "Pending"}
                </p>
              </div>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}

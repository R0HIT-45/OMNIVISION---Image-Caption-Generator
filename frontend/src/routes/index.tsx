import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import { AlertTriangle } from "lucide-react";

import { SiteHeader } from "@/components/omnivision/site-header";
import { UploadHero } from "@/components/omnivision/upload-hero";
import { CaptionResult } from "@/components/omnivision/caption-result";
import { PipelineView } from "@/components/omnivision/pipeline-view";
import { MetricsGrid } from "@/components/omnivision/metrics-grid";
import { Diagnostics } from "@/components/omnivision/diagnostics";
import { SiteFooter } from "@/components/omnivision/site-footer";
import { processImage, TimeoutError } from "@/lib/omnivision/api";
import type { BackendResponse } from "@/lib/omnivision/types";

const TITLE = "OmniVision — Enterprise Visual Intelligence Platform";
const DESCRIPTION =
  "Explainable multimodal AI: image understanding, FAISS retrieval, grounded captioning, confidence scoring, translation and speech — with full pipeline telemetry.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESCRIPTION },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESCRIPTION },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<BackendResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const elapsedRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    if (elapsedRef.current) {
      clearInterval(elapsedRef.current);
      elapsedRef.current = null;
    }
    setResult(null);
    setError(null);
    setIsProcessing(false);
    setElapsedMs(0);
  }, []);

  const generate = useCallback(async () => {
    if (!file) return;
    reset();
    const controller = new AbortController();
    abortRef.current = controller;
    setIsProcessing(true);
    setElapsedMs(0);
    const start = performance.now();
    elapsedRef.current = setInterval(() => {
      setElapsedMs(Math.round(performance.now() - start));
    }, 200);
    try {
      const res = await processImage({
        file,
        signal: controller.signal,
      });
      setResult(res);
      document.getElementById("caption-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      if (err instanceof TimeoutError) {
        setError("Processing timed out — the backend took longer than expected. Please try again.");
      } else if ((err as Error)?.name !== "AbortError") {
        setError(err instanceof Error ? err.message : "Processing failed");
      }
    } finally {
      if (elapsedRef.current) {
        clearInterval(elapsedRef.current);
        elapsedRef.current = null;
      }
      setIsProcessing(false);
      abortRef.current = null;
    }
  }, [file, reset]);

  const processingTimes = result?.metadata.processing_times ?? {};
  const totalMs = result?.metadata.processing_time_ms ?? 0;

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-[110rem] px-6 lg:px-10 xl:px-16">
        <UploadHero
          file={file}
          previewUrl={previewUrl}
          isProcessing={isProcessing}
          elapsedMs={elapsedMs}
          onSelect={(f) => {
            reset();
            setFile(f);
          }}
          onClear={() => {
            reset();
            setFile(null);
          }}
          onGenerate={generate}
          onCancel={() => abortRef.current?.abort()}
        />

        {error && (
          <div className="py-8">
            <div
              role="alert"
              className="flex flex-wrap items-center gap-4 rounded-xl border border-destructive/40 bg-destructive/10 px-5 py-4"
            >
              <AlertTriangle className="size-5 shrink-0 text-destructive" aria-hidden="true" />
              <p className="min-w-0 flex-1 text-[15px]">Processing failed — {error}</p>
              <button
                onClick={generate}
                className="min-h-11 rounded-lg border border-border bg-elevated px-4 text-[15px] transition-colors hover:bg-secondary"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        <AnimatePresence>{result && <CaptionResult result={result} />}</AnimatePresence>

        <PipelineView result={result} />
        <MetricsGrid result={result} />
        <Diagnostics />
      </main>
      <SiteFooter />
    </div>
  );
}

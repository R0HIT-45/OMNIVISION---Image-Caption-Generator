import { useCallback, useRef, useState } from "react";
import { motion } from "motion/react";
import { ImageUp, Loader2, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadHeroProps {
  file: File | null;
  previewUrl: string | null;
  isProcessing: boolean;
  elapsedMs: number;
  onSelect: (file: File) => void;
  onClear: () => void;
  onGenerate: () => void;
  onCancel: () => void;
}

const ACCEPTED = ["image/png", "image/jpeg", "image/webp"];

function formatBytes(bytes: number) {
  const units = ["B", "KB", "MB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
}

export function UploadHero({
  file,
  previewUrl,
  isProcessing,
  elapsedMs,
  onSelect,
  onClear,
  onGenerate,
  onCancel,
}: UploadHeroProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const processingStatus =
    elapsedMs < 3_000
      ? "Uploading image…"
      : elapsedMs < 10_000
        ? "Loading AI models…"
        : elapsedMs < 30_000
          ? "Analyzing image…"
          : elapsedMs < 90_000
            ? "Generating caption…"
            : elapsedMs < 150_000
              ? "Running retrieval & translation…"
              : "Finalizing pipeline…";

  const accept = useCallback(
    (next: File | undefined) => {
      if (!next) return;
      if (!ACCEPTED.includes(next.type)) {
        setError("Unsupported format. Use PNG, JPG or WEBP.");
        return;
      }
      if (next.size > 12 * 1024 * 1024) {
        setError("File exceeds the 12 MB limit.");
        return;
      }
      setError(null);
      onSelect(next);
    },
    [onSelect],
  );

  return (
    <section className="relative border-b border-border" aria-labelledby="upload-title">
      <div className="surface-grid pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="relative py-24 lg:py-28">
        <div className="mx-auto max-w-4xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-elevated px-3 py-1 text-[13px] font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-primary" aria-hidden="true" />
            Explainable multimodal intelligence
          </span>
          <h1
            id="upload-title"
            className="mt-6 text-[32px] font-bold leading-[1.15] tracking-tight md:text-[42px]"
          >
            Visual intelligence your teams can audit
          </h1>
          <p className="mx-auto mt-4 max-w-3xl text-[19px] leading-relaxed text-muted-foreground">
            Upload an image and OmniVision runs a grounded pipeline — vision encoding, FAISS
            retrieval, confidence evaluation, translation and speech — with every stage traceable.
          </p>
        </div>

        <div className="mt-12 w-full max-w-5xl mx-auto">
          {!file ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  accept(e.dataTransfer.files?.[0]);
                }}
                aria-label="Upload an image for analysis"
                className={
                  "group flex w-full flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-16 text-center transition-all duration-200 md:py-20 " +
                  (dragging
                    ? "border-primary bg-primary/10"
                    : "border-border bg-elevated/60 hover:border-primary/60 hover:bg-elevated")
                }
              >
                <span className="grid size-16 place-items-center rounded-2xl border border-border bg-secondary transition-transform duration-200 group-hover:-translate-y-0.5">
                  <ImageUp className="size-7 text-primary" aria-hidden="true" />
                </span>
                <span className="mt-6 text-[20px] font-semibold">
                  Drop an image, or click to browse
                </span>
                <span className="mt-2 text-[15px] text-muted-foreground">
                  PNG, JPG or WEBP · up to 12 MB · processed in-region
                </span>
              </button>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED.join(",")}
                className="sr-only"
                onChange={(e) => accept(e.target.files?.[0])}
              />
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.985 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="panel overflow-hidden"
            >
              <div className="grid gap-0 md:grid-cols-[minmax(0,1fr)_320px]">
                <div className="relative aspect-video bg-background">
                  {previewUrl && (
                    <img
                      src={previewUrl}
                      alt={`Preview of ${file.name}`}
                      className="size-full object-contain"
                    />
                  )}
                </div>
                <div className="flex flex-col gap-6 border-t border-border p-6 md:border-l md:border-t-0">
                  <div className="min-w-0">
                    <p className="truncate text-[15px] font-semibold">{file.name}</p>
                    <p className="mt-1 text-[13px] text-subtle">
                      {formatBytes(file.size)} · {file.type.replace("image/", "").toUpperCase()}
                    </p>
                  </div>
                  <dl className="grid grid-cols-2 gap-4 text-[13px]">
                    <div>
                      <dt className="text-subtle">Pipeline</dt>
                      <dd className="mt-1 font-medium">6 stages</dd>
                    </div>
                    <div>
                      <dt className="text-subtle">Region</dt>
                      <dd className="mt-1 font-medium">eu-west-1</dd>
                    </div>
                  </dl>
                  <div className="mt-auto flex flex-col gap-3">
                    {isProcessing ? (
                      <Button
                        size="lg"
                        variant="secondary"
                        className="h-12 w-full text-[15px]"
                        onClick={onCancel}
                      >
                        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                        Cancel run
                      </Button>
                    ) : (
                      <Button size="lg" className="h-12 w-full text-[15px]" onClick={onGenerate}>
                        <Sparkles className="size-4" aria-hidden="true" />
                        Generate analysis
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      className="h-11 w-full text-[15px] text-muted-foreground"
                      onClick={onClear}
                      disabled={isProcessing}
                    >
                      <X className="size-4" aria-hidden="true" />
                      Replace image
                    </Button>
                    {isProcessing && (
                      <p className="text-center text-[13px] text-muted-foreground">
                        {processingStatus}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {error && (
            <p role="alert" className="mt-4 text-center text-[13px] text-destructive">
              {error}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

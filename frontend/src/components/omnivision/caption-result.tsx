import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { Check, Copy, Download, Languages, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { BackendResponse } from "@/lib/omnivision/types";

interface CaptionResultProps {
  result: BackendResponse;
}

export function CaptionResult({ result }: CaptionResultProps) {
  const { explainability, data, retrieved_entries } = result;
  const caption = data.final_caption || data.raw_caption;

  const translationEntries = useMemo(
    () => Object.entries(data.translations),
    [data.translations],
  );
  const [lang, setLang] = useState("en");
  const [copied, setCopied] = useState(false);

  const displayCaption =
    lang !== "en" && data.translations[lang]
      ? data.translations[lang]
      : caption;

  const labelColors: Record<string, string> = {
    High: "border-success/40 bg-success/10 text-success",
    Medium: "border-amber-500/40 bg-amber-500/10 text-amber-500",
    Low: "border-orange-500/40 bg-orange-500/10 text-orange-500",
    Reject: "border-destructive/40 bg-destructive/10 text-destructive",
  };
  const dotColors: Record<string, string> = {
    High: "bg-success",
    Medium: "bg-amber-500",
    Low: "bg-orange-500",
    Reject: "bg-destructive",
  };

  const label = explainability.confidenceLabel ?? "High";
  const confStyle = labelColors[label] ?? labelColors.High;
  const dotStyle = dotColors[label] ?? dotColors.High;

  const speak = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const utterance = new SpeechSynthesisUtterance(displayCaption);
    utterance.lang = lang;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const download = () => {
    const blob = new Blob([displayCaption], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `omnivision-${result.request_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.section
      aria-labelledby="caption-title"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="border-b border-border"
    >
      <div className="py-14">
        <div className="max-w-4xl">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 sm:flex sm:justify-between">
            <div className="min-w-0">
              <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
                Generated caption
              </p>
              <h2 id="caption-title" className="mt-2 truncate text-[28px] font-bold">
                Grounded result
              </h2>
            </div>
            <span
              className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-[13px] font-medium ${confStyle}`}
            >
              <span className={`size-1.5 rounded-full ${dotStyle}`} aria-hidden="true" />
              {label} confidence
            </span>
          </div>

          <p className="mt-8 text-[26px] font-semibold leading-[1.5] tracking-tight md:text-[30px]">
            {displayCaption}
          </p>

          <div className="mt-6 h-1 w-full overflow-hidden rounded-full bg-secondary">
            <motion.div
              className={`h-full rounded-full ${dotStyle}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(explainability.similarity_score * 100, 100)}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
          {explainability.reason && (
            <p className="mt-3 text-[14px] font-medium text-muted-foreground">
              {explainability.reason}
            </p>
          )}
          <p className="mt-3 text-[13px] text-subtle">
            request {result.request_id}
            {retrieved_entries.length > 0 &&
              ` · grounded on ${retrieved_entries.length} retrieved passages`}
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button
              variant="secondary"
              className="h-11 text-[15px]"
              onClick={() => {
                navigator.clipboard?.writeText(displayCaption);
                setCopied(true);
                setTimeout(() => setCopied(false), 1600);
              }}
            >
              {copied ? (
                <Check className="size-4 text-success" aria-hidden="true" />
              ) : (
                <Copy className="size-4" aria-hidden="true" />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>
            <Button variant="secondary" className="h-11 text-[15px]" onClick={download}>
              <Download className="size-4" aria-hidden="true" />
              Download
            </Button>
            <Button variant="secondary" className="h-11 text-[15px]" onClick={speak}>
              <Volume2 className="size-4" aria-hidden="true" />
              Play audio
            </Button>
          </div>

          {translationEntries.length > 0 && (
            <div className="mt-10 border-t border-border pt-8">
              <div className="flex items-center gap-2 text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
                <Languages className="size-4" aria-hidden="true" />
                Translations
              </div>
              <div
                role="tablist"
                aria-label="Caption language"
                className="mt-4 flex flex-wrap gap-2"
              >
                <button
                  key="en"
                  role="tab"
                  aria-selected={lang === "en"}
                  onClick={() => setLang("en")}
                  className={
                    "min-h-11 rounded-lg border px-4 text-[15px] transition-colors " +
                    (lang === "en"
                      ? "border-primary bg-primary/15 text-foreground"
                      : "border-border bg-elevated text-muted-foreground hover:text-foreground")
                  }
                >
                  English
                </button>
                {translationEntries.map(([code, _text]) => (
                  <button
                    key={code}
                    role="tab"
                    aria-selected={lang === code}
                    onClick={() => setLang(code)}
                    className={
                      "min-h-11 rounded-lg border px-4 text-[15px] transition-colors " +
                      (lang === code
                        ? "border-primary bg-primary/15 text-foreground"
                        : "border-border bg-elevated text-muted-foreground hover:text-foreground")
                    }
                  >
                    {code === "hindi" ? "हिन्दी" : code === "telugu" ? "తెలుగు" : code}
                  </button>
                ))}
              </div>
            </div>
          )}

          {retrieved_entries.length > 0 && (
            <div className="mt-10 border-t border-border pt-8">
              <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-subtle">
                Retrieved evidence
              </p>
              <ul className="mt-4 grid gap-3">
                {retrieved_entries.map((entry, i) => (
                  <li key={i} className="panel p-6">
                    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
                      <p className="truncate text-[16px] font-medium">{entry.entity}</p>
                      <span className="shrink-0 rounded-md border border-border px-2 py-0.5 font-mono text-[13px] text-muted-foreground">
                        {entry.score.toFixed(3)}
                      </span>
                    </div>
                    <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
                      {entry.fact}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );
}

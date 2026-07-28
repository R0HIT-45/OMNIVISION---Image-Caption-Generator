export function SiteFooter() {
  return (
    <footer className="bg-background">
      <div className="mx-auto grid w-full max-w-[110rem] gap-8 px-6 py-16 lg:grid-cols-[minmax(0,1fr)_auto] lg:px-10 xl:px-16">
        <div className="min-w-0">
          <p className="text-[15px] font-semibold tracking-tight">OmniVision</p>
          <p className="mt-2 max-w-md text-[15px] leading-relaxed text-muted-foreground">
            Enterprise visual intelligence with grounded retrieval, explainable pipelines and
            auditable performance telemetry.
          </p>
        </div>
        <div className="flex flex-wrap items-start gap-x-8 gap-y-3 text-[15px] text-muted-foreground">
          <a className="transition-colors hover:text-foreground" href="#pipeline">
            Pipeline
          </a>
          <a className="transition-colors hover:text-foreground" href="#metrics">
            Performance
          </a>
          <a className="transition-colors hover:text-foreground" href="#diagnostics">
            Diagnostics
          </a>
        </div>
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex w-full max-w-[110rem] flex-wrap items-center justify-between gap-3 px-6 py-6 text-[13px] text-subtle lg:px-10 xl:px-16">
          <p>© {new Date().getFullYear()} OmniVision. All rights reserved.</p>
          <p className="font-mono">build 1.0.0 · eu-west-1</p>
        </div>
      </div>
    </footer>
  );
}

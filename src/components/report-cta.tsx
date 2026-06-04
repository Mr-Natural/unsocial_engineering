import Link from "next/link";

export function ReportCTA() {
  return (
    <div className="rounded-xl border border-warn/30 bg-warn/5 p-5">
      <h3 className="font-semibold text-fg">Seen something like this?</h3>
      <p className="mt-1 text-sm text-muted">
        Run a suspicious message through our checker, or report it so we can warn others.
      </p>
      <Link
        href="/check"
        className="mt-4 inline-flex rounded-lg bg-warn px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-warn-strong"
      >
        Report a scam
      </Link>
    </div>
  );
}

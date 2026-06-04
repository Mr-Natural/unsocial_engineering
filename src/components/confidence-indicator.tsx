// Visual confidence signal. Published articles cleared the editor's threshold,
// but surfacing the score keeps the site transparent about AI involvement.

export function ConfidenceIndicator({ value }: { value: number | null }) {
  if (value == null) return null;

  const tone =
    value >= 85
      ? "text-safe-strong"
      : value >= 70
        ? "text-warn"
        : "text-red-400";

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium ${tone}`}
      title="AI confidence score from the editorial fact-check"
    >
      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <path d="M12 2 4 5v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V5l-8-3Z" strokeLinejoin="round" />
        <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {value}% confidence
    </span>
  );
}

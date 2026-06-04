// Homepage hero search → article search. Plain GET form (no client JS) to /scams.

export function HeroSearch() {
  return (
    <form action="/scams" method="get" className="mt-8 w-full max-w-xl">
      <div className="relative">
        <svg
          viewBox="0 0 24 24"
          className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3-3" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          name="q"
          required
          placeholder="Search scams... e.g. PayPal, fake invoice, romance"
          aria-label="Search scams"
          className="w-full rounded-lg border border-line bg-surface py-3 pl-12 pr-4 text-fg placeholder:text-muted focus:border-safe focus:outline-none focus:ring-1 focus:ring-safe"
        />
        <button
          type="submit"
          aria-label="Search"
          className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-md bg-safe px-4 py-1.5 text-sm font-semibold text-ink transition-colors hover:bg-safe-strong"
        >
          Search
        </button>
      </div>
    </form>
  );
}

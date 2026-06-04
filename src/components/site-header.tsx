import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-ink/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
          <svg viewBox="0 0 24 24" className="h-7 w-7 text-safe" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M12 2 4 5v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V5l-8-3Z" strokeLinejoin="round" />
            <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="text-base sm:text-lg">
            Unsocial<span className="text-safe">Engineering</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 text-sm sm:gap-2">
          <Link href="/scams" className="rounded-md px-3 py-2 text-muted hover:bg-surface hover:text-fg">
            Browse
          </Link>
          <Link
            href="/check"
            className="rounded-md bg-warn px-3 py-2 font-medium text-ink hover:bg-warn-strong"
          >
            Is this a scam?
          </Link>
        </nav>
      </div>
    </header>
  );
}

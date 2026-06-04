import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-line bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-muted">
        <div className="flex flex-col gap-6 sm:flex-row sm:justify-between">
          <div className="max-w-md">
            <p className="font-semibold text-fg">UnsocialEngineering</p>
            <p className="mt-2">
              Practical, plain-language scam awareness. We track how scams work so
              you can spot them before they cost you.
            </p>
          </div>
          <nav className="flex flex-col gap-2">
            <Link href="/scams" className="hover:text-fg">Browse scams</Link>
            <Link href="/check" className="hover:text-fg">Is this a scam?</Link>
          </nav>
        </div>

        <p className="mt-8 border-t border-line pt-6 text-xs leading-relaxed">
          Information only. Not legal advice. If you have been scammed, contact the
          relevant authority: the ACCC (Scamwatch) in Australia, the FTC in the
          United States, or Action Fraud in the United Kingdom.
        </p>
      </div>
    </footer>
  );
}

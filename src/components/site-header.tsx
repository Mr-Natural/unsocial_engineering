import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-line bg-ink">
      {process.env.VERCEL_ENV === "preview" && <p className="bg-safe px-4 py-2 text-center text-xs text-ink">Publishing rehearsal · Test content only</p>}
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-6 px-5 py-7 sm:px-10">
        <Link href="/" className="flex items-center gap-3" aria-label="UnSocial Engineering home">
          <span className="relative border border-line px-2 text-3xl leading-10" aria-hidden="true">U<span className="absolute -right-2 -top-2 text-xl text-safe">↗</span></span>
          <span className="text-sm leading-tight">UnSocial<br /><span className="text-safe">Engineering</span></span>
        </Link>
        <nav aria-label="Main navigation" className="flex flex-wrap items-center gap-x-6 gap-y-4 text-sm">
          <Link href="/scams" className="hover:text-safe">Read</Link>
          <Link href="/casebook/2026" className="hover:text-safe">2026 Casebook</Link>
          <Link href="/sources" className="hover:text-safe">Our sources</Link>
          <Link href="/about" className="hover:text-safe">Our approach</Link>
          <Link href="/resources" className="border border-line px-4 py-3 hover:border-safe">Help &amp; resources &nbsp; ↗</Link>
        </nav>
      </div>
    </header>
  );
}

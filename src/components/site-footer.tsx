import Link from "next/link";
import { SITE_NAME, SITE_TAGLINE } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="mt-12 border-t border-line">
      <div className="mx-auto flex max-w-7xl flex-col gap-7 px-5 py-10 sm:flex-row sm:justify-between sm:px-10">
        <div><p className="font-semibold">{SITE_NAME}</p><p className="mt-2 text-sm text-muted">{SITE_TAGLINE}</p><p className="mt-4 text-xs text-muted">For readers in Australia and around the world. General education; reporting and recovery options vary by location.</p></div>
        <nav aria-label="Footer navigation" className="flex flex-wrap gap-5 text-sm"><Link href="/about">Our approach</Link><Link href="/sources">Our sources</Link><Link href="/check">Find help</Link></nav>
      </div>
    </footer>
  );
}

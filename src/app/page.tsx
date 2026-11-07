import Link from "next/link";
import { ArticleCard } from "@/components/article-card";
import { getLatestPublished } from "@/lib/queries";
import { SITE_TAGLINE } from "@/lib/site";

export const dynamic = "force-dynamic";
const pressures = [
  ["Urgency", "No time to think."], ["Authority", "Someone who seems to know."],
  ["Fear", "Something you cannot lose."], ["Reciprocity", "A favour with a hidden price."],
  ["Trust", "A familiar face. A false story."],
];

export default async function HomePage() {
  const articles = await getLatestPublished(6);
  return (
    <div className="mx-auto max-w-7xl px-5 sm:px-10">
      <section className="grid gap-12 py-16 lg:grid-cols-[1.2fr_1fr] lg:gap-20 lg:py-20" aria-labelledby="hero-title">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[.18em] text-safe">● &nbsp; The human side of deception</p>
          <h1 id="hero-title" className="mt-8 text-5xl leading-[1.04] tracking-[-.05em] sm:text-6xl xl:text-7xl">
            See the pressure.<br /><span className="editorial-serif text-safe">Break the spell.</span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-muted">A convincing scam starts with something human. Trust. Fear. Hope. We explain how manipulation works, and how to take back the decision.</p>
          <div className="mt-8 flex flex-wrap items-center gap-6">
            <Link href="/categories/psychology-of-deception" className="bg-safe px-6 py-4 text-sm font-semibold text-ink hover:bg-safe-strong">Start with the psychology &nbsp; ↗</Link>
            <Link href="/about" className="text-sm underline underline-offset-8">Why this publication</Link>
          </div>
          <p className="mt-10 text-xs text-muted">{SITE_TAGLINE}</p>
        </div>
        <aside className="self-start border border-line bg-surface" aria-labelledby="pressure-title">
          <h2 id="pressure-title" className="flex justify-between border-b border-line px-6 py-5 text-xs font-semibold uppercase tracking-wider text-safe"><span>The pressure playbook</span><span aria-hidden="true">01—05</span></h2>
          <ol>{pressures.map(([title, text], i) => (
            <li key={title} className="flex gap-6 border-b border-line px-6 py-5">
              <span className="pt-2 font-mono text-xs text-muted" aria-hidden="true">0{i + 1}</span>
              <div><h3 className="text-xl tracking-tight">{title}</h3><p className="mt-1 text-xs text-muted">{text}</p></div>
              <span className="ml-auto self-center text-safe" aria-hidden="true">↘</span>
            </li>
          ))}</ol>
          <p className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-warn">Pause. Check through another channel.</p>
        </aside>
      </section>
      <section className="border-t border-line py-12" aria-labelledby="latest-title">
        <div className="mb-7 flex items-end justify-between gap-4">
          <div><p className="text-xs uppercase tracking-wider text-safe">Education &amp; threat briefings</p><h2 id="latest-title" className="mt-2 text-3xl tracking-tight">The latest stories</h2></div>
          <Link href="/scams" className="text-sm underline underline-offset-4">Read all ↗</Link>
        </div>
        {articles.length ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{articles.map(article => <ArticleCard key={article.id} article={article} />)}</div> : <p className="border border-line p-8 text-muted">Our first reviewed stories will appear here when they are published.</p>}
      </section>
    </div>
  );
}

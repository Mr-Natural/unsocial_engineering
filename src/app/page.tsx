import { AlertBanner } from "@/components/alert-banner";
import { ArticleCard } from "@/components/article-card";
import { HeroSearch } from "@/components/hero-search";
import { TrendingSidebar } from "@/components/trending-sidebar";
import { hoursSince } from "@/lib/format";
import { getBreakingArticle, getLatestPublished, getTrendingCategories } from "@/lib/queries";

export const revalidate = 300; // ISR: refresh every 5 minutes

export default async function HomePage() {
  const [breaking, latest, trending] = await Promise.all([
    getBreakingArticle(),
    getLatestPublished(6),
    getTrendingCategories(7, 6),
  ]);

  const showAlert = breaking && hoursSince(breaking.published_at) <= 72;

  return (
    <div className="mx-auto max-w-6xl px-4">
      {/* Hero */}
      <section className="py-14 sm:py-20">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          Don&apos;t Get <span className="text-warn">Played</span>
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-muted">
          Scams evolve fast. We break down how the latest ones work, in plain
          language, so you can spot them before they cost you.
        </p>
        <HeroSearch />
      </section>

      {showAlert && (
        <div className="mb-10">
          <AlertBanner article={breaking} />
        </div>
      )}

      {/* Latest + trending */}
      <div className="grid grid-cols-1 gap-8 pb-8 lg:grid-cols-[1fr_18rem]">
        <section>
          <h2 className="mb-5 text-xl font-semibold">Latest scams</h2>
          {latest.length === 0 ? (
            <div className="rounded-xl border border-dashed border-line bg-surface p-10 text-center text-muted">
              No published scams yet. New stories appear here as they clear review.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              {latest.map((a) => (
                <ArticleCard key={a.id} article={a} />
              ))}
            </div>
          )}
        </section>

        <TrendingSidebar categories={trending} />
      </div>
    </div>
  );
}

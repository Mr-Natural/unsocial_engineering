import type { Metadata } from "next";

import { ArticleCard } from "@/components/article-card";
import { CategoryFilter } from "@/components/category-filter";
import { Pagination } from "@/components/pagination";
import { browseArticles, getCategories } from "@/lib/queries";

export const metadata: Metadata = {
  title: "Browse scams",
  description: "Search and filter scam awareness articles by category.",
};

const PAGE_SIZE = 9;

export default async function BrowsePage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string; page?: string }>;
}) {
  const sp = await searchParams;
  const page = Number(sp.page) || 1;

  const [{ articles, total }, categories] = await Promise.all([
    browseArticles({ q: sp.q, categorySlug: sp.category, page, pageSize: PAGE_SIZE }),
    getCategories(),
  ]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold tracking-tight">Browse scams</h1>

      {/* Search */}
      <form action="/scams" method="get" className="mt-6 flex max-w-lg gap-2">
        {sp.category && <input type="hidden" name="category" value={sp.category} />}
        <input
          type="search"
          name="q"
          defaultValue={sp.q ?? ""}
          placeholder="Search scams..."
          aria-label="Search scams"
          className="flex-1 rounded-lg border border-line bg-surface px-4 py-2.5 text-fg placeholder:text-muted focus:border-safe focus:outline-none focus:ring-1 focus:ring-safe"
        />
        <button type="submit" className="rounded-lg bg-surface-2 px-4 py-2.5 text-sm font-medium hover:bg-line">
          Search
        </button>
      </form>

      {/* Filter */}
      <div className="mt-6">
        <CategoryFilter categories={categories} activeSlug={sp.category} />
      </div>

      {/* Results */}
      <p className="mt-8 text-sm text-muted">
        {total} {total === 1 ? "result" : "results"}
        {sp.q ? ` for "${sp.q}"` : ""}
      </p>

      {articles.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-line bg-surface p-10 text-center text-muted">
          No scams match your search. Try a different term or category.
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}

      <Pagination
        page={page}
        total={total}
        pageSize={PAGE_SIZE}
        params={{ q: sp.q, category: sp.category }}
      />
    </div>
  );
}

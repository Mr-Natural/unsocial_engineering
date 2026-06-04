import Link from "next/link";

import { categoryAccent } from "@/lib/categories";
import type { TrendingCategory } from "@/lib/queries";

export function TrendingSidebar({ categories }: { categories: TrendingCategory[] }) {
  return (
    <aside className="rounded-xl border border-line bg-surface p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
        Trending this week
      </h2>
      {categories.length === 0 ? (
        <p className="mt-3 text-sm text-muted">No activity yet. Check back soon.</p>
      ) : (
        <ul className="mt-4 space-y-1">
          {categories.map((c) => (
            <li key={c.slug}>
              <Link
                href={`/categories/${c.slug}`}
                className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-surface-2"
              >
                <span className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${categoryAccent(c.slug).dot}`} aria-hidden />
                  {c.name}
                </span>
                <span className="text-xs text-muted">{c.count}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}

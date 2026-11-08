import Link from "next/link";

import { CategoryBadge } from "@/components/category-badge";
import { casebookYear } from "@/lib/casebook";
import { formatDate } from "@/lib/format";
import type { ArticleWithCategory } from "@/lib/queries";

export function ArticleCard({ article }: { article: ArticleWithCategory }) {
  const year = casebookYear(article.slug);
  return (
    <article className="group relative flex flex-col border border-line bg-surface p-6 transition-colors hover:border-safe hover:bg-surface-2">
      {/* z-10 keeps the category link clickable above the stretched title link */}
      <div className="relative z-10 mb-3 flex items-center justify-between gap-2">
        <CategoryBadge category={article.category} />
      </div>

      {article.evidence_label && <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-safe">{article.evidence_label}</p>}
      {year !== null && <p className="mb-3 text-xs text-muted">Retrospective · {year} Casebook</p>}
      <h3 className="text-lg font-semibold leading-snug">
        <Link href={`/scams/${article.slug}`} className="after:absolute after:inset-0">
          {article.title}
        </Link>
      </h3>

      {article.summary && (
        <p className="mt-2 line-clamp-3 text-sm text-muted">{article.summary}</p>
      )}

      <p className="mt-4 text-xs text-muted">Published {formatDate(article.published_at ?? article.created_at)}</p>
      {article.region && <p className="mt-1 text-xs text-muted">{article.region}</p>}
    </article>
  );
}

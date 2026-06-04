import Link from "next/link";

import { CategoryBadge } from "@/components/category-badge";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { formatDate } from "@/lib/format";
import type { ArticleWithCategory } from "@/lib/queries";

export function ArticleCard({ article }: { article: ArticleWithCategory }) {
  return (
    <article className="group relative flex flex-col rounded-xl border border-line bg-surface p-5 transition-colors hover:border-slate-600 hover:bg-surface-2">
      {/* z-10 keeps the category link clickable above the stretched title link */}
      <div className="relative z-10 mb-3 flex items-center justify-between gap-2">
        <CategoryBadge category={article.category} />
        <ConfidenceIndicator value={article.ai_confidence} />
      </div>

      <h3 className="text-lg font-semibold leading-snug">
        <Link href={`/scams/${article.slug}`} className="after:absolute after:inset-0">
          {article.title}
        </Link>
      </h3>

      {article.summary && (
        <p className="mt-2 line-clamp-3 text-sm text-muted">{article.summary}</p>
      )}

      <p className="mt-4 text-xs text-muted">{formatDate(article.published_at ?? article.created_at)}</p>
    </article>
  );
}

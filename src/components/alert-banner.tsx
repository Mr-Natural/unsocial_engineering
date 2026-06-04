import Link from "next/link";

import type { ArticleWithCategory } from "@/lib/queries";

// Prominent banner for a breaking/urgent scam (the most recent published story).
export function AlertBanner({ article }: { article: ArticleWithCategory }) {
  return (
    <Link
      href={`/scams/${article.slug}`}
      className="group flex items-center gap-3 rounded-lg border border-warn/40 bg-warn/10 px-4 py-3 transition-colors hover:bg-warn/15"
    >
      <span className="flex h-7 shrink-0 items-center rounded bg-warn px-2 text-xs font-bold uppercase tracking-wide text-ink">
        Alert
      </span>
      <span className="min-w-0 flex-1 truncate text-sm font-medium text-fg">
        {article.title}
      </span>
      <span className="shrink-0 text-sm text-warn group-hover:translate-x-0.5">→</span>
    </Link>
  );
}

import Link from "next/link";

import type { Category } from "@/lib/types";

export function CategoryFilter({
  categories,
  activeSlug,
}: {
  categories: Category[];
  activeSlug?: string;
}) {
  const base = "rounded-full px-3 py-1.5 text-sm ring-1 ring-inset transition-colors";
  const active = "bg-safe/15 text-safe ring-safe/40";
  const idle = "bg-surface text-muted ring-line hover:text-fg hover:ring-slate-600";

  return (
    <div className="flex flex-wrap gap-2">
      <Link href="/scams" className={`${base} ${!activeSlug ? active : idle}`}>
        All
      </Link>
      {categories.map((c) => (
        <Link
          key={c.slug}
          href={`/scams?category=${c.slug}`}
          className={`${base} ${activeSlug === c.slug ? active : idle}`}
        >
          {c.name}
        </Link>
      ))}
    </div>
  );
}

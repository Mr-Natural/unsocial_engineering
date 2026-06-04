import Link from "next/link";

import { categoryAccent } from "@/lib/categories";

export function CategoryBadge({
  category,
}: {
  category: { name: string; slug: string } | null;
}) {
  if (!category) return null;
  const accent = categoryAccent(category.slug);
  return (
    <Link
      href={`/categories/${category.slug}`}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${accent.badge}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${accent.dot}`} aria-hidden />
      {category.name}
    </Link>
  );
}

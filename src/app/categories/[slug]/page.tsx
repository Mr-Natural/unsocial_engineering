import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ArticleCard } from "@/components/article-card";
import { CategoryFilter } from "@/components/category-filter";
import { browseArticles, getCategories, getCategoryBySlug } from "@/lib/queries";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const category = await getCategoryBySlug(slug);
  if (!category) return { title: "Category not found" };
  return {
    title: category.name,
    description: category.description ?? `Latest ${category.name} scams and how to spot them.`,
    alternates: { canonical: `/categories/${slug}` },
  };
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [category, categories] = await Promise.all([getCategoryBySlug(slug), getCategories()]);
  if (!category) notFound();

  const { articles } = await browseArticles({ categorySlug: slug, pageSize: 24 });

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold tracking-tight">{category.name}</h1>
      {category.description && (
        <p className="mt-3 max-w-2xl text-muted">{category.description}</p>
      )}

      <div className="mt-6">
        <CategoryFilter categories={categories} activeSlug={slug} />
      </div>

      {articles.length === 0 ? (
        <div className="mt-8 rounded-xl border border-dashed border-line bg-surface p-10 text-center text-muted">
          No published {category.name.toLowerCase()} scams yet.
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}

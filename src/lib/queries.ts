import { supabasePublic } from "@/lib/supabase/public";
import type { Article, Category } from "@/lib/types";

export type ArticleWithCategory = Article & {
  category: Pick<Category, "name" | "slug"> | null;
};

const CARD_FIELDS =
  "id, title, slug, summary, ai_confidence, status, published_at, revised_at, created_at, source_urls, evidence_label, editorial_stream, region, research_as_of, author_credit, category_id, category:categories(name, slug)";

/** Latest published articles for the homepage grid. */
export async function getLatestPublished(limit = 6): Promise<ArticleWithCategory[]> {
  const { data, error } = await supabasePublic
    .from("articles")
    .select(CARD_FIELDS)
    .eq("status", "published")
    .order("published_at", { ascending: false })
    .limit(limit);
  if (error) throw new Error("Published content is temporarily unavailable");
  return (data as unknown as ArticleWithCategory[]) ?? [];
}

/** The most recent published article, if it is recent enough to feature as "breaking". */
export async function getBreakingArticle(): Promise<ArticleWithCategory | null> {
  const { data, error } = await supabasePublic
    .from("articles")
    .select(CARD_FIELDS)
    .eq("status", "published")
    .order("published_at", { ascending: false })
    .limit(1);
  if (error) throw new Error("Published content is temporarily unavailable");
  return ((data as unknown as ArticleWithCategory[]) ?? [])[0] ?? null;
}

export type TrendingCategory = { name: string; slug: string; count: number };

/** Categories ranked by published-article volume over the last `days`. */
export async function getTrendingCategories(days = 7, limit = 6): Promise<TrendingCategory[]> {
  const since = new Date(Date.now() - days * 864e5).toISOString();
  const { data, error } = await supabasePublic
    .from("articles")
    .select("category:categories(name, slug)")
    .eq("status", "published")
    .gte("published_at", since);

  if (error) throw new Error("Published content is temporarily unavailable");
  const counts = new Map<string, TrendingCategory>();
  for (const row of (data as unknown as ArticleWithCategory[]) ?? []) {
    const c = row.category;
    if (!c) continue;
    const entry = counts.get(c.slug) ?? { name: c.name, slug: c.slug, count: 0 };
    entry.count += 1;
    counts.set(c.slug, entry);
  }
  return [...counts.values()].sort((a, b) => b.count - a.count).slice(0, limit);
}

export type BrowseResult = { articles: ArticleWithCategory[]; total: number };

/** Filterable, searchable, paginated published articles for the browse page. */
export async function browseArticles(opts: {
  q?: string;
  categorySlug?: string;
  page?: number;
  pageSize?: number;
  casebookYear?: number;
}): Promise<BrowseResult> {
  const page = Math.max(1, opts.page ?? 1);
  const pageSize = opts.pageSize ?? 9;
  const from = (page - 1) * pageSize;

  let query = supabasePublic
    .from("articles")
    .select(CARD_FIELDS, { count: "exact" })
    .eq("status", "published");

  if (opts.categorySlug) {
    const category = await getCategoryBySlug(opts.categorySlug);
    if (!category) return { articles: [], total: 0 };
    query = query.eq("category_id", category.id);
  }
  if (opts.q) {
    const term = opts.q.replace(/[,()*%]/g, " ").trim();
    if (term) query = query.or(`title.ilike.%${term}%,summary.ilike.%${term}%`);
  }
  if (opts.casebookYear !== undefined) {
    if (!Number.isInteger(opts.casebookYear) || opts.casebookYear < 2000 || opts.casebookYear > 2099) {
      return { articles: [], total: 0 };
    }
    query = query.like("slug", `${opts.casebookYear}-%`);
  }

  const { data, count, error } = await query
    .order("published_at", { ascending: false })
    .range(from, from + pageSize - 1);

  if (error) throw new Error("Published content is temporarily unavailable");
  return { articles: (data as unknown as ArticleWithCategory[]) ?? [], total: count ?? 0 };
}

export async function getArticleBySlug(slug: string): Promise<ArticleWithCategory | null> {
  const { data, error } = await supabasePublic
    .from("articles")
    .select(`${CARD_FIELDS}, body_html`)
    .eq("status", "published")
    .eq("slug", slug)
    .limit(1);
  if (error) throw new Error("Published content is temporarily unavailable");
  return ((data as unknown as ArticleWithCategory[]) ?? [])[0] ?? null;
}

/** Published slugs for generateStaticParams. */
export async function getPublishedSlugs(): Promise<string[]> {
  const { data, error } = await supabasePublic
    .from("articles")
    .select("slug")
    .eq("status", "published");
  if (error) throw new Error("Published content is temporarily unavailable");
  return ((data as { slug: string }[] | null) ?? []).map((r) => r.slug);
}

export async function getRelatedArticles(
  article: ArticleWithCategory,
  limit = 4,
): Promise<ArticleWithCategory[]> {
  if (!article.category_id) return [];
  const { data, error } = await supabasePublic
    .from("articles")
    .select(CARD_FIELDS)
    .eq("status", "published")
    .eq("category_id", article.category_id)
    .neq("id", article.id)
    .order("published_at", { ascending: false })
    .limit(limit);
  if (error) throw new Error("Published content is temporarily unavailable");
  return (data as unknown as ArticleWithCategory[]) ?? [];
}

export async function getCategories(): Promise<Category[]> {
  const { data, error } = await supabasePublic.from("categories").select("*").order("name");
  if (error) throw new Error("Published content is temporarily unavailable");
  return (data as Category[]) ?? [];
}

export async function getCategoryBySlug(slug: string): Promise<Category | null> {
  const { data, error } = await supabasePublic
    .from("categories")
    .select("*")
    .eq("slug", slug)
    .limit(1);
  if (error) throw new Error("Published content is temporarily unavailable");
  return ((data as Category[]) ?? [])[0] ?? null;
}

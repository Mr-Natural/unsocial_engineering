import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ArticleCard } from "@/components/article-card";
import { CategoryBadge } from "@/components/category-badge";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { ReportCTA } from "@/components/report-cta";
import { ShareButtons } from "@/components/share-buttons";
import { formatDate, isoDate } from "@/lib/format";
import { getArticleBySlug, getPublishedSlugs, getRelatedArticles } from "@/lib/queries";
import { SITE_NAME, SITE_URL } from "@/lib/site";

export const revalidate = 300;

export async function generateStaticParams() {
  const slugs = await getPublishedSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);
  if (!article) return { title: "Scam not found" };
  return {
    title: article.title,
    description: article.summary ?? undefined,
    alternates: { canonical: `/scams/${slug}` },
    openGraph: {
      type: "article",
      title: article.title,
      description: article.summary ?? undefined,
      url: `${SITE_URL}/scams/${slug}`,
      publishedTime: article.published_at ?? undefined,
    },
  };
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);
  if (!article) notFound();

  const related = await getRelatedArticles(article);
  const url = `${SITE_URL}/scams/${slug}`;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.summary ?? undefined,
    datePublished: article.published_at ?? undefined,
    dateModified: article.revised_at ?? article.published_at ?? article.created_at,
    author: { "@type": "Organization", name: SITE_NAME },
    publisher: { "@type": "Organization", name: SITE_NAME },
    mainEntityOfPage: url,
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
      />

      <Link href="/scams" className="text-sm text-muted hover:text-fg">
        ← Back to all scams
      </Link>

      <div className="mt-4 grid grid-cols-1 gap-10 lg:grid-cols-[1fr_18rem]">
        <article>
          <div className="flex flex-wrap items-center gap-3">
            <CategoryBadge category={article.category} />
            <ConfidenceIndicator value={article.ai_confidence} />
            <time
              dateTime={isoDate(article.published_at ?? article.created_at)}
              className="text-sm text-muted"
            >
              {formatDate(article.published_at ?? article.created_at)}
            </time>
            {article.revised_at && (
              <time dateTime={isoDate(article.revised_at)} className="text-sm text-muted">
                Updated {formatDate(article.revised_at)}
              </time>
            )}
          </div>

          <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
            {article.title}
          </h1>

          {article.summary && (
            <p className="mt-4 border-l-2 border-warn pl-4 text-lg text-muted">
              {article.summary}
            </p>
          )}

          <div
            className="article-body mt-8"
            dangerouslySetInnerHTML={{ __html: article.body_html ?? "" }}
          />

          {/* Sources */}
          {article.source_urls.length > 0 && (
            <section className="mt-10 border-t border-line pt-6">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Sources</h2>
              <ul className="mt-3 space-y-2">
                {article.source_urls.map((src) => (
                  <li key={src} className="break-words text-sm">
                    <a
                      href={src}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-safe underline underline-offset-2 hover:text-safe-strong"
                    >
                      {hostname(src)}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div className="mt-8 border-t border-line pt-6">
            <ShareButtons url={url} title={article.title} />
          </div>
        </article>

        {/* Sidebar */}
        <aside className="space-y-6">
          <ReportCTA />
          {related.length > 0 && (
            <section>
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
                Related scams
              </h2>
              <div className="space-y-4">
                {related.map((a) => (
                  <ArticleCard key={a.id} article={a} />
                ))}
              </div>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

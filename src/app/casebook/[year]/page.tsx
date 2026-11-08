import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArticleCard } from "@/components/article-card";
import { Pagination } from "@/components/pagination";
import { CASEBOOK_YEAR } from "@/lib/casebook";
import { browseArticles } from "@/lib/queries";

export const dynamic = "force-dynamic";
const PAGE_SIZE = 9;
type Props = {
  params: Promise<{ year: string }>;
  searchParams: Promise<{ page?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { year } = await params;
  if (year !== String(CASEBOOK_YEAR)) return { title: "Casebook not found" };
  return {
    title: `${year} Scam Casebook`,
    description: "Sourced retrospectives on scams documented around the world, with clear incident, warning and publication dates.",
    alternates: { canonical: `/casebook/${year}` },
  };
}

export default async function CasebookPage({ params, searchParams }: Props) {
  const [{ year }, sp] = await Promise.all([params, searchParams]);
  if (year !== String(CASEBOOK_YEAR)) notFound();
  const requestedPage = Number(sp.page);
  const page = Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  const { articles, total } = await browseArticles({ casebookYear: CASEBOOK_YEAR, page, pageSize: PAGE_SIZE });

  return (
    <div className="mx-auto max-w-6xl px-5 py-14 sm:px-10">
      <p className="text-xs uppercase tracking-wider text-safe">The international casebook</p>
      <h1 className="mt-4 text-4xl tracking-tight">{year} Scam Casebook</h1>
      <p className="mt-6 max-w-3xl text-lg text-muted">Scams documented around the world, revisited for the lessons that still matter. Follow the evidence, understand the pressure and find a practical point to pause.</p>
      <div className="mt-7 max-w-3xl border-l-2 border-safe pl-5 text-sm text-muted">
        <p>Each retrospective identifies the date of the incident, warning or enforcement operation. An announcement date does not establish when every underlying scam occurred.</p>
        <p className="mt-3">The publication date records when the story first appeared here. These are selected accounts, not a complete record or ranking of the year’s scams.</p>
      </div>
      <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-7">
        <h2 className="text-2xl">Published retrospectives</h2>
        <p className="text-sm text-muted">{total} {total === 1 ? "story" : "stories"} · Latest publication first</p>
      </div>
      {articles.length > 0 ? (
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map(article => <ArticleCard key={article.id} article={article} />)}
        </div>
      ) : (
        <div className="mt-6 border border-line bg-surface p-8">
          <p className="text-muted">{total === 0 ? "Reviewed retrospectives will appear here as they are published." : "There are no stories on this page."}</p>
          <Link href={total === 0 ? "/scams" : `/casebook/${year}`} className="mt-4 inline-block text-safe underline underline-offset-4">{total === 0 ? "Explore the current stories" : "Return to the first page"}</Link>
        </div>
      )}
      <Pagination page={page} total={total} pageSize={PAGE_SIZE} params={{}} basePath={`/casebook/${year}`} />
      <aside className="mt-12 border-t border-line pt-6">
        <h2 className="text-lg">Looking for help with something happening now?</h2>
        <Link href="/resources" className="mt-3 inline-block text-safe underline underline-offset-4">Find reporting and support for your location</Link>
      </aside>
    </div>
  );
}

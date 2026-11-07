import type { Metadata } from "next";

import { ScamChecker } from "@/components/scam-checker";
import { getLatestPublished } from "@/lib/queries";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Is this a scam?",
  description:
    "Answer a few quick questions about what you received and get an instant, private risk assessment. No pasting, no data stored.",
};

export default async function CheckPage() {
  // Read-only: a pool of published articles so the result can link to relevant
  // reads. The checker itself runs entirely client-side and stores nothing.
  const pool = await getLatestPublished(60);
  const articles = pool.map((a) => ({
    slug: a.slug,
    title: a.title,
    categorySlug: a.category?.slug ?? null,
  }));

  return <ScamChecker articles={articles} />;
}

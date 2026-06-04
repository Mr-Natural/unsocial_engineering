import { NextResponse } from "next/server";

import { createAdminClient } from "@/lib/supabase/admin";

// Pipeline health snapshot. Reads via the service-role client (leads/social_posts
// aren't public under RLS), so this must stay server-side.
//
// NOTE: unauthenticated. If PIPELINE_STATUS_TOKEN is set, require it as a Bearer
// token — set it in production so the snapshot (incl. flagged editor notes) isn't
// world-readable.
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const token = process.env.PIPELINE_STATUS_TOKEN;
  if (token) {
    const auth = request.headers.get("authorization");
    if (auth !== `Bearer ${token}`) {
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }
  }

  const db = createAdminClient();
  const todayStart = new Date();
  todayStart.setUTCHours(0, 0, 0, 0);

  const [leadsToday, drafted, published, flaggedRes, lastLeadRes] = await Promise.all([
    db.from("leads").select("*", { count: "exact", head: true }).gte("scraped_at", todayStart.toISOString()),
    db.from("articles").select("*", { count: "exact", head: true }).eq("status", "draft"),
    db.from("articles").select("*", { count: "exact", head: true }).eq("status", "published"),
    db
      .from("articles")
      .select("id, title, slug, ai_confidence, editor_notes")
      .eq("status", "flagged")
      .order("created_at", { ascending: false }),
    db.from("leads").select("scraped_at").order("scraped_at", { ascending: false }).limit(1),
  ]);

  const lastLead = (lastLeadRes.data as { scraped_at: string }[] | null) ?? [];

  return NextResponse.json({
    last_run: lastLead[0]?.scraped_at ?? null,
    counts: {
      leads_today: leadsToday.count ?? 0,
      articles_drafted: drafted.count ?? 0,
      articles_published: published.count ?? 0,
      flagged_for_review: flaggedRes.data?.length ?? 0,
    },
    flagged: flaggedRes.data ?? [],
  });
}

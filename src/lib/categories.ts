// Per-category accent colours for badges. Falls back to a neutral slate.
// Keys are category slugs (see supabase seed migration).

type Accent = { badge: string; dot: string };

const ACCENTS: Record<string, Accent> = {
  phishing: { badge: "bg-amber-500/15 text-amber-300 ring-amber-500/30", dot: "bg-amber-400" },
  "romance-scam": { badge: "bg-rose-500/15 text-rose-300 ring-rose-500/30", dot: "bg-rose-400" },
  "crypto-fraud": { badge: "bg-orange-500/15 text-orange-300 ring-orange-500/30", dot: "bg-orange-400" },
  "investment-scam": { badge: "bg-yellow-500/15 text-yellow-300 ring-yellow-500/30", dot: "bg-yellow-400" },
  impersonation: { badge: "bg-fuchsia-500/15 text-fuchsia-300 ring-fuchsia-500/30", dot: "bg-fuchsia-400" },
  "tech-support": { badge: "bg-sky-500/15 text-sky-300 ring-sky-500/30", dot: "bg-sky-400" },
  "marketplace-fraud": { badge: "bg-teal-500/15 text-teal-300 ring-teal-500/30", dot: "bg-teal-400" },
  "employment-scam": { badge: "bg-indigo-500/15 text-indigo-300 ring-indigo-500/30", dot: "bg-indigo-400" },
  "government-impersonation": { badge: "bg-red-500/15 text-red-300 ring-red-500/30", dot: "bg-red-400" },
  "subscription-trap": { badge: "bg-violet-500/15 text-violet-300 ring-violet-500/30", dot: "bg-violet-400" },
};

const NEUTRAL: Accent = { badge: "bg-slate-500/15 text-slate-300 ring-slate-500/30", dot: "bg-slate-400" };

export function categoryAccent(slug: string | null | undefined): Accent {
  return (slug && ACCENTS[slug]) || NEUTRAL;
}

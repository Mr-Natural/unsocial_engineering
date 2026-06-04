import { createClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/types";

// Cookieless, anon-key client for public reads (published articles + categories).
// Because it doesn't touch cookies, pages using it can be statically rendered and
// revalidated (ISR) rather than forced dynamic. RLS still applies.
export const supabasePublic = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  { auth: { persistSession: false, autoRefreshToken: false } },
);

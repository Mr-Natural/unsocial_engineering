import { createClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/types";

// Cookieless, anon-key client for public reads (published articles + categories).
// Read current published state so withdrawals do not survive in Next's data cache.
export const supabasePublic = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }) },
  },
);

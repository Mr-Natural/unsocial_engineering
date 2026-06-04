import { createBrowserClient } from "@supabase/ssr";

import type { Database } from "@/lib/types";

// Browser-side Supabase client. Uses the public anon key and is bound by RLS,
// so it can only ever read published articles and categories.
export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}

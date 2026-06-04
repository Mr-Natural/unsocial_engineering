import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

import type { Database } from "@/lib/types";

// Server-side Supabase client for Server Components, Route Handlers, and
// Server Actions. Uses the anon key and is bound by RLS. Reads/writes cookies
// so that any future auth session is carried correctly.
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // `setAll` was called from a Server Component. Safe to ignore when
            // middleware is responsible for refreshing sessions.
          }
        },
      },
    },
  );
}

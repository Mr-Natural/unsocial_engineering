import Link from "next/link";

export function Pagination({
  page,
  total,
  pageSize,
  params,
}: {
  page: number;
  total: number;
  pageSize: number;
  params: Record<string, string | undefined>;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  const href = (p: number) => {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) sp.set(k, v);
    sp.set("page", String(p));
    return `/scams?${sp.toString()}`;
  };

  const link = "rounded-lg border border-line bg-surface px-4 py-2 text-sm font-medium hover:border-slate-600";
  const disabled = "pointer-events-none opacity-40";

  return (
    <nav className="mt-8 flex items-center justify-between" aria-label="Pagination">
      <Link href={href(page - 1)} className={`${link} ${page <= 1 ? disabled : ""}`} aria-disabled={page <= 1}>
        ← Previous
      </Link>
      <span className="text-sm text-muted">
        Page {page} of {totalPages}
      </span>
      <Link href={href(page + 1)} className={`${link} ${page >= totalPages ? disabled : ""}`} aria-disabled={page >= totalPages}>
        Next →
      </Link>
    </nav>
  );
}

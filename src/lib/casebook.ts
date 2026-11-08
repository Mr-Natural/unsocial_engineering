/** A year-prefixed slug reserves an immutable, reviewed Casebook membership.
 * Dates of incidents/warnings/operations belong in the approved article body.
 * Never derive an incident date from published_at or research_as_of.
 */
export function casebookYear(slug: string): number | null {
  const match = /^(20\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$/.exec(slug);
  return match ? Number(match[1]) : null;
}

export const CASEBOOK_YEAR = 2026;

// Small presentation helpers shared across components.

export function formatDate(value: string | null): string {
  if (!value) return "";
  return new Date(value).toLocaleDateString("en-AU", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function isoDate(value: string | null): string {
  return value ? new Date(value).toISOString() : "";
}

/** Hours since a timestamp, or Infinity if missing. */
export function hoursSince(value: string | null): number {
  if (!value) return Infinity;
  return (Date.now() - new Date(value).getTime()) / 36e5;
}

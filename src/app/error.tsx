"use client";

export default function ContentError({ reset }: { reset: () => void }) {
  return (
    <section className="mx-auto max-w-3xl px-5 py-16">
      <h1 className="text-3xl">Stories are temporarily unavailable</h1>
      <p className="mt-4 text-muted">We could not load the current published content. Please try again shortly.</p>
      <button type="button" onClick={reset} className="mt-6 bg-safe px-5 py-3 text-ink">Try again</button>
    </section>
  );
}

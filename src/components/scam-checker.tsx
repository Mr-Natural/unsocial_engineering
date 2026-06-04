"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import {
  AUTHORITIES,
  SCAM_TYPES,
  assessRisk,
  type RiskLevel,
  type ScamType,
} from "@/lib/checker";

type ArticleRef = { slug: string; title: string; categorySlug: string | null };

const RISK_STYLES: Record<RiskLevel, { ring: string; text: string; bg: string; label: string }> = {
  low: { ring: "ring-safe/40", text: "text-safe-strong", bg: "bg-safe/10", label: "Low risk" },
  medium: { ring: "ring-warn/40", text: "text-warn", bg: "bg-warn/10", label: "Medium risk" },
  high: { ring: "ring-red-500/50", text: "text-red-400", bg: "bg-red-500/10", label: "High risk" },
};

export function ScamChecker({ articles }: { articles: ArticleRef[] }) {
  const [step, setStep] = useState<"type" | "flags" | "result">("type");
  const [type, setType] = useState<ScamType | null>(null);
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const checkedFlags = useMemo(
    () => (type ? type.flags.filter((f) => checked[f.id]) : []),
    [type, checked],
  );
  const risk = assessRisk(checkedFlags.length);
  const related = useMemo(
    () => (type?.categorySlug ? articles.filter((a) => a.categorySlug === type.categorySlug).slice(0, 3) : []),
    [type, articles],
  );

  function chooseType(t: ScamType) {
    setType(t);
    setChecked({});
    setStep("flags");
  }
  function reset() {
    setType(null);
    setChecked({});
    setStep("type");
  }

  // STEP 1 — type
  if (step === "type") {
    return (
      <Shell>
        <p className="text-sm font-medium text-safe">Let&apos;s figure this out together.</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">What did you receive?</h1>
        <p className="mt-2 text-muted">Pick the closest match. No need to paste anything.</p>
        <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {SCAM_TYPES.map((t) => (
            <button
              key={t.id}
              onClick={() => chooseType(t)}
              className="rounded-xl border border-line bg-surface px-5 py-5 text-left text-lg font-medium transition-colors hover:border-safe hover:bg-surface-2"
            >
              {t.label}
            </button>
          ))}
        </div>
      </Shell>
    );
  }

  // STEP 2 — flags
  if (step === "flags" && type) {
    return (
      <Shell>
        <button onClick={reset} className="text-sm text-muted hover:text-fg">← Start over</button>
        <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{type.label}</h1>
        <p className="mt-2 text-muted">Tick anything that applies. Be honest, this is just for you.</p>

        <div className="mt-6 space-y-3">
          {type.flags.map((f) => {
            const on = !!checked[f.id];
            return (
              <button
                key={f.id}
                role="checkbox"
                aria-checked={on}
                onClick={() => setChecked((c) => ({ ...c, [f.id]: !c[f.id] }))}
                className={`flex w-full items-start gap-3 rounded-xl border px-4 py-4 text-left transition-colors ${
                  on ? "border-safe bg-safe/10" : "border-line bg-surface hover:border-slate-600"
                }`}
              >
                <span
                  className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border ${
                    on ? "border-safe bg-safe text-ink" : "border-slate-500"
                  }`}
                  aria-hidden
                >
                  {on ? "✓" : ""}
                </span>
                <span className="text-base">{f.q}</span>
              </button>
            );
          })}
        </div>

        <button
          onClick={() => setStep("result")}
          className="mt-8 w-full rounded-lg bg-warn px-5 py-3.5 text-center font-semibold text-ink transition-colors hover:bg-warn-strong sm:w-auto sm:px-8"
        >
          See the result
        </button>
      </Shell>
    );
  }

  // STEP 3 — result
  if (step === "result" && type) {
    const styles = RISK_STYLES[risk.level];
    return (
      <Shell>
        <button onClick={() => setStep("flags")} className="text-sm text-muted hover:text-fg">← Back to questions</button>

        <div className={`mt-4 rounded-2xl border ring-1 ring-inset ${styles.bg} ${styles.ring} border-transparent p-6`}>
          <p className={`text-sm font-semibold uppercase tracking-wide ${styles.text}`}>{styles.label}</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">{risk.headline}</h1>
          <p className="mt-2 text-muted">{risk.blurb}</p>
        </div>

        {/* Why */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">
            {checkedFlags.length > 0 ? "What stood out" : "Nothing major stood out"}
          </h2>
          {checkedFlags.length > 0 ? (
            <ul className="mt-3 space-y-3">
              {checkedFlags.map((f) => (
                <li key={f.id} className="rounded-lg border border-line bg-surface p-4">
                  <p className="font-medium">{f.q}</p>
                  <p className="mt-1 text-sm text-muted">{f.why}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-muted">
              You didn&apos;t tick any warning signs. That is a good sign, but scams change
              constantly, so keep trusting your instincts.
            </p>
          )}
        </section>

        {/* What to do */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">What to do next</h2>
          <ul className="mt-3 space-y-2 text-muted">
            <li>• Don&apos;t reply, and don&apos;t call back any number they gave you.</li>
            <li>• Don&apos;t click links or download attachments.</li>
            <li>• Don&apos;t send money, gift cards, or share passwords and codes.</li>
            <li>• Verify by contacting the organisation using details you find yourself, not the ones in the message.</li>
          </ul>
          <p className="mt-4 text-sm text-muted">Report it to the relevant authority:</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {AUTHORITIES.map((a) => (
              <a
                key={a.name}
                href={a.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm hover:border-slate-600"
              >
                {a.name} <span className="text-muted">({a.region})</span>
              </a>
            ))}
          </div>
        </section>

        {/* Related articles */}
        {related.length > 0 && (
          <section className="mt-8">
            <h2 className="text-lg font-semibold">Read up on this kind of scam</h2>
            <ul className="mt-3 space-y-2">
              {related.map((a) => (
                <li key={a.slug}>
                  <Link href={`/scams/${a.slug}`} className="text-safe underline underline-offset-2 hover:text-safe-strong">
                    {a.title}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Still not sure */}
        <section className="mt-8 rounded-xl border border-line bg-surface p-5">
          <h2 className="font-semibold">Still not sure?</h2>
          <p className="mt-1 text-sm text-muted">Search our scam database for similar reports.</p>
          <Link
            href={`/scams?q=${encodeURIComponent(type.query)}`}
            className="mt-3 inline-flex rounded-lg bg-surface-2 px-4 py-2 text-sm font-medium hover:bg-line"
          >
            Search the database
          </Link>
        </section>

        <p className="mt-8 rounded-lg bg-surface-2 p-4 text-center font-medium">
          When in doubt, don&apos;t respond and don&apos;t click anything.
        </p>

        <button onClick={reset} className="mt-6 text-sm text-muted hover:text-fg">← Check something else</button>
      </Shell>
    );
  }

  return null;
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto max-w-2xl px-4 py-10">{children}</div>;
}

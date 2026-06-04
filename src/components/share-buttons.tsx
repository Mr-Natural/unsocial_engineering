"use client";

import { useState } from "react";

export function ShareButtons({ url, title }: { url: string; title: string }) {
  const [copied, setCopied] = useState(false);
  const enc = encodeURIComponent;

  const links = [
    { label: "X", href: `https://twitter.com/intent/tweet?text=${enc(title)}&url=${enc(url)}` },
    { label: "Facebook", href: `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}` },
    { label: "LinkedIn", href: `https://www.linkedin.com/sharing/share-offsite/?url=${enc(url)}` },
    { label: "Email", href: `mailto:?subject=${enc(title)}&body=${enc(url)}` },
  ];

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable; the share links still work */
    }
  }

  const cls =
    "rounded-md border border-line bg-surface px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-slate-600 hover:text-fg";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-muted">Share</span>
      {links.map((l) => (
        <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer" className={cls}>
          {l.label}
        </a>
      ))}
      <button type="button" onClick={copy} className={cls}>
        {copied ? "Copied!" : "Copy link"}
      </button>
    </div>
  );
}

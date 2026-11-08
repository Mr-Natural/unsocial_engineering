import type { Metadata } from "next";
import Link from "next/link";
import { RESOURCE_GROUPS, RESOURCES_CHECKED_ON } from "@/lib/resources";

export const metadata: Metadata = {
  title: "Help and resources",
  description: "Find official scam reporting and support services by location, and practical steps if money or account access is at risk.",
  alternates: { canonical: "/resources" },
};

export default function ResourcesPage() {
  return (
    <div className="mx-auto max-w-5xl px-5 py-14 sm:px-10">
      <p className="text-xs uppercase tracking-wider text-safe">Help and resources</p>
      <h1 className="mt-4 text-4xl tracking-tight">Find the right place to turn.</h1>
      <p className="mt-6 max-w-3xl text-lg text-muted">Scams cross borders. The best reporting and support route depends on where you are and what happened.</p>
      <section className="mt-8 border border-warn/40 bg-surface p-6" aria-labelledby="act-now">
        <h2 id="act-now" className="text-xl">If money or account access is at risk</h2>
        <p className="mt-3 text-muted">Contact your bank or account provider promptly using an official app, a known number or a website you reach independently. Preserve messages and payment records. If someone is in immediate danger, contact the local emergency services.</p>
        <p className="mt-3 text-sm text-muted">Ask about available recovery or dispute options. Reporting helps build evidence, but cannot guarantee a refund or investigation. These steps follow guidance from <a href="https://www.ownyouronline.govt.nz/personal/get-help-now/" className="text-safe underline" rel="noopener noreferrer">New Zealand’s NCSC</a> and the <a href="https://centreantifraude-antifraudcentre.ca/scams-fraudes/victim-victime-eng.htm" className="text-safe underline" rel="noopener noreferrer">Canadian Anti-Fraud Centre</a>.</p>
      </section>
      <nav aria-label="Choose your location" className="mt-8 flex flex-wrap gap-3">
        {RESOURCE_GROUPS.map(group => <a key={group.id} href={`#${group.id}`} className="border border-line px-4 py-2 text-sm hover:border-safe focus-visible:outline-2 focus-visible:outline-safe">{group.location}</a>)}
      </nav>
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {RESOURCE_GROUPS.map(group => (
          <section key={group.id} id={group.id} className="scroll-mt-6 border border-line bg-surface p-6" aria-labelledby={`${group.id}-title`}>
            <h2 id={`${group.id}-title`} className="text-xl">{group.location}</h2>
            <ul className="mt-4 space-y-5">
              {group.resources.map(resource => <li key={resource.url}>
                <a href={resource.url} rel="noopener noreferrer" className="font-semibold text-safe underline underline-offset-4">{resource.name}</a>
                <p className="mt-2 text-sm text-muted">{resource.purpose}</p>
              </li>)}
            </ul>
          </section>
        ))}
      </div>
      <p className="mt-8 text-sm text-muted">This is a starting directory, not complete worldwide coverage. If your country is not listed, use your local official police, consumer-protection or cybersecurity service. INTERPOL’s guide explains how local police can seek cross-border assistance.</p>
      <section className="mt-8 border-t border-line pt-6">
        <h2 className="text-xl">Still assessing the request?</h2>
        <p className="mt-3 text-muted">Our private checklist can help you recognise warning signs. It does not certify a message or seller as safe.</p>
        <Link href="/check" className="mt-4 inline-block text-safe underline underline-offset-4">Check common warning signs</Link>
        <p className="mt-6 text-xs text-muted">Resource information checked <time dateTime={RESOURCES_CHECKED_ON}>8 November 2026</time>. Service availability and reporting requirements may change. Follow the current instructions on the official site.</p>
      </section>
    </div>
  );
}

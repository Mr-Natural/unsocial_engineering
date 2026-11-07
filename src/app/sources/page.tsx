import type { Metadata } from "next";
export const metadata: Metadata = { title: "Our sources" };
const sources = [
  ["Australia", "Scamwatch", "https://www.scamwatch.gov.au/"],
  ["Australia", "Australian Signals Directorate", "https://www.cyber.gov.au/"],
  ["United States", "Federal Trade Commission", "https://consumer.ftc.gov/scams"],
  ["United States", "FBI Internet Crime Complaint Center", "https://www.ic3.gov/"],
  ["United Kingdom", "National Cyber Security Centre", "https://www.ncsc.gov.uk/"],
  ["European Union", "Europol", "https://www.europol.europa.eu/"],
  ["Singapore", "ScamShield", "https://www.scamshield.gov.sg/"],
];
export default function SourcesPage() {
  return (
    <article className="article-body mx-auto max-w-3xl px-5 py-14">
      <p className="text-sm uppercase tracking-wider text-safe">Our sources</p><h1 className="mt-4 text-4xl tracking-tight">A trail you can follow.</h1>
      <p className="mt-8">We start with original advisories, published research, court or regulator records, and first-hand incident reports. We use reporting and specialist analysis to find leads and test competing explanations. Being on this list does not make every statement a settled fact.</p>
      <h2>Australian and international references</h2>
      <ul>{sources.map(([region, name, url]) => <li key={url}><a href={url} rel="noopener noreferrer">{name}</a> — {region}</li>)}</ul>
      <h2>Read the source note</h2>
      <p>Article citations identify the evidence behind individual claims. Preliminary company findings are labelled as such, research dates are visible, and we separate the date of an incident from the date it was reported. Practical advice is checked against the reader&apos;s jurisdiction where relevant.</p>
    </article>
  );
}

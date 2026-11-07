import type { Metadata } from "next";
import Link from "next/link";
export const metadata: Metadata = { title: "Our approach" };

export default function AboutPage() {
  return (
    <article className="article-body mx-auto max-w-3xl px-5 py-14">
      <p className="text-sm uppercase tracking-wider text-safe">Our approach</p>
      <h1 className="mt-4 text-4xl tracking-tight">Understanding manipulation.<br /><span className="editorial-serif text-safe">Protecting people.</span></h1>
      <p className="mt-8">UnSocial Engineering examines the human decisions behind scams, from familiar impersonation tactics to emerging forms of digital deception. Our audience is international, with Australian context clearly identified where it matters.</p>
      <h2>Evidence before alarm</h2>
      <p>Our articles distinguish documented threats from developing risks and hypothetical examples. A Confirmed Threat label identifies a documented threat; it does not mean every explanation or attribution is settled. Emerging Risk describes a developing possibility. Hypothetical Scenario identifies an illustration, not a reported incident.</p>
      <p>Each reviewed article includes a research cutoff, a source trail and practical actions. Company accounts and preliminary investigations are attributed. Country-specific reporting routes are labelled.</p>
      <h2>Review and corrections</h2>
      <p>Drafts require editorial approval before publication. Substantive updates receive a fresh review and an updated date. We can withdraw an article while its evidence is reassessed. Automated scores do not establish whether a claim is true.</p>
      <h2>No blame required</h2>
      <p>Our aim is to explain the manipulation and help readers make their next decision. We avoid treating a person&apos;s loss as entertainment.</p>
      <p><Link href="/sources">Explore our source approach</Link> or <Link href="/check">find help and reporting options</Link>.</p>
    </article>
  );
}

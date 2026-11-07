// Deterministic, client-side scam checker data. No AI, no network, no storage —
// the checklist itself is the education. Each flag carries a "why" so the result
// can explain what the user just learned.

export type Flag = { id: string; q: string; why: string };

export type ScamType = {
  id: string;
  label: string;
  /** Category slug used to surface related articles and a category link. */
  categorySlug: string | null;
  /** Pre-filled query for the "search our database" CTA. */
  query: string;
  flags: Flag[];
};

const ODD_PAYMENT: Flag = {
  id: "odd_payment",
  q: "Did it ask for payment by gift card, crypto, or bank transfer?",
  why: "These payments are hard to trace and almost never used by legitimate businesses.",
};

export const SCAM_TYPES: ScamType[] = [
  {
    id: "email",
    label: "Email or message",
    categorySlug: "phishing",
    query: "phishing email text message",
    flags: [
      { id: "urgency", q: "Did it pressure you to act immediately (\"act now\", \"your account will be closed\")?", why: "Urgency is designed to stop you thinking it through." },
      { id: "personal", q: "Did it ask for passwords, PINs, or personal details?", why: "Legitimate organisations never ask for passwords by email or text." },
      { id: "link", q: "Did it ask you to click a link or download an attachment?", why: "Links and attachments can lead to fake login pages or malware." },
      { id: "sender", q: "Was the sender unfamiliar, or the address slightly misspelled?", why: "Scammers fake the display name, but the real address often gives them away." },
      { id: "too_good", q: "Did it offer a prize, refund, or deal that seems too good to be true?", why: "Unexpected winnings and refunds are classic bait." },
      { id: "threat", q: "Did it threaten a fine, arrest, or losing your account?", why: "Real agencies don't threaten you over email or text." },
      ODD_PAYMENT,
    ],
  },
  {
    id: "phone",
    label: "Phone call",
    categorySlug: "impersonation",
    query: "phone call impersonation scam",
    flags: [
      { id: "unsolicited", q: "Was the call unexpected, claiming to be your bank, the tax office, or tech support?", why: "Scammers impersonate trusted organisations to lower your guard." },
      { id: "personal", q: "Did they ask you to confirm passwords, one-time codes, or account details?", why: "Your bank already has your details and won't ask you to read them out." },
      { id: "remote", q: "Did they ask you to install software or give remote access to your device?", why: "That hands a stranger control of your computer and accounts." },
      { id: "urgency", q: "Did they create pressure or say it was urgent?", why: "Pressure is meant to stop you hanging up to check." },
      { id: "threat", q: "Did they threaten arrest, fines, or cutting off a service?", why: "Genuine agencies send official letters, not threatening calls." },
      { id: "no_callback", q: "Did they stop you hanging up to call the official number back?", why: "Scammers keep you on the line so you can't verify them." },
      ODD_PAYMENT,
    ],
  },
  {
    id: "social",
    label: "Social media post or DM",
    categorySlug: "impersonation",
    query: "social media direct message scam",
    flags: [
      { id: "stranger", q: "Was it from someone you don't know, or an account copying someone you do?", why: "Cloned and fake profiles are extremely common." },
      { id: "too_good", q: "Did it promise easy money, a giveaway, or big investment returns?", why: "If it sounds too good to be true, it is." },
      { id: "offplatform", q: "Did they want to move the chat to WhatsApp, Telegram, or text?", why: "Scammers move off-platform to avoid moderation." },
      { id: "link", q: "Did it include a link to claim a prize or log in?", why: "These lead to fake sites that steal your details." },
      { id: "money", q: "Did they ask for money, gift cards, or personal details?", why: "Requests for money from online-only contacts are a red flag." },
      { id: "romance", q: "Have you never met in person, yet they profess strong feelings fast?", why: "Fast affection is a hallmark of romance scams." },
    ],
  },
  {
    id: "website",
    label: "Website or link",
    categorySlug: "phishing",
    query: "fake website phishing link",
    flags: [
      { id: "url", q: "Does the web address look odd, misspelled, or not match the real company?", why: "Lookalike domains are how phishing sites fool you." },
      { id: "login", q: "Does it ask you to log in or enter card details unexpectedly?", why: "You may be handing credentials straight to a scammer." },
      { id: "unexpected", q: "Did you reach it from an unexpected email, text, or ad?", why: "Type known addresses yourself rather than following links." },
      { id: "too_good", q: "Does it offer prices, prizes, or refunds that seem too good?", why: "Fake shops lure you with deals that don't exist." },
      { id: "no_contact", q: "Is there no clear contact info or address, or is the site brand new?", why: "Legitimate businesses are easy to verify." },
      ODD_PAYMENT,
    ],
  },
  {
    id: "job",
    label: "Job offer",
    categorySlug: "employment-scam",
    query: "job offer employment scam",
    flags: [
      { id: "unsolicited", q: "Did the offer arrive out of the blue for a job you didn't apply for?", why: "Real recruiters don't hire strangers unprompted." },
      { id: "fee", q: "Were you asked to pay for training, equipment, or a background check?", why: "You should never have to pay to get a job." },
      { id: "too_good", q: "Is the pay very high for very little work?", why: "Overpayment is bait to hook you." },
      { id: "personal_early", q: "Did they ask for bank or ID details before any real interview?", why: "That information enables identity theft." },
      { id: "overpay", q: "Were you sent a cheque and asked to send some money back?", why: "The cheque will bounce and you'll lose what you sent." },
      { id: "offplatform", q: "Was the interview only over chat, never a call or in person?", why: "Text-only hiring hides who you're really dealing with." },
      { id: "mule", q: "Did they ask you to buy gift cards or move money for them?", why: "That can make you a money mule, which is illegal." },
    ],
  },
  {
    id: "invoice",
    label: "Invoice or payment request",
    categorySlug: "marketplace-fraud",
    query: "fake invoice payment request",
    flags: [
      { id: "not_ordered", q: "Is it for goods or services you don't remember ordering?", why: "Fake invoices bank on you paying without checking." },
      { id: "unfamiliar", q: "Is the company unfamiliar, or are the details vague?", why: "Legitimate suppliers have a clear record with you." },
      { id: "overdue", q: "Does it claim to be overdue or threaten late fees or cut-off?", why: "Pressure stops you verifying before you pay." },
      { id: "changed_bank", q: "Does it ask you to pay to new or changed bank details?", why: "Changed account details are a sign of invoice redirection fraud." },
      { id: "mismatch", q: "Do the contact details differ from the company's official ones?", why: "Always verify using details you find independently." },
      ODD_PAYMENT,
    ],
  },
  {
    id: "other",
    label: "Something else",
    categorySlug: null,
    query: "scam",
    flags: [
      { id: "unsolicited", q: "Did it come out of the blue?", why: "Unexpected contact is the starting point of most scams." },
      { id: "urgency", q: "Was there pressure to act quickly?", why: "Urgency is designed to stop you checking." },
      { id: "personal", q: "Did it ask for personal details, passwords, or codes?", why: "Sharing these can lead to fraud and identity theft." },
      { id: "money", q: "Did it ask for money or unusual payment (gift cards, crypto, transfer)?", why: "Untraceable payment is a major warning sign." },
      { id: "too_good", q: "Did it promise something that seems too good to be true?", why: "Unrealistic offers are bait." },
      { id: "threat", q: "Did it threaten consequences if you didn't act?", why: "Threats are used to scare you into complying." },
      { id: "link", q: "Did it ask you to click a link or download something?", why: "Links and downloads can steal info or install malware." },
    ],
  },
];

export type RiskLevel = "low" | "medium" | "high";

export type RiskResult = {
  level: RiskLevel;
  headline: string;
  blurb: string;
};

export function assessRisk(flagCount: number): RiskResult {
  if (flagCount >= 4) {
    return {
      level: "high",
      headline: "This looks like a scam",
      blurb: "Several strong warning signs showed up. Treat this as a scam: don't respond, and don't send money or details.",
    };
  }
  if (flagCount >= 2) {
    return {
      level: "medium",
      headline: "This has some warning signs",
      blurb: "A few red flags showed up. Take a moment to verify before you act on anything.",
    };
  }
  return {
    level: "low",
    headline: "Probably safe, but stay alert",
    blurb: "We didn't spot many warning signs. Still, trust your instincts and verify anything that feels off.",
  };
}

export const AUTHORITIES = [
  { name: "ACCC Scamwatch", region: "Australia", url: "https://www.scamwatch.gov.au/report-a-scam" },
  { name: "FTC", region: "United States", url: "https://reportfraud.ftc.gov" },
  { name: "Report Fraud", region: "England, Wales and Northern Ireland", url: "https://www.reportfraud.police.uk/reporting-a-fraud/" },
  { name: "Police Scotland", region: "Scotland", url: "https://www.scotland.police.uk/contact-us/" },
];

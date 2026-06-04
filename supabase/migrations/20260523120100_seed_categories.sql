-- Seed the scam taxonomy. Idempotent: re-running leaves existing rows untouched.

insert into public.categories (name, slug, description, icon) values
  ('Phishing',                'phishing',                'Fake emails, texts, and websites that trick you into handing over passwords, card numbers, or personal details.', 'fish'),
  ('Romance Scam',            'romance-scam',            'Fake online relationships built to manipulate victims into sending money.',                                       'heart-crack'),
  ('Crypto Fraud',            'crypto-fraud',            'Bogus cryptocurrency investments, fake exchanges, wallet drainers, and pig-butchering schemes.',                  'bitcoin'),
  ('Investment Scam',         'investment-scam',         'Fake or rigged investment opportunities promising unrealistic returns.',                                          'trending-up'),
  ('Impersonation',           'impersonation',           'Scammers posing as a person or brand you trust to gain access or payment.',                                       'user-x'),
  ('Tech Support',            'tech-support',            'Fake support agents claiming your device is infected to gain remote access or payment.',                          'monitor-x'),
  ('Marketplace Fraud',       'marketplace-fraud',       'Scams on buy/sell platforms: fake listings, overpayment tricks, and undelivered goods.',                          'shopping-cart'),
  ('Employment Scam',         'employment-scam',         'Fake job offers used to steal money or personal data, often via upfront fees or fake cheques.',                  'briefcase'),
  ('Government Impersonation','government-impersonation','Scammers posing as tax offices, police, or agencies to demand payment or data.',                                  'landmark'),
  ('Subscription Trap',       'subscription-trap',       'Free trials and offers engineered to lock you into recurring charges that are hard to cancel.',                  'credit-card')
on conflict (slug) do nothing;

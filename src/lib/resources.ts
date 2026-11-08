export const RESOURCES_CHECKED_ON = "2026-11-08";

export const RESOURCE_GROUPS = [
  {
    "id": "australia",
    "location": "Australia",
    "resources": [
      {
        "name": "Scamwatch",
        "url": "https://www.scamwatch.gov.au/stop-check-protect",
        "purpose": "Recognising scams, immediate protective steps and the Australian reporting route."
      },
      {
        "name": "ASD / ReportCyber",
        "url": "https://www.cyber.gov.au/submit-a-report",
        "purpose": "Choose the appropriate Australian cybercrime or incident reporting option."
      }
    ]
  },
  {
    "id": "united-states",
    "location": "United States",
    "resources": [
      {
        "name": "FTC ReportFraud",
        "url": "https://reportfraud.ftc.gov/",
        "purpose": "Report scams and unfair business practices to the US Federal Trade Commission."
      },
      {
        "name": "FBI IC3",
        "url": "https://www.ic3.gov/",
        "purpose": "Report internet-enabled crime. A report does not guarantee an investigation or recovery."
      }
    ]
  },
  {
    "id": "england-wales-northern-ireland",
    "location": "England, Wales and Northern Ireland",
    "resources": [
      {
        "name": "Report Fraud",
        "url": "https://www.reportfraud.police.uk/",
        "purpose": "Fraud and cybercrime reporting, prevention information and support routes."
      }
    ]
  },
  {
    "id": "scotland",
    "location": "Scotland",
    "resources": [
      {
        "name": "Police Scotland",
        "url": "https://www.scotland.police.uk/advice/cybercrime",
        "purpose": "Scottish reporting and support options; use this jurisdiction’s route rather than assuming Report Fraud covers Scotland."
      }
    ]
  },
  {
    "id": "canada",
    "location": "Canada",
    "resources": [
      {
        "name": "Canadian Anti-Fraud Centre",
        "url": "https://centreantifraude-antifraudcentre.ca/scams-fraudes/victim-victime-eng.htm",
        "purpose": "Steps after fraud, local police reporting and the official online reporting service."
      }
    ]
  },
  {
    "id": "new-zealand",
    "location": "New Zealand",
    "resources": [
      {
        "name": "NCSC / Own Your Online",
        "url": "https://www.ownyouronline.govt.nz/personal/get-help-now/",
        "purpose": "Help after an online incident, account protection and reporting routes."
      }
    ]
  },
  {
    "id": "singapore",
    "location": "Singapore",
    "resources": [
      {
        "name": "ScamShield",
        "url": "https://www.scamshield.gov.sg/",
        "purpose": "Check suspicious approaches, find scam warnings and follow official help and reporting routes."
      }
    ]
  },
  {
    "id": "international",
    "location": "International / other locations",
    "resources": [
      {
        "name": "INTERPOL: where to report international crime",
        "url": "https://www.interpol.int/What-you-can-do/If-you-need-help",
        "purpose": "Start with police in your own country. INTERPOL supports police cooperation rather than taking public crime reports through social media."
      }
    ]
  }
] as const;

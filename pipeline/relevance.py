"""Scam-relevance gate for ingested leads.

Authority feeds (notably the FTC consumer blog) carry non-scam items too, e.g.
requests for public comment on pricing. This keyword gate keeps obvious non-scam
leads from becoming articles. It is intentionally broad and lossy on the side of
keeping leads; tighten the keyword set if too much noise gets through.
"""

from __future__ import annotations

# Lowercase substring match. Keep terms that are not dangerous substrings of
# common non-scam words (e.g. avoid bare "con"/"hack").
SCAM_KEYWORDS = (
    "scam", "scammer", "fraud", "phishing", "phish", "imposter", "impostor",
    "impersonat", "spoof", "hoax", "fake", "counterfeit", "identity theft",
    "ponzi", "pyramid scheme", "extortion", "ransom", "malware", "data breach",
    "rip-off", "ripoff", "con artist", "catfish", "skimming",
    "gift card", "wire transfer", "cyberattack", "cyber attack", "stolen",
    "swindle", "bogus", "phony", "fraudulent", "deepfake",
)


def is_scam_relevant(text: str) -> bool:
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in SCAM_KEYWORDS)

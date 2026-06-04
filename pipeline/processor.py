"""Lead processor — cluster related leads, score clusters, feed the writer.

Clusters unprocessed leads with TF-IDF + cosine similarity (greedy union-find at
a similarity threshold), writes a shared cluster_id back to each lead, then ranks
clusters by lead count, total engagement, source diversity, and recency. With
--write it hands the top clusters to the writer.

Standalone:
    python pipeline/processor.py                 # cluster + score, print ranking
    python pipeline/processor.py --write         # also draft the top clusters
    python pipeline/processor.py --write --top 5
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import config, get_supabase  # noqa: E402

log = logging.getLogger("processor")

SIMILARITY_THRESHOLD = 0.20  # cosine similarity above which two leads are "related"
# Calibrated on short lead text (title + body): clearly-related reposts/cross-posts
# land around 0.24+, unrelated leads near 0. Tune with --threshold.
RECENCY_WINDOW_HOURS = 168   # one week; older leads contribute no recency bonus


@dataclass
class Cluster:
    cluster_id: str
    leads: list[dict] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.leads)

    @property
    def total_engagement(self) -> int:
        return sum(int(l.get("relevance_score") or 0) for l in self.leads)

    @property
    def source_diversity(self) -> int:
        return len({l.get("source") for l in self.leads if l.get("source")})

    def recency_factor(self, now: datetime) -> float:
        newest = max((_parse_ts(l.get("scraped_at")) for l in self.leads), default=now)
        age_hours = max(0.0, (now - newest).total_seconds() / 3600)
        return max(0.0, 1.0 - age_hours / RECENCY_WINDOW_HOURS)

    def score(self, now: datetime) -> float:
        # Diminishing returns on count/engagement; linear on diversity and recency.
        return (
            2.0 * math.log1p(self.size)
            + 1.5 * math.log1p(self.total_engagement)
            + 1.0 * self.source_diversity
            + 2.0 * self.recency_factor(now)
        )


def _parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _lead_text(lead: dict) -> str:
    return f"{lead.get('title') or ''}\n{lead.get('raw_text') or ''}".strip()


def _cluster_leads(leads: list[dict], threshold: float) -> list[list[int]]:
    """Return groups of lead indices, clustered by TF-IDF cosine similarity."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    texts = [_lead_text(l) for l in leads]
    matrix = TfidfVectorizer(stop_words="english", max_features=5000).fit_transform(texts)
    sim = cosine_similarity(matrix)

    # Union-find over the "similar enough" graph.
    parent = list(range(len(leads)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    for i in range(len(leads)):
        for j in range(i + 1, len(leads)):
            if sim[i][j] >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(len(leads)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def build_clusters(leads: list[dict], threshold: float = SIMILARITY_THRESHOLD) -> list[Cluster]:
    if not leads:
        return []
    if len(leads) == 1:
        return [Cluster(cluster_id=str(uuid.uuid4()), leads=leads)]
    clusters = []
    for indices in _cluster_leads(leads, threshold):
        clusters.append(Cluster(cluster_id=str(uuid.uuid4()), leads=[leads[i] for i in indices]))
    return clusters


def run(write: bool = False, top: int | None = None, threshold: float = SIMILARITY_THRESHOLD,
        dry_run: bool = False) -> list[Cluster]:
    client = get_supabase()
    leads = (
        client.table("leads")
        .select("*")
        .eq("status", "new")
        .is_("cluster_id", "null")
        .execute()
        .data
        or []
    )
    log.info("Clustering %d unprocessed lead(s)", len(leads))
    if not leads:
        return []

    now = datetime.now(timezone.utc)
    clusters = build_clusters(leads, threshold)
    clusters.sort(key=lambda c: c.score(now), reverse=True)
    log.info("Formed %d cluster(s)", len(clusters))

    for rank, cluster in enumerate(clusters, 1):
        log.info(
            "#%d score=%.2f size=%d engagement=%d sources=%d :: %s",
            rank, cluster.score(now), cluster.size, cluster.total_engagement,
            cluster.source_diversity, (cluster.leads[0].get("title") or "")[:60],
        )

    if not dry_run:
        # Persist cluster_id back to each lead so we don't re-cluster them.
        for cluster in clusters:
            ids = [l["id"] for l in cluster.leads]
            client.table("leads").update({"cluster_id": cluster.cluster_id}).in_("id", ids).execute()

    if write:
        from pipeline import writer  # local import avoids a hard dependency for cluster-only runs

        limit = top if top is not None else config.max_articles_per_run
        for cluster in clusters[:limit]:
            log.info("Writing cluster %s (%d leads)", cluster.cluster_id, cluster.size)
            if not dry_run:
                writer.run(cluster_id=cluster.cluster_id)

    return clusters


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster and score leads; optionally write the top clusters.")
    parser.add_argument("--write", action="store_true", help="hand the top clusters to the writer")
    parser.add_argument("--top", type=int, help="how many top clusters to write (default: MAX_ARTICLES_PER_RUN)")
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD, help="cosine similarity threshold")
    parser.add_argument("--dry-run", action="store_true", help="do not write to the database")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(write=args.write, top=args.top, threshold=args.threshold, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

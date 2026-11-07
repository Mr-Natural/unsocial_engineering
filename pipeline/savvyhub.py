"""Explicit SavvyHub draft transport. No approval, publication, scheduling or sends.

Run from a separately provisioned Hub identity with the database 'producer' role.
An export fingerprint protects the selected file; it is not editorial approval.
The database returns the revision/hash Shaun must actually review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from pipeline.publisher import Publisher, PublishingError, revision_hash


def read_export(path: Path, expected_sha256: str):
    if path.stat().st_size > 210000:
        raise PublishingError("Hub export exceeds size limit")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise PublishingError("Hub export changed; obtain a fresh reviewed fingerprint")
    package = json.loads(raw)
    fields = {"format", "destination", "hub_item_id", "slug", "base_hash", "article"}
    if not isinstance(package, dict) or set(package) != fields:
        raise PublishingError("Unexpected Hub export contract")
    if package["format"] != "savvyhub-unsocial-draft-v1" or package["destination"] != "unsocialengineering.com":
        raise PublishingError("Wrong Hub export destination or format")
    if not isinstance(package["article"], dict):
        raise PublishingError("Structured article required")
    if not isinstance(package["hub_item_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", package["hub_item_id"]):
        raise PublishingError("Stable Hub item identifier required")
    if not isinstance(package["slug"], str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", package["slug"]):
        raise PublishingError("Invalid article slug")
    if package["base_hash"] is not None:
        revision_hash(package["base_hash"])
    return package


def deliver(package, publisher):
    # Retry this exact item and base hash. Database staging is idempotent.
    return publisher.stage("savvyhub:" + package["hub_item_id"], package["slug"],
                           package["article"], package["base_hash"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--sha256", required=True, type=revision_hash)
    parser.add_argument("--project-ref", required=True)
    args = parser.parse_args(argv)
    try:
        package = read_export(args.export, args.sha256)
        if not re.fullmatch(r"[a-z]{20}", args.project_ref):
            raise PublishingError("Explicit Supabase project ref required")
        origin = f"https://{args.project_ref}.supabase.co"
        if os.environ.get("UE_SUPABASE_URL") != origin:
            raise PublishingError("Configured project differs from selected destination")
        producer = Publisher(origin, os.environ.get("UE_SUPABASE_PUBLIC_KEY", ""),
                             os.environ.get("UE_PRODUCER_ACCESS_TOKEN", ""))
        result = deliver(package, producer)
        # Print only routing and database fingerprints, never the private body.
        print(json.dumps({"status": "staged_for_review", "revision_id": result["revision_id"],
                          "revision_hash": result["revision_hash"]}))
        return 0
    except (PublishingError, OSError, ValueError, argparse.ArgumentTypeError, KeyError):
        print("Hub draft staging failed; check contract, fingerprint, target and producer access", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Reviewed SavvyHub destination adapter. Standard library only; no implicit .env loads.

No command means no operation. Stage, review, approval and publication are separate
commands. The database validates roles and binds approval to its own revision hash.
Never call approval from an unattended writer/editor/worker.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID


class PublishingError(Exception):
    """Safe error text, without credentials, response bodies or URLs."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublishingError("RPC redirect refused; verify the configured project")


class Publisher:
    def __init__(self, url: str, public_key: str, access_token: str):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/") or parsed.port is not None):
            raise PublishingError("Configure an HTTPS Supabase project origin")
        if not public_key or not access_token:
            raise PublishingError("Public API key and authenticated access token are required")
        self.origin = url.rstrip("/")
        self.public_key = public_key
        self.access_token = access_token
        self.opener = build_opener(NoRedirect())

    @classmethod
    def from_environment(cls):
        # Deliberately do not fall back to SUPABASE_SERVICE_ROLE_KEY or broad config.py.
        return cls(os.environ.get("UE_SUPABASE_URL", ""),
                   os.environ.get("UE_SUPABASE_PUBLIC_KEY", ""),
                   os.environ.get("UE_EDITORIAL_ACCESS_TOKEN", ""))

    def _rpc(self, name: str, payload: dict) -> dict:
        request = Request(f"{self.origin}/rest/v1/rpc/{name}",
                          data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Accept": "application/json",
                                   "apikey": self.public_key,
                                   "Authorization": f"Bearer {self.access_token}"}, method="POST")
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise PublishingError("RPC response exceeded size limit")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise PublishingError("Unexpected RPC response")
                return result
        except HTTPError as exc:
            status = exc.code
            exc.close()
            raise PublishingError(f"RPC rejected (HTTP {status}); inspect roles, revision and approval") from None
        except (URLError, TimeoutError, OSError):
            raise PublishingError("RPC connection failed; retry the SAME revision after checking its receipt") from None
        except (ValueError, UnicodeError):
            raise PublishingError("Invalid RPC response") from None

    def stage(self, external_id: str, slug: str, article: dict, base_hash: str | None = None):
        return self._rpc("ue_stage_revision", {"p_external_id": external_id, "p_slug": slug,
                         "p_base_hash": base_hash, "p_article": article})

    def review(self, revision_id: str):
        return self._rpc("ue_review_revision", {"p_revision_id": revision_id})

    def approve(self, revision_id: str, revision_hash: str, approved: bool):
        return self._rpc("ue_set_approval", {"p_revision_id": revision_id,
                         "p_revision_hash": revision_hash, "p_approved": approved})

    def publish(self, revision_id: str, revision_hash: str):
        return self._rpc("ue_publish_revision", {"p_revision_id": revision_id, "p_revision_hash": revision_hash})

    def social_draft(self, revision_id: str):
        return self._rpc("ue_social_draft", {"p_revision_id": revision_id})


def revision_id(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        raise argparse.ArgumentTypeError("Expected revision UUID") from None


def revision_hash(value: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{64}", value):
        raise argparse.ArgumentTypeError("Expected the database's 64-character revision hash")
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage", help="Submit a structured draft; never publishes")
    stage.add_argument("article", type=Path)
    stage.add_argument("--external-id", required=True)
    stage.add_argument("--slug", required=True)
    stage.add_argument("--base-hash", type=revision_hash)
    for command in ("review", "approve", "revoke", "publish", "social-draft"):
        cmd = sub.add_parser(command)
        cmd.add_argument("revision_id", type=revision_id)
        if command in ("approve", "revoke", "publish"):
            cmd.add_argument("--hash", required=True, type=revision_hash)
    args = parser.parse_args(argv)
    try:
        publisher = Publisher.from_environment()
        if args.command == "stage":
            if args.article.stat().st_size > 200000:
                raise PublishingError("Article file is too large")
            result = publisher.stage(args.external_id, args.slug,
                                     json.loads(args.article.read_text(encoding="utf-8-sig")), args.base_hash)
        elif args.command == "review":
            result = publisher.review(args.revision_id)
        elif args.command in ("approve", "revoke"):
            result = publisher.approve(args.revision_id, args.hash, args.command == "approve")
        elif args.command == "publish":
            result = publisher.publish(args.revision_id, args.hash)
        else:
            result = publisher.social_draft(args.revision_id)
        # Draft output belongs in a private review workspace, never public CI logs.
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (PublishingError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, PublishingError) else "Invalid input or unreadable article file"
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

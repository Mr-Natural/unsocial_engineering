"""Central configuration for the UnsocialEngineering content pipeline.

Reads settings from a `.env` file at the project root (and real environment
variables, which take precedence). Import `config` from here rather than calling
`os.getenv` directly so that required-key validation happens in one place.

    from pipeline.config import config, get_supabase

    client = get_supabase()
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Project root is the parent of the pipeline/ directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env then .env.local (the latter overrides), mirroring Next.js behaviour.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=True)

# Use the OS certificate store for TLS verification. On machines where antivirus
# or a corporate proxy intercepts HTTPS (e.g. Norton's TLS scanning here), the
# re-signed certs are trusted by Windows/browsers but rejected by OpenSSL's
# bundled CA set. truststore delegates verification to the OS, which trusts them.
# Harmless elsewhere; silently skipped if truststore isn't installed.
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key, default)
    return value.strip() if isinstance(value, str) else value


def _env_bool(key: str, default: bool = False) -> bool:
    raw = _env(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    # Supabase
    supabase_url: str | None = field(default_factory=lambda: _env("NEXT_PUBLIC_SUPABASE_URL"))
    supabase_anon_key: str | None = field(default_factory=lambda: _env("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
    supabase_service_role_key: str | None = field(default_factory=lambda: _env("SUPABASE_SERVICE_ROLE_KEY"))

    # Anthropic
    anthropic_api_key: str | None = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    claude_model: str = field(default_factory=lambda: _env("CLAUDE_MODEL") or "claude-sonnet-4-20250514")

    # Reddit
    reddit_client_id: str | None = field(default_factory=lambda: _env("REDDIT_CLIENT_ID"))
    reddit_client_secret: str | None = field(default_factory=lambda: _env("REDDIT_CLIENT_SECRET"))
    reddit_user_agent: str = field(default_factory=lambda: _env("REDDIT_USER_AGENT") or "unsocialengineering/0.1")

    # Twitter/X (deferred — see UNSOCIALENGINEERING_CC_PROMPTS.md notes)
    twitter_bearer_token: str | None = field(default_factory=lambda: _env("TWITTER_BEARER_TOKEN"))

    # Public site URL (for links in generated social posts)
    site_url: str = field(default_factory=lambda: (_env("NEXT_PUBLIC_SITE_URL") or "http://localhost:3000").rstrip("/"))

    # Pipeline behaviour
    auto_publish: bool = field(default_factory=lambda: _env_bool("AUTO_PUBLISH", False))
    human_review: bool = field(default_factory=lambda: _env_bool("HUMAN_REVIEW", True))
    confidence_threshold: int = field(default_factory=lambda: _env_int("CONFIDENCE_THRESHOLD", 70))
    max_articles_per_run: int = field(default_factory=lambda: _env_int("MAX_ARTICLES_PER_RUN", 3))

    def require(self, *keys: str) -> None:
        """Raise if any named attribute is unset. Call at the start of a script
        so failures are loud and early rather than mid-run.

            config.require("supabase_url", "supabase_service_role_key")
        """
        missing = [k for k in keys if not getattr(self, k, None)]
        if missing:
            raise RuntimeError(
                "Missing required configuration: "
                + ", ".join(missing)
                + f". Set them in {PROJECT_ROOT / '.env'} (see .env.example)."
            )


config = Config()


@lru_cache(maxsize=1)
def get_supabase():
    """Return a Supabase client authenticated with the service-role key.

    Cached so repeated calls reuse one client. Requires `supabase` (supabase-py).
    """
    from supabase import create_client  # imported lazily so config import is cheap

    config.require("supabase_url", "supabase_service_role_key")
    return create_client(config.supabase_url, config.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_anthropic():
    """Return an Anthropic API client. Cached so repeated calls reuse one client.

    Requires the `anthropic` SDK. TLS goes through truststore (injected above), so
    this works behind the local Norton TLS inspection.
    """
    import anthropic  # imported lazily so config import is cheap

    config.require("anthropic_api_key")
    return anthropic.Anthropic(api_key=config.anthropic_api_key)


if __name__ == "__main__":
    # Quick diagnostic: show which keys are present without printing secrets.
    print(f"Project root: {PROJECT_ROOT}")
    fields = {
        "NEXT_PUBLIC_SUPABASE_URL": config.supabase_url,
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": config.supabase_anon_key,
        "SUPABASE_SERVICE_ROLE_KEY": config.supabase_service_role_key,
        "ANTHROPIC_API_KEY": config.anthropic_api_key,
        "REDDIT_CLIENT_ID": config.reddit_client_id,
        "REDDIT_CLIENT_SECRET": config.reddit_client_secret,
        "TWITTER_BEARER_TOKEN": config.twitter_bearer_token,
    }
    for key, value in fields.items():
        print(f"  {'set ' if value else 'MISSING'}  {key}")
    print(f"\nclaude_model={config.claude_model}  auto_publish={config.auto_publish}  "
          f"human_review={config.human_review}  confidence_threshold={config.confidence_threshold}")

"""Real isolated PostgreSQL tests, with synthetic Supabase auth claims.

Set UE_TEST_PG_BIN to an existing trusted PostgreSQL bin directory and
UE_TEST_WORKDIR to a writable scratch folder. No production URL or .env is read.
The fresh cluster binds only 127.0.0.1 and uses a random disposable password.
Its data/log files are preserved for inspection; the server is always stopped.
These tests do not verify Supabase's JWT issuer, PostgREST or Vercel deployment.
"""
import copy
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor


ROOT = Path(__file__).resolve().parents[2]
EDITOR = "00000000-0000-0000-0000-000000000001"
PUBLISHER = "00000000-0000-0000-0000-000000000002"
STRANGER = "00000000-0000-0000-0000-000000000003"
PRODUCER = "00000000-0000-0000-0000-000000000004"


def literal(value):
    return "null" if value is None else "'" + str(value).replace("'", "''") + "'"


def article():
    return {
        "title": "Synthetic test article", "summary": "This is a test, not editorial content.",
        "author_credit": "Test fixture", "category_slug": "psychology-of-deception",
        "stream": "evergreen_education", "region": "International",
        "evidence_label": "Hypothetical Scenario", "evidence_note": "Synthetic assertions only.",
        "research_as_of": "2026-11-07T00:00:00Z",
        "sections": [{"heading": "A test", "paragraphs": [{
            "text": '<script>alert("test")</script> & harmless quoted text', "source_ids": ["s1"]}]}],
        "sources": [{"id": "s1", "title": "Example source", "publisher": "Example",
                     "url": "https://example.org/test?a=1&b=2"}],
        "actions": ["This is a synthetic practical action."],
        "social_copy": "Synthetic social draft. Requires separate review."
    }


@unittest.skipUnless(os.environ.get("UE_TEST_PG_BIN") and os.environ.get("UE_TEST_WORKDIR"),
                     "Set UE_TEST_PG_BIN and UE_TEST_WORKDIR for isolated PostgreSQL tests")
class DatabaseTests(unittest.TestCase):
    @classmethod
    def command(cls, executable, args, **kwargs):
        creation = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        if executable == "pg_ctl":
            # PostgreSQL's background children can inherit a PIPE on Windows.
            # A real file avoids waiting indefinitely for inherited pipe handles.
            with (cls.scratch / "pg-ctl.log").open("a", encoding="utf-8") as output:
                result = subprocess.run([str(cls.bin / executable), *args], stdin=subprocess.DEVNULL,
                    stdout=output, stderr=output, env=cls.env, timeout=60, creationflags=creation)
            result.stderr = "See owned scratch pg-ctl.log"
            return result
        return subprocess.run([str(cls.bin / executable), *args], capture_output=True,
                              text=True, encoding="utf-8", env=cls.env, timeout=60,
                              creationflags=creation, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.bin = Path(os.environ["UE_TEST_PG_BIN"]).resolve()
        cls.scratch = Path(tempfile.mkdtemp(prefix="ue-pg-", dir=os.environ["UE_TEST_WORKDIR"]))
        cls.data = cls.scratch / "data"
        # Discard inherited libpq connection options; never connect to an ambient DB.
        cls.env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
        cls.env["PGPASSWORD"] = secrets.token_urlsafe(32)
        cls.env["PGCLIENTENCODING"] = "UTF8"
        # CI alone may use its digest-pinned disposable service container.
        # No arbitrary URL/host/username/database or inherited libpq options.
        external_port = os.environ.get("UE_TEST_CI_PORT")
        if external_port:
            if os.environ.get("GITHUB_ACTIONS") != "true" or not external_port.isdecimal():
                raise RuntimeError("External test port is allowed only in isolated CI")
            cls.port = int(external_port)
            if not 1024 <= cls.port <= 65535:
                raise RuntimeError("Invalid disposable CI port")
            cls.env["PGPASSWORD"] = "disposable-ci-only"
        else:
            cls.start_owned_cluster()
        cls.install_schema()

    @classmethod
    def start_owned_cluster(cls):
        password_file = cls.scratch / "init-password"
        password_file.write_text(cls.env["PGPASSWORD"], encoding="ascii")
        try:
            result = cls.command("initdb", ["-D", str(cls.data), "-U", "ue_test_owner", "--encoding=UTF8",
                "--locale=C", "--auth-host=scram-sha-256", "--auth-local=scram-sha-256",
                f"--pwfile={password_file}"])
        finally:
            password_file.unlink(missing_ok=True)
        if result.returncode:
            raise RuntimeError("Isolated initdb failed: " + result.stderr)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        result = cls.command("pg_ctl", ["-D", str(cls.data), "-l", str(cls.scratch / "postgres.log"),
            "-o", f"-h 127.0.0.1 -p {cls.port}", "-w", "start"])
        if result.returncode:
            raise RuntimeError("Isolated server start failed: " + result.stderr)
        cls.addClassCleanup(cls.stop)

    @classmethod
    def install_schema(cls):
        cls.sql("""
          create role anon nologin;
          create role authenticated nologin;
          create role service_role nologin bypassrls;
          create schema auth;
          create function auth.uid() returns uuid language sql stable as
            $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
          create function auth.role() returns text language sql stable as
            $$ select current_setting('request.jwt.claim.role', true) $$;
          grant usage on schema auth to anon, authenticated, service_role;
          -- Mimic hosted defaults so tests catch forgotten direct function grants.
          alter default privileges in schema public grant execute on functions to anon, authenticated, service_role;
        """, identity=None)
        for migration in sorted((ROOT / "supabase" / "migrations").glob("*.sql")):
            cls.sql(migration.read_text(encoding="utf-8-sig"), identity=None)
        cls.sql(f"""
          grant usage on schema public to anon, authenticated, service_role;
          grant select on public.articles, public.categories to anon, authenticated;
          insert into ue_private.members values ('{EDITOR}', 'editor'), ('{PUBLISHER}', 'publisher'), ('{PRODUCER}', 'producer');
        """, identity=None)

    @classmethod
    def stop(cls):
        result = cls.command("pg_ctl", ["-D", str(cls.data), "-m", "fast", "-w", "stop"])
        if result.returncode:
            raise RuntimeError("Could not stop owned test cluster: " + str(cls.data))

    @classmethod
    def sql(cls, sql, identity=EDITOR, role="authenticated", error=None):
        prefix = ""
        if identity is not None:
            prefix = (f"set role {role}; set request.jwt.claim.sub = {literal(identity)};"
                      f"set request.jwt.claim.role = {literal(role)};")
        result = cls.command("psql", ["-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
            "-v", "VERBOSITY=verbose", "-h", "127.0.0.1", "-p", str(cls.port),
            "-U", "ue_test_owner", "-d", "postgres"], input=prefix + sql)
        if error is not None:
            if result.returncode == 0 or error not in result.stderr:
                raise AssertionError(f"Expected SQLSTATE {error}; got {result.stderr or result.stdout}")
            return None
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def stage(self, payload=None, external=None, base=None, **kwargs):
        external = external or "test-" + secrets.token_hex(6)
        return json.loads(self.sql("select public.ue_stage_revision("
            f"{literal(external)}, {literal(external)}, {literal(base)}, "
            f"{literal(json.dumps(payload or article()))}::jsonb);", **kwargs))

    def approve(self, rev, approved=True, **kwargs):
        return self.sql(f"select public.ue_set_approval('{rev['revision_id']}',"
                        f"'{rev['revision_hash']}', {'true' if approved else 'false'});", **kwargs)

    def publish(self, rev, **kwargs):
        return self.sql(f"select public.ue_publish_revision('{rev['revision_id']}', '{rev['revision_hash']}');",
                        identity=PUBLISHER, **kwargs)

    def test_01_draft_privacy_and_role_boundaries(self):
        rev = self.stage()
        slug = rev["envelope"]["slug"]
        self.assertEqual(self.sql(f"select count(*) from public.articles where slug='{slug}';", role="anon"), "0")
        self.sql("select * from ue_private.revisions;", role="anon", error="42501")
        self.sql("select * from ue_private.revisions;", error="42501")
        self.sql(f"select public.ue_review_revision('{rev['revision_id']}');", identity=STRANGER, error="42501")
        self.sql(f"select public.ue_review_revision('{rev['revision_id']}');", role="anon", error="42501")
        self.sql(f"select public.ue_review_revision('{rev['revision_id']}');", role="service_role", error="42501")
        self.approve(rev, identity=PUBLISHER, error="42501")
        self.publish(rev, error="42501")

    def test_producer_can_stage_but_cannot_approve_publish_or_withdraw(self):
        rev = self.stage(identity=PRODUCER)
        self.approve(rev, identity=PRODUCER, error="42501")
        self.sql(f"select public.ue_publish_revision('{rev['revision_id']}', '{rev['revision_hash']}');",
                 identity=PRODUCER, error="42501")
        self.sql(f"select public.ue_withdraw_revision('{rev['revision_id']}', '{rev['revision_hash']}', 'test');",
                 identity=PRODUCER, error="42501")
        self.sql("select * from ue_private.revisions;", identity=PRODUCER, error="42501")

    def test_02_exact_approval_publication_and_retry(self):
        rev = self.stage()
        self.approve({**rev, "revision_hash": "0" * 64}, error="22023")
        self.approve(rev)
        receipt = json.loads(self.publish(rev))
        repeated = json.loads(self.publish(rev))
        self.assertTrue(repeated["replayed"])
        self.assertEqual(receipt["article_id"], repeated["article_id"])
        body = self.sql(f"select body_html from public.articles where id='{receipt['article_id']}';", role="anon")
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn('href="https://example.org/test?a=1&amp;b=2"', body)
        draft = json.loads(self.sql(f"select public.ue_social_draft('{rev['revision_id']}');"))
        self.assertEqual(draft["status"], "review_draft")
        self.assertEqual(self.sql("select count(*) from public.social_posts;", identity=None), "0")
        self.sql(f"update ue_private.revisions set envelope='{{}}' where id='{rev['revision_id']}';", error="42501")

    def test_03_corrections_stale_writes_and_old_retries(self):
        first = self.stage()
        self.approve(first)
        receipt = json.loads(self.publish(first))
        external = first["envelope"]["external_id"]
        corrected = article()
        corrected["title"] = "Reviewed correction"
        second = self.stage(corrected, external, first["revision_hash"])
        competitor = article()
        competitor["title"] = "Competing stale correction"
        stale = self.stage(competitor, external, first["revision_hash"])
        self.approve(second)
        self.approve(stale)
        self.publish(second)
        self.publish(stale, error="40001")
        old = json.loads(self.publish(first))
        self.assertFalse(old["is_current"])
        self.assertEqual(self.sql(f"select title from public.articles where id='{receipt['article_id']}';", role="anon"),
                         "Reviewed correction")
        draft = json.loads(self.sql(f"select public.ue_social_draft('{first['revision_id']}');"))
        self.assertEqual(draft["status"], "superseded")

    def test_04_revocation_and_removed_approver(self):
        rev = self.stage()
        self.approve(rev)
        self.approve(rev, approved=False)
        self.publish(rev, error="42501")
        self.approve(rev)
        self.sql(f"delete from ue_private.members where user_id='{EDITOR}';", identity=None)
        try:
            self.publish(rev, error="42501")
        finally:
            self.sql(f"insert into ue_private.members values ('{EDITOR}', 'editor');", identity=None)

    def test_05_validation_rejects_bad_links_and_missing_evidence(self):
        bad = []
        for url in ["javascript:alert(1)", "https://example.org/\" onclick=\"bad", "https://user:pw@example.org/", "http://example.org/"]:
            p = article(); p["sources"][0]["url"] = url; bad.append(p)
        p = article(); del p["evidence_note"]; bad.append(p)
        p = article(); p["sections"][0]["paragraphs"][0]["source_ids"] = ["absent"]; bad.append(p)
        p = article(); p["sources"].append(copy.deepcopy(p["sources"][0])); bad.append(p)
        p = article(); p["body_html"] = "<script>bad</script>"; bad.append(p)
        p = article(); p["research_as_of"] = "today"; bad.append(p)
        for payload in bad:
            with self.subTest(payload=payload):
                external = "invalid-" + secrets.token_hex(6)
                self.sql(f"select public.ue_stage_revision('{external}', '{external}', null,"
                         f"{literal(json.dumps(payload))}::jsonb);", error="22023")

    def test_06_legacy_slug_is_never_overwritten(self):
        slug = "legacy-" + secrets.token_hex(6)
        self.sql(f"insert into public.articles(title,slug) values ('Legacy', '{slug}');", identity=None)
        self.sql(f"select public.ue_stage_revision('{slug}', '{slug}', null,"
                 f"{literal(json.dumps(article()))}::jsonb);", error="23505")

    def test_07_simultaneous_publish_is_idempotent(self):
        rev = self.stage()
        self.approve(rev)
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(executor.map(lambda _: json.loads(self.publish(rev)), [1, 2]))
        self.assertEqual(sum(r["replayed"] for r in receipts), 1)
        self.assertEqual(receipts[0]["article_id"], receipts[1]["article_id"])

    def test_08_withdrawal_blocks_retries_and_queued_corrections(self):
        first = self.stage()
        self.approve(first)
        receipt = json.loads(self.publish(first))
        corrected = article(); corrected["title"] = "Replacement after explicit review"
        second = self.stage(corrected, first["envelope"]["external_id"], first["revision_hash"])
        self.approve(second)
        withdraw = (f"select public.ue_withdraw_revision('{first['revision_id']}',"
                    f"'{first['revision_hash']}', 'Synthetic withdrawal reason');")
        self.sql(withdraw, identity=PUBLISHER, error="42501")
        self.sql(withdraw, role="anon", error="42501")
        self.sql(withdraw.replace(first["revision_hash"], "0" * 64), error="22023")
        self.assertFalse(json.loads(self.sql(withdraw))["replayed"])
        self.assertTrue(json.loads(self.sql(withdraw))["replayed"])
        self.assertEqual(self.sql(f"select count(*) from public.articles where id='{receipt['article_id']}';", role="anon"), "0")
        retried = json.loads(self.publish(first))
        self.assertTrue(retried["withdrawn"])
        self.assertFalse(retried["is_current"])
        self.publish(second, error="40001")
        draft = json.loads(self.sql(f"select public.ue_social_draft('{first['revision_id']}');"))
        self.assertEqual(draft["status"], "withdrawn")
        self.approve(second, error="40001")
        # Restaging changes the database-bound review epoch even for identical text.
        restored = self.stage(corrected, first["envelope"]["external_id"], first["revision_hash"])
        self.assertNotEqual(restored["revision_hash"], second["revision_hash"])
        self.approve(restored)
        replacement = json.loads(self.publish(restored))
        self.assertEqual(replacement["article_id"], receipt["article_id"])
        self.sql(withdraw, error="40001")
        self.assertEqual(self.sql(f"select title from public.articles where id='{receipt['article_id']}';", role="anon"), corrected["title"])

    def test_09_editor_and_publisher_memberships_cannot_overlap(self):
        self.sql(f"insert into ue_private.members values ('{EDITOR}', 'publisher');", identity=None, error="23505")


if __name__ == "__main__":
    unittest.main()

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from pipeline.publisher import NoRedirect, Publisher, PublishingError, main


class AdapterTests(unittest.TestCase):
    def setUp(self):
        # Transport tests are mocked; creating a real TLS context is unnecessary.
        patcher = patch("pipeline.publisher.build_opener")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_never_falls_back_to_service_key(self):
        with patch.dict("os.environ", {"SUPABASE_SERVICE_ROLE_KEY": "synthetic-forbidden"}, clear=True):
            with self.assertRaises(PublishingError):
                Publisher.from_environment()

    def test_rejects_unsafe_origins(self):
        for origin in ["http://example.com", "https://user:secret@example.com", "https://example.com/path",
                       "https://example.com?token=secret", "https://example.com#fragment"]:
            with self.subTest(origin=origin), self.assertRaises(PublishingError):
                Publisher(origin, "test-public-key", "test-user-token")

    def test_never_forwards_auth_to_redirect(self):
        with self.assertRaises(PublishingError):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.example")

    def test_exact_revision_request(self):
        publisher = Publisher("https://test.example", "public-test", "token-test")
        with patch.object(publisher.opener, "open") as opener:
            opener.return_value.__enter__.return_value.read.return_value = b'{"is_current":true}'
            result = publisher.publish("11111111-1111-1111-1111-111111111111", "a" * 64)
            request = opener.call_args.args[0]
            self.assertEqual(request.full_url, "https://test.example/rest/v1/rpc/ue_publish_revision")
            self.assertEqual(json.loads(request.data)["p_revision_hash"], "a" * 64)
            self.assertTrue(result["is_current"])

    def test_error_does_not_leak_response_or_url(self):
        publisher = Publisher("https://test.example", "public-test", "token-test")
        with patch.object(publisher.opener, "open", side_effect=HTTPError(
                "https://secret.example", 403, "secret text", {}, io.BytesIO(b"secret response"))):
            with self.assertRaisesRegex(PublishingError, "HTTP 403") as caught:
                publisher.review("11111111-1111-1111-1111-111111111111")
            self.assertNotIn("secret", str(caught.exception))

    def test_cli_requires_explicit_action(self):
        with patch("pipeline.publisher.Publisher.from_environment") as connect, patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main([])
            self.assertEqual(caught.exception.code, 2)
            connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()

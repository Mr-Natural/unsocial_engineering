import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from pipeline.publisher import PublishingError
from pipeline.savvyhub import deliver, read_export


class HubTransportTests(unittest.TestCase):
    def test_changed_export_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'export.json'
            path.write_text('{}', encoding='utf-8')
            with self.assertRaises(PublishingError):
                read_export(path, '0' * 64)

    def test_delivery_only_stages_same_stable_item(self):
        package = dict(format='savvyhub-unsocial-draft-v1', destination='unsocialengineering.com',
                       hub_item_id='synthetic-1', slug='synthetic-story', base_hash=None, article={'title': 'Synthetic'})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'export.json'
            raw = json.dumps(package).encode()
            path.write_bytes(raw)
            loaded = read_export(path, hashlib.sha256(raw).hexdigest())
        transport = Mock()
        deliver(loaded, transport)
        self.assertEqual([call[0] for call in transport.mock_calls], ['stage'])
        transport.stage.assert_called_once_with('savvyhub:synthetic-1', 'synthetic-story', package['article'], None)

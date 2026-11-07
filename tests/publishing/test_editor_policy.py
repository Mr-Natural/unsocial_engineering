import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


class EditorPolicyTests(unittest.TestCase):
    def test_high_model_score_cannot_publish_even_with_legacy_flag(self):
        db = MagicMock()
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": "test-draft", "slug": "test", "status": "draft", "source_urls": []}]
        model = MagicMock()
        model.messages.create.return_value.content = [SimpleNamespace(type="tool_use", input={
            "ai_confidence": 100, "legal_risk": False, "issues": [], "editor_notes": "Synthetic review"})]
        config = SimpleNamespace(config=SimpleNamespace(auto_publish=True, confidence_threshold=85, claude_model="synthetic"),
                                 get_supabase=lambda: db, get_anthropic=lambda: model)
        path = Path(__file__).resolve().parents[2] / "pipeline" / "editor.py"
        spec = importlib.util.spec_from_file_location("editor_under_test", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"pipeline.config": config, "pipeline.fetch": SimpleNamespace(fetch_text=lambda _: "")}):
            spec.loader.exec_module(module)
            result = module.run("test-draft")
        self.assertEqual(result["status"], "review")
        self.assertNotIn("published_at", result)
        db.table.return_value.select.return_value.eq.assert_called_with("status", "draft")
        db.table.return_value.update.return_value.eq.return_value.eq.assert_called_with("status", "draft")

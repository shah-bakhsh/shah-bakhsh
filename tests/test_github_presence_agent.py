import datetime as dt
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts/github_presence_agent.py"
spec = importlib.util.spec_from_file_location("presence", SOURCE)
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

class PresenceTests(unittest.TestCase):
    def test_editorial_calendar(self):
        self.assertEqual(len(agent.TOPICS), 7)
        self.assertEqual(agent.TOPICS[2][0], "Low-resource NLP")

    def test_source_linked_post(self):
        body = agent.fallback_post(dt.date(2026, 11, 10), "Agentic AI",
            [{"type": "Paper", "title": "Example", "url": "https://arxiv.org/abs/1234.5678",
              "date": "2026-11-09", "note": "An example source."}])
        self.assertIn("https://arxiv.org/abs/1234.5678", body)
        self.assertIn("not a claim", body.lower())
        self.assertIn("Questions for AI developers", body)

    def test_authored_content_never_claims_personal_testing(self):
        body = agent.fallback_post(dt.date(2026, 11, 10), "AI", [])
        self.assertIn("not a claim", body)

    def test_duplicate_day_no_api_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            old = agent.ROOT
            agent.ROOT = pathlib.Path(temp)
            try:
                state = agent.ROOT / "docs/presence/state/2026-11-10.json"
                state.parent.mkdir(parents=True)
                state.write_text("{}")
                with patch.object(agent, "sources_for") as mocked:
                    agent.main(dt.date(2026, 11, 10))
                    mocked.assert_not_called()
            finally:
                agent.ROOT = old

    def test_no_sources_must_fail(self):
        with patch.object(agent, "fetch", side_effect=OSError("Offline")):
            with self.assertRaises(OSError):
                agent.sources_for("cs.AI", "example/repo")

if __name__ == "__main__":
    unittest.main()

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

    def test_gemini_successful_generated_post(self):
        source = {"type": "Official release", "title": "Test release",
                  "url": "https://github.com/example/repo/releases/tag/v1",
                  "date": "2026-11-10", "note": "A verified source."}
        draft = "# AI engineering\n\n" + ("Useful technical detail. " * 65)
        draft += "\nSource: " + source["url"]
        with patch.dict(agent.os.environ, {"GEMINI_API_KEY": "fake-test-key"}), \
                patch.object(agent, "gemini_generate", return_value=draft):
            body, mode = agent.write_post(dt.date(2026, 11, 10), "AI", [source])
        self.assertEqual(mode, "gemini-ai-assisted")
        self.assertIn("AI-assisted technical commentary", body)

    def test_gemini_fails_safely_without_valid_citations(self):
        source = {"type": "Official release", "title": "Test release",
                  "url": "https://github.com/example/repo/releases/tag/v1",
                  "date": "2026-11-10", "note": "Verified."}
        draft = ("Detailed prose about AI. " * 70) + "https://invalid.example/"
        with patch.dict(agent.os.environ, {"GEMINI_API_KEY": "fake-test-key"}), \
                patch.object(agent, "gemini_generate", return_value=draft):
            body, mode = agent.write_post(dt.date(2026, 11, 10), "AI", [source])
        self.assertEqual(mode, "source-linked")
        self.assertIn(source["url"], body)

    def test_gemini_request_shape_and_header(self):
        import io
        source = {"date": "2026-11-10", "topic": "AI", "sources": []}
        fake_response = {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}
        class Response:
            def __enter__(self):
                return io.BytesIO(json.dumps(fake_response).encode())
            def __exit__(self, *args):
                return False
        import json
        def check_request(request, timeout):
            self.assertEqual(request.get_header("X-goog-api-key"), "fake-test-key")
            self.assertIn("gemini-2.5-flash:generateContent", request.full_url)
            self.assertEqual(request.get_method(), "POST")
            return Response()
        with patch.dict(agent.os.environ,
                        {"GEMINI_API_KEY": "fake-test-key", "GEMINI_MODEL": "gemini-2.5-flash"}), \
                patch.object(agent.urllib.request, "urlopen", side_effect=check_request):
            self.assertEqual(agent.gemini_generate("Instructions", source), "hello")

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

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gino_os_bot", ROOT / "scripts/gino_os_bot.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ISSUE = {
    "id": 1542,
    "number": 9,
    "title": "[GINO.OS] Ask about testing",
    "body": "### Your question\n\nWhat has Gino worked on with Playwright?\n\n### Privacy confirmation\n\n- [x] I understand this is public.",
    "user": {"login": "alice"},
}


class KnowledgeTests(unittest.TestCase):
    def test_verified_qa_answer(self):
        reply = mod.build_reply("What has Gino worked on with Playwright?", env={})
        self.assertIn("Playwright", reply)
        self.assertIn("References", reply)
        self.assertIn("Verified portfolio knowledge", reply)

    def test_no_hallucinated_years(self):
        reply = mod.build_reply("How many years of experience does Gino have?", env={})
        self.assertIn("don't have verified information", reply)

    def test_ai_claims_remain_distinct(self):
        reply = mod.build_reply("What is Gino exploring in AI, MCP and Claude Code?", env={})
        self.assertIn("exploring", reply)
        self.assertIn("MCP", reply)

    def test_hot_swapped_project_appears_in_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config/profile_knowledge.json").write_text(json.dumps({"facts": []}), encoding="utf-8")
            (root / "config/projects.json").write_text(json.dumps({
                "featured": ["wardrove"],
                "catalog": {"wardrove": {
                    "title": "Wardrove Backend", "url": "https://github.com/gino23odar/myFit",
                    "description": "Spring Boot, Flyway and PostgreSQL backend prototype.",
                    "tags": ["SPRING BOOT"], "flow": ["API", "DATABASE"]
                }}
            }), encoding="utf-8")
            facts = mod.load_knowledge(root)
            self.assertEqual(1, len(facts))
            self.assertIn("Wardrove", mod.deterministic_answer("Wardrove Spring Boot", facts)[0])

    def test_out_of_scope_question_falls_back(self):
        reply = mod.build_reply("Do you sell vintage cars?", env={})
        self.assertIn("don't have verified information", reply)


class EventTests(unittest.TestCase):
    def test_issue_submit(self):
        question, request_id = mod.evaluate_event("issues", {"issue": ISSUE}, [], "gino23odar")
        self.assertEqual("What has Gino worked on with Playwright?", question)
        self.assertEqual("issue:1542", request_id)

    def test_irrelevant_issue_ignored(self):
        issue = dict(ISSUE, title="Bug report")
        self.assertEqual((None, None), mod.evaluate_event("issues", {"issue": issue}, [], "gino23odar"))

    def test_issue_form_required(self):
        issue = dict(ISSUE, body="Plain issue body")
        self.assertEqual((None, None), mod.evaluate_event("issues", {"issue": issue}, [], "gino23odar"))

    def test_follow_up_by_author(self):
        comment = {"id": 123, "body": "/ask What about Jenkins?", "user": {"login": "alice", "type": "User"}}
        question, marker = mod.evaluate_event("issue_comment", {"issue": ISSUE, "comment": comment}, [comment], "gino23odar")
        self.assertEqual("What about Jenkins?", question)
        self.assertEqual("comment:123", marker)

    def test_others_cannot_append_followup(self):
        comment = {"id": 123, "body": "/ask What about Jenkins?", "user": {"login": "random", "type": "User"}}
        self.assertEqual((None, None), mod.evaluate_event("issue_comment", {"issue": ISSUE, "comment": comment}, [comment], "gino23odar"))

    def test_no_bot_echo(self):
        comment = {"id": 123, "body": "/ask trick", "user": {"login": "github-actions[bot]", "type": "Bot"}}
        self.assertEqual((None, None), mod.evaluate_event("issue_comment", {"issue": ISSUE, "comment": comment}, [comment], "gino23odar"))

    def test_followup_limit(self):
        comment = {"id": 4, "body": "/ask fourth", "user": {"login": "alice", "type": "User"}}
        comments = [{"body": "/ask earlier"}] * 3 + [comment]
        self.assertEqual((None, None), mod.evaluate_event("issue_comment", {"issue": ISSUE, "comment": comment}, comments, "gino23odar"))

    def test_questions_limited(self):
        issue = dict(ISSUE, body="### Your question\n\n" + "x" * 601)
        self.assertEqual((None, None), mod.evaluate_event("issues", {"issue": issue}, [], "gino23odar"))

    def test_pull_requests_ignored(self):
        issue = dict(ISSUE, pull_request={"url": "https://api.github.com/a"})
        self.assertEqual((None, None), mod.evaluate_event("issues", {"issue": issue}, [], "gino23odar"))

    def test_static_response_without_external_api(self):
        with patch.object(mod, "ai_answer", side_effect=AssertionError("Must not call model")):
            mod.build_reply("Playwright", env={"GINO_OS_AI_ENABLED": "false", "OPENAI_API_KEY": "ignored"})


class WorkflowSmokeTests(unittest.TestCase):
    def test_issue_posts_answer_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps({"issue": ISSUE}), encoding="utf-8")
            api_calls = []

            def fake_api(method, path, token, payload=None):
                api_calls.append((method, path, payload))
                return [] if method == "GET" else {"id": 1}

            env = {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_EVENT_NAME": "issues",
                "GITHUB_REPOSITORY": "gino23odar/gino23odar",
                "GITHUB_TOKEN": "test-only-token",
            }
            with patch.dict("os.environ", env, clear=True), patch.object(mod, "github_api", side_effect=fake_api):
                self.assertEqual(0, mod.run())
            self.assertEqual(["GET", "POST"], [x[0] for x in api_calls])
            self.assertIn("gino-os:answered:issue:1542", api_calls[-1][2]["body"])
            self.assertIn("Playwright", api_calls[-1][2]["body"])

    def test_existing_answer_is_not_reposted(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps({"issue": ISSUE}), encoding="utf-8")
            with patch.dict("os.environ", {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_EVENT_NAME": "issues",
                "GITHUB_REPOSITORY": "gino23odar/gino23odar",
                "GITHUB_TOKEN": "test-only-token"
            }, clear=True), patch.object(mod, "github_api", return_value=[{
                "body": "previous response <!-- gino-os:answered:issue:1542 -->"
            }]) as api:
                self.assertEqual(0, mod.run())
                self.assertEqual(1, api.call_count)


if __name__ == "__main__":
    unittest.main()

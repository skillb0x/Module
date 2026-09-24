"""Smoke-Tests der Hook-Entwuerfe mit Beispiel-Eingaben aus https://code.claude.com/docs/en/hooks.

Laeuft isoliert in einem Temp-Projekt (CLAUDE_PROJECT_DIR), beruehrt das echte Archiv nicht.
Aufruf: python3 -m unittest research/2026-09_setup-skript/cc-hooks/test_cc_hooks.py
Beweist nur Skriptverhalten (stdin->stdout/exit/Dateien), NICHT das Laden durch Claude Code.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks")


def run(script, payload, root):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=root)
    env.pop("CLAUDE_CODE_REMOTE_SESSION_ID", None)
    p = subprocess.run([sys.executable, os.path.join(HOOKS, script)], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=30)
    return p.returncode, p.stdout, p.stderr


def base(root, event, **kw):
    d = {"session_id": "abc123", "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
         "transcript_path": "/tmp/x.jsonl", "cwd": root, "permission_mode": "default",
         "hook_event_name": event}
    d.update(kw)
    return d


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_prompt_archived_verbatim_no_stdout_and_dedup(self):
        text = 'Umlaute äöü, "Quotes", $(rm -rf /) `x`\nZeile2'
        payload = base(self.root, "UserPromptSubmit", prompt=text)
        for _ in range(2):
            code, out, _ = run("archive_prompt.py", payload, self.root)
            self.assertEqual((code, out), (0, ""))
        with open(os.path.join(self.root, "archive/chat/messages.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        self.assertEqual(len(rows), 1)  # Dedup ueber prompt_id+sha256
        self.assertEqual(rows[0]["text"], text)
        self.assertRegex(rows[0]["id"], r"^MSG-\d{4}-\d\d-\d\d-001$")

    def test_prompt_unwritable_reports_nicht_gespeichert(self):
        os.makedirs(os.path.join(self.root, "archive"))
        open(os.path.join(self.root, "archive", "chat"), "w").close()  # Datei statt Ordner
        code, out, _ = run("archive_prompt.py", base(self.root, "UserPromptSubmit", prompt="x"), self.root)
        self.assertEqual(code, 0)
        self.assertIn("NICHT_GESPEICHERT", json.loads(out)["systemMessage"])

    def test_stop_record_from_last_assistant_message(self):
        payload = base(self.root, "Stop", stop_hook_active=False,
                       last_assistant_message="Fertig.", background_tasks=[], session_crons=[])
        code, out, _ = run("output_record.py", payload, self.root)
        self.assertEqual((code, out), (0, ""))
        with open(os.path.join(self.root, "archive/outputs/records.jsonl"), encoding="utf-8") as fh:
            rec = json.loads(fh.readline())
        self.assertEqual((rec["text"], rec["status"], rec["event"]), ("Fertig.", "RAW", "Stop"))

    def _guard(self, tool, tool_input):
        code, out, err = run("guard.py", base(self.root, "PreToolUse", tool_name=tool,
                                               tool_input=tool_input, tool_use_id="toolu_1"), self.root)
        self.assertEqual(code, 0, err)
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None

    def test_guard_decisions(self):
        a = os.path.join(self.root, "archive/chat/messages.jsonl")
        self.assertEqual(self._guard("Write", {"file_path": a, "content": "x"}), "deny")
        self.assertEqual(self._guard("Edit", {"file_path": a, "old_string": "a", "new_string": "b"}), "deny")
        self.assertEqual(self._guard("Read", {"file_path": os.path.join(self.root, ".env")}), "deny")
        self.assertIsNone(self._guard("Read", {"file_path": os.path.join(self.root, ".env.example")}))
        self.assertEqual(self._guard("Bash", {"command": "rm -f archive/chat/messages.jsonl"}), "deny")
        self.assertEqual(self._guard("Bash", {"command": "echo x > ./archive/chat/m.jsonl"}), "deny")
        self.assertEqual(self._guard("Bash", {"command": "cat .env"}), "deny")
        self.assertIsNone(self._guard("Bash", {"command": "cat archive/chat/messages.jsonl"}))
        self.assertIsNone(self._guard("Write", {"file_path": os.path.join(self.root, "docs/a.md"), "content": "x"}))
        reg = os.path.join(self.root, "registry", "modules.approved.json")
        os.makedirs(os.path.dirname(reg))
        open(reg, "w").close()
        self.assertEqual(self._guard("Write", {"file_path": reg, "content": "{}"}), "ask")
        cfg = os.path.join(self.root, ".claude", "settings.json")
        self.assertEqual(self._guard("Edit", {"file_path": cfg, "old_string": "a", "new_string": "b"}), "ask")
        self.assertEqual(self._guard("Bash", {"command": "rm .claude/hooks/guard.py"}), "ask")

    def test_guard_symlink_into_archive_is_denied(self):
        os.makedirs(os.path.join(self.root, "archive"))
        link = os.path.join(self.root, "harmlos")
        os.symlink(os.path.join(self.root, "archive"), link)
        self.assertEqual(self._guard("Write", {"file_path": os.path.join(link, "x.jsonl"), "content": "x"}), "deny")

    def test_guard_bad_input_fails_closed(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        p = subprocess.run([sys.executable, os.path.join(HOOKS, "guard.py")], input="kein json",
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 2)

    def test_index_journal_hashes_written_file(self):
        f = os.path.join(self.root, "docs", "a.md")
        os.makedirs(os.path.dirname(f))
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("hallo")
        payload = base(self.root, "PostToolUse", tool_name="Write",
                       tool_input={"file_path": f, "content": "hallo"},
                       tool_response={"filePath": f, "type": "create"}, tool_use_id="toolu_2")
        code, out, _ = run("index_journal.py", payload, self.root)
        self.assertEqual((code, out), (0, ""))
        with open(os.path.join(self.root, "index/journal.jsonl"), encoding="utf-8") as fh:
            rec = json.loads(fh.readline())
        self.assertEqual(rec["pfad"], os.path.join("docs", "a.md"))
        self.assertEqual(rec["sha256"], "d3751d33f9cd5049c4af2b462735457e4d3baf130bcbb87f389e349fbaeb20b9")

    def test_session_context_reports_hash_mismatch(self):
        p = os.path.join(self.root, "archive/chat/messages.jsonl")
        os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "MSG-1", "text": "a", "sha256": "falsch"}) + "\n")
        code, out, _ = run("session_context.py", base(self.root, "SessionStart", source="startup"), self.root)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(code, 0)
        self.assertIn("Hash-Abweichungen: MSG-1", ctx)
        self.assertLess(len(ctx), 10000)


if __name__ == "__main__":
    unittest.main()

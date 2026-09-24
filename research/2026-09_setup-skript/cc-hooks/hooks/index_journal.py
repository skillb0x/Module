#!/usr/bin/env python3
"""PostToolUse-Hook: Hash-/Index-Journal nach Datei-Aenderungen.

Status: PREPARED (Entwurf, nicht aktiviert).
Matcher-Vorschlag: "Write|Edit|NotebookEdit|Bash"; async: true (blockiert Claude nicht).
Schreibt nur ein Ereignis-Journal (Wahrheit = Journal + Datei-Hash); das lesbare
Inventar wird daraus von einem Tool ERZEUGT (keine zweite Wahrheit).
Bash: nutzt tool_response.bashEditDiff.changedFiles, falls vorhanden (Public Beta,
best effort, v2.1.269+); sonst kein Eintrag -> Abgleich per git status/Tool noetig.
Quelle: https://code.claude.com/docs/en/hooks#posttooluse-input , #bash
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

JOURNAL_REL = os.path.join("index", "journal.jsonl")
SKIP_PREFIXES = (".git" + os.sep, "index" + os.sep)


def changed_paths(data):
    tool = data.get("tool_name")
    tin = data.get("tool_input") or {}
    if tool in ("Write", "Edit", "NotebookEdit"):
        p = tin.get("file_path") or tin.get("notebook_path")
        return [p] if p else []
    if tool == "Bash":
        diff = (data.get("tool_response") or {}).get("bashEditDiff") or {}
        return list(diff.get("changedFiles") or [])
    return []


def main():
    data, err = c.read_input()
    if err:
        return 0
    root = c.project_root(data)
    ts = c.now_utc().isoformat(timespec="seconds")
    journal = os.path.join(root, JOURNAL_REL)
    for raw in changed_paths(data):
        path = os.path.realpath(raw.replace("\\", "/"))
        if not path.startswith(root + os.sep):
            continue
        rel = os.path.relpath(path, root)
        if rel.startswith(SKIP_PREFIXES):
            continue
        exists = os.path.isfile(path)
        digest, size = c.sha256_file(path) if exists else (None, None)
        rec = {"ts": ts, "event": "PostToolUse", "tool": data.get("tool_name"),
               "tool_use_id": data.get("tool_use_id"), "pfad": rel, "existiert": exists,
               "sha256": digest, "bytes": size,
               "session": c.remote_session_url_id() or data.get("session_id"),
               "prompt_id": data.get("prompt_id"), "agent_id": data.get("agent_id")}
        try:
            c.append_jsonl_locked(journal, lambda _lines, r=rec: r)
        except Exception as exc:  # noqa: BLE001
            # async: additionalContext/systemMessage gehen erst im naechsten Turn an Claude
            c.emit({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                    "additionalContext": "Index-Journal NICHT_GESPEICHERT fuer %s (%s)."
                                         % (rel, exc.__class__.__name__)}})
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

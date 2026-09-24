#!/usr/bin/env python3
"""UserPromptSubmit-Hook: Nutzernachricht wortgetreu, append-only archivieren.

Status: PREPARED (Entwurf, nicht in .claude/settings.json aktiviert).
Eingabe (offiziell): common fields + "prompt"; Quelle https://code.claude.com/docs/en/hooks#userpromptsubmit-input
Ausgabe: Erfolg -> KEIN stdout (Plaintext-stdout wuerde als Kontext injiziert).
Fehler -> JSON systemMessage + additionalContext "NICHT_GESPEICHERT", exit 0
(Prompt wird nicht blockiert; Nutzerregel: fehlender Schreibweg wird gemeldet).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

ARCHIVE_REL = os.path.join("archive", "chat", "messages.jsonl")


def main():
    data, err = c.read_input()
    if err:
        return fail("Hook-Eingabe: " + err)
    text = data.get("prompt")
    if not isinstance(text, str):
        return fail("Feld 'prompt' fehlt")
    root = c.project_root(data)
    path = os.path.join(root, ARCHIVE_REL)
    ts = c.now_utc()
    digest = c.sha256_text(text)

    def build(lines):
        return {
            "id": c.next_daily_id(lines, "MSG", ts.date().isoformat()),
            "datum": ts.date().isoformat(),
            "zeit": ts.strftime("%H:%M:%SZ"),
            "rolle": "user",
            "session": c.remote_session_url_id() or data.get("session_id"),
            "cc_session_id": data.get("session_id"),
            "prompt_id": data.get("prompt_id"),
            "agent_id": data.get("agent_id"),
            "kontext": "hook:UserPromptSubmit",
            "text": text,
            "sha256": digest,
        }

    try:
        c.append_jsonl_locked(
            path,
            build,
            # prompt_id + Hash: verhindert Doppelablage bei erneutem Feuern/Resume.
            dedup_key=lambda r: (r.get("prompt_id"), r.get("sha256")) if r.get("prompt_id") else None,
        )
    except Exception as exc:  # noqa: BLE001
        return fail("Schreiben %s: %s" % (ARCHIVE_REL, exc.__class__.__name__))
    return 0


def fail(reason):
    c.emit({
        "systemMessage": "Archiv NICHT_GESPEICHERT (%s)" % reason,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "Archivstatus dieser Nutzernachricht: NICHT_GESPEICHERT (%s)." % reason,
        },
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())

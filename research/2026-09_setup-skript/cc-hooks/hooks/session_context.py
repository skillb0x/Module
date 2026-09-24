#!/usr/bin/env python3
"""SessionStart-Hook: Stand laden und Folgeprompt-Kontext einspeisen.

Status: PREPARED (Entwurf, nicht aktiviert).
Matcher-Vorschlag: "startup|resume|clear|compact" (compact = nach Kompaktierung erneut einspeisen).
Ausgabe: hookSpecificOutput.additionalContext (max. 10.000 Zeichen, sonst Datei+Vorschau).
Text als Fakten formulieren, nicht als "System-Anweisung" (Prompt-Injection-Abwehr).
Prueft nebenbei die Hash-Integritaet des Roharchivs (sha256 je Eintrag).
Quelle: https://code.claude.com/docs/en/hooks#sessionstart-decision-control ,
        https://code.claude.com/docs/en/hooks#add-context-for-claude
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

LIMIT = 9000  # Puffer unter der 10.000-Zeichen-Grenze
POINTERS = ["README.md", "CLAUDE.md", "registry/modules.approved.json",
            "archive/chat/messages.jsonl", "archive/outputs/records.jsonl", "index/journal.jsonl"]


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    out.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    out.append({"_parse_error": True})
    except FileNotFoundError:
        return None
    return out


def main():
    data, err = c.read_input()
    root = c.project_root(data or {})
    lines = ["Projektstand (automatisch geladen, Quelle: .claude/hooks/session_context.py):"]
    lines.append("Quelle der Sitzung: %s" % (data or {}).get("source", "UNKNOWN"))
    for rel in POINTERS:
        lines.append("- %s: %s" % (rel, "vorhanden" if os.path.exists(os.path.join(root, rel)) else "fehlt"))

    msgs = read_jsonl(os.path.join(root, "archive", "chat", "messages.jsonl"))
    if msgs is not None:
        bad = [m.get("id", "?") for m in msgs
               if m.get("_parse_error") or c.sha256_text(m.get("text", "")) != m.get("sha256")]
        lines.append("Roharchiv: %d Nachrichten, Hash-Abweichungen: %s"
                     % (len(msgs), ", ".join(bad) if bad else "keine"))

    recs = read_jsonl(os.path.join(root, "archive", "outputs", "records.jsonl")) or []
    open_todos = [t for r in recs for t in (r.get("todos") or [])]
    last = [r for r in recs if r.get("naechster_schritt")][-3:]
    if last:
        lines.append("Letzte naechste Schritte laut OutputRecords:")
        lines += ["- %s: %s" % (r.get("id"), r.get("naechster_schritt")) for r in last]
    lines.append("Offene TODOs in OutputRecords: %d" % len(open_todos))
    if err:
        lines.append("Hinweis: Hook-Eingabe unlesbar (%s)." % err)

    text = "\n".join(lines)[:LIMIT]
    c.emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}})
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Stop/SubagentStop/StopFailure-Hook: OutputRecord-Rohsatz aus last_assistant_message.

Status: PREPARED (Entwurf, nicht aktiviert).
Offiziell: last_assistant_message = Textinhalt der finalen Antwort; transcript_path kann
zum Stop-Zeitpunkt nachhinken -> Transcript NICHT parsen (enthaelt u.a. thinking-Bloecke).
Quelle: https://code.claude.com/docs/en/hooks#stop-input
Blockiert nie (exit 0, kein decision:block) -> keine Stop-Schleifen.
Strukturfelder (Entscheidungen, TODOs ...) bleiben leer/RAW und werden spaeter
von Agent/Tool befuellt (keine Heuristik, nichts erfinden).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

OUT_REL = os.path.join("archive", "outputs", "records.jsonl")


def main():
    data, err = c.read_input()
    if err:
        return 0  # Stop darf nicht an einem Log-Fehler haengen
    event = data.get("hook_event_name", "Stop")
    text = data.get("last_assistant_message") or ""
    ts = c.now_utc()
    root = c.project_root(data)

    def build(lines):
        return {
            "id": c.next_daily_id(lines, "OUT", ts.date().isoformat()),
            "ts": ts.isoformat(timespec="seconds"),
            "event": event,
            "session": c.remote_session_url_id() or data.get("session_id"),
            "cc_session_id": data.get("session_id"),
            "prompt_id": data.get("prompt_id"),
            "agent_id": data.get("agent_id"),
            "agent_type": data.get("agent_type"),
            "stop_hook_active": data.get("stop_hook_active"),
            "error": data.get("error"),  # nur StopFailure
            "text": text,
            "sha256": c.sha256_text(text),
            "status": "RAW",
            "projekt": None, "task": None, "run": None,
            "ergebnis": None, "quellen": [], "entscheidungen": [], "aenderungen": [],
            "pruefungen": [], "todos": [], "blocker": [], "naechster_schritt": None,
        }

    try:
        c.append_jsonl_locked(os.path.join(root, OUT_REL), build)
    except Exception as exc:  # noqa: BLE001
        # Stop: systemMessage wird dem Nutzer angezeigt; Claude sieht es nicht.
        c.emit({"systemMessage": "OutputRecord NICHT_GESPEICHERT (%s)" % exc.__class__.__name__})
    return 0


if __name__ == "__main__":
    sys.exit(main())

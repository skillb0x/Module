#!/usr/bin/env python3
"""SessionStart-Hook fuer das Repo "Module"  --  ENTWURF, Status PREPARED (nicht aktiv).

Aktivierung erst nach Freigabe: Datei nach .claude/hooks/ kopieren und in
.claude/settings.json unter hooks.SessionStart eintragen (siehe settings.json.draft).

Zweck (Grundaufgaben): Jeder Folgeagent bekommt beim Start, nach /clear und nach
Kompaktierung eine kurze, echte Verweisliste auf Regeln, Index, Register, Archiv und
Tests sowie einen Integritaetsstatus des Roharchivs -- statt den Stand neu zu bauen.

Eigenschaften:
- nur lesend im Repo; schreibt hoechstens idempotent in $CLAUDE_ENV_FILE
- keine Netzwerkzugriffe, keine Installationen (das gehoert ins Umgebungs-Setup-Skript)
- bricht nie ab: Exit 0 in jedem Fall, Fehler landen als Text im Kontext
- Ausgabe bleibt weit unter der 10.000-Zeichen-Grenze fuer Hook-Kontext
Nur Standardbibliothek (Python >= 3.8).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess
import sys

MAX_CHARS = 4000  # Hook-Kontext ist bei 10.000 Zeichen gedeckelt; wir bleiben deutlich darunter


def read_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError):
        return {}


def git(root: str, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "UNKNOWN"
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


def session_url() -> str:
    sid = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")
    if not sid:
        return ""
    if sid.startswith("cse_"):
        sid = "session_" + sid[len("cse_"):]
    return "https://claude.ai/code/" + sid


def persist_env(name: str, value: str) -> None:
    """Idempotent: Zeile nur anhaengen, wenn sie noch nicht in CLAUDE_ENV_FILE steht."""
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file or not value:
        return
    line = f"export {name}={json.dumps(value)}\n"
    try:
        existing = open(env_file, encoding="utf-8").read() if os.path.exists(env_file) else ""
        if line not in existing:
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(line)
    except OSError:
        pass


def check_archive(path: str) -> str:
    """Prueft Roharchiv (JSONL): parsebar, eindeutige IDs, sha256(text) stimmt."""
    if not os.path.exists(path):
        return "FEHLT"
    n = bad_json = bad_hash = 0
    ids: set[str] = set()
    dup = 0
    last_id = ""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                n += 1
                try:
                    rec = json.loads(line)
                except ValueError:
                    bad_json += 1
                    continue
                rid = str(rec.get("id", ""))
                if rid in ids:
                    dup += 1
                ids.add(rid)
                last_id = rid or last_id
                text = rec.get("text")
                if isinstance(text, str) and rec.get("sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
                    bad_hash += 1
    except OSError as exc:
        return f"NICHT LESBAR ({exc})"
    status = "OK" if not (bad_json or bad_hash or dup) else "FEHLER"
    return f"{status}: {n} Eintraege, letzte ID {last_id or '-'}, JSON-Fehler {bad_json}, Hash-Fehler {bad_hash}, doppelte IDs {dup}"


def main() -> int:
    data = read_input()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    source = data.get("source", "UNKNOWN")
    remote = os.environ.get("CLAUDE_CODE_REMOTE") == "true"
    url = session_url()

    persist_env("MANA_SESSION_URL", url)
    persist_env("PYTHONDONTWRITEBYTECODE", "1")

    def rel_existing(patterns: list[str]) -> list[str]:
        hits: list[str] = []
        for pat in patterns:
            hits += sorted(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, pat), recursive=True))
        return hits

    pointers = {
        "Regeln": rel_existing(["CLAUDE.md", ".claude/CLAUDE.md", ".claude/rules/**/*.md", "AGENTS.md"]),
        "Projektzustand/Index": rel_existing(["README.md", "registry/*.json", "index/*.jsonl", "index/*.json"]),
        "Recherche (Wahrheit)": rel_existing(["research/*/domains"]),
        "Roharchiv": rel_existing(["archive/chat/*.jsonl"]),
        "Kontrollansichten (erzeugt, nie von Hand)": rel_existing(["docs/*.md", "docs/*.xlsx"]),
        "Tests": rel_existing(["tests"]),
    }

    lines = [
        "## Projektstand beim Sessionstart (SessionStart-Hook, automatisch erzeugt)",
        f"- Ausloeser: {source}; Cloud: {'ja' if remote else 'nein'}; Sitzung: {url or 'lokal/UNKNOWN'}",
        f"- Git: Branch {git(root, 'rev-parse', '--abbrev-ref', 'HEAD')}, HEAD {git(root, 'rev-parse', '--short', 'HEAD')}",
        f"- Roharchiv archive/chat/messages.jsonl: {check_archive(os.path.join(root, 'archive', 'chat', 'messages.jsonl'))}",
    ]
    for label, items in pointers.items():
        lines.append(f"- {label}: {', '.join(items) if items else 'NICHT VORHANDEN'}")
    lines.append("- Regel: erst diese Dateien lesen, dann arbeiten; ohne Schreibweg NICHT_GESPEICHERT melden.")

    text = "\n".join(lines)
    if len(text) > MAX_CHARS:
        text = text[: MAX_CHARS - 20] + "\n[... gekuerzt]"
    print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # Hook darf den Sessionstart nie verhindern
        print(f"SessionStart-Hook-Fehler (nicht blockierend): {exc}")
        sys.exit(0)

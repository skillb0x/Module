"""Gemeinsame Helfer fuer die cc-hooks-Entwuerfe. Status: PREPARED (nicht aktiv).

Nur Standardbibliothek. Keine Shell-Aufrufe, kein eval: Hook-Eingaben sind
nicht vertrauenswuerdig (Prompt-Text, Tool-Argumente).
Quelle Eingabe-/Ausgabeformat: https://code.claude.com/docs/en/hooks
"""
import datetime
import fcntl
import hashlib
import json
import os
import sys


def read_input():
    """Liest das Hook-JSON von stdin. Gibt (dict, fehler) zurueck."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "Eingabe ist kein JSON-Objekt"
        return data, None
    except Exception as exc:  # noqa: BLE001
        return None, "Eingabe unlesbar: %s" % exc.__class__.__name__


def project_root(data):
    """CLAUDE_PROJECT_DIR bleibt am Sitzungsstart-Root, 'cwd' folgt cd/Worktree."""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or (data or {}).get("cwd") or os.getcwd()
    return os.path.realpath(root)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path, limit=50 * 1024 * 1024):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            size += len(chunk)
            if size > limit:
                return None, size
            h.update(chunk)
    return h.hexdigest(), size


def remote_session_url_id():
    """Cloud: CLAUDE_CODE_REMOTE_SESSION_ID=cse_... -> session_... (claude.ai-Link).

    Quelle: https://code.claude.com/docs/en/cloud-environments (Link output back to the session).
    """
    sid = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
    if not sid:
        return None
    return "session_" + sid[len("cse_"):] if sid.startswith("cse_") else sid


def append_jsonl_locked(path, build_record, dedup_key=None):
    """Append-only Schreiben unter exklusivem Lock mit fsync.

    build_record(existing_lines) -> dict | None. dedup_key(dict) -> hashable | None.
    Gibt den geschriebenen Datensatz oder None (Duplikat) zurueck.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            lines = fh.read().splitlines()
            record = build_record(lines)
            if record is None:
                return None
            if dedup_key is not None:
                key = dedup_key(record)
                if key is not None:
                    for line in lines:
                        try:
                            if dedup_key(json.loads(line)) == key:
                                return None
                        except Exception:  # noqa: BLE001
                            continue
            fh.seek(0, os.SEEK_END)
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            return record
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def next_daily_id(lines, prefix, day):
    """ID-Schema wie archive/chat/messages.jsonl: <PREFIX>-YYYY-MM-DD-NNN."""
    stem = "%s-%s-" % (prefix, day)
    n = 0
    for line in lines:
        try:
            rid = json.loads(line).get("id", "")
        except Exception:  # noqa: BLE001
            continue
        if isinstance(rid, str) and rid.startswith(stem):
            try:
                n = max(n, int(rid[len(stem):]))
            except ValueError:
                pass
    return "%s%03d" % (stem, n + 1)


def emit(obj):
    """Genau ein JSON-Objekt auf stdout (sonst Parse-/Plaintext-Probleme)."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()

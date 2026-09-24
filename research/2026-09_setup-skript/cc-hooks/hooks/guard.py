#!/usr/bin/env python3
"""PreToolUse-Hook: Schreibschutz Roharchiv, Loesch-/Ueberschreibschutz, Secret-Schutz.

Status: PREPARED (Entwurf, nicht aktiviert).
Matcher-Vorschlag: "Write|Edit|NotebookEdit|Read|Bash|PowerShell"
Offiziell: file_path ist fuer Write/Edit/Read immer absolut (~ und relative Pfade expandiert);
Ausgabe via hookSpecificOutput.permissionDecision "deny" wirkt auch in bypassPermissions.
Quellen: https://code.claude.com/docs/en/hooks#pretooluse-input
         https://code.claude.com/docs/en/hooks-guide#hooks-and-permission-modes
GRENZE: Bash-Pruefung ist Textheuristik (best effort). Harte Grenze nur ueber
permissions.deny + Sandbox (https://code.claude.com/docs/en/permissions#read-and-edit).
Interner Fehler -> exit 2 (fail-closed). Fehlendes python3 -> exit 127 -> fail-OPEN (Doku).
"""
import fnmatch
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402

APPEND_ONLY_DIRS = ["archive"]          # nur Hooks/Tools schreiben, nie Claude-Dateitools
NO_OVERWRITE_DIRS = ["registry"]        # Write auf bestehende Datei -> ask (erwartete Revision pruefen)
# Selbstschutz: Settings-Aenderungen werden live uebernommen (File-Watcher) -> Guard abschaltbar.
CONFIG_PATHS = [os.path.join(".claude", "settings.json"), os.path.join(".claude", "settings.local.json"),
                os.path.join(".claude", "hooks")]
SECRET_GLOBS = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
                ".netrc", "credentials*", "*.kdbx"]
SECRET_ALLOW = [".env.example", ".env.sample"]
FILE_TOOLS_WRITE = {"Write", "Edit", "NotebookEdit"}
DESTRUCTIVE = re.compile(
    r"(\brm\b|\bmv\b|\btruncate\b|\bshred\b|\bsed\s+-i|\bperl\s+-i|\btee\b|\bcp\b|\bdd\b|"
    r"\bgit\s+(rm|mv|checkout|restore|reset|clean|filter-branch|filter-repo)\b|>)")


def decide(decision, reason):
    c.emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": decision,
                                   "permissionDecisionReason": reason}})
    return 0


def under(path, root, rel_dir):
    base = os.path.join(root, rel_dir)
    return path == base or path.startswith(base + os.sep)


def is_secret(path):
    name = os.path.basename(path)
    if name in SECRET_ALLOW:
        return False
    parts = path.replace("\\", "/").split("/")
    return any(fnmatch.fnmatch(name, g) for g in SECRET_GLOBS) or "secrets" in parts


def main():
    data, err = c.read_input()
    if err:
        sys.stderr.write("guard: " + err + "\n")
        return 2
    tool = data.get("tool_name", "")
    tin = data.get("tool_input") or {}
    root = c.project_root(data)

    if tool in FILE_TOOLS_WRITE or tool == "Read":
        raw = tin.get("file_path") or tin.get("notebook_path") or ""
        path = os.path.realpath(raw.replace("\\", "/")) if raw else ""
        if path and is_secret(path):
            return decide("deny", "Secret-Schutz: Zugriff auf %s gesperrt." % os.path.basename(path))
        if tool in FILE_TOOLS_WRITE and path:
            for d in APPEND_ONLY_DIRS:
                if under(path, root, d):
                    return decide("deny", "Roharchiv %s/ ist append-only und wird nur durch Hooks/Tools "
                                          "geschrieben. Aenderung ueber Projektzustand oder neuen Eintrag." % d)
            for d in CONFIG_PATHS:
                if under(path, root, d):
                    return decide("ask", "Aenderung an Hook-/Settings-Konfiguration %s: Nutzerfreigabe noetig." % d)
            if tool == "Write" and os.path.exists(path):
                for d in NO_OVERWRITE_DIRS:
                    if under(path, root, d):
                        return decide("ask", "Ueberschreiben von %s: erwartete Revision/Hash pruefen." % d)
        return 0

    if tool in ("Bash", "PowerShell"):
        cmd = tin.get("command") or ""
        norm = cmd.replace("\\", "/")
        for d in APPEND_ONLY_DIRS:
            if re.search(r"(^|[\s'\"=/])%s/" % re.escape(d), norm) and DESTRUCTIVE.search(norm):
                return decide("deny", "Befehl veraendert/loescht moeglicherweise %s/ (append-only)." % d)
        if ".claude/" in norm and DESTRUCTIVE.search(norm):
            return decide("ask", "Befehl beruehrt moeglicherweise .claude/ (Hooks/Settings): Nutzerfreigabe noetig.")
        for tok in re.split(r"[\s'\";|&<>()]+", norm):
            if tok and is_secret(tok):
                return decide("deny", "Secret-Schutz: Befehl referenziert %s." % os.path.basename(tok))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("guard: interner Fehler %s -> blockiert (fail-closed)\n" % exc.__class__.__name__)
        sys.exit(2)

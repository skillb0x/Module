#!/bin/bash
# Cloud-Umgebungs-Setup-Skript fuer claude.ai/code  --  ENTWURF, Status PREPARED (nicht aktiv).
#
# Wird NICHT aus dem Repo geladen: Inhalt von Hand in das Feld "Setup script" der
# Cloud-Umgebung kopieren (Umgebungsmenue > Edit). Laut Doku gilt:
#   - laeuft als root auf Ubuntu 24.04, bevor Claude Code startet
#   - nur beim Aufbau des Umgebungs-Caches (erste Session, nach Aenderung von Skript/erlaubten
#     Hosts, nach ca. 7 Tagen); Resume fuehrt es nie erneut aus
#   - Exit != 0  => Session startet nicht;  Laufzeit ca. < 5 Minuten halten
#   - Netzwerk nur gemaess Zugriffsstufe (Trusted enthaelt u. a. pypi.org, files.pythonhosted.org,
#     registry.npmjs.org, archive.ubuntu.com, security.ubuntu.com; bei "None" scheitern Installs)
#   - API-Credentials der Umgebung werden an Setup-Requests NICHT angehaengt
#   - Cache ist ein Dateisystem-Snapshot: Installationen bleiben, laufende Prozesse nicht
# Deshalb: nur Werkzeuge installieren, nichts Repo-Spezifisches, keine Geheimnisse, alles
# Nicht-Kritische mit "|| true", unabhaengige Schritte parallel.

set -u
log() { echo "[setup $(date -u +%H:%M:%S)] $*"; }

log "Start (User: $(id -un), $(. /etc/os-release && echo "$PRETTY_NAME"))"

# 1) Systemwerkzeuge, die im Basis-Image fehlen (beobachtet: sqlite3-CLI, shellcheck)
(
  apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends sqlite3 shellcheck
) >/tmp/setup-apt.log 2>&1 &
APT_PID=$!

# 2) Python-Pakete fuer erzeugte Kontrollansichten (Excel) -- optional
( python3 -m pip install --quiet --disable-pip-version-check openpyxl ) >/tmp/setup-pip.log 2>&1 &
PIP_PID=$!

wait "$APT_PID" && log "apt ok" || log "apt fehlgeschlagen (nicht kritisch), siehe /tmp/setup-apt.log"
wait "$PIP_PID" && log "pip ok" || log "pip fehlgeschlagen (nicht kritisch), siehe /tmp/setup-pip.log"

# 3) Nachweis fuer das Protokoll (Status LOADED erst, wenn eine echte Session dies zeigt)
for t in python3 git jq sha256sum sqlite3 shellcheck; do
  command -v "$t" >/dev/null 2>&1 && log "vorhanden: $t" || log "FEHLT: $t"
done
python3 -c "import openpyxl" >/dev/null 2>&1 && log "vorhanden: openpyxl" || log "FEHLT: openpyxl"

log "Ende"
exit 0

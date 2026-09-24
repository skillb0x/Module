# Module – Plattform-Modulrecherche

Projektzustand (Stand 2026-09-24, in Arbeit):

| Bereich | Pfad | Rolle |
|---|---|---|
| Roharchiv | `archive/chat/messages.jsonl` | Nutzernachrichten wortgetreu, append-only, mit SHA-256 |
| Recherche (Wahrheit) | `research/2026-09_modul-scan/domains/*.json` | Kandidaten je Domain inkl. Verifikation, Status PROPOSED |
| Telefon-KI-Recherche | `research/2026-09_telefon-ki/domains/*.json` | Voice-Agent-Module (Anrufe, Kalender, Daten, Website-Aktionen), Status PROPOSED |
| Setup-Recherche | `research/2026-09_setup-skript/` | Setup-Konzept + Entwürfe (PREPARED, nicht aktiv) |
| Freigegebener Katalog | `registry/modules.approved.json` | nur nach ausdrücklicher Freigabe |
| Kontrollansicht | `docs/modulkatalog.md` | erzeugt via `python3 tools/research_catalog.py render` |
| Tests | `tests/` | `python3 -m unittest discover -s tests` |

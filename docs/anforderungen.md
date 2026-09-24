# Anforderungen (aus Nutzernachrichten abgeleitet)

Stand 2026-09-24. Quelle je Zeile = Nachrichten-ID in `archive/chat/messages.jsonl`. Status: PROPOSED (vom Nutzer nicht formal freigegeben), Interpretationen sind als INFERRED markiert.

**Geltungsregel (MSG-007):** Jede Anforderung gilt für ALLE Module in ALLEN Domänen (Website, Datenablage, DMS, Telefonie, Groupware/Outlook/Kalender, Identity/QR-Login, Clients, Suiten, Betrieb, Telefon-/Website-KI, Omnichannel, Setup), sofern die Spalte "Geltung" nichts anderes sagt. Umgebung (REQ-13/14), Sicherheit (REQ-02), Deutsch (REQ-09), Branding (REQ-10) und Integrierbarkeit (REQ-11/12) sind Querschnittskriterien, keine Eigenschaften einzelner Module.

| ID | Anforderung | Geltung | Quelle | Klasse | Prüfung / Evidenz |
|---|---|---|---|---|---|
| REQ-01 | Fertige Module (Reuse vor Neubau) für Websitebau, Datenablage, DMS, Telefonie, Outlook, Kalender | alle Module | MSG-001 | nutzervorgabe | `research/*/domains/*.json`, Feld `empfehlung` |
| REQ-02 | Alles "high-end und secure": aktiv gepflegt, Security-Prozess, SSO (OIDC/SAML), MFA/Passkeys, Verschlüsselung, Audit-Log, EU-Betrieb | alle Module (QS-01) | MSG-001 | nutzervorgabe + INFERRED (Ausprägung) | Felder `sicherheit`, `dsgvo_souveraenitaet`, `verifikation` |
| REQ-03 | QR-Code-Anmeldung für externe Nutzer mit E-Mail-Adresse, optional Konto | Identity; Anbindung aller Module per SSO | MSG-001 | nutzervorgabe | `research/2026-09_modul-scan/konzept_qr-login_oneclick.md` |
| REQ-04 | Desktop-Tool für Upload und Ordner-Sync, alternativ Chrome-Plugin oder Website-Button, mit vorbelegten Infos zur Benutzerumgebung für One-Click-Pfade | Clients; Ziel = Ablage/DMS/Website | MSG-001 | nutzervorgabe | dito, Domain `client` |
| REQ-05 | Setup-Skript, das die Grundaufgaben (Index, Archiv, Register, Tests, OutputRecord, Folgeprompt) unterstützt | Arbeitsumgebung/Repo; später Server-Bootstrap aller Module | MSG-002 | nutzervorgabe + INFERRED (Bedeutung "Grundaufgaben") | `research/2026-09_setup-skript/` |
| REQ-06 | Telefon-KI-Modul, das Websites bedient und Kalender/Daten lesen kann | KI-Modul; liest/schreibt in alle Datenmodule | MSG-003 | nutzervorgabe | `research/2026-09_telefon-ki/` |
| REQ-07 | Ein Assistent für Website-Chat-API und Telefon mit teilweise gemeinsamen Prompts; Telefon außerhalb der Öffnungszeiten; kleine Aufträge aufnehmen und wiedergeben, wenn Rufnummer bekannt oder Anrufer verifiziert | KI-Modul + Website + Telefonie + Ticket/CRM + Identity | MSG-004 | nutzervorgabe | `research/2026-09_omnichannel-sweep/loesungsmuster.md` |
| REQ-08 | Quellen: GitHub, arXiv, On-Premise-Verzeichnisse (awesome-selfhosted u. a.); "openopensourcewebsites.com" als Domain UNKNOWN | alle Recherchen | MSG-004 | nutzervorgabe | `quellen_status` in den Sweep-Dateien |
| REQ-09 | Deutsch-Fokus, mindestens anpassungsfähig (UI, Doku, Sprachmodelle) | alle Module (QS-02) | MSG-004 | nutzervorgabe | Feld `deutsch` |
| REQ-10 | Alle Module brandbar (eigenes Design, White-Label; Lizenz/Trademark erlaubt Entfernung von Herstellerhinweisen) | alle Module (QS-03) | MSG-005 | nutzervorgabe | Feld `branding`, `branding_windows_matrix.md` |
| REQ-11 | Voll integrierbar in eigene Webkonzepte (APIs, SDKs, Embedding ohne iframe-Zwang, Webhooks, SSO) | alle Module (QS-04) | MSG-005 | nutzervorgabe | Feld `schnittstellen` |
| REQ-12 | Voll integrierbar in eigene Software auf Windows-Basis (.NET/OpenAPI, Windows-Client/Dienst, AD/Entra) | alle Module (QS-05) | MSG-005 | nutzervorgabe + INFERRED (Ausprägung) | Feld `integration_windows` |
| REQ-13 | Server: meist Linux, alternativ Windows Server, jeweils mit Docker; eine RTX 3090 (24 GB); dort läuft die GESAMTE Modulsammlung | alle Module (QS-08) | MSG-006, MSG-007 | nutzervorgabe | Feld `docker`, `gpu_vram`; `research/2026-09_umgebungs-fit/` |
| REQ-14 | Nutzer kommen von extern, meist per Browser, auf üblichen Windows- oder Apple-Arbeitsplätzen; Schnittstellen: Daten teilen, Mikrofon, Video, weitere nach Bedarf | alle Module (QS-06, QS-07) | MSG-006, MSG-007 | nutzervorgabe | Felder `browser_only`, `integration_macos` |

## Querschnittskriterien QS-01..QS-08

Jeder Kandidat jeder Domain-Datei trägt diese Felder. Fehlt eines bei einem Kandidaten mit Fit ≥ 3 oder auf der Shortlist, meldet `tools/research_catalog.py validate` eine Warnung und die Kontrollansicht zeigt die Lücke ("QS x/8"). Ein fehlendes Feld bedeutet "nicht geprüft", niemals "erfüllt".

| QS | Feld | Frage an jedes Modul | Aus |
|---|---|---|---|
| QS-01 | `sicherheit` | Pflege, Security-Prozess/Advisories, SSO, MFA/Passkeys, Verschlüsselung, Audit-Log, EU-Betrieb | REQ-02 |
| QS-02 | `deutsch` | UI/Doku/Sprachmodelle auf Deutsch oder anpassbar | REQ-09 |
| QS-03 | `branding` | White-Label technisch (Theme, Logo, Domain, Clients) und lizenzrechtlich (Trademark, "powered by", AGPL-Zusätze, Enterprise-only) | REQ-10 |
| QS-04 | `schnittstellen` | APIs/SDKs/Webhooks/SSO für die Einbettung in eigene Webkonzepte | REQ-11 |
| QS-05 | `integration_windows` | .NET-SDK oder OpenAPI, Windows-Client/-Dienst, AD/Entra, Verteilung (MSIX/Winget/Intune) | REQ-12 |
| QS-06 | `integration_macos` | macOS/iOS-Clients, Safari-Tauglichkeit, CalDAV/CardDAV nativ, Notarisierung | REQ-14 |
| QS-07 | `browser_only` | Für externe Nutzer ohne Installation nutzbar (Chrome/Edge/Safari), inkl. Mikro/Video/Upload | REQ-14 |
| QS-08 | `docker` | Offizielles Linux-Container-Image/Compose, Betrieb auf dem Docker-Host, GPU-Bedarf gegen 24 GB RTX 3090, Windows-Server-Fähigkeit | REQ-13 |

## Zielumgebung (MSG-006), gilt für alle Module

| Ebene | Vorgabe | Konsequenz (INFERRED) |
|---|---|---|
| Server | Linux oder Windows Server, Docker, eine NVIDIA RTX 3090 (24 GB) | Alle Serverkomponenten als Linux-Container auf einem Host; die GPU wird von allen KI-Lasten geteilt (Sprache, OCR/Klassifikation im DMS, Embeddings/Suche, Foto-ML) – Budget-Rechnung über alle Module |
| Nutzer | extern, Internet, Browser-first | TURN-Server für WebRTC, Reverse Proxy + WAF + Identity-Aware Proxy vor allen Modulen, keine Installationspflicht |
| Arbeitsplätze | Windows und Apple (macOS, ggf. iOS) | Safari-Eigenheiten (WebRTC-Codecs, Push), Passkeys über Windows Hello und iCloud-Schlüsselbund, optionale Desktop-Clients für beide Plattformen |
| Schnittstellen | Daten teilen, Mikrofon, Video, weitere nach Bedarf | Freigabe-/Upload-Links, WebRTC-Audio/-Video, Kamera-Scan/QR, Web Share – in jedem Modul, das Externe berührt |

## Offene Klärungen (UNKNOWN)

- Organisationsgröße, Branche, vorhandenes Microsoft 365 / Exchange, Budget.
- Ist Windows Server als Host bindend oder nur eine Option? (GPU-Container auf Windows Server sind eine offene Prüffrage.)
- Anzahl gleichzeitiger externer Nutzer und gleichzeitiger Telefonate (bestimmt das GPU-Budget).
- Video-Meetings nötig oder nur Mikrofon für den Assistenten?
- Bedeutung "die Website bedienen": Assistent in der eigenen Website mit Site-Aktionen (bevorzugte Lesart) oder Steuerung fremder Websites per Browser-Automatisierung.
- Rechtliche Prüfung (KI-Offenlegung, Aufzeichnung, Werbeanrufe) durch Datenschutzbeauftragten/Juristen: nicht Teil dieser Recherche.

## Querschnitts-Audit über alle Module (TODO-01/02, PREPARED)

Die Recherchen zu REQ-01 (Plattform) und REQ-06 (Telefon-KI) starteten, bevor REQ-10..14 vorlagen; ihre Kandidaten haben die QS-Felder noch nicht. `tools/workflows/querschnitt-audit.js` ergänzt und belegt QS-01..QS-08 für JEDEN Kandidaten JEDER Domain-Datei (live geprüft für Fit ≥ 3 / Shortlist, sonst UNKNOWN), passt Fit und Empfehlung an, versioniert jede Änderung in `verifikation.korrekturen` (Quelle `QS-AUDIT`) und prüft eine adversariale Stichprobe je Datei. Start, sobald die laufenden Recherche-Workflows ihre Dateien geschrieben haben; Kontrolle danach mit `python3 tools/research_catalog.py validate && python3 tools/research_catalog.py render`.

# Anforderungen (aus Nutzernachrichten abgeleitet)

Stand 2026-09-24. Quelle je Zeile = Nachrichten-ID in `archive/chat/messages.jsonl`. Status: PROPOSED (vom Nutzer nicht formal freigegeben), Interpretationen sind als INFERRED markiert.

| ID | Anforderung | Quelle | Klasse | Prüfung / Evidenz |
|---|---|---|---|---|
| REQ-01 | Fertige Module (Reuse vor Neubau) für Websitebau, Datenablage, DMS, Telefonie, Outlook, Kalender | MSG-001 | nutzervorgabe | `research/2026-09_modul-scan/domains/*.json` |
| REQ-02 | Alles "high-end und secure": aktiv gepflegt, Security-Prozess, SSO (OIDC/SAML), MFA/Passkeys, Verschlüsselung, Audit-Log, EU-Betrieb | MSG-001 | nutzervorgabe + INFERRED (Ausprägung) | Felder `sicherheit`, `verifikation` je Kandidat |
| REQ-03 | QR-Code-Anmeldung für externe Nutzer mit E-Mail-Adresse, optional Konto | MSG-001 | nutzervorgabe | `research/2026-09_modul-scan/konzept_qr-login_oneclick.md` |
| REQ-04 | Desktop-Tool für Upload und Ordner-Sync, alternativ Chrome-Plugin oder Website-Button, mit vorbelegten Infos zur Benutzerumgebung für One-Click-Pfade | MSG-001 | nutzervorgabe | dito, Domain `client` |
| REQ-05 | Setup-Skript, das die Grundaufgaben (Index, Archiv, Register, Tests, OutputRecord, Folgeprompt) unterstützt | MSG-002 | nutzervorgabe + INFERRED (Bedeutung "Grundaufgaben") | `research/2026-09_setup-skript/` |
| REQ-06 | Telefon-KI-Modul, das Websites bedient und Kalender/Daten lesen kann | MSG-003 | nutzervorgabe | `research/2026-09_telefon-ki/` |
| REQ-07 | Ein Assistent für Website-Chat-API und Telefon mit teilweise gemeinsamen Prompts; Telefon außerhalb der Öffnungszeiten; kleine Aufträge aufnehmen und wiedergeben, wenn Rufnummer bekannt oder Anrufer verifiziert | MSG-004 | nutzervorgabe | `research/2026-09_omnichannel-sweep/loesungsmuster.md` |
| REQ-08 | Quellen: GitHub, arXiv, On-Premise-Verzeichnisse (awesome-selfhosted u. a.); "openopensourcewebsites.com" als Domain UNKNOWN | MSG-004 | nutzervorgabe | `quellen_status` in den Sweep-Dateien |
| REQ-09 | Deutsch-Fokus, mindestens anpassungsfähig | MSG-004 | nutzervorgabe | Feld `deutsch` |
| REQ-10 | Alle Module brandbar (eigenes Design, White-Label) | MSG-005 | nutzervorgabe | Feld `branding`, `branding_windows_matrix.md` |
| REQ-11 | Voll integrierbar in eigene Webkonzepte (APIs, SDKs, Embedding, SSO) | MSG-005 | nutzervorgabe | Feld `schnittstellen` |
| REQ-12 | Voll integrierbar in eigene Software auf Windows-Basis (.NET/OpenAPI, Windows-Client/Dienst, AD/Entra) | MSG-005 | nutzervorgabe + INFERRED (Ausprägung) | Feld `integration_windows` |
| REQ-13 | Server: meist Linux, alternativ Windows Server, jeweils mit Docker; eine RTX 3090 (24 GB); dort läuft die gesamte Modulsammlung | MSG-006 | nutzervorgabe | `research/2026-09_umgebungs-fit/domains/gpu-hosting.json`, `vram-sizing.json` |
| REQ-14 | Nutzer kommen von extern, meist per Browser, auf üblichen Windows- oder Apple-Arbeitsplätzen; Schnittstellen: Daten teilen, Mikrofon, Video, weitere nach Bedarf | MSG-006 | nutzervorgabe | `browser-realtime.json`, `external-clients.json`, `exposure-network.json` |

## Offene Klärungen (UNKNOWN)

- Organisationsgröße, Branche, vorhandenes Microsoft 365 / Exchange, Budget. Hosting-Präferenz ist durch MSG-006 geklärt: eigener Server mit Docker und einer RTX 3090 (On-Premise).
- Ist Windows Server als Host bindend oder nur eine Option? (GPU-Container auf Windows Server sind eine offene Prüffrage der Umgebungs-Recherche.)
- Anzahl gleichzeitiger externer Nutzer und gleichzeitiger Telefonate (bestimmt das GPU-Budget).
- Video-Meetings nötig oder nur Mikrofon für den Assistenten?
- Bedeutung "die Website bedienen": Assistent in der eigenen Website mit Site-Aktionen (bevorzugte Lesart) oder Steuerung fremder Websites per Browser-Automatisierung.
- Windows-Basis (REQ-12) ist durch MSG-006 präzisiert: Server = Docker auf Linux oder Windows Server; Nutzerseite = Browser auf Windows/macOS. Windows-Integration betrifft damit vor allem Browser, optionale Clients und eigene Windows-Software, die per API anbindet.
- Rechtliche Prüfung (KI-Offenlegung, Aufzeichnung, Werbeanrufe) durch Datenschutzbeauftragten/Juristen: nicht Teil dieser Recherche.

## Zielumgebung (MSG-006)

| Ebene | Vorgabe | Konsequenz (INFERRED) |
|---|---|---|
| Server | Linux oder Windows Server, Docker, eine NVIDIA RTX 3090 (24 GB) | Serverkomponenten als Linux-Container; GPU wird von allen KI-Lasten geteilt (STT/TTS/LLM, OCR, Embeddings); Budget-Rechnung nötig |
| Nutzer | extern, Internet, Browser-first | TURN-Server für WebRTC, Reverse Proxy + WAF + Identity-Aware Proxy, keine Installationspflicht |
| Arbeitsplätze | Windows und Apple (macOS, ggf. iOS) | Safari-Eigenheiten (WebRTC-Codecs, Push), Passkeys über Windows Hello und iCloud-Schlüsselbund, optionale Desktop-Clients für beide Plattformen |
| Schnittstellen | Daten teilen, Mikrofon, Video, weitere nach Bedarf | Freigabe-/Upload-Links, WebRTC-Audio für den Assistenten, Video-Meetings (SFU), Kamera-Scan/QR, Web Share |

## Nachträgliche Querschnittsprüfung

REQ-10 bis REQ-12 kamen nach Start der Recherchen zu REQ-01 und REQ-06. Die Sweep-Domain `branding-windows` prüft die Kernkandidaten der Gesamtplattform; die übrigen Shortlist-Kandidaten aus `2026-09_modul-scan` und `2026-09_telefon-ki` bekommen die Felder `branding` und `integration_windows` in einem Folgeschritt (TODO-01). Ebenso prüft ein Folgeschritt die Shortlists aller Recherchen gegen das Umgebungsprofil aus MSG-006 (Docker, 24 GB VRAM, Browser-first, Safari) (TODO-02).

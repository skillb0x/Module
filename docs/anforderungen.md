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

## Offene Klärungen (UNKNOWN)

- Organisationsgröße, Branche, vorhandenes Microsoft 365 / Exchange, Hosting-Präferenz (On-Premise, EU-Cloud, hybrid), Budget.
- Bedeutung "die Website bedienen": Assistent in der eigenen Website mit Site-Aktionen (bevorzugte Lesart) oder Steuerung fremder Websites per Browser-Automatisierung.
- Windows-Basis: nur Client-/Integrationsseite oder auch Serverbetrieb auf Windows Server (Serverkomponenten der meisten Kandidaten laufen auf Linux/Docker).
- Rechtliche Prüfung (KI-Offenlegung, Aufzeichnung, Werbeanrufe) durch Datenschutzbeauftragten/Juristen: nicht Teil dieser Recherche.

## Nachträgliche Querschnittsprüfung

REQ-10 bis REQ-12 kamen nach Start der Recherchen zu REQ-01 und REQ-06. Die Sweep-Domain `branding-windows` prüft die Kernkandidaten der Gesamtplattform; die übrigen Shortlist-Kandidaten aus `2026-09_modul-scan` und `2026-09_telefon-ki` bekommen die Felder `branding` und `integration_windows` in einem Folgeschritt (TODO-01).

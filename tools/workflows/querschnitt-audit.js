// Status: PREPARED. Start mit dem Workflow-Tool:
//   Workflow({ scriptPath: "tools/workflows/querschnitt-audit.js",
//              args: { datum: "YYYY-MM-DD", dateien: ["/abs/pfad/research/<scan>/domains/<domain>.json", ...] } })
// Danach: python3 tools/research_catalog.py validate && python3 tools/research_catalog.py render
export const meta = {
  name: 'querschnitt-audit',
  description: 'Querschnitts-Audit: ergänzt und belegt für JEDEN Kandidaten aller Domain-Dateien die Querschnittskriterien QS-01..QS-08 (secure, Deutsch, Branding, Web-Integration, Windows, macOS, Browser-first, Docker/GPU), passt Fit/Empfehlung an, versioniert Korrekturen, prüft adversariale Stichprobe',
  phases: [
    { title: 'Audit', detail: 'je Domain-Datei ein Schreiber' },
    { title: 'Stichprobe', detail: 'adversariale Prüfung der 3 besten Kandidaten je Datei, Korrekturen einarbeiten' },
  ],
}

const DATUM = args && args.datum
const DATEIEN = (args && args.dateien) || []
if (!DATUM || !DATEIEN.length) throw new Error('args.datum und args.dateien (absolute Pfade) sind Pflicht')

const KONTEXT = `
GELTUNGSREGEL des Nutzers (wörtlich: "es geht hier immer um alle module"): Alle Anforderungen gelten für JEDES Modul JEDER Domain.
ANFORDERUNGEN (Kurzfassung aus docs/anforderungen.md, REQ-02/09/10/11/12/13/14):
- QS-01 secure: aktiv gepflegt, Security-Prozess/Advisories, SSO (OIDC/SAML), MFA/Passkeys, Verschlüsselung, Audit-Log, EU-Betrieb/DSGVO.
- QS-02 deutsch: UI/Doku/Sprachmodelle deutsch oder gut anpassbar.
- QS-03 branding: White-Label technisch (Theme, Logo, Farben, Domain, Clients) UND lizenzrechtlich (Trademark-Policy, "powered by"-Pflicht, AGPL-§7-Zusätze, Branding nur in Enterprise-Edition?).
- QS-04 schnittstellen: REST/GraphQL/WebSocket-APIs, JS-SDK/Web Components, Embedding, Webhooks, SSO – Einbettung in eigene Webkonzepte.
- QS-05 integration_windows: .NET-SDK oder OpenAPI-Spezifikation (Client-Generierung), Windows-Client/-Dienst, AD/Entra-Anbindung, Verteilung (MSIX/Winget/Intune/GPO).
- QS-06 integration_macos: macOS/iOS-Clients, Safari-Tauglichkeit, native CalDAV/CardDAV, Notarisierung.
- QS-07 browser_only: für EXTERNE Nutzer ohne Installation nutzbar (Chrome/Edge/Safari), inkl. Upload/Freigabe, Mikrofon, Video, soweit das Modul Externe berührt.
- QS-08 docker: offizielles Linux-Container-Image/Compose, Betrieb auf EINEM Docker-Host (Linux oder Windows Server), GPU-Bedarf (Feld gpu_vram) gegen eine geteilte RTX 3090 mit 24 GB, Windows-Server-Fähigkeit.
ZIELUMGEBUNG: ein Server (Linux, alternativ Windows Server) mit Docker und einer RTX 3090; Nutzer extern per Browser auf Windows/macOS.

Heute ist ${DATUM}. Live prüfen (WebSearch/WebFetch; zuerst ToolSearch query "select:WebSearch,WebFetch"). GitHub-API per curl blockiert – WebFetch auf github.com-Seiten (LICENSE, README, Releases, Docs).
REGELN: Deutsch. Nichts erfinden; nicht Belegbares = "UNKNOWN". Belege mit URL. Korrekturen versionieren, nie still überschreiben. Keine git-Befehle. Nur die genannte Datei schreiben.
`

const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    datei: { type: 'string' },
    json_valide: { type: 'boolean' },
    kandidaten_gesamt: { type: 'integer' },
    live_geprueft: { type: 'integer' },
    nur_unknown: { type: 'integer' },
    fit_geaendert: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, alt: { type: 'integer' }, neu: { type: 'integer' }, grund: { type: 'string' } }, required: ['id', 'alt', 'neu', 'grund'] } },
    empfehlung_geaendert: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, alt: { type: 'string' }, neu: { type: 'string' }, grund: { type: 'string' } }, required: ['id', 'alt', 'neu', 'grund'] } },
    qs_verletzungen: { type: 'array', items: { type: 'string' }, description: 'Kandidaten, die ein QS-Kriterium klar verletzen (z. B. Branding lizenzrechtlich untersagt, kein Docker-Image)' },
    offene_fragen: { type: 'array', items: { type: 'string' } },
  },
  required: ['datei', 'json_valide', 'kandidaten_gesamt', 'live_geprueft', 'nur_unknown', 'fit_geaendert', 'empfehlung_geaendert', 'qs_verletzungen', 'offene_fragen'],
}

const STICHPROBE_SCHEMA = {
  type: 'object',
  properties: {
    datei: { type: 'string' },
    geprueft: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, feld: { type: 'string' }, ergebnis: { type: 'string', enum: ['CONFIRMED', 'REFUTED', 'UNKNOWN'] }, url: { type: 'string' }, notiz: { type: 'string' } }, required: ['id', 'feld', 'ergebnis', 'url', 'notiz'] } },
    korrekturen_angewendet: { type: 'array', items: { type: 'string' } },
    json_valide: { type: 'boolean' },
    urteil: { type: 'string', enum: ['ZUVERLAESSIG', 'TEILWEISE', 'UNZUVERLAESSIG'] },
  },
  required: ['datei', 'geprueft', 'korrekturen_angewendet', 'json_valide', 'urteil'],
}

const auditPrompt = datei => `${KONTEXT}
ROLLE: Querschnitts-Audit (einziger Schreiber dieser Datei): ${datei}
1. Lies die Datei vollständig (Read). Ermittle je Kandidat: relevant = fit_score >= 3 ODER id in shortlist.
2. Für RELEVANTE Kandidaten: prüfe live alle acht Felder sicherheit (Liste), deutsch, branding, schnittstellen (Liste), integration_windows, integration_macos, browser_only, docker (+ gpu_vram, falls GPU relevant) und fülle sie mit präzisen, belegten Aussagen (URL im Text oder als zusätzlicher Beleg in belege[] mit klasse/quelltyp/url). Vorhandene Werte behalten, nur ergänzen oder korrigieren.
   Für NICHT relevante Kandidaten: fehlende Felder mit "UNKNOWN (nicht geprüft, Fit < 3)" belegen – kein Live-Aufwand.
3. Bewertung anpassen: Verletzt ein relevanter Kandidat ein QS-Kriterium klar (z. B. Branding lizenz-/trademarkrechtlich untersagt oder nur Enterprise; kein Linux-Container-Betrieb; keine API/SDK; für Externe nur mit Installation nutzbar, obwohl Externe das Modul brauchen; GPU-Bedarf sprengt 24 GB im Zusammenspiel), dann fit_score senken und empfehlung anpassen (ADAPT → DEFER/REJECT o. ä.) mit Begründung im Feld begruendung (anhängen, nicht ersetzen).
4. JEDE Änderung an einem bestehenden Feld versionieren: verifikation.korrekturen um {"feld", "alt", "neu", "url", "quelle": "QS-AUDIT", "datum": "${DATUM}"} ergänzen (verifikation anlegen, falls fehlt, status unverändert lassen bzw. "PARTIAL" bei Neuanlage). Neue Felder brauchen keinen korrekturen-Eintrag. Je Kandidat zusätzlich "qs_audit": {"stand": "${DATUM}", "status": "LIVE" | "UNKNOWN_ONLY"}.
5. Alles andere (IDs, Reihenfolge, shortlist, fakten, muster, offene_fragen, suchprotokoll) unverändert lassen. Datei mit Write zurückschreiben (UTF-8, 2 Leerzeichen).
6. Validieren: python3 -c "import json;d=json.load(open('${datei}'));F=['sicherheit','deutsch','branding','schnittstellen','integration_windows','integration_macos','browser_only','docker'];bad=[c['id'] for c in d['kandidaten'] if any(not c.get(f) for f in F)];assert not bad, bad;print(len(d['kandidaten']))" – bei Fehler korrigieren.
7. Structured Output.`

const stichprobePrompt = (datei, audit) => `${KONTEXT}
ROLLE: adversariale Stichprobe für ${datei} (unabhängig vom Audit-Agenten). Audit-Zusammenfassung: ${JSON.stringify(audit)}
1. Lies die Datei. Wähle die 3 Kandidaten mit höchstem fit_score (Shortlist zuerst).
2. Versuche für jeden die Felder branding (Lizenz-/Trademark-Beleg!), integration_windows, browser_only und docker live an der Primärquelle zu WIDERLEGEN. Ergebnis je Feld CONFIRMED/REFUTED/UNKNOWN mit URL.
3. Bei REFUTED: Feld korrigieren und verifikation.korrekturen um {"feld","alt","neu","url","quelle":"QS-AUDIT-STICHPROBE","datum":"${DATUM}"} ergänzen; ggf. fit_score/empfehlung anpassen (ebenfalls versioniert). Sonst nichts ändern. Datei mit Write zurückschreiben.
4. Validieren: python3 -c "import json;json.load(open('${datei}'));print('ok')".
5. urteil: ZUVERLAESSIG (0 REFUTED), TEILWEISE (1–2), UNZUVERLAESSIG (≥3). Structured Output.`

log(`Querschnitts-Audit über ${DATEIEN.length} Domain-Dateien`)
const results = await pipeline(
  DATEIEN,
  d => agent(auditPrompt(d), { label: `audit:${d.split('/').slice(-3, -2)[0]}/${d.split('/').pop()}`, phase: 'Audit', schema: AUDIT_SCHEMA, effort: 'high' }),
  (a, d) => a ? agent(stichprobePrompt(d, a), { label: `stichprobe:${d.split('/').pop()}`, phase: 'Stichprobe', schema: STICHPROBE_SCHEMA, effort: 'high' }).then(s => ({ datei: d, audit: a, stichprobe: s })) : null,
)
const ok = results.filter(Boolean)
const fehlgeschlagen = DATEIEN.filter((d, i) => !results[i])
if (fehlgeschlagen.length) log(`ACHTUNG: Audit ohne Ergebnis für ${fehlgeschlagen.join(', ')}`)
return {
  dateien_ok: ok.map(r => r.datei),
  fehlgeschlagen,
  fit_geaendert: ok.flatMap(r => r.audit.fit_geaendert.map(x => ({ datei: r.datei, ...x }))),
  empfehlung_geaendert: ok.flatMap(r => r.audit.empfehlung_geaendert.map(x => ({ datei: r.datei, ...x }))),
  qs_verletzungen: ok.flatMap(r => r.audit.qs_verletzungen.map(x => `${r.datei}: ${x}`)),
  stichproben: ok.map(r => ({ datei: r.datei, urteil: r.stichprobe && r.stichprobe.urteil, refuted: r.stichprobe ? r.stichprobe.geprueft.filter(g => g.ergebnis === 'REFUTED').length : null })),
  offene_fragen: ok.flatMap(r => r.audit.offene_fragen),
}

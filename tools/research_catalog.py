#!/usr/bin/env python3
"""Validiert die Domain-Dateien der Modulrecherche und erzeugt die Kontrollansicht.

Wahrheit:        research/<scan>/domains/*.json   (von Recherche/Verifikation geschrieben)
Kontrollansicht: docs/modulkatalog.md              (erzeugt, nie von Hand bearbeiten)

Aufruf:
    python3 tools/research_catalog.py validate [--scan DIR ...]
    python3 tools/research_catalog.py render   [--scan DIR ...] [--out FILE]

Ohne --scan werden alle research/*/domains-Verzeichnisse gelesen; IDs müssen scanübergreifend eindeutig sein.

Exit-Code 0 = keine Fehler (Warnungen erlaubt), 1 = Fehler.
Nur Standardbibliothek (Python >= 3.11).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def default_scans() -> list[str]:
    return sorted(os.path.dirname(d) for d in glob.glob(os.path.join(ROOT, "research", "*", "domains")))

DEFAULT_OUT = os.path.join(ROOT, "docs", "modulkatalog.md")

TOP_REQUIRED = ["schema_version", "domain", "titel", "stand", "kandidaten", "shortlist"]
CAND_REQUIRED = [
    "id", "name", "subkategorie", "url", "lizenz", "betrieb", "pflege",
    "fit_score", "empfehlung", "begruendung", "belege",
]
EMPFEHLUNG = {"REUSE", "ADAPT", "EXTRACT", "NEW", "DEFER", "REJECT"}
PFLEGE = {"aktiv", "langsam", "veraltet", "unbekannt"}
KLASSE = {"NORMATIVE", "OBSERVED", "INFERRED", "HYPOTHESIS"}
VERIF_STATUS = {"VERIFIED", "PARTIAL", "UNVERIFIED", "REFUTED"}
CHECK_RESULT = {"CONFIRMED", "REFUTED", "UNKNOWN"}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_domains(scan_dir: str) -> tuple[list[tuple[str, dict]], list[str]]:
    """Lädt alle Domain-Dateien. Gibt (Dateien, Fehler) zurück; kaputtes JSON ist ein Fehler, kein Absturz."""
    files, errors = [], []
    for path in sorted(glob.glob(os.path.join(scan_dir, "domains", "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                files.append((path, json.load(f)))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{os.path.basename(path)}: nicht lesbar/kein JSON ({exc})")
    if not files and not errors:
        errors.append(f"keine Domain-Dateien in {scan_dir}/domains")
    return files, errors


def validate(files: list[tuple[str, dict]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, str] = {}
    for path, data in files:
        name = os.path.basename(path)
        if not isinstance(data, dict):
            errors.append(f"{name}: Wurzel ist kein Objekt")
            continue
        for key in TOP_REQUIRED:
            if key not in data:
                errors.append(f"{name}: Pflichtfeld '{key}' fehlt")
        cands = data.get("kandidaten") or []
        if not isinstance(cands, list):
            errors.append(f"{name}: 'kandidaten' ist keine Liste")
            continue
        local_ids = set()
        for i, c in enumerate(cands):
            where = f"{name}#{c.get('id', i) if isinstance(c, dict) else i}"
            if not isinstance(c, dict):
                errors.append(f"{where}: Kandidat ist kein Objekt")
                continue
            for key in CAND_REQUIRED:
                if key not in c:
                    errors.append(f"{where}: Pflichtfeld '{key}' fehlt")
            cid = c.get("id")
            if cid:
                if cid in seen_ids:
                    errors.append(f"{where}: ID doppelt (auch in {seen_ids[cid]})")
                seen_ids[cid] = name
                local_ids.add(cid)
            score = c.get("fit_score")
            if "fit_score" in c and not (isinstance(score, int) and not isinstance(score, bool) and 1 <= score <= 5):
                errors.append(f"{where}: fit_score muss Ganzzahl 1..5 sein, ist {score!r}")
            if "empfehlung" in c and c["empfehlung"] not in EMPFEHLUNG:
                errors.append(f"{where}: empfehlung '{c['empfehlung']}' ungültig")
            if "pflege" in c and c["pflege"] not in PFLEGE:
                warnings.append(f"{where}: pflege '{c['pflege']}' nicht im Vokabular")
            belege = c.get("belege") or []
            for b in belege:
                if not isinstance(b, dict) or not b.get("url"):
                    errors.append(f"{where}: Beleg ohne URL")
                elif b.get("klasse") not in KLASSE:
                    warnings.append(f"{where}: Beleg-Klasse '{b.get('klasse')}' ungültig")
            if isinstance(score, int) and score >= 3 and len(belege) < 2:
                warnings.append(f"{where}: fit_score {score} mit nur {len(belege)} Beleg(en)")
            verif = c.get("verifikation")
            if verif is None:
                warnings.append(f"{where}: keine verifikation")
            elif isinstance(verif, dict):
                if verif.get("status") not in VERIF_STATUS:
                    errors.append(f"{where}: verifikation.status '{verif.get('status')}' ungültig")
                for g in verif.get("geprueft") or []:
                    if isinstance(g, dict) and g.get("ergebnis") not in CHECK_RESULT:
                        warnings.append(f"{where}: Prüfergebnis '{g.get('ergebnis')}' ungültig")
        for sid in data.get("shortlist") or []:
            if sid not in local_ids:
                errors.append(f"{name}: shortlist-ID '{sid}' existiert nicht in kandidaten")
    return errors, warnings


def _cell(value) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip() or "?"


def render(files: list[tuple[str, dict]], scan_dirs: list[str]) -> str:
    sources = ", ".join(f"`{os.path.relpath(d, ROOT)}/domains/*.json`" for d in scan_dirs)
    lines = [
        "# Modulkatalog – Kontrollansicht",
        "",
        "> **ERZEUGT** von `tools/research_catalog.py render` – nicht von Hand bearbeiten.",
        f"> Wahrheit: {sources}. Status aller Einträge: **PROPOSED** (nicht freigegeben).",
        "> `?` = unbekannt. Fit = 1..5 bezogen auf den Nutzerauftrag.",
        "",
        "## Übersicht",
        "",
        "| Domain | Kandidaten | Shortlist | VERIFIED | PARTIAL | UNVERIFIED | REFUTED | Datei-SHA256 (12) |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for path, data in files:
        cands = data.get("kandidaten") or []
        by_id = {c.get("id"): c for c in cands if isinstance(c, dict)}
        counts = {s: 0 for s in VERIF_STATUS}
        for c in cands:
            st = (c.get("verifikation") or {}).get("status") if isinstance(c, dict) else None
            if st in counts:
                counts[st] += 1
        short = ", ".join(_cell(by_id.get(s, {}).get("name", s)) for s in data.get("shortlist") or [])
        lines.append(
            f"| [{_cell(data.get('domain'))}](#{_cell(data.get('domain'))}) | {len(cands)} | {short} | "
            f"{counts['VERIFIED']} | {counts['PARTIAL']} | {counts['UNVERIFIED']} | {counts['REFUTED']} | "
            f"`{sha256_file(path)[:12]}` |"
        )
    for path, data in files:
        dom = _cell(data.get("domain"))
        lines += ["", f"<a id=\"{dom}\"></a>", f"## {dom} – {_cell(data.get('titel'))}", "",
                  f"Quelle: `{os.path.relpath(path, ROOT)}` · Stand {_cell(data.get('stand'))}", ""]
        shortlist = data.get("shortlist") or []
        lines += ["| # | ID | Name | Lizenz | Betrieb | Version (Datum) | Pflege | Fit | Empfehlung | Verifikation |",
                  "|---|---|---|---|---|---|---|---:|---|---|"]
        cands = [c for c in data.get("kandidaten") or [] if isinstance(c, dict)]
        order = {sid: i for i, sid in enumerate(shortlist)}
        cands.sort(key=lambda c: (order.get(c.get("id"), 999), -(c.get("fit_score") or 0), str(c.get("name"))))
        for c in cands:
            rank = order.get(c.get("id"))
            ver = f"{_cell(c.get('letzte_version'))} ({_cell(c.get('letzte_version_datum'))})"
            lines.append(
                f"| {'★' + str(rank + 1) if rank is not None else ''} | `{_cell(c.get('id'))}` | "
                f"[{_cell(c.get('name'))}]({_cell(c.get('url'))}) | {_cell(c.get('lizenz'))} | {_cell(c.get('betrieb'))} | "
                f"{ver} | {_cell(c.get('pflege'))} | {_cell(c.get('fit_score'))} | {_cell(c.get('empfehlung'))} | "
                f"{_cell((c.get('verifikation') or {}).get('status'))} |"
            )
        top = [c for c in cands if c.get("id") in order]
        if top:
            lines += ["", "### Shortlist – Begründung und Risiken", ""]
            for c in top:
                lines.append(f"- **{_cell(c.get('name'))}** (`{_cell(c.get('id'))}`, {_cell(c.get('empfehlung'))}): {_cell(c.get('begruendung'))}")
                risiken = c.get("risiken") or []
                if risiken:
                    lines.append(f"  - Risiken: {'; '.join(_cell(r) for r in risiken[:4])}")
                korr = (c.get("verifikation") or {}).get("korrekturen") or []
                if korr:
                    lines.append(f"  - Korrekturen durch Verifikation: {len(korr)}")
        fragen = data.get("offene_fragen") or []
        if fragen:
            lines += ["", "### Offene Fragen", ""] + [f"- {_cell(q)}" for q in fragen]
    return "\n".join(lines) + "\n"


def atomic_write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["validate", "render"])
    ap.add_argument("--scan", action="append", help="Scan-Verzeichnis (mehrfach möglich)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)
    scans = a.scan or default_scans()

    files, load_errors = [], []
    for scan in scans:
        f, e = load_domains(scan)
        files += f
        load_errors += e
    if not scans:
        load_errors.append("keine research/*/domains-Verzeichnisse gefunden")
    errors, warnings = validate(files)
    errors = load_errors + errors
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FEHLER {e}")
    print(f"{len(files)} Datei(en), {sum(len(d.get('kandidaten') or []) for _, d in files)} Kandidaten, "
          f"{len(errors)} Fehler, {len(warnings)} Warnungen")
    if a.cmd == "render":
        if errors:
            print("render abgebrochen: erst Fehler beheben")
            return 1
        atomic_write(a.out, render(files, scans))
        print(f"geschrieben: {os.path.relpath(a.out, ROOT)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

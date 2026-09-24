"""Tests für tools/research_catalog.py – inkl. Korruption, falscher Evidenz und Teiländerungen."""
import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import research_catalog as rc  # noqa: E402

CAND = {
    "id": "MOD-TEST-a", "name": "A", "subkategorie": "x", "url": "https://a.example",
    "lizenz": "MIT", "betrieb": "self-hosted", "pflege": "aktiv", "fit_score": 4,
    "empfehlung": "REUSE", "begruendung": "gut",
    "belege": [
        {"aussage": "s", "klasse": "OBSERVED", "quelltyp": "anbieter", "url": "https://a.example/1"},
        {"aussage": "t", "klasse": "OBSERVED", "quelltyp": "community", "url": "https://a.example/2"},
    ],
    "verifikation": {"status": "VERIFIED", "geprueft": [{"aussage": "s", "ergebnis": "CONFIRMED", "url": "u"}]},
}
DOMAIN = {"schema_version": "1.0", "domain": "test", "titel": "Test", "stand": "2026-09-24",
          "kandidaten": [CAND], "shortlist": ["MOD-TEST-a"]}


class ValidateTests(unittest.TestCase):
    def v(self, *domains):
        return rc.validate([(f"/x/{i}.json", d) for i, d in enumerate(domains)])

    def test_valid(self):
        errors, warnings = self.v(DOMAIN)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_required_candidate_field(self):
        d = copy.deepcopy(DOMAIN)
        del d["kandidaten"][0]["lizenz"]
        errors, _ = self.v(d)
        self.assertTrue(any("'lizenz' fehlt" in e for e in errors))

    def test_duplicate_id_across_files(self):
        errors, _ = self.v(DOMAIN, copy.deepcopy(DOMAIN))
        self.assertTrue(any("doppelt" in e for e in errors))

    def test_shortlist_unknown_id(self):
        d = copy.deepcopy(DOMAIN)
        d["shortlist"] = ["MOD-TEST-gibtsnicht"]
        errors, _ = self.v(d)
        self.assertTrue(any("shortlist" in e for e in errors))

    def test_invalid_enum_and_score(self):
        d = copy.deepcopy(DOMAIN)
        d["kandidaten"][0]["empfehlung"] = "KAUFEN"
        d["kandidaten"][0]["fit_score"] = 7
        errors, _ = self.v(d)
        self.assertTrue(any("empfehlung" in e for e in errors))
        self.assertTrue(any("fit_score" in e for e in errors))

    def test_bool_is_not_score(self):
        d = copy.deepcopy(DOMAIN)
        d["kandidaten"][0]["fit_score"] = True
        errors, _ = self.v(d)
        self.assertTrue(any("fit_score" in e for e in errors))

    def test_false_evidence_without_url(self):
        d = copy.deepcopy(DOMAIN)
        d["kandidaten"][0]["belege"][0]["url"] = ""
        errors, _ = self.v(d)
        self.assertTrue(any("ohne URL" in e for e in errors))

    def test_high_score_needs_two_sources(self):
        d = copy.deepcopy(DOMAIN)
        d["kandidaten"][0]["belege"] = d["kandidaten"][0]["belege"][:1]
        _, warnings = self.v(d)
        self.assertTrue(any("Beleg" in w for w in warnings))

    def test_missing_verification_is_warning(self):
        d = copy.deepcopy(DOMAIN)
        del d["kandidaten"][0]["verifikation"]
        errors, warnings = self.v(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("keine verifikation" in w for w in warnings))


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.tmp.name, "domains"))

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def read(path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def write(self, name, text):
        with open(os.path.join(self.tmp.name, "domains", name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_corrupt_json_is_error_not_crash(self):
        self.write("kaputt.json", '{"domain": "x", "kandidaten": [')
        files, errors = rc.load_domains(self.tmp.name)
        self.assertEqual(files, [])
        self.assertTrue(any("kein JSON" in e for e in errors))

    def test_render_is_deterministic_and_marked_generated(self):
        self.write("test.json", json.dumps(DOMAIN))
        out = os.path.join(self.tmp.name, "katalog.md")
        self.assertEqual(rc.main(["render", "--scan", self.tmp.name, "--out", out]), 0)
        first = self.read(out)
        self.assertEqual(rc.main(["render", "--scan", self.tmp.name, "--out", out]), 0)
        self.assertEqual(first, self.read(out))
        self.assertIn("ERZEUGT", first)
        self.assertIn("MOD-TEST-a", first)

    def test_render_refuses_on_errors(self):
        bad = copy.deepcopy(DOMAIN)
        bad["shortlist"] = ["nope"]
        self.write("test.json", json.dumps(bad))
        out = os.path.join(self.tmp.name, "katalog.md")
        self.assertEqual(rc.main(["render", "--scan", self.tmp.name, "--out", out]), 1)
        self.assertFalse(os.path.exists(out))

    def test_pipe_in_cell_is_escaped(self):
        d = copy.deepcopy(DOMAIN)
        d["kandidaten"][0]["lizenz"] = "AGPL|kommerziell"
        self.write("test.json", json.dumps(d))
        files, _ = rc.load_domains(self.tmp.name)
        self.assertIn("AGPL\\|kommerziell", rc.render(files, self.tmp.name))


if __name__ == "__main__":
    unittest.main()

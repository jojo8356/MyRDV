#!/usr/bin/env python3
"""Vérifie le schéma JSON de récurrence (17 cas positifs/négatifs).

Dépendance : jsonschema (dev uniquement) -> pip install jsonschema
Usage : python3 tools/test_schemas.py
"""
import json
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("jsonschema manquant : pip install jsonschema", file=sys.stderr)
    sys.exit(3)

ROOT = pathlib.Path(__file__).resolve().parent.parent
schema = json.loads((ROOT / "schemas" / "recurrence-rule.schema.json").read_text())
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
failures = []


def check(obj, expected_ok, label):
    errors = list(validator.iter_errors(obj))
    ok = not errors
    status = "OK   " if ok else "REJET"
    print(f"{status} {label}" + ("" if ok else f"  -> {errors[0].message[:100]}"))
    if ok != expected_ok:
        failures.append(label)


def base(end, advanced=None):
    doc = {"freq": "WEEKLY", "interval": 1, "byWeekday": [1],
           "startDate": "2026-11-16", "startTime": "09:00",
           "timezone": "Europe/Paris", "end": end}
    if advanced:
        doc["advanced"] = advanced
    return doc


check(base({"mode": "AFTER_DURATION", "months": 3}), True, "3 mois hebdo")
check(base({"mode": "AFTER_COUNT", "count": 14}), True, "14 occurrences")
check(base({"mode": "ON_DATE", "until": "2027-02-16"}), True, "jusqu'au 16/02/2027")
check(base({"mode": "NEVER"}), True, "sans fin bornée")
check(base({"mode": "AFTER_DURATION", "months": 3, "count": 5}), False, "modes de fin exclusifs")
check(base({"mode": "AFTER_COUNT"}), False, "count manquant")
check(base({"mode": "AFTER_DURATION", "weeks": 0}), False, "semaines = 0")
check(base({"mode": "NEVER"}, {"conflictPolicy": "MERGE"}), False, "politique de conflit inconnue")
check(base({"mode": "NEVER"}, {"shiftToleranceMinutes": 250}), False, "tolérance hors plafond")
check({**base({"mode": "NEVER"}), "byWeekday": [1, 1]}, False, "jours dupliqués")
check({**base({"mode": "NEVER"}), "byWeekday": []}, False, "aucun jour sélectionné")
check({**base({"mode": "NEVER"}), "interval": 9}, False, "intervalle > 8 semaines")
check({**base({"mode": "NEVER"}), "byWeekday": [0]}, False, "jour hors plage ISO 1..7")
check({**base({"mode": "NEVER"}), "startTime": "9:00"}, False, "heure non zéro-paddée")
check(base({"mode": "AFTER_COUNT", "count": 200}), False, "200 occurrences > plafond 104")
check(base({"mode": "AFTER_DURATION", "months": 3}, {"exdate": ["2026-12-21"]}), True, "exdate valide")
check({**base({"mode": "NEVER"}), "freq": "DAILY"}, False, "DAILY réservée V2")

if failures:
    print(f"\n{len(failures)} cas en échec : {failures}", file=sys.stderr)
    sys.exit(1)
print("\nSchéma conforme à Draft 2020-12 — 17 cas vérifiés.")

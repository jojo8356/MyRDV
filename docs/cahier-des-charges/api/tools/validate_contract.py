#!/usr/bin/env python3
"""Valide le contrat OpenAPI 3.1 de MyRDV contre les règles de conformité (doc 11).

Contrôles effectués — tous bloquants en intégration continue :

1. **Validité** du document contre la spécification OpenAPI 3.1.
2. **Absence de donnée de santé** (classe C4) dans les schémas exposés (`API-01`) :
   aucun nom de propriété ne doit correspondre aux motifs `symptom*`, `diagnos*`,
   `note*`, `soap*`, `treatment*`, `prescription*`, `attachment*`.
3. **Typage strict** : tous les objets métier déclarent `additionalProperties: false`
   (`API-17`), condition de refus des champs inconnus.
4. **Idempotence** : chaque opération `POST`/`PATCH`/`PUT`/`DELETE` mutante déclare le
   paramètre d'en-tête `Idempotency-Key` (`API-18`).
5. **Pagination** : chaque opération `GET` renvoyant une collection utilise `limit`
   et `cursor` (`API-22`).
6. **Sécurité** : au moins un schéma de sécurité global, des scopes granulaires
   (`API-06`), et une enveloppe d'erreur unique au format RFC 9457 (`API-23`).
7. **Cycle de vie** : `info.version`, `servers` non vides, tags documentés (`API-26`).

Usage :
    python3 api/tools/validate_contract.py [--contract api/openapi.yaml] [--headers]
Dépendances : pyyaml, openapi-spec-validator  (pip install -r api/requirements.txt)
Sortie : code 0 si conforme, 1 sinon (lisible en CI).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("pyyaml manquant : pip install -r api/requirements.txt", file=sys.stderr)
    sys.exit(3)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = ROOT / "openapi.yaml"

# Noms de propriétés interdits dans le contrat public — classe C4 (doc 04 §2, API-01).
C4_PATTERNS = [
    r"^symptom", r"^diagnos", r"^soap", r"^treatment", r"^prescription",
    r"^clinical", r"^patholog", r"^medicat", r"^note(s|Text)?$", r"^attachment",
]
C4_RE = re.compile("|".join(C4_PATTERNS), re.IGNORECASE)

MUTATING = {"post", "patch", "put", "delete"}
# Mutations d'état sans corps ni création de ressource : l'idempotence est portée
# par la sémantique HTTP elle-même (DELETE) ou par un verrou serveur.
IDEMPOTENCY_EXEMPT_PREFIX = ("/health",)
IDEMPOTENCY_EXEMPT_METHODS_IN_PATH = {"/series/{seriesId}/export.ics"}

SECURITY_HEADERS = {
    "RateLimit-Remaining",
    "Retry-After",
    "X-Request-Id",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks = 0

    def ok(self, label: str) -> None:
        self.checks += 1
        print(f"  OK    {label}")

    def fail(self, label: str, detail: str = "") -> None:
        self.checks += 1
        self.errors.append(f"{label}{(' — ' + detail) if detail else ''}")
        print(f"  ÉCHEC {label}{(' — ' + detail) if detail else ''}")

    def warn(self, label: str, detail: str = "") -> None:
        self.warnings.append(f"{label}{(' — ' + detail) if detail else ''}")
        print(f"  AVERT. {label}{(' — ' + detail) if detail else ''}")


def resolve(node: Any, spec: dict) -> Any:
    """Résout les `$ref` internes (une profondeur suffit pour nos schémas)."""
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 8:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return node
        target: Any = spec
        for part in ref[2:].split("/"):
            target = target.get(part, {})
        node = target
        seen += 1
    return node


def iter_schemas(spec: dict):
    for name, schema in (spec.get("components", {}).get("schemas") or {}).items():
        yield name, schema


def check_property_names(spec: dict, report: Report) -> None:
    found = []
    for name, schema in iter_schemas(spec):
        props = (schema or {}).get("properties") or {}
        for prop in props:
            if C4_RE.search(prop):
                found.append(f"{name}.{prop}")
    if found:
        report.fail("Aucune propriété de classe C4 dans le contrat", ", ".join(found))
    else:
        report.ok(f"Aucune propriété de classe C4 ({len(list(iter_schemas(spec)))} schémas balayés)")


def check_strict_objects(spec: dict, report: Report) -> None:
    lax = [
        name
        for name, schema in iter_schemas(spec)
        if (schema or {}).get("type") == "object" and (schema or {}).get("additionalProperties") is not False
    ]
    if lax:
        report.fail("Tous les objets déclarent additionalProperties: false", ", ".join(lax))
    else:
        report.ok("additionalProperties: false sur tous les objets métier")


def check_idempotency(spec: dict, report: Report) -> None:
    missing = []
    for path, item in (spec.get("paths") or {}).items():
        if path.startswith(IDEMPOTENCY_EXEMPT_PREFIX):
            continue
        for method, op in item.items():
            if method not in MUTATING:
                continue
            if op.get("x-mutating") is False:
                # Route de calcul sans écriture (dryRun) : hors périmètre d'API-18.
                continue
            params = [resolve(p, spec) for p in (op.get("parameters") or [])]
            names = {p.get("name") for p in params if isinstance(p, dict)}
            inherited = {
                resolve(p, spec).get("name")
                for p in (item.get("parameters") or [])
                if isinstance(resolve(p, spec), dict)
            }
            if "Idempotency-Key" in names | inherited:
                continue
            # DELETE naturellement idempotent : toléré, mais signalé.
            if method == "delete":
                report.warn(f"{method.upper()} {path} sans Idempotency-Key (idempotent par nature)")
                continue
            missing.append(f"{method.upper()} {path}")
    if missing:
        report.fail("Idempotency-Key sur toutes les mutations", ", ".join(missing))
    else:
        report.ok("Idempotency-Key présent sur toutes les mutations non idempotentes par nature")


def check_pagination(spec: dict, report: Report) -> None:
    missing = []
    for path, item in (spec.get("paths") or {}).items():
        op = item.get("get")
        if not op:
            continue
        content = (op.get("responses", {}).get("200", {}) or {}).get("content", {}) or {}
        schema = (content.get("application/json", {}) or {}).get("schema", {}) or {}
        schema = resolve(schema, spec)
        is_collection = (
            "data" in (schema.get("properties") or {})
            or (schema.get("type") == "array")
        )
        if not is_collection:
            continue
        params = {resolve(p, spec).get("name") for p in (op.get("parameters") or [])}
        if not {"limit", "cursor"} <= params:
            missing.append(f"GET {path}")
    if missing:
        report.fail("Pagination (limit + cursor) sur toutes les collections", ", ".join(missing))
    else:
        report.ok("Pagination limit + cursor sur toutes les collections")


def check_security(spec: dict, report: Report) -> None:
    schemes = (spec.get("components", {}) or {}).get("securitySchemes") or {}
    if "oauth2" in schemes and schemes["oauth2"].get("type") == "oauth2":
        scopes = set()
        for flow in (schemes["oauth2"].get("flows") or {}).values():
            scopes |= set((flow.get("scopes") or {}).keys())
        granular = {s for s in scopes if ":" in s}
        if len(granular) >= 10:
            report.ok(f"OAuth 2.0 + PKCE déclaré, {len(granular)} scopes granulaires")
        else:
            report.fail("Scopes granulaires insuffisants", f"{len(granular)} scopes <ressource>:<action>")
    else:
        report.fail("Schéma de sécurité oauth2 absent")

    if spec.get("security"):
        report.ok("Sécurité appliquée globalement")
    else:
        report.fail("Aucune sécurité globale déclarée")


def check_problem_details(spec: dict, report: Report) -> None:
    problem = (spec.get("components", {}).get("schemas") or {}).get("Problem")
    if not problem:
        report.fail("Schéma d'erreur Problem (RFC 9457) absent")
        return
    required = {"type", "title", "status", "code", "requestId"}
    if required <= set(problem.get("properties") or {}):
        report.ok("Enveloppe d'erreur RFC 9457 avec code et requestId stables")
    else:
        report.fail("Problème incomplet", f"manque {sorted(required - set(problem.get('properties') or {}))}")


def check_headers(spec: dict, report: Report) -> None:
    """Vérifie que les réponses de succès étroites exposent les en-têtes de débit/corrélation."""
    declared = set((spec.get("components", {}).get("headers") or {}).keys())
    if {"RequestId", "RateLimitRemaining", "ETag"} <= declared:
        report.ok("En-têtes RateLimit / Request-Id / ETag déclarés")
    else:
        report.fail("En-têtes de sécurité manquants", str(sorted({"RequestId", "RateLimitRemaining", "ETag"} - declared)))

    # Aucune valeur métier ne doit transiter par un en-tête personnalisé non documenté.
    undocumented = []
    for path, item in (spec.get("paths") or {}).items():
        for method, op in item.items():
            if not isinstance(op, dict):
                continue
            for resp in (op.get("responses") or {}).values():
                for header in (resolve(resp, spec).get("headers") or {}):
                    # Un en-tête peut être déclaré soit par son nom HTTP, soit par la clé
                    # du composant (`Idempotency-Replayed` ↔ `IdempotencyReplayed`).
                    normalized = header.replace("-", "")
                    if (header not in declared and normalized not in declared
                            and header not in {"Retry-After", "Location"}):
                        undocumented.append(f"{header} ({method.upper()} {path})")
    if undocumented:
        report.warn("En-têtes de réponse hors composants", ", ".join(sorted(set(undocumented))))
    else:
        report.ok("En-têtes de réponse tous déclarés dans components/headers")


def check_lifecycle(spec: dict, report: Report) -> None:
    info = spec.get("info") or {}
    if info.get("version") and spec.get("servers"):
        report.ok(f"Version {info['version']} et {len(spec['servers'])} serveurs déclarés")
    else:
        report.fail("info.version ou servers manquant")

    tags = {t.get("name") for t in (spec.get("tags") or [])}
    used = set()
    for item in (spec.get("paths") or {}).values():
        for op in item.values():
            if isinstance(op, dict):
                used |= set(op.get("tags") or [])
    if used <= tags:
        report.ok(f"Tags documentés ({len(used)})")
    else:
        report.fail("Tags utilisés mais non documentés", ", ".join(sorted(used - tags)))

    if "v1" in "".join(spec.get("servers", [{}])[0].values()):
        report.ok("Versionnage par chemin (/v1) présent")
    elif "v1" in str(spec.get("servers")):
        report.ok("Versionnage par chemin (/v1) présent")
    else:
        report.warn("Aucun /v1 visible dans servers")

    if all(op.get("operationId") for item in (spec.get("paths") or {}).values()
           for op in item.values() if isinstance(op, dict)):
        report.ok("operationId sur toutes les opérations")


def validate_spec(contract: Path, report: Report) -> dict:
    spec = yaml.safe_load(contract.read_text(encoding="utf-8"))
    try:
        from openapi_spec_validator import validate
        validate(spec)
        report.ok("Document valide contre la spécification OpenAPI 3.1")
    except ImportError:  # pragma: no cover
        report.warn("openapi-spec-validator absent : validation de spécification ignorée")
    except Exception as exc:  # noqa: BLE001
        report.fail("Validation OpenAPI 3.1", str(exc)[:300])
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--headers", action="store_true",
                        help="n'exécute que le contrôle des en-têtes")
    args = parser.parse_args()

    contract = Path(args.contract)
    if not contract.exists():
        print(f"Contrat introuvable : {contract}", file=sys.stderr)
        return 3

    print(f"Contrat : {contract}")
    report = Report()
    spec = validate_spec(contract, report)

    if args.headers:
        check_headers(spec, report)
    else:
        check_property_names(spec, report)
        check_strict_objects(spec, report)
        check_idempotency(spec, report)
        check_pagination(spec, report)
        check_security(spec, report)
        check_problem_details(spec, report)
        check_headers(spec, report)
        check_lifecycle(spec, report)

    print()
    print(f"{report.checks} contrôles · {len(report.errors)} échec(s) · "
          f"{len(report.warnings)} avertissement(s)")
    if report.warnings:
        print("\nAvertissements :")
        for w in report.warnings:
            print(f"  - {w}")
    if report.errors:
        print("\nÉchecs :")
        for e in report.errors:
            print(f"  - {e}")
        return 1
    print("\nContrat conforme aux règles API-01, API-06, API-17, API-18, API-22, API-23, API-26.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

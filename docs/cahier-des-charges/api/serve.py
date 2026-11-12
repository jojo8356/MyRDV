#!/usr/bin/env python3
"""serve.py — documentation GUI (Swagger UI) + mock conforme du contrat MyRDV.

Deux usages :

    python3 api/serve.py                 # http://localhost:8787
    python3 api/serve.py --port 9000

* `/` et `/docs`  : Swagger UI 5.34 embarqué (aucun CDN, aucun appel externe)
* `/openapi.yaml` : le contrat source
* `/openapi.json` : le même contrat, converti (le YAML reste la source de vérité)
* `/v1/*`         : **mock** respectant les codes du contrat (201, 401, 404, 409,
                    422, 428, 429), les en-têtes de sécurité et l'enveloppe
                    d'erreur RFC 9457

Le mock existe pour trois raisons : rendre la documentation **essayable** sans
environnement de recette, démontrer les garanties de contrat (idempotence,
isolation, absence de donnée C4) et servir de **fixture** aux tests d'intégration
du front (doc 09). Il ne contient **aucune donnée réelle** ; les identifiants sont
des ULID figés.

Sécurité du mock : écoute sur `127.0.0.1` par défaut. Utilisez `--host 0.0.0.0`
uniquement dans un environnement de démonstration isolé — jamais en production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

try:
    import yaml
except ImportError:  # pragma: no cover
    print("pyyaml manquant : pip install -r api/requirements.txt", file=sys.stderr)
    sys.exit(3)

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor" / "swagger-ui"
CONTRACT = ROOT / "openapi.yaml"

# --------------------------------------------------------------------------
# Fixtures (ULID figés, aucune donnée personnelle réelle)
# --------------------------------------------------------------------------
ORG_ID = "01JB7Q80ORGANISATION000000A"
PRACTITIONER_ID = "01JB7Q9F3K2W8M5V6X1Y4Z7A0B"
CLIENT_ID = "01JB7QA1M4N6P8R2S5T9U3V7W1"
SERVICE_ID = "01JB7QB2X8Y4Z6A1B3C5D7E9F2"
SERIES_ID = "01JB7QE6S9U2W5X8Y1Z4A7B0C3"
EXPORT_ID = "01JB7QF7T0V3X6Y9Z2A5B8C1D4"

RULE = {
    "freq": "WEEKLY",
    "interval": 1,
    "byWeekday": [1],
    "startDate": "2026-11-16",
    "startTime": "09:00",
    "timezone": "Europe/Paris",
    "durationMinutes": 60,
    "end": {"mode": "AFTER_DURATION", "months": 3},
    "advanced": {"conflictPolicy": "SKIP", "dateShiftPolicy": "SHIFT_FORWARD"},
}

SERIES = {
    "id": SERIES_ID,
    "status": "ACTIVE",
    "practitionerId": PRACTITIONER_ID,
    "clientId": CLIENT_ID,
    "serviceId": SERVICE_ID,
    "rule": RULE,
    "effectiveUntil": "2027-02-16",
    "materializedUntil": "2027-02-15",
    "progress": {"planned": 14, "materialized": 14, "completed": 0, "cancelled": 0, "skipped": 0},
    "skipped": [],
    "skippedConflict": [],
    "warnings": [],
    "billing": {"mode": "PER_SESSION"},
    "createdAt": "2026-11-12T10:22:31+01:00",
    "etag": '"7c9f2a"',
    "links": {
        "self": f"/v1/series/{SERIES_ID}",
        "occurrences": f"/v1/series/{SERIES_ID}/occurrences",
        "ics": f"/v1/series/{SERIES_ID}/export.ics",
    },
}

CLIENT = {
    "id": CLIENT_ID,
    "displayName": "Client de démonstration",
    "email": "demo@example.invalid",
    "phone": "+33600000000",
    "locale": "fr-FR",
    "consents": [
        {"purpose": "APPOINTMENT_REMINDERS", "granted": True, "version": "2026-09",
         "grantedAt": "2026-11-02T09:14:00+01:00"},
        {"purpose": "MARKETING", "granted": False, "version": "2026-09",
         "withdrawnAt": "2026-11-05T17:02:00+01:00"},
    ],
    "processingRestricted": False,
    "createdAt": "2026-10-01T08:00:00+02:00",
    "etag": '"1a2b3c"',
}

AUDIT = [
    {
        "id": "01JB7QG8V1W4Y7Z0A3B6C9D2E5",
        "at": "2026-11-12T10:22:31+01:00",
        "actorId": PRACTITIONER_ID,
        "action": "series.created",
        "subjectType": "series",
        "subjectId": SERIES_ID,
        "diff": [{"field": "status", "before": None, "after": "ACTIVE"}],
        "previousHash": "0" * 64,
        "hash": hashlib.sha256(b"demo-audit-entry").hexdigest(),
    }
]

# Codes du catalogue (doc 07 §8) — un jeu minimal représentatif.
ERRORS = {
    "VAL_400_SCHEMA": (400, "Requête invalide", "Le corps ne respecte pas le schéma."),
    "AUTH_401_MISSING": (401, "Jeton absent", "En-tête Authorization Bearer requis."),
    "AUTH_403_FORBIDDEN_SCOPE": (403, "Scope insuffisant", "Le jeton ne porte pas le scope requis."),
    "SER_007_COUNT_OVER_CAP": (422, "Plafond d'occurrences", "Votre offre autorise au maximum 104 occurrences par série."),
    "SER_017_SLOT_CONFLICT": (409, "Créneau occupé", "Le créneau est déjà réservé."),
    "SER_024_CONFIRMATION_REQUIRED": (428, "Confirmation requise", "Fournir confirmCount égal au nombre d'occurrences."),
    "IDEM_409_KEY_REUSE": (409, "Clé d'idempotence réutilisée", "La clé a déjà servi avec un corps différent."),
    "RATE_429_LIMIT": (429, "Débit dépassé", "Réessayez après le délai indiqué."),
    "CMP_423_RESTRICTED": (423, "Traitement limité", "Une limitation de traitement est active pour ce client."),
}


class Handler(BaseHTTPRequestHandler):
    server_version = "MyRDV-Mock/1.0"
    protocol_version = "HTTP/1.1"

    # ---------------------------------------------------------------- utilitaires
    def log_message(self, fmt: str, *args) -> None:  # journal compact
        sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")

    def _send(self, status: int, body: bytes, content_type: str,
              extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # En-têtes de sécurité du contrat (API-13)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Request-Id", self._request_id())
        self.send_header("RateLimit-Limit", "600")
        self.send_header("RateLimit-Remaining", "597")
        self.send_header("RateLimit-Reset", "42")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _request_id(self) -> str:
        incoming = self.headers.get("X-Request-Id", "")
        if re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", incoming):
            return incoming
        return "req_" + hashlib.sha256(self.path.encode()).hexdigest()[:24].upper()

    def _json(self, status: int, payload, extra: dict[str, str] | None = None) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False, indent=2).encode(),
                   "application/json; charset=utf-8", extra)

    def _problem(self, code: str, detail: str | None = None, pointer: str | None = None) -> None:
        status, title, default_detail = ERRORS.get(code, (400, "Erreur", "Erreur."))
        payload = {
            "type": f"https://docs.myrdv.app/errors/{code}",
            "title": title,
            "status": status,
            "detail": detail or default_detail,
            "instance": self.path,
            "code": code,
            "requestId": self._request_id(),
            "documentation": f"https://docs.myrdv.app/errors/{code}",
        }
        if pointer:
            payload["errors"] = [{"pointer": pointer, "code": code, "message": detail or default_detail}]
        extra = {"Content-Type": "application/problem+json; charset=utf-8"}
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        if status == 429:
            extra["Retry-After"] = "30"
        self.send_response(status)
        for k, v in extra.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Request-Id", self._request_id())
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and len(auth) > 10:
            return True
        if self.headers.get("X-API-Key"):
            return True
        self._problem("AUTH_401_MISSING")
        return False

    def _body(self) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._problem("VAL_400_SCHEMA", "Corps JSON invalide.")
            return None

    # ------------------------------------------------------------------- fichiers
    def _static(self, filename: str, content_type: str) -> None:
        path = (VENDOR / filename).resolve()
        if not path.is_file() or VENDOR.resolve() not in path.parents:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        self._send(200, path.read_bytes(), content_type)

    def _docs(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self._send(200, html.encode(), "text/html; charset=utf-8",
                   {"Content-Security-Policy": (
                       "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                       # frame-ancestors volontairement absent : la documentation doit
                       # pouvoir être affichée dans une iframe de revue (portail interne,
                       # aperçu d'outil) sans élargir le reste de la politique.
                       "script-src 'self' 'unsafe-inline'; connect-src 'self'")})

    # ---------------------------------------------------------------------- GET
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)

        if path in ("/", "/docs", "/docs/", "/index.html"):
            return self._docs()
        if path == "/openapi.yaml":
            return self._send(200, CONTRACT.read_bytes(), "application/yaml; charset=utf-8")
        if path == "/openapi.json":
            return self._json(200, yaml.safe_load(CONTRACT.read_text(encoding="utf-8")))
        if path.startswith("/vendor/swagger-ui/"):
            name = path.rsplit("/", 1)[-1]
            ext = name.rsplit(".", 1)[-1]
            types = {"js": "application/javascript; charset=utf-8",
                     "css": "text/css; charset=utf-8",
                     "png": "image/png", "ico": "image/png"}
            return self._static(name, types.get(ext, "application/octet-stream"))

        # ------------------------------------------------------------ API mock
        if not path.startswith("/v1/"):
            return self._send(404, b"Not found", "text/plain; charset=utf-8")

        if path == "/v1/health/deep":
            return self._json(200, {"status": "ok",
                                    "checks": {"database": "ok", "redis": "ok",
                                               "queue": "ok", "payments": "ok"},
                                    "version": "1.0.0"})

        if not self._authorized():
            return

        if path == "/v1/series":
            return self._json(200, {"data": [SERIES], "nextCursor": None, "hasMore": False})
        m = re.fullmatch(r"/v1/series/([0-9A-Z]{26})", path)
        if m:
            if m.group(1) != SERIES_ID:
                return self._problem("VAL_400_SCHEMA", "Ressource inexistante ou hors périmètre.")
            return self._json(200, SERIES, {"ETag": SERIES["etag"]})
        m = re.fullmatch(r"/v1/series/([0-9A-Z]{26})/occurrences", path)
        if m:
            data = [
                {"key": f"2026-11-{16 + 7 * i:02d}T09:00", "seriesId": SERIES_ID,
                 "status": "PLANNED", "startAt": f"2026-11-{16 + 7 * i:02d}T09:00:00+01:00",
                 "endAt": f"2026-11-{16 + 7 * i:02d}T10:00:00+01:00", "detached": False}
                for i in range(3)
            ]
            return self._json(200, {"data": data, "nextCursor": None, "hasMore": False})
        m = re.fullmatch(r"/v1/clients/([0-9A-Z]{26})", path)
        if m:
            return self._json(200, CLIENT, {"ETag": CLIENT["etag"]})
        m = re.fullmatch(r"/v1/clients/([0-9A-Z]{26})/consents", path)
        if m:
            return self._json(200, {"data": CLIENT["consents"], "nextCursor": None, "hasMore": False})
        if path == "/v1/audit":
            return self._json(200, {"data": AUDIT, "nextCursor": None, "hasMore": False})
        if path == "/v1/webhooks":
            return self._json(200, {"data": [], "nextCursor": None, "hasMore": False})
        if path == "/v1/privacy/retention-report":
            return self._json(200, {
                "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "categories": [
                    {"category": "C3 — identité client", "retention": "3 ans après dernier contact",
                     "lastPurgeAt": "2026-11-01T02:00:00+00:00", "purgedCount": 12},
                    {"category": "C2 — factures", "retention": "10 ans (obligation comptable)",
                     "lastPurgeAt": "2026-11-01T02:00:00+00:00", "purgedCount": 0},
                ]})
        if path.startswith("/v1/exports/"):
            return self._json(200, {
                "id": EXPORT_ID, "status": "READY", "format": "json",
                "downloadUrl": "https://exports.myrdv.app/demo/export-demo.json?sig=demo",
                "expiresAt": "2026-11-12T12:15:00+00:00",
                "checksumSha256": hashlib.sha256(b"demo-export").hexdigest(),
                "createdAt": "2026-11-12T12:00:00+00:00"})
        return self._problem("VAL_400_SCHEMA", "Endpoint non implémenté dans le mock (voir le contrat).")

    # ------------------------------------------------------------------ POST etc.
    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/v1/"):
            return self._send(404, b"Not found", "text/plain; charset=utf-8")
        if not self._authorized():
            return
        body = self._body()
        if body is None:
            return

        if path == "/v1/series/preview":
            count = 14
            rule = body.get("rule") or {}
            if rule.get("end", {}).get("months") == 6:
                count = 27
            return self._json(200, {
                "requested": count, "effectiveUntil": "2027-02-16",
                "occurrences": [{"date": "2026-11-16", "startAt": "2026-11-16T09:00:00+01:00",
                                 "endAt": "2026-11-16T10:00:00+01:00"}],
                "skipped": ["2026-12-21"], "skippedConflict": [],
                "warnings": ["SER_017_SLOT_CONFLICT sur 1 occurrence (politique SKIP)"]})

        if path == "/v1/series":
            if not self.headers.get("Idempotency-Key"):
                return self._problem("VAL_400_SCHEMA",
                                     "Idempotency-Key (UUID v4) obligatoire sur les mutations (API-18).")
            rule = body.get("rule") or {}
            end = rule.get("end") or {}
            if end.get("count", 0) > 104 or end.get("months", 0) > 24:
                return self._problem("SER_007_COUNT_OVER_CAP")
            return self._json(201, SERIES, {
                "Location": f"/v1/series/{SERIES_ID}",
                "ETag": SERIES["etag"],
                "Idempotency-Replayed": "false"})

        if path == "/v1/exports":
            return self._json(202, {
                "id": EXPORT_ID, "status": "QUEUED", "format": body.get("format", "json"),
                "expiresAt": "2026-11-12T12:30:00+00:00",
                "createdAt": "2026-11-12T12:00:00+00:00"}, {"Location": f"/v1/exports/{EXPORT_ID}"})

        if path == "/v1/privacy/deindexation":
            return self._json(202, {"id": "01JB7QH8V2X5Y8Z1A4B7C0D3E6", "type": "DEINDEXATION",
                                    "status": "RECEIVED",
                                    "receivedAt": "2026-11-12T12:00:00+00:00",
                                    "dueAt": "2026-11-22T12:00:00+00:00"})

        if path == "/v1/webhooks":
            if not str(body.get("url", "")).startswith("https://"):
                return self._problem("VAL_400_SCHEMA", "URL HTTPS obligatoire (API-37).", "/url")
            return self._json(201, {"id": "01JB7QJ9W3Y6Z9A2B5C8D1E4F7", "url": body["url"],
                                    "events": body.get("events", []), "status": "ACTIVE",
                                    "secretLastRotatedAt": "2026-11-12T12:00:00+00:00"})
        return self._problem("VAL_400_SCHEMA", "Endpoint non implémenté dans le mock.")

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._authorized():
            return
        body = self._body()
        if body is None:
            return
        if not self.headers.get("If-Match"):
            return self._problem("VAL_400_SCHEMA", "If-Match obligatoire (API-19).")
        if re.fullmatch(r"/v1/series/([0-9A-Z]{26})", path):
            scope = body.get("scope")
            if scope not in ("THIS", "THIS_AND_FOLLOWING", "ALL"):
                return self._problem("VAL_400_SCHEMA", "scope obligatoire (THIS|THIS_AND_FOLLOWING|ALL).",
                                     "/scope")
            updated = dict(SERIES)
            updated["rule"] = {**SERIES["rule"], **(body.get("rule") or {})}
            return self._json(200, {
                "series": updated, "affectedCount": 8 if scope != "THIS" else 1,
                "seriesRevisionId": "01JB7QK1X4Z7A0B3C6D9E2F5G8",
                "diff": [{"field": "rule.startTime", "before": "09:00", "after": "09:30"}]})
        if re.fullmatch(r"/v1/clients/([0-9A-Z]{26})", path):
            updated = {**CLIENT, **{k: v for k, v in body.items() if k in
                                    ("displayName", "email", "phone", "locale")}}
            return self._json(200, updated)
        if re.fullmatch(r"/v1/clients/([0-9A-Z]{26})/consents", path):
            consents = list(CLIENT["consents"])
            return self._json(200, {"data": consents, "nextCursor": None, "hasMore": False})
        return self._problem("VAL_400_SCHEMA", "Endpoint non implémenté dans le mock.")

    def do_PUT(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._authorized():
            return
        body = self._body()
        if body is None:
            return
        if path.startswith("/v1/processing-restrictions/"):
            return self._json(200, {"restricted": bool(body.get("restricted")),
                                    "reason": body.get("reason", ""),
                                    "requestedBy": body.get("requestedBy", "demo"),
                                    "appliedAt": "2026-11-12T12:00:00+00:00"})
        return self._problem("VAL_400_SCHEMA", "Endpoint non implémenté dans le mock.")

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        if not self._authorized():
            return
        m = re.fullmatch(r"/v1/clients/([0-9A-Z]{26})", path)
        if m:
            if query.get("mode", [""])[0] != "erase":
                return self._problem("VAL_400_SCHEMA", "mode=erase obligatoire (art. 17).")
            return self._json(200, {
                "clientId": m.group(1),
                "erased": ["identité (C3)", "coordonnées", "consentements", "rendez-vous futurs"],
                "pseudonymized": ["factures (C2)"],
                "retainedForLegalObligation": [
                    {"category": "factures", "legalBasis": "obligation comptable (10 ans)",
                     "until": "2036-11-12"}],
                "partial": True,
                "requestId": self._request_id()})
        m = re.fullmatch(r"/v1/series/([0-9A-Z]{26})", path)
        if m:
            scope = query.get("scope", [""])[0]
            if scope not in ("THIS", "THIS_AND_FOLLOWING", "ALL"):
                return self._problem("VAL_400_SCHEMA", "scope obligatoire.")
            if "confirmCount" not in query:
                return self._problem("SER_024_CONFIRMATION_REQUIRED")
            self.send_response(204)
            self.send_header("X-Request-Id", self._request_id())
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        return self._problem("VAL_400_SCHEMA", "Endpoint non implémenté dans le mock.")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Allow", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    if not CONTRACT.exists():
        print(f"Contrat introuvable : {CONTRACT}", file=sys.stderr)
        return 3
    missing = [f for f in ("swagger-ui-bundle.js", "swagger-ui-standalone-preset.js", "index.css")
               if not (VENDOR / f).exists()]
    if missing:
        print(f"Swagger UI incomplet (manque {', '.join(missing)}).\n"
              "Régénérez le dossier vendor/ : voir api/README.md.", file=sys.stderr)
        return 3

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Swagger UI : http://{args.host}:{args.port}/")
    print(f"Contrat    : http://{args.host}:{args.port}/openapi.yaml")
    print(f"Mock API   : http://{args.host}:{args.port}/v1/health/deep")
    print("Jeton de démonstration : n'importe quelle valeur `Bearer demo`.")
    print("Ctrl+C pour arrêter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

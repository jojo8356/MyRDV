# API MyRDV — contrat, documentation GUI et vérifications

Ce dossier contient le **contrat exécutable** de l'API `/v1` et sa **documentation graphique**.
Il ne dépend d'aucun service externe : tout est embarqué, y compris Swagger UI.

| Fichier | Rôle |
|---|---|
| `openapi.yaml` | **Source de vérité** du contrat (OpenAPI 3.1) — séries, occurrences, droits des personnes, exports, webhooks, audit, erreurs |
| `index.html` | Interface Swagger UI (thème GitHub Light + accent startup, cohérent avec le PDF du cahier) |
| `serve.py` | Sert la documentation **et** un mock conforme du contrat (201 / 401 / 404 / 409 / 422 / 428 / 429) |
| `tools/validate_contract.py` | Vérifie 14 règles de conformité sur le contrat (voir ci-dessous) |
| `requirements.txt` | Dépendances Python (`pyyaml`, `openapi-spec-validator`) |
| `vendor/swagger-ui/` | Swagger UI 5.34.1 embarqué (bundle + preset + CSS + favicons + licences) |

Les règles **opposables** appliquées ici sont numérotées `API-01` à `API-43` dans
[`../docs/11-api-regles-et-conformite.md`](../docs/11-api-regles-et-conformite.md).

---

## 1. Lancer la documentation

```bash
pip install -r docs/cahier-des-charges/api/requirements.txt
python3 docs/cahier-des-charges/api/serve.py            # http://localhost:8787
```

Options : `--port 9000`, `--host 0.0.0.0` (démonstration isolée uniquement — jamais en production).

| URL | Contenu |
|---|---|
| `/` ou `/docs` | Swagger UI, toutes les opérations dépliables, essai possible |
| `/openapi.yaml` | Le contrat source |
| `/openapi.json` | Le même contrat en JSON (pour les outils qui n'acceptent pas YAML) |
| `/v1/health/deep` | Sonde de profondeur du mock |
| `/v1/series`, `/v1/clients/{id}`, `/v1/audit`, `/v1/exports/{id}`… | Réponses de démonstration |

**Pour essayer un endpoint** : cliquer sur *Authorize*, saisir `demo` comme jeton Bearer (le mock
accepte n'importe quelle valeur non vide), puis *Try it out*. Les mutations exigent les en-têtes du
contrat — `Idempotency-Key` sur `POST`/`PATCH`/`DELETE`, `If-Match` sur `PATCH` — ce qui rend les
garanties **visibles** : les retirer produit `400`, `428` ou `412` comme documenté.

> Le mock ne contient **aucune donnée réelle**. Les identifiants sont des ULID figés
> (`01JB7Q…`) et l'adresse du client de démonstration est en `.invalid`.

## 2. Vérifier le contrat (bloquant en CI)

```bash
python3 docs/cahier-des-charges/api/tools/validate_contract.py
```

Sortie attendue : `14 contrôles · 0 échec(s) · 0 avertissement(s)`.

| Contrôle | Règle | Ce qui est vérifié |
|---|---|---|
| Validité OpenAPI 3.1 | API-25 | document conforme à la spécification |
| Absence de classe C4 | API-01 | aucun nom de propriété de santé (`symptom*`, `diagnos*`, `note*`, `soap*`, `treatment*`, `prescription*`, `attachment*`, `clinical*`, `patholog*`, `medicat*`) |
| Typage strict | API-17 | `additionalProperties: false` sur tous les objets métier |
| Idempotence | API-18 | `Idempotency-Key` sur chaque mutation (sauf `x-mutating: false` et `DELETE`, idempotents par nature) |
| Pagination | API-22 | `limit` + `cursor` sur chaque `GET` de collection |
| Sécurité | API-03, API-06 | OAuth 2.0 + PKCE, ≥ 10 scopes `<ressource>:<action>` |
| Enveloppe d'erreur | API-23 | `Problem` RFC 9457 avec `code` et `requestId` |
| En-têtes | API-13, API-35 | `RateLimit-*`, `X-Request-Id`, `ETag` déclarés et utilisés |
| Cycle de vie | API-26 | `info.version`, `servers`, tags documentés, `operationId` partout, `/v1` dans le chemin |

Options : `--contract <chemin>` pour un autre fichier, `--headers` pour ne rejouer que le contrôle
des en-têtes.

## 3. Publier la documentation

En production, le même contrat est servi par l'API elle-même :

| Environnement | URL |
|---|---|
| Production | `https://api.myrdv.app/v1/openapi.json` |
| Documentation | `https://docs.myrdv.app` (même `index.html`, Swagger UI servi par le CDN interne) |

Le contrat est **généré depuis `packages/contracts`** (schémas Zod) à chaque fusion : si le fichier
versionné diffère du contrat généré, la CI échoue (règle API-25). Ne modifiez donc pas
`openapi.yaml` à la main sans mettre à jour les schémas — sauf pour ce dépôt de spécification, où il
fait foi jusqu'à l'implémentation.

## 4. Mettre à jour Swagger UI

Le bundle est versionné pour garantir la reproductibilité et le fonctionnement hors ligne.

```bash
npm pack swagger-ui-dist@5.34.1 && tar xzf swagger-ui-dist-5.34.1.tgz
cp package/swagger-ui-bundle.js package/swagger-ui-standalone-preset.js \
   package/index.css package/favicon-16x16.png package/favicon-32x32.png \
   package/LICENSE package/NOTICE vendor/swagger-ui/
```

Vérifier ensuite que `serve.py` démarre (il refuse de démarrer si un fichier du bundle manque) et que
la page affiche bien le contrat.

## 5. Ajouter un endpoint

1. Décrire l'opération dans `openapi.yaml` : `tags`, `operationId`, `summary`, `description`, codes
   d'erreur, paramètres (`limit`/`cursor` si collection, `Idempotency-Key` si mutation).
2. Rattacher chaque propriété nouvelle à une **classe de donnée** (C0 à C4) dans le doc 11 §2. Une
   propriété C4 n'entre pas dans ce contrat.
3. Lancer `validate_contract.py` : il doit rester à 0 échec.
4. Ajouter l'entrée de test correspondante au [plan de recette](../docs/09-plan-tests-recette.md).
5. Si l'endpoint touche à une donnée personnelle, vérifier la ligne du registre des traitements
   ([doc 04 §6.1](../docs/04-securite-conformite.md)) et, le cas échéant, la DPIA.

## 6. Licence des composants embarqués

Swagger UI est distribué sous licence Apache 2.0 (`vendor/swagger-ui/LICENSE`, `NOTICE`). Le contrat
et la documentation MyRDV restent propriétaires (voir `info.license` dans `openapi.yaml`).

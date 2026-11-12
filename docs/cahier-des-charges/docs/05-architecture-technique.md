# 05 — Architecture technique

**Document** : 05 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Objectif** : décrire l'architecture cible, le modèle de domaine, les choix technologiques et les
règles d'ingénierie permettant de satisfaire les exigences des documents 03, 06 et 08.
**Stack arrêtée** : voir §11 (décision du 12 novembre 2026, vérifiée en environnement de développement).

---

## 1. Vue d'ensemble

```
  Navigateur / PWA — site public, portail client, back-office
                               │  HTTPS / TLS 1.3
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  CDN + WAF (Cloudflare) : statiques, images, cache de bord                   │
                    └──────────┬───────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  Application web (Next.js 16, SSR/ISR)                                       │
                    │  - espace praticien, portail client                                          │
                    │  - page de réservation publique                                              │
                    └──────────┬───────────────────────────────────────────────────────────────────┘
                               │  REST /v1 (JSON)
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  API Gateway (auth OAuth2, quotas, validation de schéma)                     │
                    └───────────────┬─────────────┬─────────────┬─────────────┬─────────────┬──────┘
                                    │             │             │             │             │
                               ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
                               │  Agenda  │  │Scheduler │  │ Billing  │  │  Notify  │  │Documents │
                               └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                                │
                    ┌───────────────────────────────────────────▼──────────────────────────────────┐
                    │  PostgreSQL 18 (RLS multi-tenant, EXCLUDE GIST, partition)                   │
                    │  Redis (cache, verrous) · S3 (documents chiffrés)                            │
                    │  Files & événements : BullMQ (NATS JetStream en V2)                          │
                    └──────────────────────────────────────────────────────────────────────────────┘
```

**Principes**

1. **Monolithe modulaire** (modulith) en V1 : un seul déploiement, des modules à frontières
   explicites, prêts à être extraits en services si la charge l'exige. Ce choix réduit le coût
   d'exploitation d'une équipe de 7 personnes.
2. **PostgreSQL comme source de vérité**, y compris pour les contraintes d'exclusion temporelle.
3. **Traitements asynchrones** pour tout ce qui est long : matérialisation de séries, envois,
   synchronisation calendrier, exports.
4. **Idempotence par défaut** : toute opération mutante est rejouable.
5. **Observabilité native** : traces OpenTelemetry, métriques Prometheus, logs structurés JSON.

---

## 2. Choix technologiques

> **Note** : ce tableau est l'historique des choix de la première version du document. Il est
> conservé pour mémoire ; **le §11 (stack retenue) fait foi** pour toute décision d'implémentation,
> y compris les versions de bibliothèques et les arbitrages (ADR-011 à ADR-020).

| Couche | Choix | Justification | Alternatives écartées |
|---|---|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript strict | SSR pour le SEO de la page de réservation, PWA, écosystème | Remix (moins mature sur l'ISR), SvelteKit (recrutement) |
| UI | Tailwind CSS + Radix UI (accessibilité) | WCAG AA atteignable, thème par organisation | MUI (poids), Chakra |
| État serveur | TanStack Query | Cache, invalidation, mutations optimistes | SWR |
| API | Node.js 22 (Fastify 5) + TypeScript strict | Typage partagé front/back, validation Zod | Go (équipe moins familière), Python (perf) |
| Base | PostgreSQL 18 (min. 16) | `tstzrange`, `EXCLUDE USING GIST`, RLS, partitionnement, JSONB | MySQL (pas d'exclusion), MongoDB (pas de transactions riches) |
| Cache / verrous | Redis 7 | Verrous distribués, cache des disponibilités | Memcached |
| Files / événements | BullMQ (Redis), NATS JetStream en V2 | Léger, at-least-once, rejouable | Kafka (surdimensionné), SQS (couplage AWS) |
| Stockage fichiers | S3 compatible (OVH/Wasabi) | Chiffrement, cycle de vie, coût | Stockage local (non résilient) |
| Recherche | PostgreSQL `tsvector` puis OpenSearch en V2 | Simplicité initiale | Elasticsearch dès la V1 |
| Paiement | Stripe Connect | Standard de marché, split payments, PCI allégé | Adyen (contrat), Mollie (couverture) |
| SMS | Twilio + Vonage (fallback) | Couverture internationale, redondance | Un seul fournisseur (risque) |
| Courriel | Postmark (transactionnel) + SES (masse) | Délivrabilité | Sendgrid |
| Visio | Zoom API (V1), Whereby (option) | Attente du marché | Jitsi auto-hébergé (support) |
| IA | Fournisseur UE, API cloisonnée | Conformité art. 9 | Modèles auto-hébergés (coût GPU) |
| Infra | Kubernetes managé (EKS/OVH MKS) + Terraform | Portabilité, reproductibilité | Serverless (cold start sur l'agenda) |
| CI/CD | GitHub Actions, tests, SAST, SCA, SBOM | Intégré au dépôt | Jenkins |
| Observabilité | OpenTelemetry, Prometheus, Grafana, Loki, Sentry | Standard | Datadog (coût) |

---

## 3. Modèle de domaine

### 3.1 Entités principales

| Agrégat | Entités | Invariants |
|---|---|---|
| **Organisation** | Organization, Plan, Subscription, Feature flags | Un abonnement actif par organisation |
| **Identité** | User, Membership, Role, Permission, Session | Un utilisateur peut appartenir à N organisations |
| **Ressources** | Practitioner, Location, Room, Equipment, Service | Un service a une durée > 0 et un tarif ≥ 0 |
| **Disponibilité** | AvailabilityRule, AvailabilityException, Leave, Holiday | Pas de chevauchement de plages pour un même praticien |
| **Agenda** | Appointment, Occurrence, Series (RecurrenceRule), SeriesRevision | Pas de double réservation (contrainte d'exclusion) |
| **Client** | Client, Consent, CustomField | Un client appartient à une organisation |
| **Clinique** | ClinicalNote, TreatmentPlan, IntakeForm, FormSubmission | Une note signée est immuable (addendum uniquement) |
| **Finance** | Invoice, Payment, Refund, Package, SubscriptionBilling | Une facture émise est immuable ; avoirs explicites |
| **Communication** | MessageTemplate, Notification, Campaign, WaitlistEntry | Aucune donnée C4 dans un message sortant |
| **Audit** | AuditEntry, AccessLog | Append-only, chaîné |
| **Intégration** | ApiKey, WebhookEndpoint, CalendarConnection, SyncEvent | Signature vérifiée, rejeu borné |

### 3.2 Table `series` (extrait DDL)

```sql
CREATE TABLE series (
  id                ULID PRIMARY KEY,
  organization_id   ULID NOT NULL REFERENCES organization(id),
  practitioner_id   ULID NOT NULL REFERENCES practitioner(id),
  client_id         ULID NOT NULL REFERENCES client(id),
  service_id        ULID NOT NULL REFERENCES service(id),
  location_id       ULID REFERENCES location(id),
  freq              TEXT NOT NULL CHECK (freq = 'WEEKLY'),          -- R-01
  by_weekday        SMALLINT[] NOT NULL,                             -- ISO 1..7
  interval_weeks    SMALLINT NOT NULL CHECK (interval_weeks BETWEEN 1 AND 8),
  start_date        DATE NOT NULL,
  start_time        TIME NOT NULL,
  timezone          TEXT NOT NULL,                                   -- R-20
  duration_minutes  SMALLINT NOT NULL CHECK (duration_minutes BETWEEN 5 AND 480),
  end_mode          TEXT NOT NULL CHECK (end_mode IN
                      ('AFTER_COUNT','ON_DATE','AFTER_DURATION','NEVER')),
  end_count         SMALLINT,
  end_until         DATE,
  end_months        SMALLINT,
  end_weeks         SMALLINT,
  conflict_policy   TEXT NOT NULL DEFAULT 'SKIP'
                      CHECK (conflict_policy IN ('FAIL','SKIP','SHIFT_SAME_DAY')),
  shift_tolerance   SMALLINT NOT NULL DEFAULT 240,
  date_shift_policy TEXT NOT NULL DEFAULT 'SKIP'
                      CHECK (date_shift_policy IN ('SKIP','SHIFT_FORWARD','KEEP')),
  exdates           DATE[] NOT NULL DEFAULT '{}',
  rdates            DATE[] NOT NULL DEFAULT '{}',
  status            TEXT NOT NULL DEFAULT 'ACTIVE',
  revision          INTEGER NOT NULL DEFAULT 1,
  created_by        ULID NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT weekday_count CHECK (cardinality(by_weekday) BETWEEN 1 AND 5),
  CONSTRAINT weekday_range CHECK (by_weekday <@ ARRAY[1,2,3,4,5,6,7]::SMALLINT[]),
  CONSTRAINT end_mode_exclusive CHECK (
    (end_mode = 'AFTER_COUNT'    AND end_count IS NOT NULL AND end_until IS NULL AND end_months IS NULL AND end_weeks IS NULL) OR
    (end_mode = 'ON_DATE'        AND end_until IS NOT NULL AND end_count IS NULL AND end_months IS NULL AND end_weeks IS NULL) OR
    (end_mode = 'AFTER_DURATION' AND (end_months IS NOT NULL OR end_weeks IS NOT NULL) AND end_count IS NULL AND end_until IS NULL) OR
    (end_mode = 'NEVER'          AND end_count IS NULL AND end_until IS NULL AND end_months IS NULL AND end_weeks IS NULL)
  ),
  CONSTRAINT exdate_rdates_disjoint CHECK (NOT (exdates && rdates))
);
```

### 3.3 Table `appointment` et contrainte d'exclusion

```sql
CREATE TABLE appointment (
  id                ULID PRIMARY KEY,
  organization_id   ULID NOT NULL,
  series_id         ULID REFERENCES series(id) ON DELETE SET NULL,
  occurrence_key    TEXT,                    -- series_id@YYYYMMDDTHHMM  (R-17)
  client_id         ULID NOT NULL,
  practitioner_id   ULID NOT NULL,
  room_id           ULID,
  service_id        ULID NOT NULL,
  period            TSTZRANGE NOT NULL,      -- temps réel réservé (tampons inclus)
  status            TEXT NOT NULL,
  detached          BOOLEAN NOT NULL DEFAULT FALSE,
  detached_at       TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (series_id, occurrence_key),
  EXCLUDE USING GIST (
    practitioner_id WITH =,
    period WITH &&
  ) WHERE (status NOT IN ('CANCELLED_BY_CLIENT','CANCELLED_BY_PROVIDER','EXPIRED','RESCHEDULED'))
);

CREATE EXCLUDE INDEX ON appointment USING GIST (room_id WITH =, period WITH &&)
  WHERE room_id IS NOT NULL AND status NOT IN (…);

CREATE INDEX ON appointment (organization_id, practitioner_id, period);
CREATE INDEX ON appointment (client_id, period);
```

**Portée.** La contrainte `EXCLUDE` garantit au niveau **base de données** qu'aucun praticien (ni
salle) ne peut avoir deux rendez-vous chevauchants, même sous concurrence. C'est la seule manière
fiable de tenir l'exigence F-APT-06 ; un simple `SELECT` de vérification applicatif laisserait une
fenêtre de course.

---

## 4. Modules et frontières

| Module | Responsabilité | Publie | Consomme |
|---|---|---|---|
| `identity` | Utilisateurs, organisations, rôles, sessions | `user.*` | — |
| `scheduling` | Séries, occurrences, agenda, disponibilités | `series.*`, `occurrence.*` | `payment.captured` |
| `recurrence` | Moteur de récurrence pur (sans effet de bord) | — (bibliothèque) | — |
| `resources` | Lieux, salles, équipements, plafonds | `resource.*` | — |
| `clients` | Fiches, consentements, doublons | `client.*` | — |
| `clinical` | Notes, formulaires, documents | `note.*`, `document.*` | `occurrence.completed` |
| `billing` | Factures, paiements, forfaits | `invoice.*`, `payment.*` | `occurrence.completed` |
| `notifications` | Modèles, envois, préférences | `notification.*` | tous les événements |
| `waitlist` | Liste d'attente, offres | `waitlist.*` | `occurrence.cancelled` |
| `sync` | Google/Microsoft, ICS, webhooks | `sync.*` | `series.*`, `occurrence.*` |
| `analytics` | Agrégats, rapports | — | événements (projections) |
| `audit` | Journal immuable | — | tous |

**Règle d'or** : le module `recurrence` est une **bibliothèque pure**, sans accès base ni horloge
implicite (`now` injecté), testable en isolation ; c'est ce qui permet d'exécuter la double
implémentation (simulateur Python ↔ production TypeScript) et de comparer les résultats.

---

## 5. Stratégie de données

- **Multi-tenancy** : colonne `organization_id` sur toutes les tables métier + `ROW LEVEL SECURITY`
  PostgreSQL, avec `SET LOCAL app.organization_id` par transaction. Aucun accès applicatif ne peut
  omettre le filtre.
- **Partitionnement** : `appointment` partitionnée par mois (`period`), purge/archivage simples.
- **Index** : `GIST` pour les plages, `GIN` pour la recherche plein texte, `B-tree` composites pour
  les listes.
- **Migrations** : outil versionné (Atlas/Prisma Migrate), migrations **rétrocompatibles** (expand →
  migrate → contract), jamais de `DROP` dans le même déploiement que le code qui l'utilise.
- **Sauvegardes** : WAL continu + base de secours en lecture, restauration testée mensuellement.
- **Anonymisation** : job `gdpr-erasure` avec conservation pseudonymisée des factures.

---

## 6. Exigences de performance et dimensionnement

| Scénario | Volume de référence | Budget |
|---|---|---|
| Lecture d'agenda hebdomadaire (12 praticiens) | 300 rendez-vous | p95 < 250 ms |
| Création de série (14 occurrences) | — | p95 < 400 ms |
| `dryRun` de 40 occurrences | — | p95 < 150 ms |
| Matérialisation quotidienne | 10 000 séries actives | < 10 min, parallélisable |
| Envoi de 10 000 SMS | — | < 5 min, débit fournisseur |
| Export CSV de 100 000 lignes | — | < 60 s, en tâche de fond |
| Recherche client | 50 000 fiches | p95 < 120 ms |

**Dimensionnement V1** : 3 instances applicatives (2 vCPU / 4 Go), 1 PostgreSQL `db.r6g.large`
+ 1 réplica de lecture, Redis 1 Go, NATS 3 nœuds. Coût d'infrastructure estimé : 1 150 €/mois à
1 000 organisations actives (doc 10 §4).

---

## 7. Sécurité de l'architecture

Report détaillé au [document 04](04-securite-conformite.md). Points d'architecture :

- Terminaison TLS au CDN, TLS interne obligatoire, certificats gérés.
- Isolation des secrets par environnement, injection à l'exécution.
- Principe du « zero trust interne » : chaque service vérifie le jeton, pas seulement la gateway.
- Aucune donnée C4 en cache Redis ; les caches sont purgés sur changement de permission.
- Journalisation centralisée avec masquage automatique (regex sur e-mails, téléphones, noms).

---

## 8. Intégrations et interopérabilité

| Intégration | Protocole | Contraintes |
|---|---|---|
| Google Calendar | OAuth 2.0, Google Calendar API v3, push notifications | Quotas par utilisateur, reconnexion gérée |
| Microsoft Graph | OAuth 2.0, `delta` queries | Tenant admin consentement |
| Zoom | OAuth 2.0 / Server-to-Server | Limite de réunions simultanées |
| Stripe Connect | API REST + webhooks signés | Idempotence obligatoire, réconciliation quotidienne |
| ICS | RFC 5545, `RRULE`, `RECURRENCE-ID` | Voir R-24 |
| Webhooks sortants | HMAC-SHA256 | Rejeu, file morte |
| Comptabilité | CSV/FEC, QuickBooks (V1.1) | Période verrouillée |

---

## 9. Déploiement et exploitation

| Élément | Choix |
|---|---|
| Environnements | `dev`, `staging` (données synthétiques), `prod` (UE), `prod-ca` (Canada), `prod-us` (HIPAA, option) |
| Stratégie de release | Blue/green applicatif, migrations compatibles, feature flags |
| Rollback | Image précédente + migration inverse documentée pour chaque migration risquée |
| Runbooks | Incident, restauration, rotation de secrets, bascule régionale, purge RGPD |
| Astreinte | 24/7, escalade en 15 min, post-mortem sous 10 jours |
| Feature flags | `series.multi_weekday`, `series.shift_same_day`, `ai.notes`, `hipaa.region` |

---

## 10. Décisions d'architecture (ADR)

| ADR | Décision | Statut |
|---|---|---|
| ADR-001 | Monolithe modulaire plutôt que microservices en V1 | Acceptée |
| ADR-002 | PostgreSQL pour les contraintes temporelles (`EXCLUDE GIST`) | Acceptée |
| ADR-003 | Moteur de récurrence en bibliothèque pure, double implémentation de test | Acceptée |
| ADR-004 | Matérialisation paresseuse à horizon glissant (D1/R-11) | Acceptée |
| ADR-005 | Clé d'occurrence déterministe `series_id@YYYYMMDDTHHMM` (R-17) | Acceptée |
| ADR-006 | NATS JetStream pour les événements internes | **Révisée par ADR-015** (BullMQ en V1) |
| ADR-007 | Aucune donnée C4 en cache ni dans les notifications | Acceptée |
| ADR-008 | RLS PostgreSQL plutôt que filtres applicatifs seuls | Acceptée |
| ADR-009 | PWA avant application native | Acceptée |
| ADR-010 | Double région (UE/CA) dès la V1 sur l'offre Business | Acceptée |

---

## 11. Stack retenue (décision d'implémentation)

> **Statut** : arrêtée le 12 novembre 2026 · **Remplace** les colonnes « alternatives écartées »
> du §2 (conservées pour mémoire) · **ADR** : ADR-011 à ADR-020 (§12).
> **Vérification** : chaque brique majeure a été exécutée dans l'environnement de développement
> (Node 22.22, PostgreSQL 18.6 via PGlite, npm) avant d'être inscrite ici — voir §11.9.

### 11.1 Vue d'ensemble

```
  Navigateur / PWA — site public, portail client, back-office
                               │  HTTPS / TLS 1.3
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  Cloudflare (CDN, WAF, R2 pour les statiques)                                │
                    └──────────┬───────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  Next.js 16 (App Router) — TypeScript strict                                 │
                    │  Tailwind CSS 4 · Radix UI · TanStack Query 5                                │
                    └──────────┬───────────────────────────────────────────────────────────────────┘
                               │  REST /v1 (JSON, OAuth 2.0)
                    ┌──────────────────────────────────────────────────────────────────────────────┐
                    │  Fastify 5 + Zod 4 (validation + typage)                                     │
                    │  Drizzle ORM 0.45 · OpenAPI 3.1 générée                                      │
                    └───────────────┬─────────────┬─────────────┬─────────────┬─────────────┬──────┘
                                    │             │             │             │             │
                               ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
                               │  Agenda  │  │Scheduler │  │ Billing  │  │  Notify  │  │Documents │
                               └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                                │
                    ┌───────────────────────────────────────────▼──────────────────────────────────┐
                    │  PostgreSQL 18 (RLS, EXCLUDE GIST) · Redis 7 · S3 / R2                       │
                    │  Workers : matérialisation des séries, envois,                               │
                    │  synchronisation calendrier, exports, webhooks                               │
                    └──────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Tableau de la stack

| Couche | Technologie retenue | Version cible | Rôle | Pourquoi ce choix (et ce qui a été écarté) |
|---|---|---|---|---|
| **Langage** | TypeScript (strict) de bout en bout | 5.9 LTS *(TS 7 native en veille)* | Front, back, workers, scripts | Un seul langage = types partagés entre la règle de récurrence, l'API et l'UI ; écarté : Go (écosystème agenda faible), Python côté service (duplication de modèle) |
| **Runtime** | Node.js LTS | 22 (24 en V2) | Exécution serveur | Support long, `Intl`/ICU complet indispensable aux fuseaux IANA ; écarté : Deno/Bun (maturité des connecteurs Stripe/SMS, support opérateur) |
| **Monorepo** | pnpm workspaces + Turborepo | pnpm 10+, turbo 2.11 | Builds incrémentaux | Cache de build et de test ; `apps/web`, `apps/api`, `packages/recurrence`, `packages/contracts`, `packages/ui` |
| **Frontend** | Next.js (App Router) + React | 16.x / 19.x | Espace praticien, portail client, page de réservation | SSR/ISR pour le SEO de la réservation publique, PWA ; écarté : Remix, SvelteKit |
| **UI** | Tailwind CSS 4 + Radix UI | 4.3 / Radix 1.x | Design system accessible | Radix apporte le clavier, le focus et les rôles ARIA (RGAA/WCAG AA) ; jetons de thème par organisation |
| **État serveur** | TanStack Query | 5.107 | Cache, mutations optimistes | Invalidation fine après création de série |
| **Formulaires** | TanStack Form + Zod | 1.33 | Formulaires complexes (règle de récurrence) | Validation partagée client/serveur avec le **même schéma Zod** |
| **API** | Fastify + `fastify-type-provider-zod` | 5.12 | API REST `/v1` | Validation native du contrat, sérialisation typée, 422 automatiques, OpenAPI générée ; écarté : NestJS (surcharge de décorateurs), Hono (excellent mais écosystème de plugins moins complet côté Node) |
| **Validation** | Zod | 4.6 | Schémas d'entrée/sortie | Source unique : les schémas de `packages/contracts` alimentent API, formulaires, tests et `schemas/recurrence-rule.schema.json` |
| **Base de données** | PostgreSQL | 18 (min. 16) | Source de vérité | `tstzrange`, `EXCLUDE USING GIST`, `RLS`, partitionnement, `btree_gist` (extension requise pour l'exclusion multi-colonnes) ; **testé en local** (chevauchement refusé, créneau contigu accepté) |
| **ORM / migrations** | Drizzle ORM + Drizzle Kit | 0.45 / 0.31 | Accès typé, migrations SQL versionnées | SQL explicite conservé (contraintes d'exclusion, index partiels) ; écarté : Prisma (moins bon accès aux types PostgreSQL avancés) |
| **Cache / verrous** | Redis | 7 | Cache de disponibilités, verrous, files légères | Verrou pessimiste par praticien-jour en appoint de la contrainte SQL |
| **Files / événements** | BullMQ (Redis) en V1, NATS JetStream si montée en charge | 6.7 | Matérialisation, envois, exports, webhooks | BullMQ suffit à 10 000 organisations et se teste en local ; l'abstraction `packages/jobs` permet le passage à NATS sans réécrire les consommateurs |
| **Temps & fuseaux** | `Temporal` (polyfill) encapsulé dans `packages/recurrence` | Polyfill TC39 | Résolution des heures murales (R-06) | **Vérifié** : `Temporal` n'est pas exposé par Node 22 — on l'embarque derrière une interface `LocalTime` (remplaçable par le natif sans changer le domaine) ; aucun stockage sans fuseau IANA |
| **Moteur de récurrence** | `packages/recurrence` (TypeScript pur) + oracle Python | — | Génération des occurrences | Bibliothèque pure, sans I/O ni horloge implicite (`now` injecté) ; comparée en CI aux 400 séries du simulateur, montée à 10 000 en nightly (doc 06 §14, doc 09 §1.2) |
| **Authentification** | OAuth 2.0 + PKCE, lien magique, TOTP, WebAuthn | SimpleWebAuthn 14 | Sessions praticiens et clients | Argon2id pour les secrets ; aucune bibliothèque maison |
| **Paiements** | Stripe Connect | SDK 23 | Encaissement, acomptes, forfaits | Comptes connectés = MyRDV n'est pas marchand, périmètre PCI allégé |
| **Notifications** | Postmark (transactionnel), SES (masse), Twilio + Vonage (SMS) | SDK 5 / 6 | Rappels, confirmations, récapitulatif de série | Templates MJML versionnés ; fallback SMS pour la redondance ; **aucune donnée de santé** dans les messages (NFR-CMP-06) |
| **Visio** | Zoom API (V1), Whereby (option) | — | Téléconsultation | Lien par occurrence, identifiant chiffré |
| **Fichiers** | S3 compatible (OVH / Cloudflare R2) | — | Documents, exports, ICS | Chiffrement au repos, cycle de vie, URL présignées courtes |
| **PDF (documents clients)** | `build_pdf.py` (reportlab) pour la documentation ; moteur interne TypeScript pour les factures | — | Cahier des charges, dossier patient, factures | Deux besoins distincts : documentation éditoriale (Python) et documents transactionnels (rendu serveur, gabarits HTML→PDF) |
| **Tests** | Vitest (+ fast-check), Testcontainers/PGlite, Playwright, k6 | Vitest 5.1 / Playwright 1.65 | Unitaires, propriétés, intégration, E2E, charge | PGlite (PostgreSQL 18 WASM) permet des tests d'intégration **sans Docker** en local et en CI |
| **Observabilité** | OpenTelemetry, Prometheus, Grafana, Loki, Sentry | SDK 0.301 | Traces, métriques, logs, erreurs | Corrélation `requestId` de bout en bout, alerte sur la divergence récurrence |
| **CI/CD** | GitHub Actions + Turborepo remote cache, SAST/SCA, SBOM | — | Qualité et livraison | Gates : typage, lint, tests, couverture, `schemas`, budget de perf |
| **Infrastructure** | Kubernetes managé (OVH MKS / EKS) + Terraform, 2 régions (UE + Canada) | — | Hébergement | Région UE par défaut, Canada pour la Loi 25 ; images distroless, secrets via KMS |
| **Outillage dev** | Node 22 + `--experimental-strip-types` (scripts), ESLint, Prettier, Drizzle Studio | — | Scripts internes | Exécution des scripts TypeScript sans étape de build |

### 11.3 Chaîne de versions et politique de mise à jour

| Élément | Règle |
|---|---|
| Node.js | LTS uniquement, mise à jour dans les 90 jours suivant le passage en LTS |
| Dépendances | Renovate en mode « PR groupées » ; correctifs de sécurité < 7 jours (critique), < 30 jours (élevé) |
| TypeScript | Version LTS ; pas de migration vers TypeScript 7 natif avant stabilisation de l'écosystème (types, ESLint, Drizzle) |
| PostgreSQL | Version majeure N-1 minimum ; montée testée en staging sur un dump réel anonymisé |
| Navigateurs | 2 dernières versions de Chrome, Firefox, Safari, Edge ; Safari iOS 16+ |

### 11.4 Ce que la stack garantit vis-à-vis du cahier des charges

| Exigence | Mécanisme de la stack |
|---|---|
| F-APT-06 / F-APT-13 (aucun double booking) | Contrainte `EXCLUDE USING GIST` PostgreSQL + transaction sérialisable, pas seulement un contrôle applicatif |
| R-06 / R-20 (heures murales, changement d'heure) | `Temporal` encapsulé, fuseau IANA obligatoire en base (`TEXT NOT NULL` + validation), tests DST dans `packages/recurrence` |
| R-14 (aucune perte silencieuse) | Schéma Zod de sortie obligatoire : `skipped[]`, `skippedConflict[]`, `warnings[]` non optionnels |
| R-17 (idempotence) | `UNIQUE (series_id, occurrence_key)` + `Idempotency-Key` persistée côté API |
| NFR-SEC-06 (cloisonnement rôles) | RLS PostgreSQL + permissions atomiques vérifiées dans la couche service |
| NFR-PERF-01/02 | Index `GIST`/`B-tree` ciblés, cache Redis des disponibilités, mesures k6 en CI nocturne |
| NFR-CMP-06 (pas de donnée de santé dans les messages) | Templates MJML contrôlés par une liste blanche de variables + test automatisé |
| Doc 06 §1.2 (double implémentation) | `packages/recurrence` (TS) vs `tools/recurrence_simulator.py` (oracle), comparés à chaque CI |

### 11.5 Coût de la stack

| Poste | Coût mensuel (1 000 organisations actives) |
|---|---|
| Kubernetes (2 régions, 3 nœuds applicatifs + base managée) | ≈ 620 € |
| PostgreSQL managé (HA, sauvegardes PITR) | ≈ 260 € |
| Redis, stockage objet, CDN/WAF | ≈ 150 € |
| Observabilité (traces, logs, erreurs) | ≈ 90 € |
| Outils de développement (CI, cache distant, design) | ≈ 50 € |
| **Total** | **≈ 1 170 €/mois** (cible NFR-CST-01 : < 1,60 € par organisation) |

### 11.6 Risques liés à la stack et parades

| Risque | Parade |
|---|---|
| Immaturité de `Temporal` (polyfill) | Interface `LocalTime` isolée dans `packages/recurrence`, tests DST exhaustifs, bascule vers le natif sans impact domaine |
| Écosystème TypeScript 7 encore partiel | Rester sur la version LTS tant que Drizzle, ESLint et les types ne sont pas alignés |
| Dépendance à PostgreSQL pour les contraintes d'exclusion | Aucune alternative ne garantit l'atomicité : contrainte conservée, migration vers un autre SGBD écartée (ADR-002) |
| Fournisseurs SMS/e-mail | Double fournisseur SMS, file de reprise, alertes de délivrabilité |
| Absence de Docker en local (poste dev léger) | PGlite pour les tests d'intégration ; Testcontainers en CI |

### 11.7 Ce qui n'est **pas** dans la stack V1

- Pas de microservices : monolithe modulaire (ADR-001).
- Pas d'application mobile native : PWA ; React Native/Expo évalué en V2 (§10 du doc 10).
- Pas de GraphQL : REST + OpenAPI 3.1 (ADR-011).
- Pas de recherche externe : `tsvector` PostgreSQL ; OpenSearch en V2.
- Pas d'IA en V1 : fournisseur UE cloisonné en V1.1 (F-AI-01).

### 11.8 Adoptions à confirmer en revue d'architecture

| # | Question | Recommandation |
|---|---|---|
| 1 | Fastify vs Hono pour l'API | **Fastify** (plugins, validation Zod native, écosystème Node) — Hono reste candidat si l'on privilégie l'exécution en Edge |
| 2 | BullMQ vs NATS JetStream dès la V1 | **BullMQ** (coût d'exploitation), abstraction `packages/jobs` prête pour NATS |
| 3 | Polyfill `Temporal` vs `date-fns-tz` | **`Temporal`** (sémantique normalisée), repli `Intl` documenté |
| 4 | Rendu PDF des factures | Gabarits HTML + moteur serveur (Chromium headless ou Wolf) ; à trancher avec les contraintes d'archivage légal |

### 11.9 Vérifications exécutées le 12 novembre 2026

| Brique | Test | Résultat |
|---|---|---|
| Node 22.22 + `--experimental-strip-types` | import d'un module TypeScript | OK |
| Vitest 5.1 | test unitaire sur `addMonths` (écrêtage fin de mois) | 1/1 |
| PostgreSQL 18.6 (PGlite 0.5) | `EXCLUDE USING GIST (period WITH &&)` | chevauchement refusé (`23P01`), créneau contigu accepté |
| Zod 4.6 + Fastify 5.12 | validation de `POST /v1/series/preview` | 200 conforme, 400 sur `interval = 0` |
| Drizzle 0.45 + PGlite | insertion et lecture typées | 1 ligne |
| `Intl` ICU complet | offsets Europe/Paris autour des changements d'heure | +01:00 / +02:00 corrects |
| `Temporal` | disponibilité native dans Node 22 | **indisponible → polyfill requis** |
| Versions npm | `next`, `react`, `tailwindcss`, `drizzle-orm`, `zod`, `fastify`, `vitest`, `playwright`, `stripe`, `twilio` | résolues et notées au §11.2 |

---

## 12. ADR complémentaires

| ADR | Décision | Statut |
|---|---|---|
| ADR-011 | API REST/JSON avec OpenAPI 3.1 générée depuis les schémas Zod | Acceptée |
| ADR-012 | Fastify + Zod comme socle de l'API (plutôt que NestJS) | Acceptée |
| ADR-013 | Drizzle ORM avec SQL explicite pour les contraintes PostgreSQL avancées | Acceptée |
| ADR-014 | `Temporal` encapsulé derrière une interface `LocalTime` (polyfill en V1) | Acceptée |
| ADR-015 | BullMQ en V1, abstraction `packages/jobs` compatible NATS | Acceptée |
| ADR-016 | Monorepo pnpm + Turborepo, `packages/recurrence` sans dépendance framework | Acceptée |
| ADR-017 | PGlite pour les tests d'intégration sans Docker | Acceptée |
| ADR-018 | Double fournisseur SMS (Twilio + Vonage) avec bascule automatique | Acceptée |
| ADR-019 | Deux régions (UE + Canada) dès la V1 sur l'offre Business | Acceptée |
| ADR-020 | Pas de GraphQL, pas de microservices, pas de mobile natif en V1 | Acceptée |


---

*Suite : [`08-exigences-non-fonctionnelles.md`](08-exigences-non-fonctionnelles.md).*

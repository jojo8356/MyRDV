# 05 — Architecture technique

**Document** : 05 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Objectif** : décrire l'architecture cible, le modèle de domaine, les choix technologiques et les
règles d'ingénierie permettant de satisfaire les exigences des documents 03, 06 et 08.

---

## 1. Vue d'ensemble

```
                       ┌────────────────────────────────────────────┐
   Navigateur / PWA ───▶│  CDN + WAF (Cloudflare)                    │
   Site public         └───────────────┬────────────────────────────┘
                                       │ TLS 1.3
                       ┌───────────────▼────────────────────────────┐
                       │  Application web (Next.js 15, SSR/ISR)     │
                       │  - espace praticien, portail client        │
                       │  - page de réservation publique            │
                       └───────────────┬────────────────────────────┘
                                       │ REST /v1 (JSON)
        ┌──────────────────────────────▼───────────────────────────────┐
        │  API Gateway (auth OAuth2, quotas, validation de schéma)      │
        └───┬──────────┬──────────┬──────────┬──────────┬──────────────┘
            │          │          │          │          │
     ┌──────▼───┐ ┌────▼─────┐ ┌──▼──────┐ ┌─▼───────┐ ┌▼──────────┐
     │ Agenda   │ │Scheduler │ │ Billing │ │ Notify  │ │ Documents │
     │ service  │ │(récurrence│ │ service │ │ service │ │ service   │
     └──────┬───┘ └────┬─────┘ └──┬──────┘ └─┬───────┘ └┬──────────┘
            │          │          │          │          │
     ┌──────▼──────────▼──────────▼──────────▼──────────▼──────────┐
     │  PostgreSQL 16 (RLS multi-tenant, EXCLUDE GIST, partition)   │
     │  Redis (cache, verrous, files) · S3 (documents chiffrés)     │
     └──────────────────────────┬───────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ Bus d'événements       │
                    │ (NATS JetStream)       │
                    └────────────────────────┘
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

| Couche | Choix | Justification | Alternatives écartées |
|---|---|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript strict | SSR pour le SEO de la page de réservation, PWA, écosystème | Remix (moins mature sur l'ISR), SvelteKit (recrutement) |
| UI | Tailwind CSS + Radix UI (accessibilité) | WCAG AA atteignable, thème par organisation | MUI (poids), Chakra |
| État serveur | TanStack Query | Cache, invalidation, mutations optimistes | SWR |
| API | Node.js 22 (Fastify) + TypeScript, ou NestJS | Typage partagé front/back, validation Zod | Go (équipe moins familière), Python (perf) |
| Base | PostgreSQL 16 | `tstzrange`, `EXCLUDE USING GIST`, RLS, partitionnement, JSONB | MySQL (pas d'exclusion), MongoDB (pas de transactions riches) |
| Cache / verrous | Redis 7 | Verrous distribués, cache des disponibilités | Memcached |
| Files / événements | NATS JetStream | Léger, at-least-once, rejouable | Kafka (surdimensionné), SQS (couplage AWS) |
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
| ADR-006 | NATS JetStream pour les événements internes | Acceptée |
| ADR-007 | Aucune donnée C4 en cache ni dans les notifications | Acceptée |
| ADR-008 | RLS PostgreSQL plutôt que filtres applicatifs seuls | Acceptée |
| ADR-009 | PWA avant application native | Acceptée |
| ADR-010 | Double région (UE/CA) dès la V1 sur l'offre Business | Acceptée |

---

*Suite : [`08-exigences-non-fonctionnelles.md`](08-exigences-non-fonctionnelles.md).*

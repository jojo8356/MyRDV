# 09 — Plan de tests et de recette

**Document** : 09 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Objectif** : démontrer que le produit satisfait les documents 03, 04, 06 et 08, avec un niveau de
preuve proportionné au risque (données de santé, facturation, temps).

---

## 1. Stratégie

### 1.1 Pyramide des tests

| Niveau | Part | Outils | Portée |
|---|---|---|---|
| Unitaires | 60 % | Vitest (TS), pytest (Python) | Moteur de récurrence, arithmétique de dates, calculs de facturation |
| Propriétés (property-based) | 8 % | fast-check, Hypothesis | Invariants I-1 à I-10 du document 06 |
| Intégration | 22 % | Vitest + Testcontainers (PostgreSQL, Redis) | Contraintes SQL, transactions, contraintes d'exclusion |
| Contrat d'API | 5 % | Schemathesis / Dredd | OpenAPI 3.1, erreurs, idempotence |
| End-to-end | 4 % | Playwright | Parcours critiques |
| Charge / chaos | 1 % | k6, Toxiproxy | SLO, résilience |
| Manuel / recette | — | Cahier de recette | UX, accessibilité, conformité |

### 1.2 Principe de la **double implémentation**

Le moteur de récurrence fait l'objet de deux réalisations indépendantes :

1. **Oracle** : [`tools/recurrence_simulator.py`](../tools/recurrence_simulator.py) (Python, sans
   dépendance, écrit à partir du document 06).
2. **Production** : bibliothèque TypeScript `@myrdv/recurrence`.

En CI, **10 000 séries générées aléatoirement** (graine fixe + tirage quotidien) sont exécutées sur
les deux implémentations ; toute divergence est bloquante (`series_generation_discrepancy_total > 0`).
Cette technique attrape les erreurs de type « jour de fin de mois », « changement d'heure » et
« semaine ISO » qui échappent aux tests d'exemple.

---

## 2. Couverture et qualité

| Périmètre | Couverture minimale |
|---|---|
| Module `recurrence` | 100 % des branches, 100 % des règles R-01 → R-24 |
| Module `billing` | 95 % |
| Modules `scheduling`, `clients` | 90 % |
| Global | 80 % |
| Tests de non-régression | 1 test par code d'erreur (`SER_*`) |

**Gates CI bloquants** : typage strict, lint, tests, couverture, SAST, SCA, SBOM, contrat d'API,
budget de performance nocturne.

---

## 3. Cas de test du moteur de récurrence

Tous les cas ci-dessous sont dérivés des règles et du simulateur ; ils constituent le **cahier de
recette du module**.

### 3.1 Bornes et bases

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-001 | 3 mois, lundi 16/11/2026 09:00, 1 j/sem | 14 séances, dernière le 15/02/2027, `until=2027-02-16` | R-05 |
| T-REC-002 | Même série pour les 7 jours de départ | 14 séances chacune | R-05 |
| T-REC-003 | `weeks=6` | 7 séances, `until=2026-12-28` | R-05 |
| T-REC-004 | `until=2026-12-14` | 5 séances, dernière incluse | R-04 |
| T-REC-005 | Prévisualisation de 40 occurrences | < 150 ms, `count` exact, liste datée | R-14 |
| T-REC-006 | `count=5`, intervalle 2, mardi | 17/11, 01/12, 15/12, 29/12, 12/01 | R-03 |
| T-REC-007 | `BYDAY=MO,WE,FR`, 3 mois | 40 séances | R-01 |
| T-REC-008 | Intervalle 1 à 8 acceptés, 0 et 9 refusés | `SER_003_BAD_INTERVAL` | R-02 |
| T-REC-009 | `byWeekday` vide, doublon, valeur 0/8 | `SER_001` / `SER_002` | R-01 |
| T-REC-010 | Début un mardi avec `BYDAY=MO` | `SER_005_START_WEEKDAY_MISMATCH` | R-01 |

### 3.2 Calendrier et fuseaux

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-011 | `addMonths(2026-01-31, 1)` | 2026-02-28 | R-05 |
| T-REC-012 | `addMonths(2024-01-31, 1)` | 2024-02-29 | R-05 |
| T-REC-013 | `addMonths(2024-02-28, 12)` | 2025-02-28 | R-05 |
| T-REC-014 | Paris, dimanche 02:30, 28/03/2027 | 03:00 CEST, même jour, durée 60 min | R-06 |
| T-REC-015 | Paris, dimanche 02:30, 25/10/2026 | premier passage (CEST) | R-06 |
| T-REC-016 | Montréal 09:00 traversant le 14/03/2027 | 09:00 EST puis 09:00 EDT, UTC décalé | R-06 |
| T-REC-017 | Série à 23:30 traversant un passage | heure murale conservée | R-06 |
| T-REC-018 | Fuseau inconnu (`Mars/Olympus`) | `SER_023_TIMEZONE_REQUIRED` / validation | R-20 |
| T-REC-019 | Fuseau absent du payload | `422 SER_023_TIMEZONE_REQUIRED` | R-20 |

### 3.3 Exceptions et jours fermés

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-020 | 2 jours fermés sur 12, politique `SKIP` | 10 occurrences + `skipped[BLACKOUT]` | R-07/R-14 |
| T-REC-021 | Jour férié `SHIFT_FORWARD` | report au premier jour disponible, sans doublon | R-07 |
| T-REC-022 | `KEEP` sur jour férié | occurrence maintenue | R-07 |
| T-REC-023 | `exdate` sur une occurrence future | occurrence retirée, compteur non consommé | R-08 |
| T-REC-024 | `rdate` hors borne | ignorée + avertissement | R-08 |
| T-REC-025 | Date à la fois `exdate` et `rdate` | `SER_021_EXDATE_RDATE_CONFLICT` | R-08 |
| T-REC-026 | Congé praticien de 2 semaines | occurrences de la période exclues avec motif `LEAVE` | R-07 |

### 3.4 Idempotence et régénération

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-026b | Double génération identique | aucune création, aucune suppression | R-17 |
| T-REC-027 | Régénération après `exdate` | la date retirée n'est pas recréée | R-17 |
| T-REC-028 | Régénération après occurrence `COMPLETED` | occurrence conservée intacte | R-17 |
| T-REC-029 | Occurrence orpheline (règle modifiée) | supprimée si future et non détachée | R-17 |

### 3.5 Conflits

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-030 | `FAIL` avec 1 conflit sur 12 | aucune occurrence créée, `409` | R-09 |
| T-REC-031 | `SHIFT_SAME_DAY`, 09:00 occupé | 10:00, `shiftedMinutes=60` | R-09 |
| T-REC-032 | `SHIFT_SAME_DAY` avec tolérance 0 | `SKIP` implicite | R-09 |
| T-REC-033 | `SHIFT_SAME_DAY` sans créneau dans ±4 h | occurrence ignorée + motif | R-09 |
| T-REC-034 | 6 conflits avec budget 5 | `422 SER_018_CONFLICT_BUDGET` | R-09 |
| T-REC-035 | 3 conflits consécutifs | `409 SER_019_CONSECUTIVE_CONFLICTS` | R-09 |
| T-REC-036 | Conflit de **salle** uniquement sur 1 occurrence | `FAIL` refuse tout ; `SKIP` retire 1 | R-19 |
| T-REC-037 | Concurrence : 2 créations simultanées du même créneau | 1 succès, 1 `409`, aucune incohérence | F-APT-13 |
| T-REC-038 | Tampon de 15 min, autre RDV à 10:10 | conflit détecté (E18b) | R-09 |

### 3.6 Modification et suppression

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-039 | `THIS` sur le 07/12 → 14:00 | une occurrence détachée, règle inchangée | R-13 |
| T-REC-040 | `THIS_AND_FOLLOWING` au 11/01 | occurrences antérieures conservées, suivantes recalculées, `diff` | R-12 |
| T-REC-041 | `ALL` de 09:00 → 09:30 | `diff.updated` listé, passées intactes, détachées préservées | R-12 |
| T-REC-042 | `ALL` réduisant `count` de 14 à 12 | 2 suppressions futures, 0 suppression passée | R-12 |
| T-REC-043 | Suppression `THIS` | `exdate` ajouté, série intacte | R-22 |
| T-REC-044 | Suppression totale sans `confirmCount` | `428 SER_024_CONFIRMATION_REQUIRED` | R-22 |
| T-REC-045 | Suppression avec occurrences facturées | occurrences passent `CANCELLED`, jamais supprimées | R-22/R-23 |
| T-REC-046 | Détachement vers une date de la série | `409 SER_022_OCCURRENCE_COLLISION` | R-13 |
| T-REC-047 | Retour arrière (`revert`) | état de la règle restauré, audit tracé | R-12 |

### 3.7 Plafonds, sécurité et performance

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-048 | `count=200` (offre Pro) | `422 SER_007_COUNT_OVER_CAP`, `details.limit=104` | R-16 |
| T-REC-049 | `months=13` | `422 SER_010_DURATION_OVER_CAP` | R-10 |
| T-REC-050 | Première occurrence dans 1 h | `422 SER_016_LEAD_TIME` | R-10 |
| T-REC-051 | `months` + `count` ensemble | `422 SER_020_END_MODE_EXCLUSIVE` | R-03/R-05 |
| T-REC-052 | Série `NEVER` | bornée, `windowEndsAt` renseigné | R-15 |
| T-REC-053 | 26 séries actives (offre Solo, plafond 20) | `402 SER_026_PLAN_LIMIT_SERIES` | R-16 |
| T-REC-054 | Divergence simulateur / production sur 10 000 tirages | 0 divergence | R-17 |
| T-REC-055 | Série de 104 occurrences, `dryRun` | < 60 ms p95 | doc 06 §6.2 |
| T-REC-056 | Récapitulatif de série | 1 seul message, pas de donnée de santé | R-18/NFR-CMP-06 |

### 3.8 Interopérabilité

| ID | Cas | Attendu | Règle |
|---|---|---|---|
| T-REC-057 | Export ICS réimporté dans Google Agenda | mêmes dates et heures | R-24 |
| T-REC-058 | Export ICS réimporté dans Outlook | mêmes dates, `RRULE` respectée | R-24 |
| T-REC-059 | Export ICS avec occurrence détachée | `RECURRENCE-ID` correct | R-24 |
| T-REC-060 | Import ICS récurrent d'un tiers | règle équivalente reconstituée ou refus explicite | R-24 |

---

## 4. Cas de test transverses

| ID | Domaine | Cas |
|---|---|---|
| T-SEC-002 | Sécurité | MFA obligatoire pour admin |
| T-SEC-003 | Sécurité | Refresh token rejoué → révocation de la famille |
| T-SEC-012 | Sécurité | Absence de donnée C4 dans les logs, courriels, SMS, webhooks |
| T-SEC-020 | Sécurité | Isolation multi-tenant (accès croisé refusé sur 62 endpoints) |
| T-SEC-021 | Sécurité | Intégrité du journal d'audit (chaîne de hachage) |
| T-SEC-030 | Sécurité | Limitation de débit et refus des séries géantes |
| T-SEC-040 | Sécurité | Matrice de rôles : 7 rôles × 64 permissions |
| T-API-030 | API | Idempotence (rejeu, clé réutilisée avec corps différent) |
| T-API-040 | API | Pagination et curseurs stables |
| T-CMP-010 | Conformité | Export complet (JSON/CSV) restituable |
| T-CMP-011 | Conformité | Effacement + pseudonymisation des factures |
| T-A11Y-001 | Accessibilité | Parcours de réservation au clavier et lecteur d'écran |
| T-A11Y-002 | Accessibilité | Création de série au clavier (NVDA) |
| T-PERF-01..20 | Performance | Budgets du document 08 §1 |
| T-CHAOS-001 | Résilience | Perte d'un nœud applicatif en pleine création de série |
| T-CHAOS-002 | Résilience | Indisponibilité de Stripe → file de reprise, aucune perte |
| T-UX-001 | Ergonomie | Création d'une série de 3 mois en ≤ 45 s (5 utilisateurs) |
| T-UX-002 | Ergonomie | Réservation client en ≤ 4 écrans (test modéré) |

---

## 5. Recette utilisateur

### 5.1 Protocole

- **5 utilisateurs** par persona (P1, P2, P3, P5) + **8 clients finaux** (P4).
- Sessions filmées, observation, mesure du temps de réalisation et du taux de réussite.
- Scénarios :

| # | Scénario | Critère de succès |
|---|---|---|
| S1 | Poser une série de 3 mois, 1 fois par semaine, en excluant les jours fériés | Réussite sans aide en < 45 s |
| S2 | Décaler une seule séance sans casser la série | Réussite 100 %, aucune occurrence perdue |
| S3 | Passer la série en bi-hebdomadaire à partir de janvier | `diff` compris et validé |
| S4 | Supprimer la série avec confirmation du nombre de séances | Aucune suppression accidentelle |
| S5 | Comprendre pourquoi 2 séances n'ont pas été planifiées | L'utilisateur explique le motif |
| S6 | Réserver un rendez-vous depuis un téléphone sans compte | ≤ 4 écrans, < 90 s |
| S7 | Annuler en ligne dans le délai | Confirmation reçue, créneau libéré |
| S8 | Retrouver les notes d'une séance dans le dossier client | < 30 s, rôles respectés |

### 5.2 Critères de sortie de recette

| Critère | Seuil |
|---|---|
| Scénarios critiques S1-S5 réussis sans aide | ≥ 90 % des participants |
| Note d'utilisabilité (SUS) | ≥ 80 |
| Défauts bloquants ouverts | 0 |
| Défauts majeurs ouverts | ≤ 3, avec plan |
| Couverture des exigences MUST testées | 100 % |
| Tests automatisés verts (tous niveaux) | 100 % |

### 5.3 Recette de conformité (RSSI + DPO)

- Revue du registre des traitements, de la DPIA et des mentions d'information.
- Vérification du contenu des notifications (aucune donnée de santé).
- Vérification de l'export, de l'effacement et de la pseudonymisation.
- Vérification des journaux d'audit sur un échantillon de 20 actions.
- Vérification du DPA et de la liste des sous-traitants.

---

## 6. Environnements et jeux de données

| Environnement | Données | Usage |
|---|---|---|
| `dev` | Synthétiques, réinitialisées à la demande | Développement |
| `staging` | Synthétiques réalistes (10 000 rendez-vous, 500 séries, 5 fuseaux) | Tests E2E, performance, recette |
| `prod` | Réelles | Aucune donnée réelle hors production |

**Jeu de données de référence** : 12 praticiens, 4 lieux, 9 salles, 3 000 clients, 500 séries couvrant
les 4 modes de fin, 5 fuseaux (Europe/Paris, America/Montreal, America/Toronto, Asia/Tokyo, UTC),
2 années de rendez-vous, 3 jours fériés par pays. Ce jeu est versionné et reproductible par script.

---

## 7. Gestion des anomalies

| Sévérité | Définition | Délai de correction |
|---|---|---|
| **Bloquant** | Perte de données, facturation erronée, accès non autorisé, rendez-vous manqué sans alerte | Immédiat, rollback si nécessaire |
| **Majeur** | Fonction inutilisable sans contournement raisonnable | < 5 jours ouvrés |
| **Mineur** | Gêne avec contournement | Prochain sprint |
| **Cosmétique** | Esthétique, libellé | Backlog |

Toute anomalie touchant la récurrence est étiquetée `module:recurrence` et **ajoutée au jeu de
non-régression** avec un test automatisé, sans exception.

---

## 8. Traçabilité des tests

| Document source | Exigences | Tests associés |
|---|---|---|
| 03 (exigences) | 195 | T-REC-*, T-API-*, T-SEC-*, T-UX-*, T-CMP-* |
| 06 (récurrence) | 24 règles | T-REC-001 → T-REC-060 |
| 04 (sécurité/conformité) | 10 mesures | T-SEC-*, T-CMP-* |
| 08 (NFR) | 87 | T-PERF-*, T-A11Y-*, T-CHAOS-*, T-UX-* |

La matrice détaillée (exigence → test → résultat) est produite automatiquement par l'outil de
gestion des tests à chaque exécution de CI et archivée avec la version.

---

## 9. Planning de recette

| Semaine | Activité |
|---|---|
| S18 | Gel des fonctionnalités, jeu de données complet, tests automatisés complets |
| S19 | Recette interne (QA), performance, sécurité (pentest interne) |
| S20 | Recette utilisateur (5 + 8 participants), corrections |
| S21 | Recette de conformité (RSSI + DPO), audit d'accessibilité |
| S22 | Go/no-go, répétition générale de déploiement, mise en production (GA) |

---

*Suite : [`10-roadmap-budget-risques.md`](10-roadmap-budget-risques.md).*

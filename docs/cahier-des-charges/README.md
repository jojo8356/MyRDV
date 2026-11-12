# Cahier des charges — MyRDV

> **Nom de code du produit** : MyRDV
> **Référence de comparaison** : GOrendezvous (plateforme québécoise de prise de rendez-vous et de gestion de clinique)
> **Version du document** : 1.0
> **Date** : 12 novembre 2026
> **Statut** : Baseline de spécification — soumise à revue (comité produit, architecture, sécurité, juridique)
> **Classification** : Interne + diffuseurs partenaires

---

## 1. Objet

Ce dossier constitue le **cahier des charges fonctionnel et technique complet** de MyRDV, une
plateforme SaaS de prise de rendez-vous, de gestion d'agenda multi-professionnels et de tenue de
dossiers clients, destinée aux professionnels de la santé, du bien-être, de la beauté et des
services.

Il poursuit trois objectifs :

1. **Analyse concurrentielle exhaustive** des fonctionnalités de GOrendezvous, secteur par secteur,
   avec grille de couverture et écarts assumés (§4).
2. **Spécification produit consolidée** de MyRDV : personas et parcours (doc 02), 195 exigences
   fonctionnelles numérotées (doc 03), sécurité et conformité (doc 04), architecture et modèle de
   domaine (doc 05), 87 exigences non fonctionnelles (doc 08), plan de tests (doc 09) et trajectoire
   budgétée (doc 10).
3. **Spécification de référence du module « rendez-vous récurrents »** — le différenciateur majeur
   du produit : récurrence hebdomadaire, limites de répétition (nombre, date, durée : « 3 mois, une
   fois par semaine »), exceptions, conflits, fuseaux horaires et changement d'heure — 24 règles
   normatives (doc 06), contrat d'API (doc 07), simulateur exécutable et schéma JSON.

## 2. Structure du dossier

| # | Document | Contenu | Public principal |
|---|----------|---------|------------------|
| 00 | [`00-synthese-executive.md`](docs/00-synthese-executive.md) | Synthèse dirigeante, chiffres clés, décisions attendues, risques | Direction, investisseurs |
| 01 | [`01-contexte-analyse-marche.md`](docs/01-contexte-analyse-marche.md) | Contexte, marché, concurrence, **analyse fonctionnelle exhaustive de GOrendezvous** | Produit, marketing |
| 02 | [`02-personas-utilisateurs.md`](docs/02-personas-utilisateurs.md) | Personas, parcours utilisateurs, JTBD, matrice de droits | Produit, design |
| 03 | [`03-exigences-fonctionnelles.md`](docs/03-exigences-fonctionnelles.md) | Catalogue d'exigences numérotées, priorités MoSCoW, critères d'acceptation, hors-périmètre | Produit, QA |
| 04 | [`04-securite-conformite.md`](docs/04-securite-conformite.md) | Sécurité, RGPD / Loi 25 / HIPAA, modèle de menaces, PSSI, gouvernance des données | RSSI, juridique |
| 05 | [`05-architecture-technique.md`](docs/05-architecture-technique.md) | Architecture, modèle de domaine, API REST, événements, performance, exploitation | Architecture, dev |
| 06 | [`06-moteur-rdv-recurrents.md`](docs/06-moteur-rdv-recurrents.md) | **Moteur de récurrence : règles R-01 à R-24, algorithmes, cas limites, garde-fous** | Architecture, dev, QA |
| 07 | [`07-api-et-schemas-rdv-recurrents.md`](docs/07-api-et-schemas-rdv-recurrents.md) | Contrats d'API, machines à états, schémas JSON, catalogue d'erreurs | Dev, intégrateurs |
| 08 | [`08-exigences-non-fonctionnelles.md`](docs/08-exigences-non-fonctionnelles.md) | SLO, performance, capacité, accessibilité, i18n, observabilité | Architecture, ops |
| 09 | [`09-plan-tests-recette.md`](docs/09-plan-tests-recette.md) | Stratégie de tests, plan de recette, critères de sortie | QA, direction |
| 10 | [`10-roadmap-budget-risques.md`](docs/10-roadmap-budget-risques.md) | Roadmap, estimations, budget, registre des risques | Direction |

### Annexes et artefacts exécutables

| Artefact | Rôle |
|----------|------|
| [`annexes/vecteurs-test-recurrence.json`](annexes/vecteurs-test-recurrence.json) | 10 vecteurs de test normatifs générés par le simulateur |
| [`annexes/glossaire.md`](annexes/glossaire.md) | Glossaire métier et technique |
| [`annexes/tracabilite-gorendezvous.md`](annexes/tracabilite-gorendezvous.md) | Matrice de traçabilité fonctionnalité GOrendezvous → exigence MyRDV |
| [`tools/recurrence_simulator.py`](tools/recurrence_simulator.py) | **Spécification exécutable** du moteur de récurrence (Python 3.9+, sans dépendance) |
| [`schemas/recurrence-rule.schema.json`](schemas/recurrence-rule.schema.json) | Schéma JSON (Draft 2020-12) de validation d'une règle de récurrence |
| [`tools/test_schemas.py`](tools/test_schemas.py) | 17 cas de validation du schéma JSON |

## 3. Comment lire ce dossier

- **Exigences** : identifiants stables `F-<domaine>-<n>` (fonctionnel), `NFR-<domaine>-<n>`
  (non fonctionnel), `R-<n>` (règles du moteur de récurrence), `SER_xxx` (codes d'erreur métier).
  Un identifiant ne doit **jamais** être réutilisé ni renuméroté après publication.
- **Priorités** : `MUST` (indispensable à la mise en service), `SHOULD` (attendu, différable d'un
  sprint), `COULD` (confort), `WON'T` (hors périmètre V1, explicitement exclu).
- **Critères d'acceptation** : formulés en *Étant donné / Quand / Alors* et rattachés à un test
  automatisé ou à un cas de recette manuelle dans le document 09.
- **Normativité** : en cas de contradiction, l'ordre de primauté est 06 (règles de récurrence) >
  07 (contrats d'API) > 03 (exigences) > 05 (architecture) > reste du dossier.

## 4. Périmètre en une page

**Inclus en V1** : agenda multi-professionnels et multi-sites, réservation en ligne 24/7 sans mot de
passe, moteur de récurrence hebdomadaire complet, liste d'attente intelligente avec remplissage
automatique, rappels et confirmations multicanal (courriel, SMS, notification), portail client,
dossiers clients et notes cliniques structurées (SOAP), formulaires d'admission, facturation et
paiements en ligne, salles et équipements, droits par rôle, journal d'audit, exports, tableau de
bord analytique, conformité RGPD / Loi 25 / HIPAA-ready.

**Exclus de la V1** (assumés, voir §10 du document 03) : téléconsultation intégrée en marque blanche
(partenariat Zoom/Whereby en V1.1), télécodage et télétransmission des feuilles de soins (France),
comptabilité générale complète, paie, marketing automation avancé, application mobile native
(PWA en V1, natif en V2).

**Différenciateur spécifié à un niveau d'ingénierie complet** : le module de rendez-vous récurrents
hebdomadaires avec bornes de répétition, exceptions, gestion des conflits et des fuseaux horaires
(document 06, 24 règles normatives R-01 à R-24, contrat d'API du document 07, simulateur exécutable
et 10 vecteurs de test normatifs).

## 5. Vérifier le dossier en local

```bash
cd docs/cahier-des-charges
python3 tools/recurrence_simulator.py --self-test   # 400 séries, 6 invariants
python3 tools/recurrence_simulator.py --demo        # « 1 fois/semaine pendant 3 mois » = 14 séances
python3 tools/recurrence_simulator.py --vectors > annexes/vecteurs-test-recurrence.json
pip install jsonschema && python3 tools/test_schemas.py
```

---

*Fin du document d'entrée. Ce fichier sert de table des matières maître ; la numérotation des
documents (00 à 10) est indépendante de celle des chapitres de chaque document.*

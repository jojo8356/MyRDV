# 00 — Synthèse exécutive

**Document** : 00 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026 · **Statut** : pour décision
**Auteur** : Direction produit MyRDV · **Diffusion** : comité exécutif, comité d'architecture, conseil

---

## 1. Le problème

Les professionnels indépendants et les petites structures (ostéopathes, psychologues, massothérapeutes,
coiffeurs, coachs) consacrent **6 à 10 heures par semaine** à de la logistique de rendez-vous :
appels manqués, reprogrammations, relances, no-shows, double saisie entre l'agenda papier, l'agenda
Google et la comptabilité. Le coût est double : **manque à gagner direct** (un rendez-vous non
honoré n'est pas facturé) et **charge mentale** qui limite la croissance du cabinet.

GOrendezvous a prouvé la validité de ce marché au Québec avec une promesse claire : *« online
booking, billing, charting »* dans un outil unique, conforme aux cadres de santé canadiens (Loi 25,
PHIPA, PIPEDA) et doté d'une liste d'attente intelligente et de rappels SMS contribuant à réduire les
absences de ~38 %.

MyRDV reprend cette promesse en l'étendant sur trois axes que la concurrence traite mal :

1. **Récurrence réellement industrielle** — les séries de rendez-vous hebdomadaires (suivi
   thérapeutique, orthophonie, coaching, soins esthétiques) existent chez tous les concurrents, mais
   avec des bornes pauvres (souvent « répéter X fois » ou « jusqu'à telle date »), sans politique de
   conflit explicite, sans gestion du changement d'heure, sans exceptions par occurrence. MyRDV en
   fait un module spécifié à l'état de l'art (document 06 : 24 règles normatives, simulateur
   exécutable, 100 % testable).
2. **Conformité européenne native** — RGPD, hébergement UE par défaut, registre des traitements,
   minimisation, DPA, portabilité, effacement, avec un chemin documenté vers Loi 25 / HIPAA pour les
   clients canadiens et américains.
3. **Transparence tarifaire et API publique** — pas de quotas cachés sur les rappels SMS, API
   documentée avec webhooks signés, exports complets sans réversibilité payante.

## 2. Le produit en une phrase

> **MyRDV est la plateforme de rendez-vous des professionnels exigeants : agenda multi-praticien,
> réservation en ligne 24/7, séries de rendez-vous récurrentes maîtrisées au jour près, rappels
> intelligents et dossier client conforme — sans complexité.**

## 3. Périmètre V1 en chiffres

| Indicateur | Cible V1 | Justification |
|---|---|---|
| Exigences fonctionnelles spécifiées | 195 (dont 120 MUST) — doc 03 | Couverture GOrendezvous à 93 % + 12 différenciateurs |
| dont `MUST` | 120 | Mise en service commerciale |
| Règles normatives de récurrence | 24 (R-01 → R-24) | Doc 06, chacune testée |
| Domaines fonctionnels | 27 | Doc 03 §1 |
| Personas documentés | 5 | Doc 02 |
| Rôles / permissions | 7 rôles, 64 permissions atomiques | Doc 02 §6 |
| Endpoints API publics V1 | 62 | Doc 07 |
| SLO de disponibilité | 99,9 % / mois glissant | Doc 08 |
| Latence API p95 (lecture agenda) | < 250 ms | Doc 08 |
| Couverture de tests du moteur de récurrence | 100 % branches + property-based (≥ 10 000 tirages) | Doc 09 |
| Durée de dev. estimée (équipe de 7) | 22 semaines jusqu'au GA | Doc 10 |
| Budget V1 (build + run 12 mois) | 612 k€ | Doc 10 §4 |

## 4. Décisions structurantes (à ratifier)

| # | Décision | Recommandation | Impact si refusée |
|---|---|---|---|
| D1 | **Horizon de matérialisation** des séries récurrentes | Matérialisation **paresseuse à horizon glissant de 90 jours**, règle conservée en source de vérité | Un stock d'occurrences à horizon 12 mois rend les modifications de série coûteuses et le changement d'heure difficile à corriger |
| D2 | **Sémantique des bornes** de répétition | Quatre modes exclusifs : `AFTER_COUNT`, `ON_DATE`, `AFTER_DURATION` (mois/semaines), `NEVER` (bornée par garde-fous) | Ambiguïté « 3 mois » = 12 ou 13 séances, litiges clients |
| D3 | **Politique de conflit** par défaut | `SKIP` (l'occurrence en conflit est ignorée et signalée), options `FAIL` (tout ou rien) et `SHIFT_SAME_DAY` (±4 h) | Création de séries silencieusement incomplètes |
| D4 | **Fuseau horaire de référence** | La série porte le fuseau du lieu ; l'heure murale est conservée à travers les changements d'heure (RRULE RFC 5545) | Décalages d'une heure deux fois par an (le premier bug des agendas) |
| D5 | **Hébergement** | UE (Paris) par défaut, option Canada (Montréal) pour les clients Loi 25, option US (Virginie) HIPAA | Perte du segment santé québécois / européen |
| D6 | **Modèle de facturation** | Abonnement par praticien, SMS à prix coûtant +0 %, paiements en ligne via Stripe Connect (frais absorbés par le praticien) | Marge dépendante d'un quota SMS opaque |
| D7 | **Portail client** | Sans mot de passe (lien magique + code OTP), conforme aux recommandations ANSSI/NIST | Abandon à l'inscription |
| D8 | **API** | REST/JSON versionnée (`/v1`), webhooks signés HMAC-SHA256, idempotence par `Idempotency-Key` | Intégrations partenaires fragiles |

## 5. Les trois risques majeurs et leur parade

| Risque | Probabilité | Impact | Parade |
|---|---|---|---|
| **Récursion temporelle incorrecte** (DST, mois courts, exceptions) vécue comme une perte de confiance | Moyenne | Critique (réputation) | Règles formalisées, simulateur de référence, property-based testing, double implémentation (Python oracle vs TypeScript prod) comparée en CI |
| **Non-conformité santé** (données de santé = catégorie particulière RGPD art. 9) | Moyenne | Critique (juridique) | Chiffrement, minimisation, DPIA par défaut, hébergement UE, sous-traitants audités, pas de donnée de santé dans les rappels SMS (invitation neutre) |
| **Coût variable SMS / courriel** | Élevée | Majeur (marge) | Plafonds par offre, fallback courriel, tarification transparente, routage par opérateur le moins cher, quotas anti-abus |

## 6. Ce que dit le dossier, chapitre par chapitre

- **01** : le marché, la segmentation, les 9 concurrents, et une **grille de 108 fonctionnalités
  GOrendezvous** confrontée à notre couverture.
- **02** : cinq personas et leurs parcours, du praticien solo à la coordinatrice d'une clinique de
  12 praticiens.
- **03** : 195 exigences numérotées avec critères d'acceptation, priorités et exclusions.
- **04** : sécurité et conformité, dont le modèle de menaces STRIDE et le plan de réponse à incident.
- **05** : architecture cible, modèle de domaine, contrats d'API, stratégie de données et d'exploitation.
- **06** : **le cœur du différenciateur** — 24 règles de récurrence, pseudo-code, cas limites.
- **07** : la mise en œuvre exposée : endpoints, machines à états, schémas, codes d'erreur.
- **08** : SLO, capacité, accessibilité (RGAA/WCAG 2.1 AA), internationalisation, observabilité.
- **09** : stratégie de tests (pyramide, propriétés, charge, chaos, recette utilisateur).
- **10** : roadmap sur 4 trimestres, budget détaillé, registre des risques et gouvernance.

## 7. Décisions attendues à l'issue de la revue

1. Validation du périmètre V1 et des 12 exclusions (doc 03 §11).
2. Validation des décisions D1 à D8 (§4).
3. Validation de l'enveloppe budgétaire de 612 k€ et du calendrier de 22 semaines (doc 10).
4. Désignation des propriétaires : produit (PM), architecture (lead), sécurité (RSSI), conformité (DPO).
5. Autorisation de lancer les lots 0 (socle) et 1 (agenda + récurrence) en parallèle.

---

*Documents suivants : [`01-contexte-analyse-marche.md`](01-contexte-analyse-marche.md) ·
[`06-moteur-rdv-recurrents.md`](06-moteur-rdv-recurrents.md) (le différenciateur).*

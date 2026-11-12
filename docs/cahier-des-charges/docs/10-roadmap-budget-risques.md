# 10 — Roadmap, budget, organisation et risques

**Document** : 10 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Horizon** : 4 trimestres (T1 2027 → T4 2027) · **Objectif** : mise en service commerciale (GA) en
semaine 22 (≈ mai 2027), puis deux montées de version.

---

## 1. Équipe cible

| Rôle | ETP | Rattachement |
|---|---|---|
| Product manager | 1,0 | Produit |
| Product designer (UX/UI) | 1,0 | Produit |
| Lead architecte | 1,0 | Technique |
| Développeurs full-stack | 3,0 | Technique |
| Ingénieur qualité (QA automatisé) | 1,0 | Technique |
| DevOps / SRE | 0,5 | Technique |
| RSSI (à temps partiel) | 0,3 | Sécurité |
| DPO / juriste conformité | 0,2 | Conformité |
| Support / onboarding (à partir de S14) | 1,0 | Opérations |
| **Total** | **9,0** | |

---

## 2. Roadmap par lots

| Lot | Semaines | Contenu | Jalons |
|---|---|---|---|
| **L0 — Socle** | S1-S4 | Monorepo, CI/CD, design system, authentification, multi-tenancy, RLS, observabilité, audit | Squelette déployé en staging |
| **L1 — Agenda & récurrence** | S3-S10 | Modèle de domaine, disponibilités, agenda, **moteur de récurrence complet**, API `/series`, contraintes d'exclusion, simulateur + double implémentation | Démo interne de la série de 3 mois (S8), module validé (S10) |
| **L2 — Réservation & clients** | S7-S12 | Page publique, portail client, fiches, consentements, formulaires, notifications, liste d'attente | Première réservation réelle en staging (S12) |
| **L3 — Finance & clinique** | S11-S16 | Facturation, Stripe, forfaits, notes SOAP, documents, signature, exports | Facturation de bout en bout (S16) |
| **L4 — Équipe, sync, analytics** | S14-S19 | Rôles avancés, Google/Microsoft, ICS, tableaux de bord, webhooks, API publique | API publique documentée (S19) |
| **L5 — Durcissement** | S17-S22 | Performance, sécurité, accessibilité, recette, conformité, documentation, migration | GA (S22) |
| **V1.1** | S23-S34 | Cours et groupes, demandes de service, annuaire, IA de notes, connecteur comptable, séries en attente d'approbation | Release V1.1 |
| **V2** | S35-S52 | Application native, récurrence quotidienne/mensuelle, multi-praticiens par série, OpenSearch, SSO SAML, ISO 27001 (préparation) | Release V2 |

**Parallélisation** : L1 et L2 démarrent ensemble dès que le socle d'authentification est stable
(S4). Le moteur de récurrence (L1) est développé par 2 développeurs en binôme, avec le simulateur
Python écrit **avant** le code de production (spécification exécutable).

---

## 3. Jalons et critères de passage

| Jalon | Date | Critère |
|---|---|---|
| J1 — Socle validé | S4 | CI verte, déploiement automatisé, RLS testée |
| J2 — Récurrence validée | S10 | 100 % des règles R-01 → R-24 testées, 0 divergence avec le simulateur |
| J3 — Réservation en ligne | S12 | Parcours client complet, aucun compte requis |
| J4 — Finance | S16 | Facture conforme, remboursement, réconciliation Stripe |
| J5 — API publique | S19 | OpenAPI publiée, 62 endpoints, webhooks signés |
| J6 — Recette | S21 | Critères du document 09 §5.2 satisfaits |
| J7 — GA | S22 | Go/no-go du comité, 0 défaut bloquant |
| J8 — V1.1 | S34 | Cours, annuaire, IA, connecteur comptable |
| J9 — V2 | S52 | Natif, récurrence étendue, SSO |

---

## 4. Budget

### 4.1 Coûts de construction (jusqu'au GA, 22 semaines)

| Poste | Calcul | Montant |
|---|---|---|
| Équipe produit et technique (9 ETP × 22 sem. ≈ 4,2 ETP-année) | 4,2 × 120 k€ | 504 k€ |
| Design system, illustrations, rédaction UX | forfait | 18 k€ |
| Tests d'intrusion externe | 1 campagne | 15 k€ |
| Audit d'accessibilité (RGAA/WCAG) | 1 audit | 8 k€ |
| Conseil juridique (DPA, CGU, CGV, mentions, DPIA) | forfait | 22 k€ |
| Outils (CI, observabilité, design, gestion de projet) | 22 semaines | 9 k€ |
| Infrastructure de staging et production (avant revenus) | 22 semaines | 6 k€ |
| Marge d'aléas (10 %) | — | 30 k€ |
| **Total construction** | | **612 k€** |

### 4.2 Coûts de fonctionnement (année 1 après GA)

| Poste | Hypothèse | Montant |
|---|---|---|
| Infrastructure (UE + CA) | 1 000 organisations actives | 28 k€ |
| SMS et courriels | facturés au client, à prix coûtant | 0 k€ (refacturé) |
| Support et onboarding | 1 ETP | 45 k€ |
| Maintenance et évolutions (V1.1) | 4 ETP | 240 k€ |
| Sécurité (pentest annuel, bug bounty) | — | 22 k€ |
| Licences et outils | — | 14 k€ |
| **Total fonctionnement** | | **349 k€** |

### 4.3 Modèle économique (hypothèses)

| Offre | Prix / mois | Inclus | Cible à 12 mois |
|---|---|---|---|
| Solo | 19 € | 1 praticien, 20 séries, 30 j d'horizon, 100 SMS | 600 comptes |
| Pro | 39 € | 1 praticien, 200 séries, 90 j, SMS à prix coûtant, portail client | 320 comptes |
| Business | 89 € | 5 praticiens, séries illimitées, 180 j, multi-sites, Loi 25 | 70 comptes |
| Entreprise | sur devis | praticiens illimités, HIPAA/HDS, SSO, SLA 99,95 % | 8 comptes |

**Revenu récurrent mensuel visé à 12 mois** ≈ 600×19 + 320×39 + 70×89 + 8×450 ≈ **31,3 k€**/mois
(375 k€ annualisés), soit un point d'équilibre atteint au mois 20 avec l'équipe de maintenance réduite.

---

## 5. Registre des risques

| # | Risque | P | I | Criticité | Parade | Propriétaire |
|---|---|---|---|---|---|---|
| R1 | Erreur de calcul de récurrence (DST, fin de mois) | Moyenne | Critique | **Élevée** | Simulateur de référence, double implémentation, 10 000 tirages quotidiens | Lead technique |
| R2 | Non-conformité données de santé | Faible | Critique | **Élevée** | DPIA, chiffrement, minimisation, DPO, hébergement UE | DPO |
| R3 | Dérive de planning sur le lot L1 | Moyenne | Majeur | Moyenne | Binôme dédié, spécification exécutable écrite avant le code, revue hebdomadaire | PM |
| R4 | Coût SMS supérieur aux prévisions | Moyenne | Majeur | Moyenne | Tarification à prix coûtant, fallback courriel, plafonds par offre | PM |
| R5 | Indisponibilité d'un sous-traitant (Stripe, Twilio) | Faible | Majeur | Moyenne | Redondance SMS, file de reprise, statut public, communication | SRE |
| R6 | Adoption insuffisante (pas de product-market fit) | Moyenne | Critique | **Élevée** | 15 entretiens utilisateurs avant L1, bêta privée en S16 avec 20 cabinets, boucle de feedback hebdomadaire | PM |
| R7 | Fuite de données (incident) | Faible | Critique | **Élevée** | Modèle de menaces, pentest, plan de réponse, assurance cyber | RSSI |
| R8 | Vulnérabilité d'une dépendance | Moyenne | Majeur | Moyenne | SBOM, Dependabot, SCA bloquante, politique de correctifs | Lead technique |
| R9 | Complexité perçue de l'interface de récurrence | Moyenne | Majeur | Moyenne | Mode simple par défaut (4 champs), options avancées repliées, tests utilisateurs S20 | Designer |
| R10 | Contentieux sur une facturation de série | Faible | Majeur | Moyenne | Règles R-23 explicites, journal d'audit, conditions d'annulation affichées | DPO/PM |
| R11 | Dépendance à un fournisseur cloud | Faible | Majeur | Moyenne | Kubernetes + Terraform, portabilité, sauvegardes exportables | Lead technique |
| R12 | Recrutement (2 profils clés) | Moyenne | Majeur | Moyenne | Vivier de freelances, documentation stricte, binôme sur les modules critiques | Direction |
| R13 | Accessibilité insuffisante (marché public) | Faible | Mineur | Faible | Audit externe, composants Radix, tests NVDA | Designer |
| R14 | Support submergé au lancement | Moyenne | Mineur | Faible | Base de connaissances, onboarding assisté, astreinte renforcée 30 j | Opérations |
| R15 | Réglementation changeante (Loi 25, RGPD, EHDS) | Moyenne | Majeur | Moyenne | Veille trimestrielle, architecture de consentement évolutive | DPO |

**Échelle** : P = probabilité (faible/moyenne/élevée), I = impact (mineur/majeur/critique).
Revue mensuelle du registre, escalade au comité pour toute criticité élevée.

---

## 6. Gouvernance

| Instance | Fréquence | Participants | Décisions |
|---|---|---|---|
| Comité de pilotage | Mensuel | Direction, PM, lead technique, DPO | Budget, périmètre, risques élevés |
| Revue de sprint | Hebdomadaire | Équipe | Avancement, blocages |
| Comité d'architecture | Bimensuel | Architectes, leads | ADR, choix techniques |
| Comité sécurité et conformité | Trimestriel | RSSI, DPO, CTO | Mesures, incidents, conformité |
| Revue de recette | À chaque jalon | QA, PM, designer | Go/no-go de jalon |

**Indicateurs suivis** : vélocité, défauts par sévérité, couverture de tests, budget d'erreur SLO,
nombre de séries créées, taux d'adoption des fonctionnalités clés (récurrence, liste d'attente,
paiement en ligne), NPS.

---

## 7. Définition de « terminé » (Definition of Done)

Une exigence est terminée lorsque :

1. Le code est revu et fusionné, typé, linté.
2. Les tests unitaires et d'intégration couvrent le comportement et les cas limites.
3. Les critères d'acceptation du document 03 sont vérifiés par un test automatisé ou une recette
   documentée.
4. La documentation d'API et le guide utilisateur sont mis à jour.
5. L'événement d'audit est émis si l'exigence touche une donnée sensible.
6. La mesure de performance est dans le budget (doc 08).
7. L'accessibilité est vérifiée (clavier, contraste, libellés) si l'exigence a une interface.
8. Le texte est traduit en anglais.
9. Aucune régression sur les vecteurs du document 06.

---

## 8. Après la V1 : trajectoire

| Horizon | Objectifs |
|---|---|
| V1.1 (S23-S34) | Cours et groupes, annuaire public, assistant IA de notes, connecteur comptable, séries en attente d'approbation, listes d'attente par série |
| V2 (S35-S52) | Application native iOS/Android, récurrence quotidienne et mensuelle par ordinal, séries multi-praticiens, SSO SAML, OpenSearch, paiements en plusieurs fois |
| V3 | Mode single-tenant dédié, certification ISO 27001, HDS en propre, récurrence événementielle (fuseaux dynamiques, séries transfrontalières avancées), marketplace de partenaires |

---

## 9. Synthèse des décisions à valider

| # | Décision | Recommandation |
|---|---|---|
| 1 | Périmètre V1 (195 exigences, 120 MUST) et 8 exclusions | Valider |
| 2 | Décisions D1 à D8 du document 00 §4 | Valider |
| 3 | Budget 612 k€ + 349 k€ de fonctionnement | Valider |
| 4 | Calendrier de 22 semaines jusqu'au GA | Valider |
| 5 | Priorité absolue au module de récurrence (lot L1) | Valider |
| 6 | Deux régions (UE + Canada) dès la V1 | Valider |
| 7 | Bêta privée de 20 cabinets en S16 | Valider |
| 8 | Propriétaires nommés : PM, lead technique, RSSI, DPO | Nommer |

---

*Fin du dossier. Retour à la [table des matières](../README.md).*

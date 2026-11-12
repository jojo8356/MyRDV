# Annexe — Matrice de traçabilité GOrendezvous → MyRDV

**Document** : annexe du cahier des charges MyRDV · **Version** 1.0 · 12 novembre 2026
**Objet** : démontrer, fonctionnalité par fonctionnalité, la couverture de GOrendezvous par MyRDV.
**Sources** : voir [document 01 §5](../docs/01-contexte-analyse-marche.md). Consultées le 12 novembre 2026.

Légende : **V1** = couvert en V1 · **V1.1** = différé à la version 1.1 · **V2** = version 2 ·
**Hors** = hors périmètre assumé.

---

## 1. Réservation en ligne

| Fonctionnalité GOrendezvous | MyRDV | Exigence |
|---|---|---|
| Réservation en ligne 24/7 | V1 | F-BKG-01 |
| Page personnalisée (logo, couleurs, textes) | V1 | F-BKG-02 |
| URLs par service/praticien | V1 | F-BKG-03 |
| Sélection lieu → service → praticien → créneau | V1 | F-BKG-04 |
| Affichage des tarifs et durées | V1 | F-BKG-05 |
| Réservation sans mot de passe | V1 | F-BKG-06 |
| Confirmation immédiate ou approbation | V1 | F-BKG-07 |
| Créneaux réservés aux clients existants | V1 | F-BKG-08 |
| Blocage d'un client | V1 | F-CLI-09 |
| Rendez-vous pour deux | V1 | F-BKG-09 |
| Cours et groupes | V1.1 | F-CLS-01 |
| Liste d'attente manuelle | V1 | F-WAIT-01 |
| Liste d'attente intelligente | V1 | F-WAIT-02 |
| Demandes de service / repérage urgent | V1.1 | F-REQ-01 |
| Page publique bilingue | V1 | F-I18N-01 |
| Annuaire public | V1.1 | F-DIR-01 |
| Mini-site praticien | V1.1 | F-DIR-02 |
| Widget intégrable | V1 | F-BKG-10 |
| Recherche « près de moi » | V1.1 | F-DIR-03 |
| CAPTCHA invisible | V1 | F-BKG-12 |

## 2. Rendez-vous et récurrence

| Fonctionnalité | MyRDV | Exigence / règle |
|---|---|---|
| Création manuelle | V1 | F-APT-01 |
| Reprogrammation | V1 | F-APT-02 |
| Politique d'annulation configurable | V1 | F-APT-03 |
| **Rendez-vous récurrents — jours de la semaine** | **V1 (étendu)** | F-REC-01 / R-01 |
| **Récurrence — fréquence** | **V1 (étendu : 1 à 8 semaines)** | F-REC-02 / R-02 |
| **Récurrence — nombre d'occurrences** | **V1** | F-REC-03 / R-03 |
| **Récurrence — date de fin** | **V1** | F-REC-03 / R-04 |
| **Récurrence — durée (« 3 mois »)** | **V1** | F-REC-04 / R-05 |
| **Récurrence — sans fin bornée** | **V1** | F-REC-10 / R-15 |
| **Récurrence — prévisualisation** | **V1** | F-REC-05 |
| **Récurrence — politique de conflit** | **V1 (différenciateur)** | F-REC-06 / R-09 |
| **Récurrence — jours fériés et congés** | **V1** | F-REC-07 / R-07 |
| **Récurrence — exceptions et détachement** | **V1** | F-REC-08, F-REC-09 / R-08, R-13 |
| **Récurrence — modification par portée** | **V1** | F-REC-13 / R-12 |
| **Récurrence — rapport de pertes** | **V1 (différenciateur)** | F-REC-17 / R-14 |
| Confirmations automatiques | V1 | F-NOT-01 |
| Rappels multicanal | V1 | F-NOT-02 |
| Confirmation de présence depuis le SMS | V1 | F-NOT-03 |
| Téléconsultation Zoom | V1 | F-TEL-01 |
| Tampon après rendez-vous | V1 | F-APT-07 |
| Limite de rendez-vous par jour | V1 | F-AVL-05 |
| Statuts (arrivé, manqué, annulé) | V1 | F-APT-04 |
| Notes de rendez-vous | V1 | F-APT-05 |
| Détection de conflit | V1 (contrainte base) | F-APT-06, F-APT-13 |

## 3. Agenda et disponibilités

| Fonctionnalité | MyRDV | Exigence |
|---|---|---|
| Vues jour/semaine/mois | V1 | F-AGD-01 |
| Glisser-déposer | V1 | F-AGD-02 |
| Agenda d'équipe | V1 | F-AGD-03 |
| Semaine type de disponibilités | V1 | F-AVL-01 |
| Plages exceptionnelles | V1 | F-AVL-02 |
| Congés | V1 | F-AVL-03 |
| Synchronisation Google Calendar | V1 | F-SYN-01 |
| Synchronisation Outlook / 365 | V1 | F-SYN-02 |
| Fuseaux horaires multiples | V1 | F-TZ-01..04 |
| Codes couleur | V1 | F-AGD-04 |
| Vue mobile | V1 (PWA) | F-AGD-05 |

## 4. Ressources, clients, dossier

| Fonctionnalité | MyRDV | Exigence |
|---|---|---|
| Multi-sites | V1 | F-LOC-01 |
| Salles réservables | V1 | F-RES-01 |
| Équipements réservables | V1 | F-RES-02 |
| Rendez-vous à domicile | V1 | F-LOC-02 |
| Conflit de ressource bloquant | V1 | F-RES-03 |
| Base clients et fiche | V1 | F-CLI-01, F-CLI-02 |
| Historique rendez-vous/paiements | V1 | F-CLI-03 |
| Formulaires d'admission personnalisables | V1 | F-FRM-01 |
| Formulaires conditionnels | V1 | F-FRM-02 |
| DME / notes SOAP | V1 | F-MED-01 |
| Plans de traitement | V1 | F-MED-03 |
| Assistant IA de notes cloisonné | V1.1 | F-MED-08, F-AI-01 |
| Signature électronique | V1 | F-DOC-02, F-SIG |
| Partage sécurisé de fichiers | V1 | F-DOC-01 |
| Export PDF du dossier | V1 | F-MED-06, F-DOC-03 |
| Portail client sécurisé | V1 | F-PRT-01..06 |
| Évaluations post-traitement | V1.1 | F-FDB-01 |
| Demande d'avis en ligne | V1.1 | F-FDB-02 |

## 5. Communications

| Fonctionnalité | MyRDV | Exigence |
|---|---|---|
| Rappels SMS | V1 | F-NOT-02 |
| Rappels courriel | V1 | F-NOT-02 |
| Rappels avec confirmation | V1 | F-NOT-03 |
| Messages bilingues | V1 | F-NOT-04 |
| Communications de masse | V1.1 | F-NOT-05 |
| Modèles personnalisables | V1 | F-NOT-06 |
| Notifications internes | V1 | F-NOT-07 |
| Relance no-show | V1 | F-NOT-08 |
| Remerciement / demande d'avis | V1.1 | F-NOT-09 |
| **Récapitulatif de série** | **V1** | F-NOT-10 / R-18 |

## 6. Paiements et facturation

| Fonctionnalité | MyRDV | Exigence |
|---|---|---|
| Paiement en ligne (Stripe) | V1 | F-BIL-01 |
| Encaissement sur place | V1 | F-BIL-02 |
| Factures et reçus | V1 | F-BIL-03 |
| Facturation récurrente | V1 | F-BIL-04 |
| Taxes | V1 | F-BIL-05 |
| Rapports de revenus | V1 | F-BIL-06 |
| Point de vente | V1.1 | F-BIL-07 |
| Inventaire | V2 | F-BIL-08 |
| Cartes-cadeaux | V1.1 | F-BIL-09 |
| Programme de fidélité | V2 | F-BIL-10 |
| Télétransmission assurance / feuilles de soins | Hors (V2) | F-BIL-11 |
| QuickBooks | V1.1 | F-INT-04 |
| Remboursements | V1 | F-BIL-12 |

## 7. Organisation, analyse, technique

| Fonctionnalité | MyRDV | Exigence |
|---|---|---|
| Comptes employés inclus | V1 | F-ORG-01 |
| Permissions granulaires | V1 (64 permissions) | F-ORG-02 |
| Télésecrétariat | V1 | F-ORG-03 |
| Masquage des noms en accueil | V1 | F-ORG-04 |
| Horaires de travail | V1 | F-AVL-01 |
| Tableau de bord | V1 | F-ANL-01 |
| Rapports personnalisables | V1.1 | F-ANL-02 |
| Insights clients | V1 | F-ANL-03 |
| Export CSV/Excel/PDF | V1 | F-ANL-04 |
| Google Analytics page publique | V1.1 | F-ANL-05 |
| Taux de no-show | V1 | F-ANL-06 |
| Performance par praticien | V1 | F-ANL-07 |
| API publique | V1 (62 endpoints) | F-INT-01 |
| Webhooks signés | V1 | F-INT-02 |
| Zapier / Make | V2 | F-INT-06 |
| Chiffrement transit/repos | V1 | NFR-SEC-01 |
| MFA | V1 | NFR-SEC-02 |
| Déconnexion automatique | V1 | NFR-SEC-03 |
| Journal d'audit | V1 | NFR-SEC-04 |
| Sauvegardes / PITR | V1 | NFR-OPS-01..02 |
| Protection réseau (WAF/CDN) | V1 | NFR-SEC-05 |
| Hébergement Canada | V1 (option) | NFR-CMP-01 |
| Conformité Loi 25 / PIPEDA / PHIPA | V1 (option Canada) | NFR-CMP-02 |
| Conformité HIPAA | V1 (offre Business/Entreprise) | NFR-CMP-03 |
| Accès en lecture seule après résiliation | V1 | NFR-CMP-04 |
| Multi-langue | V1 (FR/EN) | F-I18N-01 |
| Onboarding assisté | V1 | F-ONB-01..03 |
| Offre on-premise | Hors | — |
| Application native | V2 (PWA en V1) | — |

---

## 8. Différenciateurs MyRDV (au-delà de GOrendezvous)

| # | Différenciateur | Exigences | Preuve |
|---|---|---|---|
| 1 | Récurrence à quatre modes de fin avec bornes exactes et arithmétique de mois documentée | F-REC-03/04/05, R-03/04/05 | Doc 06 §3, vecteurs E1-E10 |
| 2 | Politique de conflit explicite (`FAIL`/`SKIP`/`SHIFT_SAME_DAY`) avec budget | F-REC-06, R-09 | Doc 06 §5, T-REC-030..038 |
| 3 | Gestion normative des changements d'heure et des fuseaux | F-REC-18, R-06, R-20 | Doc 06 §7.1-7.2, tests T-REC-014..017 |
| 4 | Rapport d'occurrences non planifiées (aucune perte silencieuse) | F-REC-17, R-14 | Doc 06 §5, T-REC-020 |
| 5 | Modification par portée avec `diff` et réversibilité 30 jours | F-REC-13, R-12 | Doc 07 §7 |
| 6 | Détachement d'occurrence préservé à la régénération | F-REC-09, R-13, R-17 | T-REC-039, T-REC-041 |
| 7 | Double implémentation et propriétés (10 000 tirages) | R-17 | Doc 09 §1.2 |
| 8 | Conformité UE native (RGPD, DPIA, hébergement UE par défaut) | NFR-CMP-01..10 | Doc 04 §3 |
| 9 | API publique documentée (OpenAPI 3.1, 62 endpoints, webhooks signés) | F-INT-01, F-INT-02 | Doc 07 |
| 10 | Tarification sans quota de rendez-vous, SMS à prix coûtant | NFR-CST-02, NFR-CST-04 | Doc 10 §4.3 |
| 11 | Accessibilité WCAG 2.1 AA sur les parcours critiques | NFR-A11Y-01..08 | Doc 09 T-A11Y |
| 12 | Réversibilité complète (export sans surcoût, lecture seule après résiliation) | NFR-CMP-04, F-CLI-07 | Doc 04 §6.3 |

---

*Retour à la [table des matières](../README.md).*

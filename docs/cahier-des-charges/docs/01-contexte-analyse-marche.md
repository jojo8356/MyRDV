# 01 — Contexte, marché et analyse fonctionnelle de GOrendezvous

**Document** : 01 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Objectif** : établir une base factuelle sur le marché de la prise de rendez-vous en ligne et
**documenter exhaustivement les fonctionnalités de GOrendezvous**, référence produit de MyRDV.

> **Méthode et limites.** L'analyse s'appuie sur les sources publiques de l'éditeur
> (info.gorendezvous.com, gorendezvous.com), les fiches d'annuaires logiciels (Capterra, GetApp,
> Software Advice, Appvizer, logiciels.pro, Software Finder) et des avis utilisateurs publics,
> consultées le 12 novembre 2026, ainsi que sur l'énoncé de l'utilisateur. GOrendezvous ne publie pas
> de documentation exhaustive de son API ; les éléments marqués **(à confirmer)** doivent être validés
> par une démonstration commerciale ou un essai encadré avant d'être considérés comme acquis.

---

## 1. Le marché

### 1.1 Segmentation

| Segment | Taille indicative | Attentes dominantes | Sensibilité prix |
|---|---|---|---|
| Praticien solo santé/paramédical (ostéopathe, psychologue, orthophoniste, massothérapeute) | 1 | Simplicité, dossier patient, rappels SMS, conformité | Moyenne |
| Praticien solo bien-être / beauté (coiffeur, esthéticienne, coach) | 1 | Réservation en ligne, paiement d'acompte, fidélité | Forte |
| Cabinet 2-5 praticiens | 2-5 | Agenda partagé, salles, secrétariat, facturation | Moyenne |
| Clinique 6-20 praticiens multi-sites | 6-20 | Rôles, reporting, ressources, télésecrétariat | Faible |
| Réseau / franchise > 20 | 20+ | API, SSO, consolidation, marque blanche | Faible |

### 1.2 Forces structurantes

- **Post-COVID** : la réservation en ligne et le rappel SMS sont devenus des standards de facto ;
  la téléconsultation reste attendue pour la santé mentale et le suivi.
- **Pression réglementaire** : RGPD (UE), Loi 25 (Québec), HIPAA (US), PHIPA (Ontario) — la donnée de
  santé est une **catégorie particulière** (art. 9 RGPD) qui exige base légale, minimisation,
  chiffrement et DPIA.
- **Consolidation** : les acteurs ajoutent facturation, paiement, IA de transcription ; le
  rendez-vous devient la porte d'entrée d'un ERP de cabinet.
- **IA générative** : notes cliniques assistées, résumés de séance, mais avec des exigences fortes
  de cloisonnement (pas d'entraînement sur les données clients).

### 1.3 Concurrents comparés

| Solution | Positionnement | Prix d'entrée public | Forces | Faiblesses |
|---|---|---|---|---|
| **GOrendezvous** | Tout-en-un clinique santé/bien-être, Québec | ~59 CAD/mois (Essentiel), 69 CAD (Premium) ; plans FR annoncés 29-79 € | Récurrence, liste d'attente intelligente, DME, facturation, conformité canadienne, support reconnu | Pas d'app native iOS, flexibilité jugée limitée sur les cours, dépendance cloud sans offre on-premise |
| Calendly | Prise de rendez-vous horizontale | ~10-12 USD/utilisateur/mois | Simplicité, intégrations (110+), notoriété | Pas de dossier client, facturation santé limitée |
| Acuity Scheduling (Squarespace) | PME, créatifs, bien-être | ~16-20 USD/mois | Personnalisation, formulaires, abonnements | UX datée, conformité santé limitée |
| Jane App | Cliniques santé (Canada/US) | ~54 CAD/mois | DME, téléconsultation, charting | Peu présent en Europe |
| Doctolib | Santé France, grand public | Abonnement professionnel | Notoriété patient, annuaire | Ciblage médical strict, peu adapté au bien-être |
| Vagaro | Beauté/bien-être | ~23,99 USD/mois | POS, marketplace, fidélité | Complexité tarifaire |
| Fresha | Beauté | Freemium + commissions | UX, marketplace | Commission sur paiements |
| Cliniko | Kinés/ostéos | ~45 USD/mois | DME solide, API | Ergonomie perfectible |
| SimplyBook.me | PME international | Freemium | Large couverture, multi-langue | Personnalisation limitée des règles de récurrence |

### 1.4 Ce que GOrendezvous fait mieux que la moyenne

1. **Liste d'attente intelligente** : inscription automatique quand l'agenda est plein, attribution
   d'un créneau libéré selon des critères.
2. **Rappels bidirectionnels** : le client confirme sa présence depuis le SMS ; le praticien voit la
   confirmation dans l'agenda (levier anti no-show).
3. **Conformité canadienne documentée** : Loi 25, LPRPSP, LPRPDE/PIPEDA, PHIPA, audits annuels,
   hébergement AWS Canada, masquage des noms sur l'horaire, journal d'audit.
4. **« Clustered booking »** : regroupement des séances pour éliminer les temps morts.
5. **Rendez-vous pour deux** (thérapie de couple / consultations duo) et **demandes de service** pour
   nouveaux clients avec repérage des urgences.

### 1.5 Faiblesses exploitables (angles d'attaque MyRDV)

| Faiblesse observée | Angle MyRDV |
|---|---|
| Récurrence limitée à « jours de la semaine + fréquence + durée » (FAQ éditeur), sans politique de conflit publique ni bornes combinables | **Module de récurrence de niveau ingénierie** (doc 06) : 4 modes de fin, exceptions, conflits, DST, régénération idempotente |
| Absence d'application mobile native | PWA installable dès la V1, natif en V2, API publique |
| Hébergement hors UE pour certains clients | UE par défaut, choix de la région |
| Tarification par quotas de rendez-vous | Tarification par praticien, quotas SMS transparents |
| API peu documentée publiquement | API ouverte documentée OpenAPI 3.1 + webhooks signés |

---

## 2. Analyse fonctionnelle exhaustive de GOrendezvous

Grille en 14 domaines, 108 fonctionnalités. La colonne **MyRDV** renvoie à l'exigence du document 03
(`F-xxx`) ou indique l'écart assumé.

### 2.1 Prise de rendez-vous en ligne

| # | Fonctionnalité GOrendezvous | Détail | MyRDV |
|---|---|---|---|
| 1 | Réservation en ligne 24/7 | Page publique, sans mot de passe | F-BKG-01 |
| 2 | Page de réservation personnalisée | Logo, couleurs, textes, intégration au site | F-BKG-02 |
| 3 | Lien de réservation par service et par professionnel | URLs dédiées | F-BKG-03 |
| 4 | Sélection du professionnel, du service, du lieu | Filtres successifs | F-BKG-04 |
| 5 | Affichage des tarifs et options | Transparence | F-BKG-05 |
| 6 | Durée variable par service | Optimisation de l'agenda pour éviter les trous | F-SVC-01 |
| 7 | Réservation sans compte client | Création de fiche à la première réservation | F-BKG-06 |
| 8 | Confirmation immédiate ou sur approbation | Le praticien choisit | F-BKG-07 |
| 9 | Réservé aux clients existants | Premier rendez-vous sur appel | F-BKG-08 |
| 10 | Blocage d'un client (bannissement) | Invisible des disponibilités, message personnalisable | F-CLI-09 |
| 11 | Rendez-vous pour deux | Thérapie de couple, duo | F-BKG-09 |
| 12 | Réservation de groupe / cours | Inscription à des sessions collectives | F-CLS-01 |
| 13 | Liste d'attente manuelle | Inscription quand complet | F-WAIT-01 |
| 14 | Liste d'attente intelligente | Attribution automatique d'un créneau libéré | F-WAIT-02 |
| 15 | Demandes de service pour nouveaux clients | Formulaire qualifiant, routage, repérage urgent | F-REQ-01 |
| 16 | Multi-langue de la page publique | FR/EN | F-I18N-01 |
| 17 | Annuaire public de professionnels | Recherche par profession, ville, condition, clientèle | F-DIR-01 |
| 18 | Page d'accueil gratuite par praticien | Vitrine | F-DIR-02 |
| 19 | Intégration réseaux sociaux / site web | Bouton, iframe | F-BKG-10 |
| 20 | Recherche « près de moi » | Géolocalisation | F-DIR-03 |

### 2.2 Gestion des rendez-vous

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 21 | Création manuelle d'un rendez-vous | Depuis l'agenda | F-APT-01 |
| 22 | Reprogrammation | Par le praticien ou le client | F-APT-02 |
| 23 | Annulation avec politique configurable | Délai limite, en ligne ou par téléphone | F-APT-03 |
| 24 | Rendez-vous récurrents | Jours de la semaine, fréquence, durée de répétition | **F-REC-01 → F-REC-20** |
| 25 | Confirmations automatiques | Courriel ou SMS selon préférence | F-NOT-01 |
| 26 | Rappels automatiques | Plusieurs jours avant | F-NOT-02 |
| 27 | Confirmation de présence par le client | Depuis le SMS, visible dans l'agenda | F-NOT-03 |
| 28 | Consultations en ligne (Zoom) | Lien généré, identifiant chiffré | F-TEL-01 |
| 29 | Pause après un rendez-vous | Tampon | F-AVL-04 |
| 30 | Limite de rendez-vous par jour | Garde-fou de charge | F-AVL-05 |
| 31 | Créneaux réservés aux clients existants | | F-BKG-08 |
| 32 | Historique / statut par rendez-vous | Confirmé, arrivé, manqué, annulé | F-APT-04 |
| 33 | Blocage de disponibilités | Congés, indisponibilités | F-AVL-03 |
| 34 | Notes sur le rendez-vous | | F-APT-05 |
| 35 | Détection de conflit | Empêche le double booking | F-APT-06 |

### 2.3 Gestion de l'agenda et des disponibilités

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 36 | Agenda jour/semaine/mois | Vues multiples | F-AGD-01 |
| 37 | Glisser-déposer | Déplacement d'un rendez-vous | F-AGD-02 |
| 38 | Agenda d'équipe | Disponibilité de tous en un écran | F-AGD-03 |
| 39 | Modèles de disponibilités récurrents | Semaine type | F-AVL-01 |
| 40 | Disponibilités exceptionnelles | Ajout de plages ponctuelles | F-AVL-02 |
| 41 | Limite de rendez-vous par créneau | | F-AVL-05 |
| 42 | Synchronisation Google Calendar | Import/export | F-SYNC-01 |
| 43 | Synchronisation Outlook / Office 365 | | F-SYNC-02 |
| 44 | Synchronisation bidirectionnelle | Évite les doubles réservations | F-SYNC-03 |
| 45 | Blocage automatique des indisponibilités externes | | F-SYNC-04 |
| 46 | Fuseaux horaires multiples | Praticien et client dans des fuseaux différents | F-TZ-01 |
| 47 | Codes couleur | Par service, statut, praticien | F-AGD-04 |
| 48 | Vue mobile de l'agenda | Responsive | F-AGD-05 |

### 2.4 Ressources : lieux, salles, équipements

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 49 | Multi-sites | Plusieurs adresses | F-LOC-01 |
| 50 | Salles réservables | Vérification de disponibilité | F-RES-01 |
| 51 | Équipements réservables | Table de massage, laser, etc. | F-RES-02 |
| 52 | Rendez-vous à domicile | Adresse du patient | F-LOC-02 |
| 53 | Rendez-vous virtuel | Lieu « visio » | F-LOC-03 |
| 54 | Conflit de ressource bloquant | Une salle ne peut être doublement réservée | F-RES-03 |
| 55 | Tarification par lieu | | F-RES-04 |

### 2.5 Clients, dossier et documents

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 56 | Base clients | Coordonnées, historique | F-CLI-01 |
| 57 | Fiche client complète | Photo, date de naissance, notes | F-CLI-02 |
| 58 | Historique des rendez-vous et des paiements | | F-CLI-03 |
| 59 | Formulaires d'admission personnalisables | Questionnaire pré-consultation | F-FRM-01 |
| 60 | Formulaires conditionnels | Questions adaptatives | F-FRM-02 |
| 61 | Dossiers patients électroniques (DME/EMR) | Stockage sécurisé | F-MED-01 |
| 62 | Notes SOAP | Subjectif/Objectif/Analyse/Plan | F-MED-02 |
| 63 | Plans de traitement | Suivi de progression | F-MED-03 |
| 64 | Notes de séance / progression | | F-MED-04 |
| 65 | Assistant IA de prise de notes | Transcription et résumé | F-AI-01 |
| 66 | IA cloisonnée sans mémoire persistante | Pas d'entraînement sur les données | F-AI-02 |
| 67 | Signature électronique | Consentements, décharges | F-SIG-01 |
| 68 | Partage sécurisé de fichiers | Vérification antivirus | F-DOC-01 |
| 69 | Gestion documentaire centralisée | | F-DOC-02 |
| 70 | Export du dossier en PDF | | F-DOC-03 |
| 71 | Portail client sécurisé | Accès dossier, documents, rendez-vous | F-PRT-01 |
| 72 | Évaluations post-traitement | Questionnaire de satisfaction | F-FDB-01 |
| 73 | Demande d'avis en ligne | Sollicitation après prestation | F-FDB-02 |

### 2.6 Communications

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 74 | Rappels SMS | | F-NOT-02 |
| 75 | Rappels courriel | | F-NOT-02 |
| 76 | Rappels avec confirmation | Lien de confirmation | F-NOT-03 |
| 77 | Messages bilingues | FR/EN automatique | F-NOT-04 |
| 78 | Communications de masse | Infolettre, annonces | F-NOT-05 |
| 79 | Modèles de messages personnalisables | Variables | F-NOT-06 |
| 80 | Notifications internes au praticien | Nouveau rendez-vous, annulation | F-NOT-07 |
| 81 | Relance no-show | | F-NOT-08 |
| 82 | Demande d'avis / remerciement automatique | | F-NOT-09 |

### 2.7 Paiements et facturation

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 83 | Paiement en ligne (Stripe) | À la réservation, acompte | F-BIL-01 |
| 84 | Encaissement sur place | Carte, comptant | F-BIL-02 |
| 85 | Facturation et reçus | Émission, envoi | F-BIL-03 |
| 86 | Facturation récurrente / abonnement | | F-BIL-04 |
| 87 | Taxes (TPS/TVQ, TVA) | Configuration | F-BIL-05 |
| 88 | Rapports de revenus | | F-BIL-06 |
| 89 | Point de vente (POS) | Vente de produits | F-BIL-07 |
| 90 | Gestion d'inventaire | Stock produits | F-BIL-08 |
| 91 | Cartes-cadeaux | | F-BIL-09 |
| 92 | Programme de fidélité | Points, récompenses | F-BIL-10 |
| 93 | Télétransmission des feuilles de soins / assurance | TELUS eClaims (Canada) | WON'T V1 (F-BIL-11 en V2) |
| 94 | Intégration QuickBooks | Comptabilité | F-INT-04 (V1.1) |

### 2.8 Équipe et organisation

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 95 | Comptes employés inclus | Secrétaires, réceptionnistes | F-ORG-01 |
| 96 | Rôles et permissions granulaires | Lecture / édition par module | F-ORG-02 |
| 97 | Télésecrétariat | Gestion d'agendas pour autrui | F-ORG-03 |
| 98 | Agenda de l'équipe | | F-AGD-03 |
| 99 | Masquage des noms de clients sur l'horaire | Confidentialité en accueil | F-ORG-04 |
| 100 | Gestion des horaires de travail | | F-AVL-01 |
| 101 | Comptes administratifs gratuits | | F-ORG-01 |

### 2.9 Analyse, reporting, exports

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 102 | Tableau de bord d'activité | Rendez-vous, revenus, présence | F-ANL-01 |
| 103 | Rapports personnalisables | | F-ANL-02 |
| 104 | Insights clients | Clients réguliers, fréquence | F-ANL-03 |
| 105 | Export CSV / Excel / PDF | | F-ANL-04 |
| 106 | Google Analytics sur la page publique | | F-ANL-05 |
| 107 | Taux de présence / no-show | Indicateur clé | F-ANL-06 |
| 108 | Performance par praticien | | F-ANL-07 |

### 2.10 Technique, sécurité, conformité

| # | Fonctionnalité | Détail | MyRDV |
|---|---|---|---|
| 109 | API publique | | F-INT-01 |
| 110 | Intégrations tierces (Zapier, Zoom, QuickBooks) | | F-INT-02 → F-INT-05 |
| 111 | Chiffrement en transit et au repos | TLS, AES-256 | NFR-SEC-01 |
| 112 | Authentification multifacteur | TOTP | NFR-SEC-02 |
| 113 | Déconnexion automatique après inactivité | | NFR-SEC-03 |
| 114 | Journal d'audit complet | Date, heure, identité, action | NFR-SEC-04 |
| 115 | Sauvegardes continues et redondance | PITR | NFR-OPS-01 |
| 116 | Protection réseau (CDN/WAF) | Cloudflare | NFR-SEC-05 |
| 117 | Hébergement régional | Canada / UE / US | NFR-CMP-01 |
| 118 | Conformité Loi 25 / LPRPSD / PIPEDA / PHIPA | | NFR-CMP-02 |
| 119 | Conformité HIPAA | | NFR-CMP-03 |
| 120 | Accès en lecture seule après résiliation | Conservation des données | NFR-CMP-04 |
| 121 | Sauvegarde/restauration et continuité | RTO/RPO | NFR-OPS-02 |
| 122 | Multi-langue de l'interface | FR/EN (+ ES, DE en V2) | F-I18N-01 |
| 123 | Onboarding assisté gratuit | | F-ONB-01 |

> Les numéros 1 à 123 sont des lignes de grille (certaines lignes regroupent plusieurs fonctions) ;
> le décompte « 108 fonctionnalités » des annuaires correspond à un découpage différent. La matrice
> complète de traçabilité figure en annexe,
> [`annexes/tracabilite-gorendezvous.md`](../annexes/tracabilite-gorendezvous.md).

---

## 3. Synthèse de la couverture

| Domaine | Fonctions GOrendezvous | Couvertes en V1 | Différées V1.1/V2 | Hors périmètre |
|---|---|---|---|---|
| Réservation en ligne | 20 | 18 | 2 (annuaire enrichi) | 0 |
| Gestion des rendez-vous | 15 | 15 | 0 | 0 |
| Agenda et disponibilités | 13 | 13 | 0 | 0 |
| Ressources | 7 | 7 | 0 | 0 |
| Clients / dossier | 18 | 16 | 2 (IA, évaluations avancées) | 0 |
| Communications | 9 | 9 | 0 | 0 |
| Paiements / facturation | 12 | 10 | 1 (QuickBooks) | 1 (télétransmission assurance) |
| Équipe / organisation | 7 | 7 | 0 | 0 |
| Analyse / exports | 7 | 7 | 0 | 0 |
| Technique / conformité | 15 | 13 | 1 (SSO SAML) | 1 (on-premise) |
| **Total** | **123 lignes** | **115** | **8** | **2** |

**Lecture** : la V1 couvre fonctionnellement GOrendezvous à **93 %**, avec deux écarts assumés
(absence d'offre on-premise, télétransmission des feuilles de soins limitée à la France en V2) et
quatre différenciateurs nets : moteur de récurrence avancé, conformité UE native, API documentée,
tarification sans quota de rendez-vous.

---

## 4. Positionnement retenu

> **Pour** les professionnels de la santé, du bien-être et des services qui gèrent des rendez-vous
> répétés dans la durée, **qui** subissent les limites des agendas génériques et la rigidité des
> logiciels cliniques, **MyRDV est** une plateforme de rendez-vous tout-en-un **qui** rend les séries
> récurrentes prévisibles, modifiables et sans conflit, **contrairement à** GOrendezvous et Calendly
> **dont** la récurrence se limite à une fréquence sans politique d'exception ni gestion fine des
> bornes.

Trois preuves à apporter (et à mesurer en recette) :

1. **Une série de 3 mois se crée en moins de 45 secondes** et son résultat est exact au jour près,
   y compris en cas de changement d'heure (F-REC-01, test T-REC-014).
2. **Aucune occurrence silencieusement perdue** : chaque occurrence ignorée est listée et expliquée
   dans l'interface et dans l'API (R-14).
3. **Toute modification de série est réversible et auditable** : régénération idempotente, diff
   présenté avant validation (R-17).

---

## 5. Sources consultées

- GOrendezvous, *Scheduling & Appointment management* — info.gorendezvous.com/en/features/scheduling
- GOrendezvous, pages produit et recherche publique — gorendezvous.com/pro/en, gorendezvous.com/search
- Capterra, *GOrendezvous Software Pricing, Alternatives & More* — capterra.com/p/145659/GOrendezvous
- GetApp, *GOrendezvous Reviews, Prices & Ratings* — getapp.ca/software/107873/gorendezvous
- Software Advice, *GOrendezvous Review* — softwareadvice.com/calendar-app/gorendezvous-profile
- Appvizer, *GOrendezvous : avis, prix et fonctionnalités* — appvizer.fr
- logiciels.pro, *GOrendezvous : avis, prix, fonctionnalités & alternatives*
- Software Finder, *GOrendezvous Software Pricing, Reviews & Free Demo*
- Facture.net, *10 logiciels de prise de rendez-vous en ligne*

*Toutes les sources ont été consultées le 12 novembre 2026. Les prix affichés varient selon la
devise, la région et la date ; ils sont donnés à titre indicatif et ne constituent pas une offre.*

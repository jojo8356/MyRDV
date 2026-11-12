# Annexe — Glossaire

**Document** : annexe du cahier des charges MyRDV · **Version** 1.0 · 12 novembre 2026

---

## A. Termes métier

| Terme | Définition |
|---|---|
| **Abonnement de série** | Mode de facturation `SUBSCRIPTION` (R-23) : prélèvement périodique indépendant du nombre d'occurrences. |
| **Acompte** | Paiement partiel exigé à la réservation en ligne. |
| **Admission (formulaire d')** | Questionnaire rempli par le client avant la première consultation. |
| **Annuaire** | Page publique de recherche de professionnels (fonction V1.1). |
| **Attente (liste d')** | File de clients souhaitant un créneau indisponible, avec attribution automatique lors d'une libération. |
| **Avoir** | Document financier créditant un client (remboursement partiel, correction d'une série réduite). |
| **Clé d'occurrence** | Identifiant stable d'une séance au sein d'une série (`series_id@YYYYMMDDTHHMM`), garantissant l'idempotence (R-17). |
| **Clustered booking** | Regroupement de séances pour éliminer les temps morts (fonctionnalité concurrente reprise en V1.1). |
| **Congé** | Indisponibilité planifiée d'un praticien, impactant les séries (R-07). |
| **Créneau** | Intervalle de temps réservable. |
| **Détachement** | Action de modifier une occurrence sans altérer la règle de la série (R-13). |
| **DME / DMR** | Dossier médical électronique / dossier médical renseigné. |
| **Empreinte (d'un rendez-vous)** | Intervalle occupé incluant les tampons avant/après (R-09). |
| **ExDate (exception de date)** | Date retirée d'une série (R-08). |
| **Fenêtre de matérialisation** | Horizon glissant (30/90/180 jours) jusqu'auquel les occurrences sont créées en base (R-11). |
| **Forfait** | Ensemble prépayé de séances (mode `PREPAID_PACKAGE`, R-23). |
| **Jalon (milestone)** | Point de contrôle du projet (doc 10 §3). |
| **Jour férié** | Jour non travaillé légal, calculé par pays (y compris fêtes mobiles) (R-07). |
| **Liste d'attente intelligente** | Liste d'attente avec attribution automatique et offre multi-candidats. |
| **Matérialisation** | Écriture en base des occurrences calculées par la règle. |
| **No-show** | Client ne s'étant pas présenté sans annulation préalable. |
| **Occurrence** | Séance individuelle issue d'une série. |
| **Politique de conflit** | Conduite à tenir lorsqu'un créneau est indisponible : `FAIL`, `SKIP`, `SHIFT_SAME_DAY` (R-09). |
| **Portail client** | Espace personnel du client (rendez-vous, documents, factures). |
| **Praticien** | Professionnel délivrant des prestations, rattaché à une organisation. |
| **RDate (date ajoutée)** | Date ajoutée hors règle à une série (R-08). |
| **Récurrence** | Répétition planifiée d'un rendez-vous selon une règle (fréquence, jours, borne). |
| **Règle de récurrence** | Définition formelle d'une série (`FREQ`, `INTERVAL`, `BYDAY`, borne, exceptions). |
| **Rendez-vous pour deux** | Séance concernant deux clients (thérapie de couple, duo). |
| **Ressource** | Salle, équipement ou praticien mobilisé par un rendez-vous. |
| **Série** | Objet persistant portant une règle de récurrence et produisant des occurrences. |
| **Séance** | Synonyme d'occurrence dans le vocabulaire utilisateur. |
| **SOAP** | Structure de note clinique : Subjectif, Objectif, Analyse, Plan. |
| **Tampon (buffer)** | Temps de préparation ou de nettoyage avant/après un rendez-vous. |
| **Télésecrétariat** | Gestion des agendas d'autrui par un assistant habilité. |
| **Vacation** | Période de travail d'un praticien. |
| **Zone de déplacement** | Périmètre géographique d'une prestation à domicile. |

## B. Termes techniques

| Terme | Définition |
|---|---|
| **API REST** | Interface HTTP/JSON versionnée (`/v1`). |
| **Argon2id** | Fonction de dérivation de mot de passe résistante au GPU. |
| **at-least-once** | Garantie de livraison d'un message au moins une fois (impose l'idempotence côté consommateur). |
| **Blue/green** | Déploiement en deux environnements permutés, sans interruption. |
| **B-tree / GIN / GIST** | Familles d'index PostgreSQL ; `GIST` supporte les types spatiaux et temporels (`tstzrange`). |
| **CDN / WAF** | Réseau de diffusion et pare-feu applicatif en amont de l'application. |
| **CSP** | Content Security Policy, en-tête HTTP limitant les sources de contenu. |
| **DEK / KEK** | Clé de chiffrement de données / clé de chiffrement de clé (chiffrement d'enveloppe). |
| **Draft 2020-12** | Version du standard JSON Schema utilisée pour nos contrats. |
| **ETag / If-Match** | Mécanisme de concurrence optimiste sur les ressources. |
| **Fast-check / Hypothesis** | Bibliothèques de tests basés sur les propriétés. |
| **FREQ / INTERVAL / BYDAY** | Composantes d'une règle RFC 5545 (`RRULE`). |
| **HMAC-SHA256** | Code d'authentification de message utilisé pour signer les webhooks. |
| **IANA (fuseau)** | Base de données des fuseaux horaires (`Europe/Paris`, `America/Montreal`). |
| **ICS** | Format de calendrier (RFC 5545). |
| **Idempotency-Key** | En-tête garantissant qu'une requête rejouée n'a pas d'effet supplémentaire. |
| **JWT** | Jeton signé portant les droits, de courte durée. |
| **Kubernetes** | Orchestrateur de conteneurs. |
| **Modulith** | Monolithe organisé en modules à frontières explicites. |
| **NATS JetStream** | Bus d'événements persistant utilisé en interne. |
| **OpenAPI 3.1** | Spécification de description d'API REST. |
| **OWASP ASVS** | Référentiel de vérification de sécurité applicative. |
| **P95 / P99** | Percentiles de latence (95 % / 99 % des requêtes en dessous). |
| **PWA** | Application web progressive, installable, avec cache hors-ligne. |
| **RBAC** | Contrôle d'accès basé sur les rôles. |
| **RLS** | Row-Level Security PostgreSQL : filtrage des lignes par tenant. |
| **RPO / RTO** | Perte de données maximale admissible / durée de rétablissement maximale. |
| **RRULE** | Propriété iCalendar décrivant une récurrence. |
| **SBOM** | Inventaire logiciel (Software Bill of Materials). |
| **SLO / SLA** | Objectif de niveau de service / engagement contractuel. |
| **STRIDE** | Taxonomie de menaces (Spoofing, Tampering, Repudiation, Information disclosure, DoS, Elevation). |
| **TSTZRANGE** | Type PostgreSQL représentant un intervalle horodaté avec fuseau. |
| **ULID** | Identifiant unique triable chronologiquement (26 caractères). |
| **Webhook** | Notification HTTP poussée vers un système tiers, signée. |

## C. Sigles

| Sigle | Signification |
|---|---|
| ADR | Architecture Decision Record |
| BAA | Business Associate Agreement (HIPAA) |
| CAI | Commission d'accès à l'information (Québec) |
| CNIL | Commission nationale de l'informatique et des libertés (France) |
| CCT / SCC | Clauses contractuelles types |
| DPA | Data Processing Agreement |
| DPIA / EFVP | Analyse d'impact relative à la protection des données / évaluation des facteurs relatifs à la vie privée |
| GA | General Availability (mise en service commerciale) |
| HDS | Hébergement de données de santé (certification française) |
| HIPAA | Health Insurance Portability and Accountability Act |
| MoSCoW | Must / Should / Could / Won't |
| PHIPA | Personal Health Information Protection Act (Ontario) |
| PIPEDA | Personal Information Protection and Electronic Documents Act (Canada) |
| RGAA | Référentiel général d'amélioration de l'accessibilité (France) |
| RGPD | Règlement général sur la protection des données |
| SUS | System Usability Scale |
| WCAG | Web Content Accessibility Guidelines |

---

*Retour à la [table des matières](../README.md).*

# 04 — Sécurité, protection des données et conformité

**Document** : 04 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Référentiels** : RGPD (UE 2016/679) · Loi 25 (Québec) · PIPEDA/LPRPDÉ (Canada) · PHIPA (Ontario) ·
HIPAA (US, sur option) · ISO/IEC 27001:2022 (annexe A) · OWASP ASVS 4.0 niveau 2 · NIST SP 800-63B
**Propriétaires** : RSSI (sécurité), DPO (conformité), CTO (technique)

---

## 1. Principes directeurs

1. **Privacy by design & by default** — minimisation, finalité, conservation limitée, sécurité dès la
   conception (art. 25 RGPD).
2. **Séparation des données de santé et des données administratives** — tables, clés de chiffrement
   et droits distincts (un comptable ne voit jamais une note clinique ; un assistant non plus).
3. **Moindre privilège** — 7 rôles, 64 permissions atomiques, revue trimestrielle des accès.
4. **Traçabilité intégrale** — toute action sur une donnée de santé, une série ou une facture est
   auditée de façon immuable.
5. **Réversibilité** — export complet à tout moment, suppression réelle sur demande, pas de
   rétention cachée.

---

## 2. Classification des données

| Classe | Exemples | Chiffrement | Accès | Conservation |
|---|---|---|---|---|
| **C4 — Santé (art. 9)** | Notes SOAP, formulaires d'admission, diagnostics, ordonnances, transcription IA | AES-256-GCM au repos, clé dédiée par organisation (enveloppe KEK/DEK), TLS 1.3 | Praticien propriétaire + admin sur habilitation explicite | Durée légale locale (20 ans France pour le dossier médical ; 5 ans post-dernier-contact Québec) |
| **C3 — Identité client** | Nom, e-mail, téléphone, date de naissance, adresse | AES-256-GCM, colonnes sensibles chiffrées au niveau applicatif | Selon rôle | Tant que le compte est actif + 3 ans |
| **C2 — Transactionnel** | Rendez-vous, factures, paiements | AES-256-GCM | Rôles financiers et praticiens | 10 ans (obligation comptable) |
| **C1 — Métadonnées** | Logs techniques, métriques, audit | Chiffrement au repos standard | Ops, RSSI | 12 mois (logs), 10 ans (audit de sécurité) |
| **C0 — Public** | Page de réservation, annuaire | — | Tout public | — |

**Règle de sécurité** : aucune donnée C3/C4 ne doit apparaître dans un journal applicatif, un message
d'erreur, un webhook ou une notification (SMS/push). Un test automatisé vérifie l'absence de motifs
sensibles dans les logs (doc 09 T-SEC-012).

---

## 3. Cadre réglementaire et conformité

### 3.1 RGPD (Union européenne)

| Obligation | Mise en œuvre MyRDV |
|---|---|
| Base légale (art. 6) | Exécution du contrat (réservation, facturation) ; consentement explicite pour les communications marketing et l'IA ; intérêt légitime documenté pour la sécurité |
| Donnée de santé (art. 9.2.h) | Traitement sous responsabilité du professionnel de santé ; MyRDV = **sous-traitant** (art. 28), DPA signable en ligne |
| Information (art. 13-14) | Politique de confidentialité par finalité, registre des traitements public (annexe) |
| Droits (art. 15-22) | Portail client + API : accès, rectification, effacement, portabilité (JSON/CSV), opposition, limitation — délai de réponse 15 jours ouvrés |
| DPIA (art. 35) | DPIA type par usage (santé, géolocalisation de l'annuaire) — réalisée avant mise en service |
| Violation (art. 33-34) | Procédure de notification CNIL sous 72 h, modèle de communication aux personnes |
| Sous-traitants (art. 28) | Registre, clauses contractuelles types, audit annuel (Stripe, Twilio, AWS/OVH, Zoom) |
| Transferts (art. 44+) | Hébergement UE par défaut ; transfert hors UE uniquement sur décision d'adéquation ou CCT, avec analyse d'impact |
| DPO | Désigné, contact publié, registre tenu |
| Cookies (art. 82 LIL + ePrivacy) | Bandeau conforme CNIL, refus aussi simple que l'acceptation, aucun traceur avant consentement |

### 3.2 Loi 25 (Québec)

- Politiques de gouvernance des renseignements personnels publiées et accessibles.
- **Évaluation des facteurs relatifs à la vie privée (EFVP)** avant tout projet traitant des
  renseignements personnels.
- Registre des incidents de confidentialité ; obligation de notifier la CAI et les personnes en cas de
  préjudice sérieux.
- Droit à la portabilité et à la désindexation ; « renseignement personnel » inclut les données
  pseudonymisées.
- Consentement **manifeste, libre, éclairé et donné à des fins spécifiques** ; consentement renforcé
  pour les mineurs de moins de 14 ans (accord du titulaire de l'autorité parentale).
- Hébergement : option **Canada (Montréal)** avec engagement contractuel de non-transfert.

### 3.3 PHIPA (Ontario) et HIPAA (US, option)

| Exigence | Mise en œuvre |
|---|---|
| PHIPA : custodien des renseignements sur la santé | Contrat de HSP (Health Information Network Provider) disponible ; hébergement canadien ; journal d'accès |
| HIPAA : Security Rule (administrative, physical, technical safeguards) | BAA signable (Business Associate Agreement) ; chiffrement au repos et en transit ; contrôle d'accès unique ; audit logs 6 ans ; plan de réponse à incident ; formation du personnel |
| HIPAA : Privacy Rule | Minimisation, pas de marketing sans autorisation, droits d'accès 30 jours, divulgation comptable |
| HIPAA : Breach Notification Rule | Notification sous 60 jours, modèle de notification, analyse de risque documentée |
| Exigences techniques §164.312 | Contrôle d'accès, audit, intégrité, authentification, transmission sécurisée |

**Périmètre** : les options Loi 25/PHIPA/HIPAA ne sont disponibles que sur les offres Business et
Entreprise, après signature d'un avenant et sélection d'une région d'hébergement compatible.

### 3.4 Autres cadres sectoriels

- **OPQ / OPSQ (Québec)** : formats de dossier compatibles avec les exigences de tenue de dossier des
  ordres professionnels (notes datées, signées, versionnées).
- **France** : recommandations ANSI/ANS — hébergement de données de santé (HDS) **si** un client
  exige la certification HDS : l'offre Entreprise peut être déployée chez un hébergeur certifié HDS
  (partenariat OVHcloud HDS).
- **Accessibilité** : RGAA 4.1 / WCAG 2.1 AA (doc 08 §5).

---

## 4. Sécurité applicative

### 4.1 Authentification

| Mesure | Détail |
|---|---|
| Mots de passe | Argon2id (m=64 MiB, t=3, p=4) ; longueur minimale 12 ; vérification contre les bases de fuites (k-anonymity HIBP) |
| MFA | TOTP obligatoire pour OWNER/ADMIN ; proposé aux praticiens ; WebAuthn disponible |
| Portail client | Lien magique (jeton 256 bits, usage unique, 15 min) + OTP 6 chiffres ; aucune création de mot de passe imposée |
| Sessions | JWT courts (15 min) + refresh token rotatif (30 j), révocation immédiate, cookie `HttpOnly`, `Secure`, `SameSite=Lax` |
| Verrouillage | 10 échecs / 15 min → blocage 15 min ; détection de bourrage d'identifiants |
| Déconnexion | Inactivité 30 min (paramétrable), déconnexion à distance par l'admin |
| Journalisation | Connexions, échecs, changements de mot de passe, activations MFA |

### 4.2 Sécurité des interfaces

- En-têtes : HSTS 1 an avec `preload`, CSP stricte (nonce, pas d'`unsafe-inline`), `X-Content-Type-Options`,
  `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` minimal, `frame-ancestors`
  limité aux domaines autorisés pour le widget de réservation.
- CSRF : jetons synchrones sur les formulaires, `SameSite` sur les cookies, vérification `Origin`.
- XSS : échappement systématique, pas de `dangerouslySetInnerHTML`, assainissement du HTML des
  courriels (DOMPurify côté serveur pour les modèles personnalisés).
- Téléversements : antivirus (ClamAV + moteur heuristique), validation MIME réelle (magic bytes),
  taille max 25 Mo, stockage hors racine web, noms UUID, quarantaine avant analyse.
- Upload d'ICS : validation stricte, refus des `VEVENT` imbriqués, taille max 5 Mo.
- SSRF : liste d'autorisation des hôtes sortants (webhooks), résolution DNS contrôlée.
- IDOR : tous les accès sont filtrés par `organization_id` au niveau du dépôt (row-level security).

### 4.3 Sécurité des API

- OAuth 2.0 + PKCE, scopes granulaires (`series:read`, `series:write`, `appointments:read`…).
- Clés d'API hachées (SHA-256) en base, préfixe visible (`mrdv_live_pk_…`), rotation sans coupure.
- Limitation de débit par organisation, par utilisateur et par IP ; protection anti-rejeu.
- Validation stricte des schémas (les champs inconnus sont refusés).
- Réponses d'erreur sans fuite d'information interne (pas de stack trace, pas de nom de table).

### 4.4 Modèle de menaces (STRIDE)

| Menace | Scénario | Contre-mesure | Test |
|---|---|---|---|
| **S**poofing | Vol de session praticien | JWT courts, rotation refresh, MFA, détection d'IP inhabituelle | T-SEC-003 |
| **T**ampering | Modification d'un rendez-vous d'un autre tenant | RLS PostgreSQL, vérification d'appartenance sur chaque écriture | T-SEC-020 |
| **R**epudiation | Contestation d'une annulation | Journal d'audit signé (chaîne de hachage), rétention 10 ans | T-SEC-021 |
| **I**nformation disclosure | Note clinique dans un courriel de rappel | Règle de contenu neutre, tests d'absence de motifs sensibles | T-SEC-012 |
| **D**enial of service | Série de 10 000 occurrences par API | Plafonds R-10/R-16, limitation de débit, CAPTCHA | T-SEC-030 |
| **E**levation of privilege | Assistant accédant aux notes | Permissions atomiques, tests matriciels de rôles | T-SEC-040 |
| Rejeu d'idempotence | Série créée en double | `Idempotency-Key` + contrainte d'unicité | T-API-030 |
| Fuite de webhook | Secret compromis | Rotation semestrielle, signature, IP allowlist optionnelle | T-SEC-050 |
| Injection SQL | Paramètre de recherche | Requêtes paramétrées, ORM, tests SAST et fuzzing | T-SEC-060 |
| Dépendance compromise | Paquet npm malveillant | SBOM, Dependabot, signature des artefacts, `npm audit` bloquant en CI | T-SEC-070 |

### 4.5 Sécurité de l'infrastructure

- Isolation réseau (VPC, sous-réseaux privés), aucun accès public aux bases.
- Chiffrement des volumes, sauvegardes chiffrées avec clé distincte.
- Secrets dans un coffre (AWS Secrets Manager / Vault), jamais en clair dans le dépôt ni dans les
  variables d'environnement de build.
- Accès administrateur par bastion avec MFA et session enregistrée ; pas de compte root quotidien.
- Correctifs : critique < 7 jours, élevé < 30 jours, moyen < 90 jours.
- Tests d'intrusion annuels par un tiers, scan continu (SAST, DAST, SCA), bug bounty privé en V1.1.
- SBOM (CycloneDX) livré à chaque version, signé.

---

## 5. Résilience et continuité

| Objectif | Valeur | Vérification |
|---|---|---|
| RPO (perte de données max) | 5 minutes | Sauvegarde continue WAL + restauration testée mensuellement |
| RTO (reprise max) | 1 heure | Runbook de bascule testé chaque trimestre |
| Disponibilité cible | 99,9 % / mois | SLO doc 08 |
| Sauvegardes | Quotidiennes complètes 35 j, mensuelles 12 mois, restauration ponctuelle | Exercice de restauration documenté |
| Région de secours | Lecture seule en cas de sinistre régional, bascule complète < 4 h | Test annuel |
| Journal d'audit | Immuable (append-only, chaîne de hachage), répliqué | Vérification d'intégrité quotidienne |

**Plan de réponse à incident** (extrait) : détection → qualification (P1 : fuite de données, indisponibilité
totale ; P2 : dégradation) → confinement → éradication → rétablissement → notification (CNIL 72 h,
CAI, personnes concernées) → retour d'expérience sous 10 jours ouvrés → mise à jour du registre.

---

## 6. Gouvernance des données

### 6.1 Registre des traitements (extrait)

| Traitement | Finalité | Base légale | Catégories | Durée | Destinataires |
|---|---|---|---|---|---|
| Gestion des rendez-vous | Exécution du service | Contrat | C2, C3 | 3 ans après dernier contact | Praticien, client |
| Dossier patient | Soins | Art. 9.2.h (sous responsabilité du praticien) | C4 | Durée légale locale | Praticien habilité |
| Rappels SMS/e-mail | Réduction du no-show | Contrat / consentement | C3 (minimal) | 30 jours (contenu), 12 mois (logs) | Opérateur SMS |
| Facturation | Obligation légale | Obligation légale | C2 | 10 ans | Autorité fiscale, comptable |
| Anonymisation analytique | Amélioration du service | Intérêt légitime | C1 | 24 mois | Équipe produit |
| Assistant IA de notes | Aide à la rédaction | Consentement explicite | C4 | Durée de la note | Fournisseur IA sous-traitant (UE) |

### 6.2 Sous-traitants (extrait)

| Sous-traitant | Rôle | Localisation | Garanties |
|---|---|---|---|
| AWS / OVHcloud | Hébergement | UE / Canada / US (selon option) | ISO 27001, SOC 2, CCT, HDS (option FR) |
| Stripe | Paiement | UE / US | PCI-DSS niveau 1, CCT |
| Twilio / Vonage | SMS | UE / US | CCT, DPA |
| Postmark / SES | Courriel | UE / US | CCT, DPA |
| Zoom / Whereby | Visioconférence | UE / US | DPA, chiffrement de bout en bout optionnel |
| Fournisseur IA (EU) | Aide à la rédaction | UE | Pas d'entraînement sur les données, isolation, DPA |

### 6.3 Rétention et purge

| Donnée | Durée | Mécanisme |
|---|---|---|
| Notes cliniques | Durée légale (20 ans FR, 5 ans QC ou selon ordre) | Archivage à froid, purge automatique documentée |
| Factures | 10 ans | Purge impossible avant terme (obligation légale) |
| Rendez-vous | 3 ans | Anonymisation au-delà |
| Logs techniques | 12 mois | Rotation et suppression |
| Journal d'audit | 10 ans | Conservation immuable |
| Enregistrements de séance (si option) | 30 jours | Suppression automatique |
| Comptes supprimés | 30 jours de corbeille | Effacement définitif (sauf obligations) |

**Effacement et anonymisation.** Sur demande d'un client, les données C3/C4 sont supprimées ; les
données C2 indispensables (facturation) sont conservées mais **pseudonymisées** (nom remplacé par
« Client supprimé #hash »), conformément à l'obligation comptable. L'utilisateur est informé de cette
limite.

---

## 7. Journal d'audit

| Événement audité | Champs |
|---|---|
| Connexion/déconnexion, échec, MFA | acteur, IP, user-agent, horodatage, résultat |
| Création/modification/suppression d'une série | acteur, série, portée, `diff`, avant/après |
| Modification d'une occurrence | acteur, clé, avant/après |
| Accès à une note clinique | acteur, client, note, action (lecture/écriture) |
| Export de données | acteur, périmètre, format, volume |
| Changement de permission | acteur, cible, avant/après |
| Modification de paramètre d'organisation | acteur, paramètre, avant/après |
| Accès administrateur (support) | acteur, motif, durée, périmètre |

**Propriétés** : append-only, chaîne de hachage (chaque entrée contient le hash de la précédente),
horodatage serveur, conservation 10 ans, export CSV/JSON, recherche par acteur/client/période
(réservée aux rôles `OWNER`/`ADMIN`).

**Accès support (impersonation)** : uniquement sur demande écrite du client, durée limitée, bannière
visible dans l'application du client, audit complet, notification au client.

---

## 8. Sécurité du module de récurrence (analyse spécifique)

Le module de récurrence introduit des risques propres :

| Risque | Description | Mesure |
|---|---|---|
| Déni de service par séries géantes | Une API peut créer 10 000 occurrences | Plafonds R-10/R-16, limitation de débit, `dryRun` borné à 400 occurrences |
| Amplification de notifications | Une modification `ALL` envoie 40 SMS | Anti-flood R-18 : un seul message de synthèse |
| Décalage silencieux de séances | Bug de fuseau non détecté | Double implémentation (simulateur + production) comparée en CI (T-REC-050) |
| Fuite par récapitulatif de série | Le récapitulatif révèle un suivi psychologique | Message neutre, pas de motif, pas de spécialité, en-tête générique |
| Manipulation d'un `exdate` pour masquer une annulation | Fraude interne | Journal d'audit immuable, motif obligatoire pour un retrait manuel |
| Dépassement de plafond par fractionnement | Un utilisateur crée 10 séries de 12 au lieu d'une de 120 | Plafond de séries actives par offre (R-16) et détection de motifs (métrique d'alerte) |
| Effet de bord lors d'un changement de fuseau de lieu | Occurrences décalées | Le fuseau de la série est figé à la création ; un changement de fuseau du lieu crée une révision explicite avec `diff` |

---

## 9. Sensibilisation et organisation

- Charte de sécurité signée par chaque collaborateur, formation annuelle obligatoire (phishing,
  données de santé, RGPD).
- Séparation des environnements (dev, staging, prod) ; aucune donnée réelle en dev (jeu de données
  synthétique).
- Revue de code obligatoire (2 approbations pour le code touchant à la santé ou aux paiements).
- Gestion des secrets et rotation trimestrielle.
- Astreinte 24/7 pour les incidents P1, avec escalade documentée.
- Assurance cyber et plan de communication de crise.

---

## 10. Matrice de conformité synthétique

| Exigence | Statut cible V1 | Preuve |
|---|---|---|
| Registre des traitements | Conforme | Annexe publique |
| DPA signable en ligne | Conforme | Document contractuel |
| DPIA santé réalisée | Conforme | Dossier DPIA |
| Chiffrement au repos et en transit | Conforme | Configuration + tests |
| MFA disponible, obligatoire pour admins | Conforme | Test T-SEC-002 |
| Journal d'audit immuable | Conforme | Test T-SEC-021 |
| Notification de violation < 72 h | Procédure prête | Runbook + exercice |
| Portabilité (export JSON/CSV) | Conforme | Test T-CMP-010 |
| Effacement/anonymisation | Conforme | Test T-CMP-011 |
| Hébergement UE par défaut | Conforme | Choix d'infrastructure |
| Option Canada (Loi 25) | Conforme sur Business | Test de déploiement |
| HIPAA (BAA) | Sur option Business/Entreprise | Dossier de conformité |
| ISO 27001 | Visé V2 (S1 2028) | Feuille de route |
| HDS (France) | Option Entreprise via partenaire | Contrat partenaire |
| WCAG 2.1 AA | Visé V1 sur parcours critiques | Audit doc 09 |

---

*Suite : [`05-architecture-technique.md`](05-architecture-technique.md).*

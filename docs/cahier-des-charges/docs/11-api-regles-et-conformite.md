# 11 — Règles d'API et conformité (RGPD et standards d'entreprise)

**Document** : 11 / 11 · **Version** 1.0 · **Date** : 12 novembre 2026 · **Statut** : normatif
**Portée** : toutes les interfaces exposées par MyRDV — API publique `/v1`, API partenaires, webhooks
sortants, consoles d'administration, futurs endpoints `/v2`
**Référentiels** : RGPD (UE 2016/679) et lignes directrices EDPB · Directive ePrivacy 2002/58/CE ·
Loi 25 (Québec) · PIPEDA/LPRPDÉ · PHIPA (Ontario) · HIPAA (option US) · **ISO/IEC 27001:2022**
(annexe A) · **ISO/IEC 27701:2019** (gestion de la vie privée) · **OWASP ASVS 4.0 niveau 2** ·
**OWASP API Security Top 10 (2023)** · NIST SP 800-63B (authentification) · RFC 9110/9111/9457 ·
PCI-DSS v4.0 (périmètre délégué à Stripe)
**Propriétaires** : DPO (conformité), RSSI (sécurité), lead API (technique)
**Normativité** : les règles `API-xx` ci-dessous sont **opposables**. Toute dérogation exige une ADR
et une validation DPO + RSSI. Les exigences fonctionnelles citées (`F-*`, `NFR-*`) proviennent du
[document 03](03-exigences-fonctionnelles.md) et du [document 08](08-exigences-non-fonctionnelles.md).

---

## 1. Objet et méthode

Ce document répond à une question précise : **qu'est-ce qu'une API conforme, quand on traite des
données de santé de clients européens et canadiens ?** Il ne répète pas le catalogue d'endpoints du
[document 07](07-api-et-schemas-rdv-recurrents.md) ni le cadre juridique général du
[document 04](04-securite-conformite.md) : il traduit les deux en **règles vérifiables appliquées à
l'interface**.

Trois principes gouvernent l'ensemble :

1. **L'API est une surface de traitement de données personnelles.** Chaque endpoint a une finalité,
   une base légale, une durée de conservation et un niveau de classification (doc 04 §2,
   C0 → C4). Un endpoint sans finalité documentée n'est pas livré.
2. **Le droit ne se « déclare » pas, il se teste.** Chaque règle de ce document renvoie à un test du
   [plan de recette](09-plan-tests-recette.md) ou à un contrôle automatisé décrit ici (§12).
3. **Ce qui n'est pas nécessaire est interdit par défaut.** Pas de champ optionnel « au cas où »,
   pas de journal contenant une donnée C3/C4, pas d'endpoint d'export « pour le confort ».

### 1.1 Ce qui était couvert avant ce document

| Sujet | Où il était traité | Complétude |
|---|---|---|
| Cadre juridique (RGPD, Loi 25, HIPAA), registre, DPA, rétention | doc 04 §3 et §6 | complet |
| Sécurité API (OAuth, scopes, débit, validation) | doc 04 §4.3 | 5 puces — **insuffisant** pour une revue sécurité |
| Conventions et contrat des endpoints de récurrence | doc 07 §1 à §12 | complet sur `/series` et `/occurrences` |
| **Règles transverses d'API, droits des personnes, sous-traitance technique, en-têtes, versionnage, dépréciation, journalisation, traitement des incidents, webhooks conformes** | — | **manquant → ce document** |
| **Contrat OpenAPI 3.1 exécutable et interface Swagger** | — | **manquant → `api/`** |

---

## 2. Classification appliquée au contrat d'API

Chaque propriété du contrat porte une classification, qui détermine son chiffrement, sa présence
dans les journaux et son sort en cas d'effacement.

| Classe (doc 04 §2) | Exemples dans l'API | Règle de contrat |
|---|---|---|
| **C4 — Santé** | note clinique, formulaire d'admission, diagnostic | **Jamais** dans le contrat `/v1` public (API-01). Accessible uniquement via l'API interne de l'application, sous habilitation explicite et journalisation C4 |
| **C3 — Identité client** | `clientId`, nom, e-mail, téléphone, date de naissance | Exposé en lecture, masquable, effaçable, exportable ; chiffré au repos ; jamais journalisé (API-02) |
| **C2 — Transactionnel** | `seriesId`, `startAt`, montants, factures | Exposé, conservé 10 ans, pseudonymisé en cas d'effacement (API-14) |
| **C1 — Métadonnées** | `requestId`, statuts, compteurs, `etag` | Exposé, journalisé, 12 mois |
| **C0 — Public** | page de réservation, annuaire | Contrat séparé, sans authentification, limitation de débit par IP |

**API-01** — Aucun schéma de réponse de l'API publique ne contient de champ de classe C4. Le contrôle
est automatisé : la liste des noms de champs interdits (`symptom*`, `diagnos*`, `note*`, `soap*`,
`treatment*`, `prescription*`, `attachment*`) est vérifiée sur le contrat OpenAPI en intégration
continue (test T-SEC-012). Toute tentative de contournement (champ libre de type `object`) est
refusée par `additionalProperties: false`.

**API-02** — Aucune valeur de classe C3/C4 n'apparaît dans un journal, une trace, un message d'erreur,
un webhook ou un libellé de métrique. Les journaux ne contiennent que des identifiants opaques
(ULID), des codes d'erreur et des durées.

---

## 3. Règles de contrat (normatives)

### 3.1 Identité, authentification, autorisation

| ID | Règle | Vérification |
|---|---|---|
| API-03 | OAuth 2.0 **authorization code + PKCE (S256)** obligatoire pour tout client agissant au nom d'un utilisateur ; `client_credentials` réservé aux intégrations serveur-à-serveur d'organisation | tests de conformité OAuth (T-API-010) |
| API-04 | Jeton d'accès JWT signé **RS256**, durée **≤ 15 min**, `aud` = API ciblée, `iss` vérifié, `jti` unique, `kid` en en-tête (rotation de clés mensuelle) | analyse statique + test de rejeu |
| API-05 | Refresh token **rotatif à usage unique**, lié à l'appareil, famille révoquée à la première réutilisation (détection de vol) | T-SEC-003 |
| API-06 | **Scopes granulaires** `<ressource>:<action>` (`series:read`, `series:write`, `series:delete`, `series:regenerate`, `appointment:*`, `client:read`, `invoice:*`, `report:read`, `audit:read`, `webhook:manage`, `export:create`) ; un scope n'accorde jamais plus que le rôle | T-SEC-040 |
| API-07 | **Double barrière** : le scope (ce que l'intégration peut faire) **et** le rôle dans l'organisation (ce que la personne peut faire). Les deux sont évalués à chaque requête, dans cet ordre : authentification → scope → appartenance à l'organisation (`organization_id` du jeton) → rôle → propriété de la ressource | T-SEC-020 (62 endpoints, accès croisé refusé) |
| API-08 | **Aucune confiance dans un identifiant d'organisation fourni par le client** : `organization_id` est toujours dérivé du jeton, jamais du corps ou du chemin | revue de code + test d'escalade |
| API-09 | Clés d'API d'organisation hachées en base (**Argon2id**), préfixe identifiable (`mrdv_live_pk_…`, `mrdv_live_sk_…`), rotation sans coupure avec chevauchement de 24 h, révocation immédiate possible | test de rotation |
| API-10 | MFA (TOTP ou WebAuthn) **obligatoire** pour les rôles `OWNER`/`ADMIN` et pour toute création de clé d'API ; l'API refuse (`AUTH_403_MFA_REQUIRED`) une opération sensible issue d'une session sans MFA | T-SEC-002 |
| API-11 | Impersonation de support interdite par l'API publique ; elle n'existe que dans la console interne, sur demande écrite du client, avec bannière visible, durée limitée et entrée d'audit | T-SEC-021 |

### 3.2 Transport et en-têtes

| ID | Règle | Vérification |
|---|---|---|
| API-12 | **HTTPS/TLS 1.3 uniquement** (TLS 1.2 toléré jusqu'à fin 2027), HSTS `max-age=63072000; includeSubDomains; preload`, redirection HTTP → HTTPS, pas de HTTP/1.0 | scan TLS automatisé |
| API-13 | En-têtes de réponse systématiques : `Cache-Control: no-store` sur toute réponse contenant du C2/C3, `X-Content-Type-Options: nosniff`, `X-Request-Id`, `RateLimit-Limit/Remaining/Reset`, `Retry-After` sur 429/503, `Content-Security-Policy: default-src 'none'` sur les réponses JSON, `Referrer-Policy: no-referrer` | test d'en-têtes sur 100 % des routes |
| API-14 | **CORS** : liste blanche par organisation (domaines vérifiés par enregistrement DNS ou fichier), jamais `*` avec credentials, préflight mis en cache 600 s | test CORS |
| API-15 | **Client Hints et données de connexion** : l'API n'expose jamais l'IP réelle d'un client final à un tiers ; les webhooks ne transportent ni IP ni `User-Agent` du client final | revue de contrat |
| API-16 | **Aucun identifiant séquentiel** exposé : ULID uniquement (anti-énumération), et les identifiants d'objet d'une autre organisation renvoient `404`, jamais `403` (pas d'oracle d'existence) | T-SEC-020 |

### 3.3 Validation, intégrité, robustesse

| ID | Règle | Vérification |
|---|---|---|
| API-17 | Validation **stricte** de l'entrée : schémas Zod/JSON Schema, `additionalProperties: false`, tailles maximales (corps ≤ 1 Mo, 100 éléments par tableau, 1 000 caractères par texte libre), refus des doublons de clé JSON, refus des types implicites | tests de robustesse (fuzzing) |
| API-18 | **Idempotence obligatoire** sur tout `POST`/`PATCH`/`DELETE` mutant via `Idempotency-Key` (UUID v4), conservation 24 h, réponse rejouée à l'identique avec `Idempotency-Replayed: true` ; réutilisation d'une clé avec un corps différent → `409 IDEM_409_KEY_REUSE` | T-API-030 |
| API-19 | **Concurrence optimiste** : `ETag` en réponse, `If-Match` obligatoire sur `PATCH`, `412` sinon — protège des écrasements silencieux sur une série partagée entre deux praticiens | T-API-031 |
| API-20 | **Limitation de débit** à trois niveaux (organisation, utilisateur, IP) : 600 req/min par organisation, 60/min par utilisateur en écriture, 10/min par IP sur les routes publiques ; en-têtes `RateLimit-*` ; réponse `429` avec `Retry-After` ; pas de blocage silencieux | T-SEC-030 |
| API-21 | **Anti-rejeu** : horodatage signé sur les webhooks (fenêtre 5 min), `jti` unique sur les jetons, refus des requêtes hors fenêtre sur les endpoints d'écriture sensibles | test de rejeu |
| API-22 | **Pagination obligatoire** sur toute collection (`limit` ≤ 100, curseur opaque), pas d'endpoint « tout renvoyer » ; les exports passent par `POST /exports` (asynchrone, signé, expirant en 15 min) | T-API-040 |
| API-23 | **Codes d'erreur stables** et documentés (catalogue doc 07 §8), enveloppe unique, `requestId` toujours présent, messages localisés (`Accept-Language`) mais code invariant ; aucune trace de pile, aucun nom de table, aucune requête SQL dans la réponse | revue + test |
| API-24 | **Dégradation explicite** : un service indisponible renvoie `503` avec `Retry-After` et un code dédié, jamais une donnée partielle silencieuse (cohérent avec R-14 du doc 06) | test de chaos (doc 09) |

### 3.4 Cycle de vie du contrat

| ID | Règle | Vérification |
|---|---|---|
| API-25 | **OpenAPI 3.1 est la source de vérité** ; le contrat est généré depuis les schémas Zod de `packages/contracts` et publié à chaque fusion (fichier `api/openapi.yaml`, versionné, diffusé sur `https://api.myrdv.app/v1/openapi.json`) | CI : contrat généré = contrat versionné |
| API-26 | **Versionnage** : `/v1` dans le chemin ; une évolution compatible (champ additif optionnel, nouvel endpoint, nouvel enum **avec** consigne de tolérance) ne change pas la version ; une rupture ouvre `/v2` avec **12 mois de support simultané** et un guide de migration | revue de contrat (règle de compatibilité) |
| API-27 | **Dépréciation** : en-têtes `Deprecation` (RFC 9745) et `Sunset` (RFC 8594), période minimale **6 mois**, journal des appels aux routes dépréciées par consommateur, courriel au propriétaire de la clé d'API | test de cycle de vie |
| API-28 | **Tolérance des clients** documentée : un client doit ignorer les champs inconnus en réponse et ne pas dépendre de l'ordre des clés ; l'API n'envoie jamais de champ retiré sans période de transition | guide d'intégration |
| API-29 | **Contrat testé** : tests de conformité (le contrat est-il respecté par l'implémentation ?) et tests de rupture (un client de référence écrit contre `/v1` continue de fonctionner) | T-API-050 |

---

## 4. Droits des personnes, exercés par l'API

Le RGPD (art. 15 à 22), la Loi 25 (art. 27 à 32 : accès, rectification, retrait du consentement,
portabilité, désindexation) et le PIPEDA imposent des droits **opposables dans un délai**. MyRDV les
traite comme des fonctionnalités d'API de première classe, et non comme des demandes manuelles au
support.

| Droit | Endpoint | Délai cible (API) | Délai légal | Note de conformité |
|---|---|---|---|---|
| Accès (art. 15) | `GET /v1/clients/{id}/export` → `POST /v1/exports` | < 1 min (asynchrone) | 1 mois (prorogeable 2 mois motivés) | export **structuré, lisible, complet** : identité, consentements, rendez-vous, séries, factures, journal d'audit le concernant |
| Rectification (art. 16) | `PATCH /v1/clients/{id}` | immédiat | 1 mois | trace d'audit avant/après obligatoire |
| Effacement (art. 17) | `DELETE /v1/clients/{id}?mode=erase` | < 24 h | 1 mois | suppression C3, **pseudonymisation** C2 (factures, 10 ans) ; le refus partiel est expliqué dans la réponse (`209 Partial content` sémantique documentée) |
| Limitation (art. 18) | `PATCH /v1/clients/{id} { "processingRestricted": true }` | immédiat | 1 mois | l'API refuse ensuite toute création de rendez-vous pour ce client (`CMP_423_RESTRICTED`) |
| Portabilité (art. 20) | `POST /v1/exports { "format": "json"\|"csv" }` | < 5 min | 1 mois | format **JSON Schema documenté** + CSV UTF-8 BOM, archive `.zip` signée, lien expirant 15 min |
| Opposition (art. 21) | `PATCH /v1/clients/{id}/consents` | immédiat | 1 mois | opposition marketing et rappels non essentiels appliquée en < 60 s à tous les canaux |
| Retrait du consentement (art. 7.3) | idem | immédiat | — | historisation des consentements (preuve, horodatage, version du texte) |
| Décision automatisée (art. 22) | — | — | — | **aucune** décision entièrement automatisée à effet juridique en V1 ; le score de priorité de la liste d'attente (F-WAIT-03) est une aide, toujours modifiable par un humain |
| Désindexation (Loi 25, art. 28.1) | `POST /v1/privacy/deindexation` | < 72 h | 10 jours | l'annuaire public retire la fiche et propage aux moteurs |

**API-30** — Tout endpoint de droits est **traçable** : l'entrée d'audit enregistre l'auteur, la base
légale invoquée, le périmètre et l'horodatage, et ce journal est conservé 10 ans (doc 04 §7).

**API-31** — Une demande de droit exercée sur un client rattaché à plusieurs organisations déclenche
un traitement par organisation, avec un état par organisation dans la réponse : l'API ne peut pas
« effacer à moitié » sans le dire.

**API-32** — Le **sous-traitant** qu'est MyRDV notifie le responsable de traitement (le professionnel)
via le webhook `privacy.request.received` **et** par courriel, dans les 24 h ; le professionnel
dispose d'un délai de 10 jours pour contester une demande d'effacement qui heurterait une obligation
de conservation (dossier médical). Passé ce délai, l'effacement s'applique.

---

## 5. Journalisation, preuve et auditabilité

**API-33** — **Aucune donnée personnelle dans les journaux techniques.** Un journal d'accès contient :
horodatage, `requestId`, `organizationId` (ULID), `actorId` (ULID), route **normalisée**
(`PATCH /v1/series/{id}`), statut HTTP, durée, code d'erreur, empreinte de la clé d'API. Les
paramètres de requête sont journalisés **nommés mais tronqués et hachés** (`q=<hash>`).

**API-34** — **Journal d'audit métier** distinct, append-only, chaîné par hachage, conservé 10 ans :
création/modification/suppression d'une série, portée et `diff`, accès à une note clinique, export,
changement de permission, accès support (doc 04 §7). Exposé en lecture par `GET /v1/audit` aux rôles
`OWNER`/`ADMIN`, jamais modifiable ni supprimable par l'API.

**API-35** — **Corrélation de bout en bout** : `X-Request-Id` accepté du client (format ULID validé,
sinon généré), propagé dans les traces OpenTelemetry et dans les webhooks (`X-Correlation-Id`),
restitué dans l'enveloppe d'erreur — condition d'un diagnostic support sans accès aux données.

**API-36** — **Mesures de sécurité** exposées aux clients entreprise : tableau de bord de sécurité par
organisation (échecs d'authentification, appels refusés, dépassements de débit, webhooks en échec) et
flux `audit.security.*` pour leur SIEM.

---

## 6. Webhooks et sous-traitance technique

**API-37** — Signature **HMAC-SHA256** obligatoire (`X-MyRDV-Signature: t=<timestamp>,v1=<hmac>` sur
`t + "." + corps brut`), fenêtre de tolérance 5 min, secret par endpoint, rotation semestrielle
assistée (double secret pendant 7 jours). Un endpoint sans TLS valide est refusé ; les adresses
privées et les métadonnées de cloud sont bloquées (**anti-SSRF**).

**API-38** — **Minimisation** : un webhook ne transporte que ce qui est nécessaire à l'action du
destinataire (`seriesId`, `key`, statut, montant), jamais de donnée C3/C4. Le destinataire récupère le
détail par un appel authentifié.

**API-39** — **Idempotence et rejeu** : `X-MyRDV-Event-Id` stable, déduplication côté récepteur
documentée, 3 tentatives exponentielles (1 min, 5 min, 30 min), puis file morte consultable et
rejouable depuis `GET /v1/webhooks/{id}/deliveries`.

**API-40** — **Sous-traitants ultérieurs** : l'API n'appelle aucun sous-traitant non inscrit au
registre du doc 04 §6.2. Tout nouveau prestataire exige une DPIA/EFVP, un DPA signé, une évaluation
de localisation (UE par défaut, Canada pour la Loi 25, US seulement sur option HIPAA) et une mise à
jour de la page publique des sous-traitants — **avant** la mise en service.

**API-41** — **Transferts hors UE** : un endpoint dont le traitement sort de l'UE renvoie dans sa
documentation la base du transfert (décision d'adéquation ou clauses contractuelles types + analyse
d'impact), et l'organisation peut choisir une **résidence de données** (UE, Canada) qui contraint le
routage.

---

## 7. Sécurité applicative : application d'OWASP API Top 10 (2023)

| Risque OWASP API | Traitement MyRDV | Règle |
|---|---|---|
| API1 — Broken object level authorization | `organization_id` dérivé du jeton, vérification de propriété par ressource, `404` au lieu de `403`, tests d'accès croisé sur 62 endpoints | API-07, API-08, API-16 |
| API2 — Broken authentication | PKCE, JWT court, refresh rotatif, MFA admin, verrouillage progressif, détection de bourrage d'identifiants | API-03 à API-10 |
| API3 — Broken object property level authorization | `additionalProperties: false`, sérialisation par liste blanche de champs par rôle, pas de champ C4 dans le contrat public | API-01, API-17 |
| API4 — Unrestricted resource consumption | plafonds métier (R-03/04/05/15 du doc 06), débit à trois niveaux, taille de corps, pagination obligatoire, exports asynchrones | API-20, API-22 |
| API5 — Broken function level authorization | permissions par rôle × scope, refus par défaut, revue trimestrielle de la matrice | API-06, API-07 |
| API6 — Unrestricted access to sensitive business flows | `/series/preview` limité, `confirmCount` obligatoire au-delà de 50 occurrences, anti-automatisation sur la réservation publique | API-20, doc 07 §7 |
| API7 — SSRF | webhooks : résolution DNS contrôlée, blocage des plages privées/link-local, redirections interdites | API-37 |
| API8 — Security misconfiguration | en-têtes par défaut, TLS 1.3, CORS en liste blanche, erreurs sans fuite, images distroless, secrets via KMS | API-12 à API-15 |
| API9 — Improper inventory management | inventaire d'API généré depuis OpenAPI, aucune route hors contrat (test de parité), environnements étiquetés | API-25, API-29 |
| API10 — Unsafe consumption of third-party APIs | validation des réponses Stripe/SMS/visio, délais et disjoncteurs, aucune donnée tierce non validée écrite en base | API-24, API-40 |

**Score ASVS visé** : niveau 2 complet sur les chapitres V2 (authentification), V3 (session), V4
(contrôle d'accès), V5 (validation), V7 (gestion des erreurs et journalisation), V9 (communication),
V12 (fichiers), V13 (API), V14 (configuration). Preuve : revue externe avant mise en production, puis
annuelle.

---

## 8. Cadre de conformité : ce que chaque référentiel exige de l'API

| Référentiel | Exigence clé | Traduction dans l'API |
|---|---|---|
| **RGPD** art. 5 | Minimisation, exactitude, limitation de conservation | aucun champ superflu au contrat ; purge applicative ; pas d'export « total » implicite |
| **RGPD** art. 25 | Privacy by design & by default | classification par champ, refus par défaut, `processingRestricted` respecté partout |
| **RGPD** art. 30 | Registre des activités de traitement | chaque endpoint appartient à un traitement du registre (doc 04 §6.1) ; le contrat le mentionne |
| **RGPD** art. 32 | Sécurité du traitement | TLS 1.3, chiffrement au repos, MFA, débit, audit, tests d'intrusion |
| **RGPD** art. 33-34 | Notification de violation sous 72 h | procédure + journal permettant d'identifier le périmètre exact des données exposées via `requestId` |
| **RGPD** art. 35 | DPIA avant traitement à risque | DPIA santé et DPIA annuaire géolocalisé ; toute nouvelle route C4 déclenche une DPIA |
| **ePrivacy** | Consentement pour traceurs et communications | aucun traceur côté API ; consentement vérifié avant envoi marketing (`CMP_403_NO_CONSENT`) |
| **Loi 25** | Transparence, EFVP, incident, désindexation | page publique des sous-traitants, EFVP par traitement, webhook `audit.security.*`, endpoint de désindexation |
| **PIPEDA** | Consentement éclairé, accès | consentements horodatés et versionnés, export accessible |
| **PHIPA / HIPAA** (option) | Garde des renseignements de santé, journal d'accès | journal d'accès C4, BAA/HINP signable, résidence canadienne |
| **ISO/IEC 27001:2022** A.8.20-A.8.23 | Sécurité des réseaux et des services web | en-têtes, TLS, filtrage, séparation des environnements, inventaire |
| **ISO/IEC 27701:2019** | Rôles responsable/sous-traitant, clauses | `DPA` signable en ligne, registre, sous-traitants ultérieurs (API-40) |
| **PCI-DSS v4.0** | Périmètre carte | aucune donnée de carte ne traverse l'API : Stripe Connect, périmètre **SAQ A** |
| **OWASP ASVS 4.0 L2** | Vérification de sécurité applicative | §7 + revue externe |
| **RFC 9457** (Problem Details) | Format d'erreur standard | enveloppe d'erreur alignée : `type`, `title`, `status`, `detail`, `instance` + extensions `code`, `requestId` |

---

## 9. Gouvernance et cycle de vie de la conformité

| Rituel | Fréquence | Propriétaire | Sortie |
|---|---|---|---|
| Revue de contrat d'API (nouvelle route, nouveau champ) | à chaque PR touchant `packages/contracts` | lead API + DPO | avis consigné dans la PR |
| Test d'accès croisé multi-tenant (62 endpoints) | à chaque fusion | QA | rapport T-SEC-020 |
| Revue de la matrice rôles × permissions | trimestrielle | RSSI | matrice versionnée |
| Test d'intrusion API externe | annuelle + avant toute nouvelle offre entreprise | RSSI | rapport + plan de remédiation |
| Exercice de violation de données (72 h) | semestrielle | DPO + RSSI | compte rendu horodaté |
| Revue des sous-traitants et transferts | annuelle | DPO | registre à jour, page publique actualisée |
| Purge et vérification de rétention | mensuelle | DPO | attestation automatisée (`GET /v1/privacy/retention-report`) |

---

## 10. Contrat exécutable et documentation GUI (Swagger)

Le contrat n'est pas un document mort : il est publié, validé et **navigable**.

| Artefact | Chemin | Rôle |
|---|---|---|
| Contrat OpenAPI 3.1 | [`api/openapi.yaml`](../api/openapi.yaml) | source de vérité du contrat `/v1` (séries, occurrences, droits des personnes, webhooks, erreurs) |
| Interface Swagger UI | [`api/index.html`](../api/index.html) | documentation GUI hors ligne (Swagger UI 5.34 embarqué), avec jeu de démonstration local |
| Serveur de démonstration | [`api/serve.py`](../api/serve.py) | sert le Swagger UI et un **mock** de l'API respectant les codes du contrat |
| Validation du contrat | [`api/tools/validate_contract.py`](../api/tools/validate_contract.py) | valide OpenAPI 3.1, vérifie l'absence de champ C4 et la présence des en-têtes de sécurité |
| README d'utilisation | [`api/README.md`](../api/README.md) | lancement, publication, conventions |

**API-42** — Le Swagger UI embarqué est **autonome** (aucun CDN) : la documentation reste consultable
en avion, en revue client ou dans un environnement sans accès Internet, et ne dépend d'aucun service
tiers (donc d'aucun transfert de données lors de la consultation).

**API-43** — Le Swagger UI est configuré avec `persistAuthorization: false` (aucun jeton conservé
entre deux visites), `withCredentials: false` (aucun cookie envoyé) et un serveur par défaut limité au
**mock local** ; l'essai d'un endpoint ne peut donc viser la production que par un choix explicite de
l'utilisateur, et jamais avec des identifiants réels, que la page ne demande pas.

---

## 11. Matrice de traçabilité

| Règle | Exigence source | Test / preuve |
|---|---|---|
| API-01, API-02 | NFR-CMP-06, T-SEC-012 | test automatisé sur le contrat + test de logs |
| API-03 à API-11 | doc 04 §4.1, T-SEC-002, T-SEC-040 | tests d'authentification et de matrice de rôles |
| API-12 à API-16 | doc 04 §4.2, ASVS V9/V14 | scan TLS + tests d'en-têtes + T-SEC-020 |
| API-17 à API-24 | doc 07 §1, doc 08 (robustesse) | fuzzing, T-API-030/031/040, chaos |
| API-25 à API-29 | doc 05 §11 (ADR-011) | CI de contrat |
| API-30 à API-32 | RGPD art. 15-22, Loi 25 art. 27-32, T-CMP-010/011 | tests de droits + journal d'audit |
| API-33 à API-36 | doc 04 §7, T-SEC-021 | test d'intégrité de la chaîne de hachage |
| API-37 à API-41 | doc 04 §6.2, OWASP API7 | test de signature, anti-SSRF, registre |
| API-42, API-43 | doc 04 §3.1 (transferts) | revue de la documentation publiée |

---

## 12. Contrôles automatisés ajoutés par ce document

| Contrôle | Commande | Bloquant en CI |
|---|---|---|
| Validité OpenAPI 3.1 + conformité des en-têtes + absence de champ C4 | `python3 api/tools/validate_contract.py` | oui |
| Parité implémentation ↔ contrat (aucune route hors contrat) | test d'intégration T-API-050 | oui |
| Recherche de données personnelles dans les journaux (motifs e-mail, téléphone, nom) | test T-SEC-012 | oui |
| Vérification des en-têtes de sécurité sur 100 % des routes | `validate_contract.py --headers` | oui |
| Vérification de la présence de `Idempotency-Key` sur tous les mutants | `validate_contract.py --idempotency` | oui |

---

*Suite : annexes et artefacts exécutables — voir le [sommaire du dossier](../README.md).*

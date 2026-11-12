# 02 — Personas, parcours et matrice de droits

**Document** : 02 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Objectif** : ancrer les exigences dans des usages réels et fixer le modèle d'habilitation.

---

## 1. Personas

### P1 — Camille, ostéopathe indépendante (persona primaire)

- **Profil** : 34 ans, Lyon, exercice solo en cabinet partagé, 2 salles mutualisées, ~28 rendez-vous/semaine.
- **Outils actuels** : agenda Google + carnet papier + Stripe à la main + SMS manuels.
- **Objectifs (JTBD)** : « Quand un patient doit revenir toutes les semaines pendant 3 mois, je veux
  poser la série en une fois, sans avoir à vérifier chaque lundi si le créneau est libre. »
- **Frustrations** : reprogrammations en cascade, trous dans l'agenda, patients qui oublient, temps
  administratif le soir.
- **Critères de succès** : poser une série de 12 séances en < 1 minute ; aucun doublon ; un seul écran
  pour la journée.
- **Sensibilité** : UX irréprochable sur mobile ; prix < 40 €/mois ; conformité RGPD rassurante.

### P2 — Dr Nabil, psychiatre, suivi long (persona récurrence intensive)

- **Profil** : 47 ans, Paris, 40 patients suivis, séances de 45 min toutes les 2 semaines ou 3 semaines.
- **Contraintes** : secret médical, données de santé, notes SOAP, ordonnances, téléconsultation.
- **Objectifs** : « Je veux poser le cadre du suivi : toutes les 2 semaines pendant 6 mois, puis
  réévaluer ; et pouvoir décaler une séance sans casser la série. »
- **Besoins spécifiques** : exceptions ponctuelles (absence du patient, congé du praticien), historique
  de série, traçabilité des modifications, effacement sélectif sur demande du patient.
- **Sensibilité** : sécurité >> prix ; hébergement UE ; DPA signable.

### P3 — Sofia, gérante d'un centre de bien-être (persona équipe)

- **Profil** : 39 ans, 6 praticiens (massage, esthétique, réflexologie), 2 sites, 9 salles.
- **Objectifs** : remplir les plannings, éviter les conflits de salle, piloter le taux d'occupation,
  fidéliser (forfaits 5 séances).
- **Besoins** : rôles (réception vs praticien), agenda d'équipe, ressources, forfaits/abonnements,
  reporting, cartes-cadeaux.
- **Sensibilité** : prix par praticien, marge sur les paiements, simplicité pour l'accueil.

### P4 — Thomas, client final (persona demandeur)

- **Profil** : 29 ans, réserve depuis son téléphone, entre deux rendez-vous.
- **Objectifs** : « Je veux voir les créneaux libres, réserver en 3 taps, recevoir un rappel, annuler
  sans appeler. »
- **Frustrations** : formulaires longs, création de compte imposée, appels en journée.
- **Sensibilité** : rapidité, aucune friction, transparence sur l'annulation.

### P5 — Léa, coordinatrice de clinique (persona opérationnel)

- **Profil** : 31 ans, gère les agendas de 12 praticiens, 1 800 rendez-vous/mois.
- **Objectifs** : zéro conflit, gérer les urgences, absorber les annulations, répondre au téléphone
  en ayant la bonne information.
- **Besoins** : vue d'équipe, recherche client, télésecrétariat, masquage des noms en accueil,
  journal d'audit, exports.
- **Sensibilité** : fiabilité et rapidité de l'interface (> 2 s = friction).

## 2. Cartographie des parcours

### 2.1 Parcours « créer une série de rendez-vous » (cœur du différenciateur)

| Étape | Acteur | Écran / action | Exigence | Durée cible |
|---|---|---|---|---|
| 1 | Camille | Agenda → « Nouveau rendez-vous » → onglet **Récurrent** | F-REC-01 | 2 s |
| 2 | Camille | Choisit le client, le service, le lieu, la salle | F-REC-02, F-RES-03 | 10 s |
| 3 | Camille | Sélectionne les jours : lundi et jeudi | R-01 | 3 s |
| 4 | Camille | Fréquence : toutes les semaines (intervalle 1) | R-02 | 2 s |
| 5 | Camille | Fin : « Pendant 3 mois » → date de fin calculée 2027-02-16 | R-05 | 3 s |
| 6 | MyRDV | Aperçu : « 14 séances — du 16/11/2026 au 15/02/2027 », conflits signalés | R-14, F-REC-06 | 1 s |
| 7 | Camille | Ajuste : « Jours fériés : décaler au lendemain » | R-07 | 5 s |
| 8 | MyRDV | Contrôle de disponibilité, ressources, plafonds | R-09, R-10 | < 400 ms |
| 9 | Camille | Valide → série créée, occurrences matérialisées à 90 jours | R-11, R-16 | 1 s |
| 10 | Thomas | Reçoit une invitation par séance + un récapitulatif de série | F-NOT-10 | — |
| **Total** | | | | **< 45 s** |

### 2.2 Parcours « décaler une occurrence sans casser la série »

1. Camille ouvre la série → liste des occurrences.
2. Elle sélectionne le 7 décembre → « Déplacer cette occurrence ».
3. MyRDV propose les créneaux libres le même jour ± 4 h, puis les jours voisins.
4. Elle valide : la 7e occurrence est détachée (`is_detached = true`), la règle de série est intacte.
5. Le client reçoit une notification de modification ; le journal d'audit enregistre l'action.
6. Exigences : F-REC-12, R-13, F-APT-02, NFR-SEC-04.

### 2.3 Parcours « annulation et remplissage » (liste d'attente)

1. Thomas annule à J-1 (dans le délai autorisé) → créneau libéré.
2. MyRDV interroge la liste d'attente du service : critères (praticien, créneau préféré, urgence,
   ancienneté d'inscription).
3. Il envoie une offre à 3 candidats simultanément avec une fenêtre de 20 minutes (« premier qui
   confirme »).
4. Le premier confirmé obtient le créneau ; les autres reçoivent un message de non-attribution.
5. Exigences : F-WAIT-02, F-WAIT-03, R-22 (une série ne doit pas capturer un créneau libéré).

### 2.4 Parcours « patient récurrents et forfaits »

1. Sofia vend un forfait « 5 massages » (débit progressif).
2. Le client réserve 5 rendez-vous, éventuellement via une série récurrente.
3. Chaque séance consomme une unité ; à zéro, la réservation en ligne est bloquée avec un message clair.
4. Exigences : F-BIL-04, F-BIL-09.

## 3. User stories principales (extrait)

| ID | En tant que | Je veux | Afin de | Exigences |
|---|---|---|---|---|
| US-01 | pratiquen | poser une série hebdomadaire bornée à 3 mois | sécuriser mon planning sans y revenir | F-REC-01..06 |
| US-02 | praticien | choisir la conduite en cas de conflit | ne jamais créer de doublon | F-REC-09 |
| US-03 | praticien | exclure les jours fériés avec décalage | respecter les jours de fermeture | F-REC-07 |
| US-04 | praticien | déplacer une seule séance | préserver la série | F-REC-12 |
| US-05 | coordinatrice | voir l'agenda de 12 praticiens | répondre au téléphone vite | F-AGD-03 |
| US-06 | client | réserver sans mot de passe | gagner du temps | F-BKG-06 |
| US-07 | client | annuler en ligne dans le délai | éviter l'appel | F-APT-03 |
| US-08 | praticien | recevoir un récapitulatif de série | éviter les no-shows sur séries | F-NOT-10 |
| US-09 | gérante | réserver une salle | éviter le conflit physique | F-RES-03 |
| US-10 | praticien | tracer qui a modifié une série | répondre à un litige | NFR-SEC-04 |

## 4. Non-utilisateurs et exclusions

- Patients mineurs sans représentant légal (contrainte de consentement — traité par le formulaire
  d'admission, pas par un compte dédié).
- Structures hospitalières à parcours de soins intégrés (pas de gestion de lits ni de dossier
  hospitalier) : hors périmètre.
- Marchés sans connectivité stable : le mode hors-ligne est limité à la consultation (PWA), pas à
  l'écriture.

## 5. Modèle de rôles

| Rôle | Portée | Peut faire | Ne peut pas |
|---|---|---|---|
| `OWNER` | Organisation | Tout, facturation, suppression de compte | — |
| `ADMIN` | Organisation | Gérer praticiens, services, plafonds, exports | Supprimer l'organisation, changer le moyen de paiement |
| `PRACTITIONER` | Ses agendas | Gérer ses rendez-vous, séries, notes, disponibilités | Voir les notes des autres praticiens, gérer la facturation de l'organisation |
| `ASSISTANT` | Agendas délégués | Créer/déplacer/annuler, encaisser | Accéder aux notes cliniques, supprimer une série |
| `RECEPTION` | Agendas délégués | Créer/déplacer/annuler, voir les coordonnées | Voir les notes, les diagnostics, les montants détaillés si masqués |
| `ACCOUNTANT` | Organisation | Voir factures et rapports financiers | Voir les données de santé |
| `CLIENT` | Son dossier | Réserver, annuler, voir ses documents | Voir d'autres clients |

**Principe** : moindre privilège, séparation des données de santé et des données financières,
`ASSISTANT` et `RECEPTION` n'accèdent **jamais** aux notes cliniques (exigence NFR-SEC-06).

## 6. Permissions atomiques

64 permissions de la forme `<domaine>:<action>` : `appointment:read|write|delete`,
`series:read|write|delete|regenerate`, `client:read|write|delete`, `note:read|write`,
`invoice:read|write|refund`, `resource:read|write`, `report:read`, `audit:read`, `setting:write`,
etc. Les rôles sont des **ensembles de permissions** stockés en base (`role_permission`), jamais des
conditions codées en dur, afin de permettre des rôles personnalisés en V1.1 (F-ORG-02).

| Domaine | Permissions | OWNER | ADMIN | PRACTITIONER | ASSISTANT | RECEPTION | ACCOUNTANT |
|---|---|---|---|---|---|---|---|
| appointment | read/write/delete | ✓✓✓ | ✓✓✓ | ✓✓✓ (ses agendas) | ✓✓– | ✓✓– | ––– |
| series | read/write/delete/regenerate | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓✓ | ✓✓–– | ✓✓–– | –––– |
| client | read/write/delete | ✓✓✓ | ✓✓✓ | ✓✓– | ✓✓– | ✓✓– | ––– |
| note | read/write | ✓✓ | ✓✓ | ✓✓ (ses clients) | –– | –– | –– |
| invoice | read/write/refund | ✓✓✓ | ✓✓✓ | ✓✓– | ✓✓– | ✓✓– | ✓–– |
| resource | read/write | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓– | –– |
| report | read | ✓ | ✓ | ✓ (soi) | – | – | ✓ |
| audit | read | ✓ | ✓ | – | – | – | – |
| setting | write | ✓ | ✓ | – | – | – | – |

## 7. Accessibilité et inclusion

- Objectif **WCAG 2.1 niveau AA** (RGAA 4.1 pour la France) sur les parcours critiques : réservation,
  agenda, création de série, annulation.
- Contraste minimum 4,5:1, navigation clavier complète, libellés explicites, pas d'information portée
  par la couleur seule (les statuts de rendez-vous sont doublés d'un libellé).
- Interface disponible en français et anglais en V1 ; espagnol et allemand en V2 (F-I18N-01).
- Lecture d'écran testée sur les trois parcours critiques avec NVDA et VoiceOver (doc 09, T-A11Y).

---

*Suite : [`03-exigences-fonctionnelles.md`](03-exigences-fonctionnelles.md).*

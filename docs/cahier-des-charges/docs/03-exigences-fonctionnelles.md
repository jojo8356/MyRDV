# 03 — Exigences fonctionnelles

**Document** : 03 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Périmètre** : 195 exigences, 27 domaines · **Priorités** : MUST / SHOULD / COULD / WON'T
**Convention** : identifiant stable `F-<domaine>-<n>`, jamais renuméroté après publication.

> **Décompte de référence** : 195 exigences — 120 MUST, 54 SHOULD, 20 COULD, 1 WON'T — réparties
> en 27 domaines (§1). Les contraintes transverses de sécurité, de performance et de qualité sont
> portées par les documents 04 et 08 (exigences `NFR-*`).

> Les exigences du module de rendez-vous récurrents (`F-REC-*`) sont détaillées dans le
> [document 06](06-moteur-rdv-recurrents.md) : ici ne figurent que leurs énoncés et critères
> d'acceptation de haut niveau.

---

## 1. Domaines

| Code | Domaine | Nb exigences | MUST |
|---|---|---|---|
| BKG | Réservation en ligne | 12 | 9 |
| APT | Rendez-vous | 14 | 10 |
| REC | Rendez-vous récurrents | 20 | 18 |
| AGD | Agenda | 8 | 5 |
| AVL | Disponibilités | 8 | 6 |
| RES | Ressources (lieux, salles, équipements) | 6 | 3 |
| CLI | Clients | 12 | 8 |
| FRM | Formulaires d'admission | 5 | 3 |
| MED | Dossier patient / notes | 9 | 5 |
| PRT | Portail client | 6 | 5 |
| NOT | Notifications | 10 | 7 |
| BIL | Paiements et facturation | 13 | 6 |
| SVC | Services et tarifs | 7 | 4 |
| CLS | Cours et groupes | 5 | 0 |
| WAIT | Liste d'attente | 5 | 3 |
| REQ | Demandes de service | 4 | 0 |
| DIR | Annuaire | 4 | 0 |
| ORG | Organisation, équipe, droits | 8 | 7 |
| SYN | Synchronisation calendrier | 5 | 2 |
| TZ | Fuseaux horaires / DST | 4 | 4 |
| TEL | Téléconsultation | 3 | 1 |
| AI | Assistants IA | 3 | 2 |
| DOC | Documents et signature | 5 | 3 |
| FDB | Avis et satisfaction | 3 | 0 |
| ANL | Analyse et reporting | 7 | 4 |
| INT | Intégrations et API | 6 | 3 |
| ONB | Onboarding | 3 | 2 |
| **Total** | **27 domaines** | **195** | **120** |

*Les 14 domaines « cœur » du document 01 sont inclus dans ces 28 domaines de spécification ; les
autres domaines sont transverses.*

---

## 2. Réservation en ligne (BKG)

| ID | Exigence | Prio |
|---|---|---|
| F-BKG-01 | Le client réserve en ligne 24/7 depuis une URL publique, sans installation. | MUST |
| F-BKG-02 | L'organisation personnalise logo, couleurs, textes et sous-domaine de sa page de réservation. | MUST |
| F-BKG-03 | Des URLs par praticien, par service et par lieu sont générables et partageables. | MUST |
| F-BKG-04 | Le parcours de réservation filtre successivement lieu → service → praticien → créneau. | MUST |
| F-BKG-05 | Tarifs, durées et modalités d'annulation sont affichés avant la confirmation. | MUST |
| F-BKG-06 | La réservation ne requiert pas la création d'un compte ; un e-mail vérifié suffit (lien magique + OTP). | MUST |
| F-BKG-07 | L'organisation choisit entre confirmation immédiate et approbation manuelle par praticien. | MUST |
| F-BKG-08 | Le praticien peut réserver certains créneaux aux clients existants uniquement. | MUST |
| F-BKG-09 | Un rendez-vous peut concerner deux clients (thérapie de couple, duo). | SHOULD |
| F-BKG-10 | Un widget intégrable (iframe/script) expose la réservation sur un site tiers. | SHOULD |
| F-BKG-11 | La réservation est accessible sans JavaScript pour les parcours de lecture (dégradation gracieuse). | SHOULD |
| F-BKG-12 | Un CAPTCHA invisible protège les formulaires publics du spam, sans friction pour l'utilisateur. | MUST |

**Critère d'acceptation (F-BKG-06)** — *Étant donné* un client non authentifié, *quand* il confirme
un rendez-vous avec un e-mail inconnu, *alors* une fiche client est créée à l'état `PENDING_VERIFICATION`,
le rendez-vous est retenu 15 minutes, et un e-mail de vérification est envoyé ; sans vérification
dans ce délai, le créneau est libéré et l'événement `appointment.hold_expired` est publié.

## 3. Rendez-vous (APT)

| ID | Exigence | Prio |
|---|---|---|
| F-APT-01 | Création manuelle d'un rendez-vous depuis l'agenda (praticien, secrétariat). | MUST |
| F-APT-02 | Reprogrammation par le praticien, l'assistant ou le client (selon politique). | MUST |
| F-APT-03 | Politique d'annulation configurable : délai limite, canal autorisé, penalité éventuelle. | MUST |
| F-APT-04 | États du rendez-vous : `HELD`, `SCHEDULED`, `CONFIRMED`, `ARRIVED`, `COMPLETED`, `NO_SHOW`, `CANCELLED_BY_CLIENT`, `CANCELLED_BY_PROVIDER`, `RESCHEDULED`, `REJECTED`. | MUST |
| F-APT-05 | Notes libres sur le rendez-vous (non cliniques), visibles selon rôle. | SHOULD |
| F-APT-06 | Détection de conflit **bloquante** : aucune ressource (praticien, salle, équipement, client) ne peut être doublement réservée. | MUST |
| F-APT-07 | Tampon avant/après par service (nettoyage, préparation, compte rendu). | MUST |
| F-APT-08 | Un rendez-vous peut être marqué « arrivé », « terminé », « manqué » en un tap. | MUST |
| F-APT-09 | Envoi de l'invitation calendrier (.ics) aux participants internes et externes. | MUST |
| F-APT-10 | Rendez-vous sans client (bloc opératoire, réunion, temps administratif). | SHOULD |
| F-APT-11 | Modification en masse d'une journée (retard, fermeture exceptionnelle). | SHOULD |
| F-APT-12 | Historique des modifications d'un rendez-vous, avec auteur et horodatage. | MUST |
| F-APT-13 | Vérification des chevauchements **transactionnelle** (verrou pessimiste par praticien-jour). | MUST |
| F-APT-14 | Fusion des rendez-vous consécutifs d'un même client de moins de 5 minutes d'écart dans la facturation. | COULD |

**Critère d'acceptation (F-APT-06)** — *Étant donné* deux requêtes concurrentes visant le créneau
`2026-11-16 09:00–10:00` du praticien P et de la salle S, *quand* elles sont émises à moins de 50 ms
d'intervalle, *alors* exactement une réussit et l'autre reçoit `409 SER_017_SLOT_CONFLICT`, sans état
partiel (vérifié par test de concurrence, doc 09 T-APT-031).

## 4. Rendez-vous récurrents (REC)

> **Voir le document 06 pour les 24 règles normatives (R-01 → R-24) et le document 07 pour l'API.**

| ID | Exigence | Prio |
|---|---|---|
| F-REC-01 | Créer une série à partir d'un rendez-vous, avec jours de la semaine multiples (1 à 5 jours). | MUST |
| F-REC-02 | Fréquence exprimée en intervalle de semaines (1 à 8) : toutes les semaines, toutes les 2 semaines, etc. | MUST |
| F-REC-03 | Quatre modes de fin : nombre d'occurrences, date de fin, durée (mois/semaines), sans fin bornée. | MUST |
| F-REC-04 | Limite de répétition explicite par l'utilisateur (« sur 3 mois, 1 fois par semaine ») et prévisualisation du nombre exact de séances. | MUST |
| F-REC-05 | Prévisualisation avant validation : liste datée, comptage, alertes de conflit et de fermeture. | MUST |
| F-REC-06 | Politique de conflit sélectionnable : `FAIL` (tout ou rien), `SKIP` (conflit ignoré et signalé), `SHIFT_SAME_DAY` (±4 h). | MUST |
| F-REC-07 | Jours fériés et congés exclus, avec décalage automatique au jour ouvré suivant (ou suppression). | MUST |
| F-REC-08 | Exceptions par occurrence : RDate (ajout) et ExDate (suppression), sans rompre la série. | MUST |
| F-REC-09 | Détachement d'une occurrence (modification isolée) sans altérer la règle. | MUST |
| F-REC-10 | Bornes de sécurité par offre : 104 occurrences max, horizon 12 mois max, 8 semaines d'intervalle max. | MUST |
| F-REC-11 | Anti-abus : refus si heure passée, délai minimum de 2 h, budget de conflits dépassé. | MUST |
| F-REC-12 | Notification spécifique : récapitulatif de série + rappels par occurrence. | MUST |
| F-REC-13 | Modifier « cette occurrence / suivantes / toute la série ». | MUST |
| F-REC-14 | Supprimer « cette occurrence / les suivantes / toute la série », avec confirmation chiffrée. | MUST |
| F-REC-15 | Idempotence : rejouer une génération n'entraîne ni doublon ni perte. | MUST |
| F-REC-16 | La série expose son état (`ACTIVE`, `ENDED`, `CANCELLED`, `EXHAUSTED`) et sa progression (`3/14`). | MUST |
| F-REC-17 | Aucune occurrence silencieusement perdue : les occurrences non placées sont listées avec motif. | MUST |
| F-REC-18 | Fuseau horaire attaché à la série ; heure murale conservée à travers les changements d'heure. | MUST |
| F-REC-19 | Export d'une série (ICS, CSV) et import d'un ICS récurrent. | SHOULD |
| F-REC-20 | Les séries sont visibles et pilotables depuis l'agenda (icône, filtre, liste dédiée). | SHOULD |

**Critère d'acceptation (F-REC-04)** — *Étant donné* un début le lundi 16/11/2026 à 09:00, une seule
séance par semaine, *quand* l'utilisateur choisit « pendant 3 mois », *alors* l'aperçu affiche
« 14 séances — du 16/11/2026 au 15/02/2027 » et la série créée contient exactement 14 occurrences
jusqu'au 2027-02-15 inclus (date de fin calculée 2027-02-16, incluse ; cf. R-05).

**Critère d'acceptation (F-REC-17)** — *Étant donné* une série de 12 séances dont 2 tombent un jour de
fermeture, *quand* la politique est `SKIP`, *alors* la réponse expose `count: 10`,
`skipped: [{date, reason: BLACKOUT}]` et l'interface affiche un bandeau « 2 séances non planifiées —
voir détail ».

## 5. Agenda (AGD)

| ID | Exigence | Prio |
|---|---|---|
| F-AGD-01 | Vues jour, semaine, mois, liste ; navigation clavier. | MUST |
| F-AGD-02 | Glisser-déposer pour déplacer et redimensionner (avec recalcul de facturation). | MUST |
| F-AGD-03 | Agenda d'équipe : superposition des praticiens avec filtres. | MUST |
| F-AGD-04 | Codes couleur par praticien, service ou statut. | SHOULD |
| F-AGD-05 | Interface responsive utilisable en mobile (cible 360 px de large). | MUST |
| F-AGD-06 | Vue « série » : toutes les séries actives et leur progression. | SHOULD |
| F-AGD-07 | Recherche instantanée de client ou de rendez-vous. | MUST |
| F-AGD-08 | Impression / export de la journée. | COULD |

## 6. Disponibilités (AVL)

| ID | Exigence | Prio |
|---|---|---|
| F-AVL-01 | Semaine type récurrente par praticien et par lieu (créneaux multiples). | MUST |
| F-AVL-02 | Plages exceptionnelles (ajout ou suppression ponctuelle). | MUST |
| F-AVL-03 | Congés et indisponibilités, avec impact sur les séries (voir R-07). | MUST |
| F-AVL-04 | Tampon configurable avant/après rendez-vous. | MUST |
| F-AVL-05 | Limite de rendez-vous par jour et par créneau (charge maximale). | MUST |
| F-AVL-06 | Délai minimum de réservation (2 h par défaut) et maximum (J+120 par défaut). | MUST |
| F-AVL-07 | Pause déjeuner bloquante et gestion des coupures. | SHOULD |
| F-AVL-08 | Copie des disponibilités d'un praticien à un autre. | COULD |

## 7. Ressources (RES)

| ID | Exigence | Prio |
|---|---|---|
| F-RES-01 | Salles réservables par site, avec capacité. | MUST |
| F-RES-02 | Équipements réservables (table de massage, appareil laser…). | SHOULD |
| F-RES-03 | Conflit de ressource bloquant, à la création manuelle comme à la réservation en ligne. | MUST |
| F-RES-04 | Tarification et durée imposée par ressource. | COULD |
| F-RES-05 | Vue « occupation des salles » par jour et par semaine. | SHOULD |
| F-RES-06 | Les séries récurrentes réservent la ressource à chaque occurrence, avec la même politique de conflit. | MUST |

## 8. Clients (CLI)

| ID | Exigence | Prio |
|---|---|---|
| F-CLI-01 | Fiche client : identité, coordonnées, préférences de contact, langue. | MUST |
| F-CLI-02 | Fusion de doublons de fiches avec conservation de l'historique. | MUST |
| F-CLI-03 | Historique des rendez-vous, paiements, documents, notes. | MUST |
| F-CLI-04 | Champs personnalisés par organisation. | SHOULD |
| F-CLI-05 | Consentements (communications, données de santé) horodatés et versionnés. | MUST |
| F-CLI-06 | Import de clients (CSV) avec déduplication et rapport d'erreurs. | MUST |
| F-CLI-07 | Export complet au format JSON/CSV (portabilité RGPD). | MUST |
| F-CLI-08 | Droit à l'effacement : anonymisation avec conservation des données comptables obligatoires. | MUST |
| F-CLI-09 | Blocage d'un client : il ne voit plus de disponibilités ; message personnalisable. | MUST |
| F-CLI-10 | Segment « clients inactifs » (dernier rendez-vous > X mois) avec relance. | SHOULD |
| F-CLI-11 | Rattachement d'un client à une organisation mutuelle/employeur (facultatif). | COULD |
| F-CLI-12 | Historique de la valeur vie client (LTV) et fréquence. | SHOULD |

## 9. Formulaires d'admission (FRM)

| ID | Exigence | Prio |
|---|---|---|
| F-FRM-01 | Constructeur de formulaires (champs texte, choix, date, fichier, consentement). | MUST |
| F-FRM-02 | Logique conditionnelle (afficher une question selon une réponse). | SHOULD |
| F-FRM-03 | Formulaires obligatoires avant le premier rendez-vous, avec blocage contrôlé. | MUST |
| F-FRM-04 | Génération PDF signée et archivée dans le dossier. | MUST |
| F-FRM-05 | Bibliothèque de modèles cliniques validés par défaut. | COULD |

## 10. Dossier patient et notes (MED)

| ID | Exigence | Prio |
|---|---|---|
| F-MED-01 | Notes structurées SOAP rattachées au rendez-vous et au client. | MUST |
| F-MED-02 | Versionnement des notes, immuabilité après signature (addendum). | MUST |
| F-MED-03 | Plan de traitement avec objectifs et progression. | SHOULD |
| F-MED-04 | Modèles de notes par praticien et par motif. | SHOULD |
| F-MED-05 | Recherche plein texte dans les notes (avec contrôle de rôle). | SHOULD |
| F-MED-06 | Export PDF du dossier pour un patient identifié. | MUST |
| F-MED-07 | Masquage par défaut de l'accueil (initiales seulement). | MUST |
| F-MED-08 | Assistance IA de rédaction, opt-in explicite, cloisonnée, sans entraînement. | COULD |
| F-MED-09 | Suppression d'une note avec journalisation et période de rétention définie. | MUST |

## 11. Portail client (PRT)

| ID | Exigence | Prio |
|---|---|---|
| F-PRT-01 | Accès sans mot de passe (lien magique/OTP), session courte. | MUST |
| F-PRT-02 | Consultation et annulation/reprogrammation des rendez-vous dans le délai autorisé. | MUST |
| F-PRT-03 | Téléchargement des reçus, factures et documents. | MUST |
| F-PRT-04 | Remplissage des formulaires d'admission. | MUST |
| F-PRT-05 | Téléversement de documents (avec antivirus). | SHOULD |
| F-PRT-06 | Gestion des préférences de notification et des consentements. | MUST |

## 12. Notifications (NOT)

| ID | Exigence | Prio |
|---|---|---|
| F-NOT-01 | Confirmation immédiate à la réservation (courriel et/ou SMS). | MUST |
| F-NOT-02 | Rappels paramétrables (délais multiples : J-7, J-2, H-3). | MUST |
| F-NOT-03 | Confirmation de présence en un clic depuis le message, visible dans l'agenda. | MUST |
| F-NOT-04 | Langue du message alignée sur la préférence du client (FR/EN). | MUST |
| F-NOT-05 | Communications groupées avec segmentation. | SHOULD |
| F-NOT-06 | Modèles avec variables, prévisualisation et test. | MUST |
| F-NOT-07 | Notifications internes (nouveau rendez-vous, annulation, conflit de série). | MUST |
| F-NOT-08 | Relance des no-shows selon une cadence configurable. | SHOULD |
| F-NOT-09 | Demande d'avis post-prestation avec lien public. | SHOULD |
| F-NOT-10 | Récapitulatif de série récurrente (liste des dates) à la création et modification. | MUST |

**Contrainte de conformité forte** : les messages SMS et les notifications push **ne contiennent jamais
de donnée de santé** (pas de motif, pas de spécialité explicite, pas de nom de médicament). Le message
type est neutre : « Rappel : rendez-vous le 16/11 à 09:00. Confirmer : {lien} » (NFR-CMP-06).

## 13. Paiements et facturation (BIL)

| ID | Exigence | Prio |
|---|---|---|
| F-BIL-01 | Paiement en ligne à la réservation et/ou acompte (Stripe Connect). | MUST |
| F-BIL-02 | Encaissement sur place (carte, espèces, virement) avec rapprochement. | MUST |
| F-BIL-03 | Factures et reçus conformes (mentions légales, numérotation séquentielle, TVA). | MUST |
| F-BIL-04 | Forfaits et abonnements (débit progressif, rechargement). | SHOULD |
| F-BIL-05 | Taxes configurables par pays et par service. | MUST |
| F-BIL-06 | Rapport de revenus par période, praticien, service, mode de paiement. | MUST |
| F-BIL-07 | Vente de produits (point de vente simple). | SHOULD |
| F-BIL-08 | Inventaire de produits avec seuil d'alerte. | COULD |
| F-BIL-09 | Cartes-cadeaux et avoirs. | SHOULD |
| F-BIL-10 | Programme de fidélité (points). | COULD |
| F-BIL-11 | Télétransmission des feuilles de soins (France) / assurance (Canada). | WON'T V1 |
| F-BIL-12 | Remboursements totaux ou partiels avec journalisation. | MUST |
| F-BIL-13 | Export comptable normalisé (CSV, FEC en France). | SHOULD |

## 14. Services et tarifs (SVC)

| ID | Exigence | Prio |
|---|---|---|
| F-SVC-01 | Service = durée, tarif, tampons, ressource requise, couleur, praticiens associés. | MUST |
| F-SVC-02 | Durées différentes par praticien pour un même service. | SHOULD |
| F-SVC-03 | Tarifs différenciés (nouveau client, enfant, mutuelle). | SHOULD |
| F-SVC-04 | Catégories et ordre d'affichage sur la page publique. | MUST |
| F-SVC-05 | Service « visio » avec génération de lien. | MUST |
| F-SVC-06 | Service « à domicile » avec zone de déplacement. | SHOULD |
| F-SVC-07 | Services archivables sans perte d'historique. | MUST |

## 15. Cours et groupes (CLS)

| ID | Exigence | Prio |
|---|---|---|
| F-CLS-01 | Session collective avec capacité, liste de participants, tarif. | SHOULD |
| F-CLS-02 | Série de sessions (yoga, ateliers) avec inscription à la série entière. | SHOULD |
| F-CLS-03 | Gestion des présences et des places libérées. | SHOULD |
| F-CLS-04 | Liste d'attente par session. | COULD |
| F-CLS-05 | Abonnements de cours (crédits). | COULD |

## 16. Liste d'attente (WAIT)

| ID | Exigence | Prio |
|---|---|---|
| F-WAIT-01 | Inscription manuelle quand l'agenda est complet. | MUST |
| F-WAIT-02 | Remplissage automatique avec critères (service, praticien, plage, urgence, ancienneté). | MUST |
| F-WAIT-03 | Offre multi-candidats avec fenêtre de réponse (20 min par défaut) et attribution au premier confirmé. | SHOULD |
| F-WAIT-04 | Priorisation des urgences signalées. | SHOULD |
| F-WAIT-05 | Un créneau libéré par une annulation de série profite à la liste d'attente (R-22). | MUST |

## 17. Demandes de service (REQ)

| ID | Exigence | Prio |
|---|---|---|
| F-REQ-01 | Formulaire public de demande avec motif, disponibilités, coordonnées. | SHOULD |
| F-REQ-02 | Routage vers le praticien compétent. | SHOULD |
| F-REQ-03 | Marquage « urgent » et file dédiée. | SHOULD |
| F-REQ-04 | Conversion d'une demande en rendez-vous en un clic. | SHOULD |

## 18. Annuaire (DIR)

| ID | Exigence | Prio |
|---|---|---|
| F-DIR-01 | Page publique de recherche par profession, ville, condition, clientèle. | COULD |
| F-DIR-02 | Mini-site gratuit par praticien (photo, présentation, services). | COULD |
| F-DIR-03 | Recherche « près de moi » géolocalisée. | COULD |
| F-DIR-04 | Indexation SEO maîtrisée et balises structurées. | COULD |

## 19. Organisation, équipe, droits (ORG)

| ID | Exigence | Prio |
|---|---|---|
| F-ORG-01 | Comptes illimités pour les assistants et réceptionnistes selon l'offre. | MUST |
| F-ORG-02 | Rôles et permissions granulaires, rôles personnalisés. | MUST |
| F-ORG-03 | Télésecrétariat : gestion d'agendas délégués. | MUST |
| F-ORG-04 | Mode accueil : masquage des noms des clients sur l'horaire. | MUST |
| F-ORG-05 | Invitation par e-mail, désactivation, transfert de propriété. | MUST |
| F-ORG-06 | Multi-organisations pour un même utilisateur (praticiens multi-cabinets). | SHOULD |
| F-ORG-07 | Journal d'audit consultable et exportable. | MUST |
| F-ORG-08 | Paramétrage des plafonds de série par offre (R-16). | MUST |

## 20. Synchronisation calendrier (SYN)

| ID | Exigence | Prio |
|---|---|---|
| F-SYN-01 | Synchronisation Google Calendar (OAuth 2.0, compte de service par praticien). | MUST |
| F-SYN-02 | Synchronisation Microsoft 365 / Outlook. | SHOULD |
| F-SYN-03 | Synchronisation bidirectionnelle avec résolution de conflit déterministe (MyRDV = source de vérité pour ses rendez-vous). | SHOULD |
| F-SYN-04 | Les indisponibilités externes bloquent les disponibilités MyRDV. | SHOULD |
| F-SYN-05 | Synchronisation des séries : envoi d'un ICS RRULE unique, pas d'occurrences individuelles. | MUST |

## 21. Fuseaux horaires (TZ)

| ID | Exigence | Prio |
|---|---|---|
| F-TZ-01 | Chaque lieu et chaque série porte un fuseau IANA. | MUST |
| F-TZ-02 | Affichage dans le fuseau du lecteur, avec mention du fuseau de référence. | MUST |
| F-TZ-03 | Heure murale conservée lors des changements d'heure (R-06). | MUST |
| F-TZ-04 | Réservation transfrontalière affichant les deux heures. | MUST |

## 22. Téléconsultation (TEL)

| ID | Exigence | Prio |
|---|---|---|
| F-TEL-01 | Génération d'un lien de visioconférence par rendez-vous (Zoom/Whereby), identifiant chiffré. | MUST |
| F-TEL-02 | Salle d'attente virtuelle et témoin de présence. | SHOULD |
| F-TEL-03 | Enregistrement et transcription de séance (opt-in, conservation limitée). | COULD |

## 23. Assistants IA (AI)

| ID | Exigence | Prio |
|---|---|---|
| F-AI-01 | Synthèse de la note de séance à partir de la dictée, à la demande. | COULD |
| F-AI-02 | Aucune donnée client utilisée pour l'entraînement ; traitement cloisonné, journalisé. | MUST (si AI activée) |
| F-AI-03 | Désactivation de l'IA au niveau de l'organisation. | MUST (si AI activée) |

## 24. Documents et signature (DOC, SIG)

| ID | Exigence | Prio |
|---|---|---|
| F-DOC-01 | Téléversement sécurisé avec analyse antivirus et quarantaine. | MUST |
| F-DOC-02 | Signature électronique simple (eIDAS) des consentements. | MUST |
| F-DOC-03 | Horodatage et piste d'audit de signature. | MUST |
| F-DOC-04 | Gestion de versions de documents. | SHOULD |
| F-DOC-05 | Politique de rétention et purge automatique. | SHOULD |

## 25. Avis et satisfaction (FDB)

| ID | Exigence | Prio |
|---|---|---|
| F-FDB-01 | Questionnaire de satisfaction post-prestation (NPS, note, commentaire). | SHOULD |
| F-FDB-02 | Demande d'avis public avec lien vers la fiche. | COULD |
| F-FDB-03 | Tableau de bord de satisfaction. | SHOULD |

## 26. Analyse et reporting (ANL)

| ID | Exigence | Prio |
|---|---|---|
| F-ANL-01 | Tableau de bord : rendez-vous, taux de présence, revenus, nouveaux clients. | MUST |
| F-ANL-02 | Rapports personnalisables avec filtres et périodes. | SHOULD |
| F-ANL-03 | Insights clients (fréquence, récurrence moyenne, valeur). | SHOULD |
| F-ANL-04 | Export CSV/PDF de tout rapport. | MUST |
| F-ANL-05 | Mesure d'audience de la page publique (consentement préalable). | COULD |
| F-ANL-06 | Indicateur no-show et coût estimé des absences. | MUST |
| F-ANL-07 | Performance par praticien et par service. | MUST |

## 27. Intégrations et API (INT)

| ID | Exigence | Prio |
|---|---|---|
| F-INT-01 | API REST publique versionnée, OpenAPI 3.1, authentification OAuth 2.0. | MUST |
| F-INT-02 | Webhooks signés (HMAC-SHA256) avec rejeu et idempotence. | MUST |
| F-INT-03 | Export ICS et abonnement calendrier (flux). | SHOULD |
| F-INT-04 | Connecteur comptable (QuickBooks / Pennylane / Tiime) — V1.1. | SHOULD |
| F-INT-05 | Connecteur Zoom (visio) et Stripe (paiement). | MUST |
| F-INT-06 | Zapier / Make : déclencheurs et actions. | COULD |

## 28. Onboarding (ONB)

| ID | Exigence | Prio |
|---|---|---|
| F-ONB-01 | Assistant de création d'organisation en moins de 10 minutes (services, disponibilités, premier rendez-vous). | MUST |
| F-ONB-02 | Import de l'agenda existant (CSV, ICS). | MUST |
| F-ONB-03 | Centre d'aide contextuel et tutoriels. | SHOULD |

## 28bis. Internationalisation (I18N)

| ID | Exigence | Prio |
|---|---|---|
| F-I18N-01 | Interface FR/EN en V1, ES/DE en V2 ; dates, nombres et devises localisés. | MUST |
| F-I18N-02 | Messages clients dans la langue de leur fiche, repli sur la langue de l'organisation. | MUST |
| F-I18N-03 | Format de fuseau et premier jour de semaine configurables. | SHOULD |

---

## 29. Matrice de priorisation (MoSCoW) — synthèse

| Priorité | Nombre | Effort estimé (jours-homme) | Mise en service |
|---|---|---|---|
| MUST | 120 | 640 | V1 |
| SHOULD | 54 | 260 | V1.1 |
| COULD | 20 | 120 | V2 |
| WON'T (V1) | 1 | — | V2/V3 |
| **Total** | **195** | **1 020** | — |

## 30. Hors périmètre explicite (WON'T V1)

1. **Télétransmission des feuilles de soins** (France) et facturation aux assureurs (Canada) —
   dépendance à des organismes et à des certifications, reporté V2.
2. **Offre on-premise** — le produit est cloud uniquement ; un mode « données chez le client »
   (single-tenant dédié) est envisagé en V3 pour les grands comptes.
3. Application mobile **native** iOS/Android — la V1 est une PWA installable.
4. Comptabilité générale et paie.
5. Gestion de lits / hospitalisation, parcours de soins hospitaliers.
6. Marketplace avec commission sur les paiements (modèle volontairement différent de Fresha).
7. Marketing automation avancé (scénarios multi-étapes, scoring).
8. Signature électronique qualifiée eIDAS niveau « avancé » avec certificat matériel.

## 31. Contraintes transverses

- Toute exigence **MUST** de santé ou de facturation doit être couverte par un test automatisé avant
  la mise en production (doc 09 §4).
- Toute exigence touchant des données de santé déclenche une revue de conformité (doc 04 §6).
- Les exigences `F-REC-*` sont **normatives** : le comportement exact est décrit au document 06 ; en
  cas de divergence, le document 06 prévaut.

---

*Suite : [`04-securite-conformite.md`](04-securite-conformite.md).*

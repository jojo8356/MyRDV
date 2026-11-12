# 08 — Exigences non fonctionnelles

**Document** : 08 / 10 · **Version** 1.0 · **Date** : 12 novembre 2026
**Convention** : `NFR-<domaine>-<n>`. Chaque exigence est mesurable et rattachée à un moyen de
vérification (test, sonde, revue).

---

## 1. Performance

| ID | Exigence | Cible | Vérification |
|---|---|---|---|
| NFR-PERF-01 | Latence p95 de lecture d'agenda hebdomadaire (12 praticiens) | < 250 ms | test de charge T-PERF-01 |
| NFR-PERF-02 | Latence p95 de création de série (14 occurrences) | < 400 ms | T-PERF-02 |
| NFR-PERF-03 | Latence p95 de `dryRun` (40 occurrences) | < 150 ms | T-PERF-03 |
| NFR-PERF-04 | Latence p99 de réservation publique | < 800 ms | T-PERF-04 |
| NFR-PERF-05 | Temps de chargement initial de la page de réservation (3G rapide) | < 2,5 s (LCP) | Lighthouse |
| NFR-PERF-06 | Débit soutenu d'API | 500 req/s sur 3 instances | T-PERF-10 |
| NFR-PERF-07 | Matérialisation de 10 000 séries | < 10 min | test de job |
| NFR-PERF-08 | Export de 100 000 lignes | < 60 s | test asynchrone |
| NFR-PERF-09 | Taille des réponses paginées | < 512 Ko | test de contrat |
| NFR-PERF-10 | Recherche client (50 000 fiches) | p95 < 120 ms | T-PERF-20 |

**Absence de dégradation** : toute fonctionnalité qui ne tient pas son budget en p95 sous la charge de
référence est bloquante pour la mise en production (gate de performance en CI la nuit).

---

## 2. Disponibilité et résilience

| ID | Exigence | Cible |
|---|---|---|
| NFR-OPS-01 | Disponibilité mensuelle de l'API et de l'agenda | ≥ 99,9 % (≈ 43 min d'indisponibilité/mois) |
| NFR-OPS-02 | RPO / RTO | 5 min / 1 h |
| NFR-OPS-03 | Aucune perte de rendez-vous en cas de panne d'un nœud | Vérifié par test de chaos |
| NFR-OPS-04 | Déploiement sans interruption | Blue/green, 0 downtime |
| NFR-OPS-05 | Dégradation gracieuse : lecture seule si la base d'écriture est indisponible | Bandeau + file de reprise |
| NFR-OPS-06 | Restauration complète testée | Mensuelle, résultat archivé |
| NFR-OPS-07 | Sauvegarde chiffrée hors site | Quotidienne + continue |
| NFR-OPS-08 | Bascule régionale documentée | Test annuel < 4 h |

**Calcul du budget d'erreur** : 99,9 % ⇒ 43,2 min/mois ; alerte à 50 % du budget consommé,
gel des déploiements à 100 % jusqu'à retour dans le budget.

---

## 3. Scalabilité

| ID | Exigence | Cible |
|---|---|---|
| NFR-SCL-01 | Organisations actives | 10 000 sans refonte |
| NFR-SCL-02 | Rendez-vous stockés | 100 M |
| NFR-SCL-03 | Séries actives | 500 000 |
| NFR-SCL-04 | Utilisateurs simultanés | 5 000 |
| NFR-SCL-05 | Croissance horizontale | Ajout d'instance sans changement de code |
| NFR-SCL-06 | Isolation des performances | Une organisation ne peut consommer > 20 % du CPU (quotas) |

---

## 4. Sécurité (renvoi et compléments)

Voir [document 04](04-securite-conformite.md). Exigences mesurables :

| ID | Exigence |
|---|---|
| NFR-SEC-01 | TLS 1.3 obligatoire en externe, TLS 1.2+ en interne ; HSTS 1 an |
| NFR-SEC-02 | MFA disponible pour tous, obligatoire pour `OWNER`/`ADMIN` |
| NFR-SEC-03 | Déconnexion automatique après 30 min d'inactivité (paramétrable 5..120) |
| NFR-SEC-04 | Journal d'audit immuable, 10 ans, recherche < 2 s sur 12 mois |
| NFR-SEC-05 | WAF + protection DDoS, blocage géographique optionnel |
| NFR-SEC-06 | Aucun rôle non clinique n'accède aux notes (vérifié par test matriciel) |
| NFR-SEC-07 | Aucun secret dans les logs, dépôt ou artefact (scan automatisé) |
| NFR-SEC-08 | Chiffrement au repos AES-256, clés gérées par KMS, rotation annuelle |
| NFR-SEC-09 | Scan des dépendances bloquant en CI (aucune vulnérabilité critique ou élevée non traitée) |
| NFR-SEC-10 | Tests d'intrusion annuels, plan de remédiation sous 30 jours pour les critiques |

---

## 5. Accessibilité

| ID | Exigence | Cible |
|---|---|---|
| NFR-A11Y-01 | Conformité RGAA 4.1 / WCAG 2.1 AA sur les parcours critiques | 100 % des critères applicables |
| NFR-A11Y-02 | Navigation clavier complète (réservation, agenda, création de série) | Aucun piège de focus |
| NFR-A11Y-03 | Contraste | ≥ 4,5:1 (texte), ≥ 3:1 (composants) |
| NFR-A11Y-04 | Compatibilité lecteurs d'écran | NVDA + VoiceOver sur 3 parcours |
| NFR-A11Y-05 | Zoom 200 % sans perte de contenu | Test manuel |
| NFR-A11Y-06 | Information non portée par la couleur seule | Statuts doublés de libellés/icônes |
| NFR-A11Y-07 | Formulaires : libellés, erreurs explicites, `aria-describedby` | Audit |
| NFR-A11Y-08 | Alternatives textuelles, sous-titres des tutoriels | Audit |

---

## 6. Internationalisation et localisation

| ID | Exigence |
|---|---|
| NFR-I18N-01 | Interface FR/EN en V1 (ES/DE en V2), externalisation des chaînes, aucune concaténation |
| NFR-I18N-02 | Formats de date, heure, nombre, devise localisés (`Intl`) |
| NFR-I18N-03 | Fuseaux IANA exclusivement ; aucun stockage en heure locale sans fuseau |
| NFR-I18N-04 | Prise en charge des noms non latins (UTF-8, unicité insensible à la casse et aux accents) |
| NFR-I18N-05 | Devises et taxes configurables par pays |
| NFR-I18N-06 | Langue des messages clients alignée sur la fiche, repli documenté |
| NFR-I18N-07 | Support RTL prévu dans l'architecture UI (V2 pour l'arabe/hébreu) |

---

## 7. Observabilité

| ID | Exigence |
|---|---|
| NFR-OBS-01 | Traces distribuées OpenTelemetry sur 100 % des requêtes API |
| NFR-OBS-02 | Métriques métier : séries créées, occurrences générées, conflits, no-show, latence par endpoint |
| NFR-OBS-03 | Logs structurés JSON, corrélation `requestId`/`correlationId`, rétention 12 mois |
| NFR-OBS-04 | Tableaux de bord SLO avec budget d'erreur et alertes |
| NFR-OBS-05 | Alerting : p95 > budget 10 min, taux d'erreur > 1 %, job de matérialisation en retard > 30 min |
| NFR-OBS-06 | Erreurs frontend collectées avec source maps, taux d'erreur suivi |
| NFR-OBS-07 | Synthétique : parcours de réservation testé toutes les 5 min depuis 3 régions |
| NFR-OBS-08 | Métrique dédiée `series_generation_discrepancy_total` comparant simulateur et production (R-17) |

**Sondes de santé** : `/health/live`, `/health/ready`, `/health/deep` (base, Redis, files BullMQ, Stripe).

---

## 8. Maintenabilité et qualité de code

| ID | Exigence |
|---|---|
| NFR-QUA-01 | TypeScript strict, ESLint + Prettier bloquants en CI |
| NFR-QUA-02 | Couverture ≥ 80 % global, ≥ 95 % sur `recurrence` et `billing` |
| NFR-QUA-03 | Aucun `any` implicite, aucune dépendance non auditée |
| NFR-QUA-04 | Revue de code obligatoire, 2 approbations pour santé/paiement |
| NFR-QUA-05 | Documentation d'API générée (OpenAPI 3.1) et testée (contrat) |
| NFR-QUA-06 | Migrations rétrocompatibles uniquement |
| NFR-QUA-07 | Dette technique suivie, plafond de 10 % du temps d'itération |
| NFR-QUA-08 | Tests de non-régression sur tous les vecteurs du document 06 |

---

## 9. Ergonomie et expérience

| ID | Exigence | Cible |
|---|---|---|
| NFR-UX-01 | Création d'une série de 3 mois | ≤ 45 s, ≤ 8 interactions |
| NFR-UX-02 | Réservation client | ≤ 4 écrans, sans compte |
| NFR-UX-03 | Toute action destructive | Confirmation chiffrée (nombre d'occurrences) |
| NFR-UX-04 | Feedback | Tout appel > 300 ms affiche un indicateur ; > 2 s un état de progression |
| NFR-UX-05 | Messages d'erreur | Actionnables, en langue de l'utilisateur, avec code stable |
| NFR-UX-06 | Mobile | Utilisable à 360 px, cibles tactiles ≥ 44 px |
| NFR-UX-07 | Cohérence | Design system unique, composants accessibles Radix |
| NFR-UX-08 | Annulation | Toute suppression de série est réversible 30 jours (corbeille) |

---

## 10. Conformité et vie privée (mesures)

| ID | Exigence |
|---|---|
| NFR-CMP-01 | Hébergement UE par défaut ; Canada et US sur option |
| NFR-CMP-02 | Conformité RGPD, Loi 25, PIPEDA documentée et auditable |
| NFR-CMP-03 | HIPAA disponible sur offre Business/Entreprise avec BAA |
| NFR-CMP-04 | Accès en lecture seule aux données après résiliation (12 mois) |
| NFR-CMP-05 | Export complet en 1 clic (JSON + CSV + PDF), sans surcoût |
| NFR-CMP-06 | Aucune donnée de santé dans les SMS, notifications push ou objets de courriel |
| NFR-CMP-07 | Consentements horodatés, versionnés, révocables |
| NFR-CMP-08 | DPIA disponible pour les clients (modèle documenté) |
| NFR-CMP-09 | Sous-traitants listés publiquement, DPA signable en ligne |
| NFR-CMP-10 | Purge automatique conforme aux durées de rétention |

---

## 11. Coût et efficience

| ID | Exigence | Cible |
|---|---|---|
| NFR-CST-01 | Coût d'infrastructure par organisation active | < 1,60 €/mois à 1 000 organisations |
| NFR-CST-02 | Coût d'un SMS | Prix coûtant + 0 %, plafond par offre |
| NFR-CST-03 | Coût de stockage par organisation | < 0,10 €/mois (hors documents volumineux) |
| NFR-CST-04 | Aucun coût variable caché facturé au client | Transparence tarifaire |

---

## 12. Récapitulatif et priorisation

| Domaine | Nb d'exigences | Bloquantes V1 |
|---|---|---|
| Performance | 10 | 6 |
| Disponibilité / résilience | 8 | 5 |
| Scalabilité | 6 | 3 |
| Sécurité | 10 | 8 |
| Accessibilité | 8 | 4 |
| Internationalisation | 7 | 3 |
| Observabilité | 8 | 5 |
| Maintenabilité | 8 | 5 |
| Ergonomie | 8 | 4 |
| Conformité | 10 | 8 |
| Coût | 4 | 1 |
| **Total** | **87** | **52** |

Les exigences non bloquantes de la V1 sont planifiées en V1.1 avec un propriétaire nommé.

---

*Suite : [`09-plan-tests-recette.md`](09-plan-tests-recette.md).*

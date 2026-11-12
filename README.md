# MyRDV

Plateforme de prise de rendez-vous et de gestion d'agenda pour les professionnels de la santé, du
bien-être et des services.

## Cahier des charges

Le dossier complet de spécification (analyse du marché, exigences, architecture, sécurité, moteur de
rendez-vous récurrents, API, tests, roadmap) se trouve dans
[`docs/cahier-des-charges/`](docs/cahier-des-charges/README.md).

Points d'entrée :

- [`docs/cahier-des-charges/README.md`](docs/cahier-des-charges/README.md) — table des matières
- [`docs/00-synthese-executive.md`](docs/cahier-des-charges/docs/00-synthese-executive.md) — synthèse pour décision
- [`docs/06-moteur-rdv-recurrents.md`](docs/cahier-des-charges/docs/06-moteur-rdv-recurrents.md) — spécification normative des rendez-vous récurrents
- [`docs/01-contexte-analyse-marche.md`](docs/cahier-des-charges/docs/01-contexte-analyse-marche.md) — analyse fonctionnelle de GOrendezvous

## Spécification exécutable du module de récurrence

```bash
cd docs/cahier-des-charges
python3 tools/recurrence_simulator.py --self-test   # invariants du moteur
python3 tools/recurrence_simulator.py --demo        # exemple « 1 fois/semaine pendant 3 mois »
python3 tools/test_schemas.py                       # validation du schéma JSON (nécessite jsonschema)
```

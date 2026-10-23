# boreal-Sagdo

Entrepôt de données et analyse du portefeuille de **Boréal Assurances** (assurance auto et habitation, janvier 2020 à juin 2025). Projet M2 Data Engineering et Data Analyse.

Chaîne : sources → `raw` (copie fidèle) → `prep` (typage et contrôles) → `core` (schéma en étoile) → `marts` → dashboard et notebooks.
Outils : Python, DuckDB, dbt, Makefile, Streamlit.

| Livrable | Documents |
|---|---|
| L1 · Architecture et ingestion | [docs/architecture.md](docs/architecture.md) |
| L2 · Qualité et modélisation | [docs/qualite_modelisation.md](docs/qualite_modelisation.md) |
| L3 · Analyse technique | [docs/analyse_technique.md](docs/analyse_technique.md), notebook [notebooks/L3_analyse_technique.ipynb](notebooks/L3_analyse_technique.ipynb) |
| L4 · Clients et sinistres | [docs/clients_sinistres.md](docs/clients_sinistres.md), notebook [notebooks/L4_clients_sinistres.ipynb](notebooks/L4_clients_sinistres.ipynb) |
| Dossier complet (30 pages) | [dossier/SAGDO_Boreal.pdf](dossier/SAGDO_Boreal.pdf), régénéré par `make dossier` |
| Note exécutive (1 page) | [dossier/SAGDO_Boreal_note_executive.pdf](dossier/SAGDO_Boreal_note_executive.pdf), régénérée par `make dossier` |
| L5 · Dashboard, exploitation, gouvernance | Dashboard `dashboard/app.py`, [catalogue des données](docs/catalogue.md), [lignage du S/P](docs/lignage_sp.md), [note exécutive](docs/note_executive.md), [analyse RGPD](docs/rgpd.md) |

## Exécution en 5 commandes

Prérequis : Python 3.10 ou plus, `make`, le dépôt cloné (`git clone https://github.com/Nevs0255/boreal-Sagdo.git`) et l'archive `sources_boreal.zip` extraite.

```bash
make install                                  # 1. environnement Python et dépendances
make sources SRC=~/Downloads/sources_boreal   # 2. copie des sources dans data/sources
make run                                      # 3. ingestion, transformations, tests bloquants
make test                                     # 4. idempotence, effacement, orchestration, dashboard
make dashboard                                # 5. tableau de bord sur http://localhost:8501
```

## Exploitation

| Commande | Effet |
|---|---|
| `make reload MOIS=2024_03` | Recharge un mois de règlements (aucun doublon créé) |
| `make surveiller` | Lance le pipeline seulement si un fichier source nouveau ou modifié est arrivé ; alerte en cas d'échec |
| `make planifier` / `make deplanifier` | Installe ou retire la planification macOS (launchd) : déclenchement à l'arrivée d'un fichier, et chaque jour à 7 h en filet de sécurité. Pour cron : `orchestration/crontab.txt` |
| `make journal` | Dernière exécution et état de chaque source |
| `make notebooks` | Réexécute les notebooks d'analyse sur l'entrepôt |
| `make dossier` | Régénère le dossier PDF (Google Chrome et pandoc requis) |
| `make docs` | Régénère le catalogue des données (`docs/catalogue.md`) ; lignage interactif avec `dbt docs serve` |
| `make effacer CLIENT=123` | Droit à l'effacement RGPD (voir [docs/rgpd.md](docs/rgpd.md)) |
| `make clean` | Supprime l'entrepôt (les sources sont conservées) |

**Alertes.** Un échec de `make surveiller` écrit dans `logs/alertes.log` et affiche une notification macOS. Il poste aussi un message JSON sur le webhook défini par la variable `BOREAL_WEBHOOK_ALERTE` (Slack, Teams…), si elle existe.

**Tests bloquants.** `make run` s'arrête au premier test dbt en échec. Les résultats sont publiés dans `meta.resultats_tests` et affichés sur la page Exploitation du dashboard.

## Dashboard

Quatre pages, alimentées uniquement par les tables `marts` de l'entrepôt :

| Page | Contenu |
|---|---|
| Portefeuille | Primes acquises, contrats actifs, fréquence, coût moyen, S/P, taux de résiliation ; comparaison à période égale avec l'année précédente ; alerte visuelle au-delà d'un S/P de 70 % |
| Technique et clients | S/P par zone, formule, canal et âge ; décomposition de l'évolution du S/P ; rétention par cohorte ; concentration de la valeur client |
| Exploitation | Dernier chargement par source, lignes écartées par règle, résultats des tests, fraîcheur des données, délais de gestion des sinistres |
| Définitions | Définition de chaque indicateur et justification du seuil d'alerte |

**Filtres croisés :** période, produit, région, canal et zone de risque. Une option exclut le sinistre atypique de 2,48 M€.

## Organisation du dépôt

| Chemin | Contenu |
|---|---|
| `pipeline/` | Ingestion, journal, publication des tests, surveillance et alertes, effacement RGPD, catalogue |
| `dbt/` | Modèles SQL `prep`, `quarantaine`, `core`, `marts` ; catalogue des règles de qualité ; tests de données ; dictionnaire des colonnes |
| `analyse/` | Définitions des indicateurs, décomposition du S/P, intervalles de confiance et tests (partagés par les notebooks et le dashboard) |
| `dashboard/` | Application Streamlit |
| `notebooks/` | Notebooks d'analyse exécutés |
| `orchestration/` | Planification launchd (macOS) et cron |
| `tests/` | Tests pytest : ingestion, analyse, effacement, surveillance, dashboard |
| `docs/` | Documentation des livrables, catalogue, figures |
| `dossier/` | Dossier PDF, ses sections propres, sa mise en page et son générateur |
| `data/` | Sources et entrepôt DuckDB, non versionnés |

Les données sources, pseudonymisées, ne sont pas versionnées : elles sont fournies par le cours.

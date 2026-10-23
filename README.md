# boreal-Sagdo

Entrepôt de données et analyse du portefeuille de **Boréal Assurances** (assurance auto et habitation, janvier 2020 à juin 2025). Projet M2 Data Engineering et Data Analyse.

Chaîne : sources → `raw` (copie fidèle) → `prep` (typage) → `core` (schéma en étoile) → `marts` → dashboard.
Outils : Python, DuckDB, dbt, Makefile, Streamlit.

| Livrable | Document |
|---|---|
| L1 · Architecture et ingestion | [docs/architecture.md](docs/architecture.md) |
| L2 · Qualité et modélisation | [docs/qualite_modelisation.md](docs/qualite_modelisation.md) |
| L3 · Analyse technique | [docs/analyse_technique.md](docs/analyse_technique.md), notebook [notebooks/L3_analyse_technique.ipynb](notebooks/L3_analyse_technique.ipynb) |

## Exécution en 5 commandes

Prérequis : Python 3.10 ou plus, `make`, et l'archive `sources_boreal.zip` extraite.

```bash
git clone https://github.com/Nevs0255/boreal-Sagdo.git && cd boreal-Sagdo
make install                                  # environnement Python et dépendances
make sources SRC=~/Downloads/sources_boreal   # copie des sources dans data/sources
make run                                      # ingestion + transformations + tests bloquants
make test                                     # preuve d'idempotence et tests de l'entrepôt
```

Autres commandes :

| Commande | Effet |
|---|---|
| `make reload MOIS=2024_03` | Recharge un mois de règlements (aucun doublon créé) |
| `make journal` | Dernière exécution et état de chaque source |
| `make notebooks` | Réexécute les notebooks d'analyse sur l'entrepôt |
| `make docs` | Catalogue de données et lignage (dbt docs) |
| `make clean` | Supprime l'entrepôt (les sources sont conservées) |

## Organisation du dépôt

| Chemin | Contenu |
|---|---|
| `pipeline/` | Ingestion Python vers la couche brute, journal d'ingestion |
| `dbt/` | Modèles SQL `prep`, `quarantaine`, `core` et `marts`, catalogue des règles de qualité, tests de données |
| `analyse/` | Définitions des indicateurs, décomposition du S/P, intervalles de confiance et tests (partagés notebooks et dashboard) |
| `notebooks/` | Notebooks d'analyse exécutés (dossier) |
| `tests/` | Tests d'ingestion (idempotence, rechargement, livraisons anormales) |
| `docs/` | Architecture et documentation des livrables |
| `data/` | Sources et entrepôt DuckDB, non versionnés |

Les données sources, pseudonymisées, ne sont pas versionnées : elles sont fournies par le cours.

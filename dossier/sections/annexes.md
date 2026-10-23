# Annexes

Les commandes pour reproduire les résultats figurent au chapitre 5 et dans le `README.md` du dépôt (`make install`, `make sources`, `make run`, `make test`, `make dashboard` ; ce dossier : `make dossier`).

## A. Origine des chiffres clés

| Chiffre | Valeur | Produit par |
|---|---|---|
| Lignes et paiements distincts des règlements | 3 207 / 3 175 | Requête du chapitre 1 sur `raw.reglements` |
| Volume de chaque règle de qualité | 36 règles | Table `qualite.bilan_regles` (modèle `dbt/models/qualite/bilan_regles.sql`) |
| Réconciliation des règlements | 11 176 660,34 € + 118 175,46 € = 11 294 835,80 € | Test `reconciliation_reglements_brut_coeur` |
| Taux de doublons clients | 1,32 % | Requête du chapitre 2 ; table `core.client_rapprochement` |
| Exposition et primes acquises par année | 45 215 années-police, 20,0 M€ | Requête du chapitre 2 sur `core.fct_exposition` |
| Indicateurs par axe, décomposition du S/P, intervalles de confiance, tests, queue des coûts | Chapitre 3 | Notebook L3 : § 1 (`tableau([...])`), § 2 (`decomposer_sp`), § 3 (cellules IC, Test 1, Test 2, queue de distribution) |
| Rétention, multi-détention, valeur client | Chapitre 4, § 1 et 2 | Notebook L4, § 1 et 2 ; marts `mart_retention_contrats`, `mart_retention_clients`, `mart_clients` |
| Délais et audits | Chapitre 4, § 3 et 4 | Notebook L4, § 3 et 4 ; mart `mart_sinistres` |

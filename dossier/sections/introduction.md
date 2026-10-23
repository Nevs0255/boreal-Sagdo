# Introduction

## Contexte et mission

Boréal Assurances assure 20 264 contrats auto et habitation, et a enregistré 2 805 sinistres déclarés entre janvier 2020 et juin 2025.

**Le problème.** Ses données sont réparties entre cinq outils qui ne se parlent pas : CRM, gestion des contrats, gestion des sinistres, comptabilité (règlements) et antifraude. Le ratio sinistres sur primes diffère selon le service qui le calcule, et un même client peut apparaître plusieurs fois.

**La demande.** La directrice technique, Camille Roux, veut une source unique de vérité, mise à jour sans intervention manuelle, et un tableau de bord qui réponde à trois questions :
- où le portefeuille gagne ou perd de l'argent ;
- comment les clients se comportent dans la durée ;
- si les délais de gestion des sinistres sont tenus.

**Mission de MarketSense.**
1. Construire un entrepôt de données alimenté par un pipeline reproductible et testé.
2. L'exploiter pour une analyse descriptive et explicative du portefeuille. Aucun modèle prédictif n'est construit.
3. Restituer les résultats dans un tableau de bord branché sur l'entrepôt.

## Démarche et organisation du dossier

| Chapitre | Livrable | Question traitée |
|---|---|---|
| 1 | Architecture et ingestion | Comment charger les 68 fichiers sans intervention manuelle ni doublon ? |
| 2 | Qualité et modélisation | Quels défauts contiennent les sources, et quel modèle les rend exploitables ? |
| 3 | Analyse technique | Où le portefeuille gagne-t-il ou perd-il de l'argent, et pourquoi le ratio S/P évolue-t-il ? |
| 4 | Clients et sinistres | Les clients restent-ils, lesquels créent de la valeur, les délais et les audits sont-ils maîtrisés ? |
| 5 | Dashboard et exploitation | Comment la directrice et l'équipe data suivent-elles ces résultats au quotidien ? |
| 6 | RGPD | Quelles données personnelles l'entrepôt contient-il, et comment les protéger ? |

La note exécutive, en tête du dossier, résume les constats et les décisions proposées pour une lectrice non technicienne.

## Conventions

- **Origine des chiffres.** Tous les chiffres viennent de l'entrepôt DuckDB construit par `make run` : couche `marts` pour les analyses, `core` pour les contrôles. Chaque valeur est reproductible. L'annexe A indique, pour chaque chiffre clé, la requête, le modèle ou la cellule de notebook qui le produit.
- **Cohérence des restitutions.** Les indicateurs sont définis une seule fois, dans `analyse/indicateurs.py`, et partagés par les notebooks et le dashboard. Les chiffres du dossier, du dashboard et de l'entrepôt sont donc identiques.
- **Fréquences.** Elles sont toujours calculées par année-police (durée de couverture), jamais par nombre de contrats.
- **Périmètre temporel.** Les données s'arrêtent au 30/06/2025 : l'année 2025 est incomplète.

## Contribution

Ce projet a été réalisé **individuellement** par Teddy Sagdo, auteur de l'ensemble des travaux : architecture, ingestion et orchestration, règles de qualité et modélisation, analyses statistiques, tableau de bord, documentation et dossier. Le dépôt se nomme `boreal-Sagdo` et ce dossier `SAGDO_Boreal.pdf`.

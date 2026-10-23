# Analyse RGPD de l'entrepôt

*Analyse établie par l'équipe data. Les durées de conservation et les bases légales sont des propositions à valider avec le délégué à la protection des données (DPO) de Boréal Assurances.*

## 1. Données personnelles présentes

Les sources sont **pseudonymisées** : aucun nom, aucune adresse, aucun téléphone ni aucun e-mail en clair. Les données restent pourtant **personnelles** au sens du RGPD (considérant 26) : Boréal détient dans son CRM la correspondance entre les identifiants et les personnes, et le croisement de plusieurs attributs peut suffire à isoler un individu.

| Donnée | Où | Nature | Sensibilité |
|---|---|---|---|
| `client_id` | Toutes les couches | Identifiant pseudonyme | Rattache toutes les autres données à une personne |
| `email_hash` | raw, prep, core, snapshots, quarantaine | Empreinte de l'e-mail | Pseudonyme. Une empreinte sans sel peut être retrouvée par essai d'adresses connues |
| `date_naissance` | raw, prep, core, snapshots | Donnée d'identification | Combinée à la région, elle réduit fortement l'anonymat |
| `region`, `csp` | raw, prep, core, snapshots, marts (`mart_clients`, `mart_technique`) | Profil socio-démographique | Modérée |
| `consent_marketing` | raw, prep, core, snapshots | Choix de la personne | Conditionne tout usage commercial |
| Contrats (prime, bonus-malus, puissance, surface, zone) | raw, prep, core, marts | Données contractuelles liées à une personne | Modérée |
| Sinistres et règlements | raw, prep, core, marts | Événements de la vie de l'assuré | Modérée à forte selon le sinistre |
| Audits (`fraude_confirmee`) | raw, prep, core, marts | Soupçon ou constat de fraude | **Forte** : données relatives à des infractions potentielles (article 10), à accès très restreint |

**Ce qui n'en contient pas :**
- **Journal et tests :** `meta.journal_ingestion`, `meta.resultats_tests` et `qualite.*` ne décrivent que des fichiers et des volumes.
- **Registre des effacements :** `meta.effacements` ne conserve que des identifiants techniques.
- **Dashboard :** il n'affiche que des agrégats. La page Technique et clients calcule la courbe de valeur client à partir de `mart_clients`, sans afficher aucune ligne individuelle.

**Volumes.** 15 000 clients conservés dans le cœur, dont 10 348 ayant consenti à la prospection.

## 2. Pseudonymisation et minimisation

| Mesure | État |
|---|---|
| Absence d'identité directe (nom, coordonnées) | Respectée dès la source |
| Identifiants techniques à la place des personnes | Respectée (`client_id`, `contrat_id`, `sinistre_id`) |
| E-mail remplacé par une empreinte | Respectée. **Recommandation :** utiliser une empreinte salée (HMAC), dont la clé est détenue par le DPO, pour empêcher la recherche par essai d'adresses |
| Exactitude (article 5.1.d) | Les 200 fiches clients en double sont rapprochées (`core.client_rapprochement`). Les dates de naissance impossibles sont neutralisées (règles CLI_02 et CLI_03) |
| Minimisation de la restitution | Les analyses et le dashboard travaillent sur des agrégats (marts). Les tables détaillées (`raw`, `prep`, `core`) sont réservées à l'équipe data |
| Accès | Entrepôt local (fichier DuckDB). En production : chiffrement du disque, droits d'accès par schéma, audits restreints à l'équipe antifraude |

## 3. Bases légales et finalités

| Finalité | Base légale proposée |
|---|---|
| Gestion des contrats et des sinistres | Exécution du contrat (article 6.1.b) |
| Conservation des pièces comptables et contractuelles | Obligation légale (article 6.1.c) |
| Pilotage technique du portefeuille (tarification, S/P, rétention) | Intérêt légitime de l'assureur (article 6.1.f). Les analyses sont agrégées |
| Lutte contre la fraude | Intérêt légitime (article 6.1.f), dans le cadre du référentiel de la CNIL sur la lutte contre la fraude |
| Prospection commerciale | **Consentement** (article 6.1.a) : seuls les clients `consent_marketing = 1` peuvent être ciblés. La segmentation de la valeur client (livrable 4) ne doit pas servir à une campagne sans ce filtre |

## 4. Durées de conservation proposées

| Données | Durée proposée | Fondement (à valider par le DPO) |
|---|---|---|
| Clients et contrats | Durée du contrat + 2 ans après sa fin, puis anonymisation | Prescription biennale des actions dérivant du contrat d'assurance (article L114-1 du Code des assurances) |
| Sinistres corporels (RC) | Jusqu'à 10 ans après la consolidation | Prescription des dommages corporels |
| Règlements (pièces comptables) | 10 ans | Conservation des pièces comptables (article L123-22 du Code de commerce) |
| Audits concluant à une fraude | 5 ans après la clôture du dossier de fraude | Référentiel CNIL de lutte contre la fraude |
| Audits sans fraude confirmée | Suppression rapide (ex. 6 mois) | Une suspicion non confirmée ne doit pas suivre l'assuré |
| Consentement à la prospection | Jusqu'au retrait, ou 3 ans sans contact | Recommandations CNIL sur la prospection |
| Journal d'ingestion et résultats de tests | 2 ans | Traçabilité technique, sans donnée personnelle |
| Fichiers sources livrés (`data/sources`) | Jusqu'au chargement validé, puis archivage chiffré limité à la reprise sur incident | Minimisation |

**Mise en œuvre.** Une tâche annuelle appliquerait ces durées en appelant la procédure d'effacement (§ 5) sur les clients dont la relation est éteinte depuis plus de 2 ans. La base `date_resiliation` le permet.

## 5. Droit à l'effacement dans chaque couche

**Procédure :** `make effacer CLIENT=<identifiant>`, code dans `pipeline/effacer_client.py`. Elle est testée par `tests/test_effacement.py`.

**Effacement partiel, et pourquoi.** Les contrats, sinistres et règlements sont **conservés** : ils relèvent d'obligations légales et de la défense de droits en justice (article 17.3.b et 17.3.e). Ce sont les attributs personnels qui sont effacés : date de naissance, région, CSP, consentement et empreinte d'e-mail. Le client devient un identifiant technique sans attribut. Les fiches doublons qui partagent son empreinte sont effacées avec lui.

| Couche | Effet de l'effacement | Mécanisme |
|---|---|---|
| Fichiers sources (`data/sources`) | **Hors du périmètre de l'entrepôt** : le CRM de Boréal doit effacer la personne à la source. La prochaine livraison ne la contiendra plus | Procédure CRM |
| Brut (`raw.clients`) | Attributs personnels vidés | Mise à jour immédiate, et **réappliquée à chaque rechargement du CRM** à partir de `meta.effacements`. Un ancien fichier rechargé ne fait donc pas réapparaître les données |
| Registre (`meta.effacements`) | Conserve l'identifiant, l'identifiant conservé, la date et le motif, **sans** donnée personnelle | Preuve de traitement de la demande |
| Préparation, quarantaine, cœur, marts | Attributs vides, client marqué `est_efface` ; tranche d'âge « Inconnu » | Reconstruction par dbt (`make build`, lancé par `make effacer`) |
| Historique (`snapshots.snap_clients`) | Toutes les versions passées du client supprimées | Suppression explicite (le snapshot n'est pas reconstructible) |
| Notebooks et dossier | Uniquement des agrégats : effet négligeable | Réexécution `make notebooks` |
| Sauvegardes | Les données effacées disparaissent au terme du cycle de rotation des sauvegardes. Elles ne doivent pas être restaurées sans réappliquer `meta.effacements` | Procédure d'exploitation |

**Ce que vérifie le test automatique (`tests/test_effacement.py`) :**
- les attributs du client et de son doublon sont vidés dans la couche brute et dans `core.dim_client` ;
- ses contrats sont conservés ;
- le nombre de clients du cœur reste de 15 000, car le doublon reste rattaché au client conservé ;
- un rechargement forcé du CRM ne fait pas réapparaître les données.

# Catalogue des données

Généré par `make docs` à partir des métadonnées dbt : chaque table et chaque colonne de l'entrepôt `data/warehouse/boreal.duckdb`, avec son type et sa définition. Une même notion porte une seule définition dans tout le projet.

## Schéma `raw`

Couche brute : copie fidèle des sources, toutes valeurs en texte.

### `raw.audits`

Audits antifraude : dossiers contrôlés uniquement (antifraude/audits.csv).

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | VARCHAR | Identifiant du sinistre. |
| `date_audit` | VARCHAR | Date de l'audit antifraude. |
| `fraude_confirmee` | VARCHAR | Résultat de l'audit : fraude confirmée (vide si non audité). |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `raw.clients`

CRM : un client par ligne (crm/clients.csv, séparateur ';').

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | VARCHAR | Identifiant pseudonymisé du client (CRM). |
| `date_naissance` | VARCHAR | Date de naissance du client. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | VARCHAR | Consentement à la prospection commerciale (1 = oui). |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `raw.contrats`

Gestion des contrats auto et habitation (contrats/contrats.csv).

| Colonne | Type | Définition |
|---|---|---|
| `contrat_id` | VARCHAR | Identifiant du contrat. |
| `client_id` | VARCHAR | Identifiant pseudonymisé du client (CRM). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `date_effet` | VARCHAR | Date de début de couverture. |
| `date_resiliation` | VARCHAR | Date de fin de couverture (vide si le contrat est en cours). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `zone_risque` | VARCHAR | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `franchise` | VARCHAR | Franchise du contrat, en euros. |
| `bonus_malus` | VARCHAR | Coefficient de bonus-malus (auto uniquement). |
| `puissance_cv` | VARCHAR | Puissance fiscale du véhicule en chevaux (auto uniquement). |
| `surface_m2` | VARCHAR | Surface du logement en m² (habitation uniquement). |
| `prime_annuelle` | VARCHAR | Prime annuelle du contrat, en euros. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `raw.reglements`

Paiements de sinistres, un fichier par mois (reglements/reglements_AAAA_MM.csv).

| Colonne | Type | Définition |
|---|---|---|
| `paiement_id` | VARCHAR | Identifiant du paiement. |
| `sinistre_id` | VARCHAR | Identifiant du sinistre. |
| `date_paiement` | VARCHAR | Date du paiement. |
| `montant` | VARCHAR | Montant payé, en euros. |
| `_fichier_source` | VARCHAR | Chemin du fichier d'origine, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `raw.rejets_ingestion`

Lignes illisibles à l'ingestion (vides, nombre de champs incorrect, JSON invalide), avec leur motif.

| Colonne | Type | Définition |
|---|---|---|
| `fichier` | VARCHAR | Fichier source, relatif au dossier des sources. |
| `source` | VARCHAR | Source de données : clients, contrats, sinistres, reglements ou audits. |
| `numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine. |
| `contenu` | VARCHAR | Contenu brut de la ligne rejetée. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `raw.sinistres`

Gestion des sinistres, un objet JSON par ligne (sinistres/sinistres.jsonl).

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | VARCHAR | Identifiant du sinistre. |
| `contrat_id` | VARCHAR | Identifiant du contrat. |
| `date_survenance` | VARCHAR | Date de survenance du sinistre. |
| `date_declaration` | VARCHAR | Date de déclaration du sinistre à l'assureur. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `reserve_initiale` | VARCHAR | Réserve ouverte à la déclaration, en euros. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_id_chargement` | VARCHAR | Identifiant du chargement du fichier (journal d'ingestion). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

## Schéma `meta`

Pilotage de la chaîne : journal d'ingestion, résultats des tests, registre des effacements.

### `meta.effacements`

Demandes d'effacement RGPD appliquées à la couche brute (pipeline/effacer_client.py).

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `client_id_retenu` | INTEGER | Identifiant du client conservé après rapprochement des doublons. |
| `demande_le` | TIMESTAMP | Date d'application de l'effacement. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

### `meta.journal_ingestion`

Une ligne par fichier traité et par exécution : empreinte, lignes lues, chargées, rejetées, durée, statut.

| Colonne | Type | Définition |
|---|---|---|
| `id_execution` | VARCHAR | Identifiant de l'exécution (ingestion ou dbt). |
| `id_chargement` | VARCHAR | Identifiant du chargement du fichier. |
| `fichier` | VARCHAR | Fichier source, relatif au dossier des sources. |
| `source` | VARCHAR | Source de données : clients, contrats, sinistres, reglements ou audits. |
| `sha256` | VARCHAR | Empreinte SHA-256 du contenu du fichier (détection des fichiers déjà chargés). |
| `encodage` | VARCHAR | Encodage détecté du fichier. |
| `separateur` | VARCHAR | Séparateur détecté (CSV). |
| `lignes_lues` | INTEGER | Lignes de données lues dans le fichier. |
| `lignes_chargees` | INTEGER | Lignes chargées dans la couche brute. |
| `lignes_rejetees` | INTEGER | Lignes illisibles envoyées dans raw.rejets_ingestion. |
| `debut` | TIMESTAMP | Horodatage du traitement du fichier. |
| `duree_s` | DOUBLE | Durée du traitement, en secondes. |
| `statut` | VARCHAR | Résultat du traitement du fichier : CHARGE, RECHARGE, IGNORE (déjà chargé à l'identique), DOUBLON_LIVRAISON ou ECHEC. |
| `message` | VARCHAR | Message complémentaire (motif d'échec, fichier homonyme…). |

### `meta.resultats_tests`

Résultats des tests dbt de chaque exécution, publiés par pipeline/publier_tests.py.

| Colonne | Type | Définition |
|---|---|---|
| `id_execution` | VARCHAR | Identifiant de l'exécution (ingestion ou dbt). |
| `genere_le` | TIMESTAMP | Horodatage de l'exécution des tests. |
| `outil` | VARCHAR | Outil ayant exécuté le test (dbt). |
| `nom` | VARCHAR | Nom du test. |
| `objet` | VARCHAR | Identifiant complet du test dans dbt. |
| `statut` | VARCHAR | Résultat du test : PASS, FAIL, WARN ou ERROR. |
| `echecs` | INTEGER | Nombre de lignes en échec renvoyées par le test. |
| `duree_s` | DOUBLE | Durée du traitement, en secondes. |
| `message` | VARCHAR | Message complémentaire (motif d'échec, fichier homonyme…). |

## Schéma `prep`

Préparation : typage (stg_*) et contrôles de qualité (int_*).

### `prep.int_audits`

Audits contrôlés : règles AUD_01 à AUD_04.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_audit` | DATE | Date de l'audit antifraude. |
| `fraude_confirmee` | INTEGER | Résultat de l'audit : fraude confirmée (vide si non audité). |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |

### `prep.int_clients`

Clients contrôlés : règles CLI_01 à CLI_07, rapprochement des doublons (client_id_retenu), date de naissance corrigée.

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `date_naissance` | DATE | Date de naissance du client. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | INTEGER | Consentement à la prospection commerciale (1 = oui). |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `date_premiere_souscription` | DATE | Date d'effet du premier contrat du client. |
| `est_efface` | BOOLEAN | Vrai si les attributs personnels du client ont été effacés (droit à l'effacement). |
| `client_id_retenu` | INTEGER | Identifiant du client conservé après rapprochement des doublons. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `date_naissance_corrigee` | DATE | Date de naissance après correction (vide si sentinelle ou impossible : règles CLI_02, CLI_03). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |

### `prep.int_contrats`

Contrats contrôlés : règles CTR_01 à CTR_08, rattachement au client conservé.

| Colonne | Type | Définition |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `date_effet` | DATE | Date de début de couverture. |
| `date_resiliation` | DATE | Date de fin de couverture (vide si le contrat est en cours). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `franchise` | DOUBLE | Franchise du contrat, en euros. |
| `bonus_malus` | DOUBLE | Coefficient de bonus-malus (auto uniquement). |
| `puissance_cv` | DOUBLE | Puissance fiscale du véhicule en chevaux (auto uniquement). |
| `surface_m2` | DOUBLE | Surface du logement en m² (habitation uniquement). |
| `prime_annuelle` | DECIMAL(12,2) | Prime annuelle du contrat, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `client_id_retenu` | INTEGER | Identifiant du client conservé après rapprochement des doublons. |
| `client_retenu_exclu` | BOOLEAN | Vrai si le client conservé est lui-même en quarantaine. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |

### `prep.int_reglements`

Règlements contrôlés : règles REG_01 à REG_08, dédoublonnage des livraisons (première livraison conservée).

| Colonne | Type | Définition |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant du paiement. |
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_paiement` | DATE | Date du paiement. |
| `montant` | DECIMAL(12,2) | Montant payé, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `mois_livraison` | VARCHAR | Mois du fichier de livraison (AAAA_MM). |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_livraison` | BIGINT | Rang de la livraison d'un paiement (1 = première livraison, conservée ; > 1 = copie écartée). |
| `nb_livraisons` | BIGINT | Nombre de fichiers ayant livré le paiement (2 = livré en double). |
| `sinistre_connu` | BOOLEAN | Vrai si le sinistre du paiement existe. |
| `sinistre_exclu` | BOOLEAN | Vrai si le sinistre du paiement est en quarantaine. |
| `sinistre_date_survenance` | DATE | Date de survenance du sinistre du paiement. |
| `sinistre_statut` | VARCHAR | Statut du sinistre du paiement. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |

### `prep.int_sinistres`

Sinistres contrôlés : règles SIN_01 à SIN_09, cohérence avec la période de couverture et la garantie.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `date_survenance` | DATE | Date de survenance du sinistre. |
| `date_declaration` | DATE | Date de déclaration du sinistre à l'assureur. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `reserve_initiale` | DECIMAL(12,2) | Réserve ouverte à la déclaration, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `contrat_connu` | BOOLEAN | Vrai si le contrat du sinistre existe dans les contrats. |
| `contrat_exclu` | BOOLEAN | Vrai si le contrat du sinistre est en quarantaine. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `contrat_date_effet` | DATE | Date d'effet du contrat du sinistre. |
| `contrat_date_resiliation` | DATE | Date de résiliation du contrat du sinistre. |
| `garantie_compatible` | BOOLEAN | Vrai si la garantie existe pour le produit du contrat. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |

### `prep.stg_audits`

Audits antifraude typés. Vue.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_audit` | DATE | Date de l'audit antifraude. |
| `fraude_confirmee` | INTEGER | Résultat de l'audit : fraude confirmée (vide si non audité). |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `prep.stg_clients`

Clients typés (dates JJ/MM/AAAA, entiers), sans filtrage. Vue.

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `date_naissance` | DATE | Date de naissance du client. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | INTEGER | Consentement à la prospection commerciale (1 = oui). |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `prep.stg_contrats`

Contrats typés (dates, montants), sans filtrage. Vue.

| Colonne | Type | Définition |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `date_effet` | DATE | Date de début de couverture. |
| `date_resiliation` | DATE | Date de fin de couverture (vide si le contrat est en cours). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `franchise` | DOUBLE | Franchise du contrat, en euros. |
| `bonus_malus` | DOUBLE | Coefficient de bonus-malus (auto uniquement). |
| `puissance_cv` | DOUBLE | Puissance fiscale du véhicule en chevaux (auto uniquement). |
| `surface_m2` | DOUBLE | Surface du logement en m² (habitation uniquement). |
| `prime_annuelle` | DECIMAL(12,2) | Prime annuelle du contrat, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `prep.stg_reglements`

Règlements typés, avec le mois de livraison déduit du nom de fichier. Vue.

| Colonne | Type | Définition |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant du paiement. |
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_paiement` | DATE | Date du paiement. |
| `montant` | DECIMAL(12,2) | Montant payé, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `mois_livraison` | VARCHAR | Mois du fichier de livraison (AAAA_MM). |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

### `prep.stg_sinistres`

Sinistres typés, sans filtrage. Vue.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `date_survenance` | DATE | Date de survenance du sinistre. |
| `date_declaration` | DATE | Date de déclaration du sinistre à l'assureur. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `reserve_initiale` | DECIMAL(12,2) | Réserve ouverte à la déclaration, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |

## Schéma `quarantaine`

Lignes écartées avec leur motif.

### `quarantaine.q_audits`

Audits écartés.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_audit` | DATE | Date de l'audit antifraude. |
| `fraude_confirmee` | INTEGER | Résultat de l'audit : fraude confirmée (vide si non audité). |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

### `quarantaine.q_clients`

Fiches clients écartées, avec les règles violées et leur libellé. Rien n'est supprimé sans trace.

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `date_naissance` | DATE | Date de naissance du client. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | INTEGER | Consentement à la prospection commerciale (1 = oui). |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `date_premiere_souscription` | DATE | Date d'effet du premier contrat du client. |
| `est_efface` | BOOLEAN | Vrai si les attributs personnels du client ont été effacés (droit à l'effacement). |
| `client_id_retenu` | INTEGER | Identifiant du client conservé après rapprochement des doublons. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `date_naissance_corrigee` | DATE | Date de naissance après correction (vide si sentinelle ou impossible : règles CLI_02, CLI_03). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

### `quarantaine.q_contrats`

Contrats écartés (prime invalide, dates incohérentes, client inconnu…).

| Colonne | Type | Définition |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `date_effet` | DATE | Date de début de couverture. |
| `date_resiliation` | DATE | Date de fin de couverture (vide si le contrat est en cours). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `franchise` | DOUBLE | Franchise du contrat, en euros. |
| `bonus_malus` | DOUBLE | Coefficient de bonus-malus (auto uniquement). |
| `puissance_cv` | DOUBLE | Puissance fiscale du véhicule en chevaux (auto uniquement). |
| `surface_m2` | DOUBLE | Surface du logement en m² (habitation uniquement). |
| `prime_annuelle` | DECIMAL(12,2) | Prime annuelle du contrat, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `client_id_retenu` | INTEGER | Identifiant du client conservé après rapprochement des doublons. |
| `client_retenu_exclu` | BOOLEAN | Vrai si le client conservé est lui-même en quarantaine. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

### `quarantaine.q_reglements`

Lignes de règlement écartées, dont les copies de paiements livrés deux fois.

| Colonne | Type | Définition |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant du paiement. |
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `date_paiement` | DATE | Date du paiement. |
| `montant` | DECIMAL(12,2) | Montant payé, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `mois_livraison` | VARCHAR | Mois du fichier de livraison (AAAA_MM). |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_livraison` | BIGINT | Rang de la livraison d'un paiement (1 = première livraison, conservée ; > 1 = copie écartée). |
| `nb_livraisons` | BIGINT | Nombre de fichiers ayant livré le paiement (2 = livré en double). |
| `sinistre_connu` | BOOLEAN | Vrai si le sinistre du paiement existe. |
| `sinistre_exclu` | BOOLEAN | Vrai si le sinistre du paiement est en quarantaine. |
| `sinistre_date_survenance` | DATE | Date de survenance du sinistre du paiement. |
| `sinistre_statut` | VARCHAR | Statut du sinistre du paiement. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

### `quarantaine.q_sinistres`

Sinistres écartés (hors couverture, contrat en quarantaine…).

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `date_survenance` | DATE | Date de survenance du sinistre. |
| `date_declaration` | DATE | Date de déclaration du sinistre à l'assureur. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `reserve_initiale` | DECIMAL(12,2) | Réserve ouverte à la déclaration, en euros. |
| `colonnes_illisibles` | VARCHAR[] | Colonnes renseignées en brut mais illisibles dans leur type cible. |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |
| `_date_chargement` | TIMESTAMP | Horodatage de l'exécution d'ingestion qui a chargé la ligne. |
| `rang_id` | BIGINT | Rang de la ligne parmi celles de même identifiant (1 = conservée). |
| `contrat_connu` | BOOLEAN | Vrai si le contrat du sinistre existe dans les contrats. |
| `contrat_exclu` | BOOLEAN | Vrai si le contrat du sinistre est en quarantaine. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `contrat_date_effet` | DATE | Date d'effet du contrat du sinistre. |
| `contrat_date_resiliation` | DATE | Date de résiliation du contrat du sinistre. |
| `garantie_compatible` | BOOLEAN | Vrai si la garantie existe pour le produit du contrat. |
| `anomalies` | VARCHAR[] | Liste des règles de qualité violées par la ligne (voir qualite.regles_qualite). |
| `est_exclu` | BOOLEAN | Vrai si au moins une règle EXCLURE est violée : la ligne part en quarantaine. |
| `motif` | VARCHAR | Règles EXCLURE violées et leur libellé : raison de la mise en quarantaine. |

## Schéma `qualite`

Catalogue et bilan des règles de qualité.

### `qualite.bilan_regles`

Volume constaté pour chaque règle de qualité, y compris les règles sans anomalie.

| Colonne | Type | Définition |
|---|---|---|
| `regle_id` | VARCHAR | Identifiant de la règle de qualité (préfixe = source : CLI, CTR, SIN, REG, AUD). |
| `entite` | VARCHAR | Source contrôlée par la règle. |
| `dimension` | VARCHAR | Dimension de qualité : complétude, unicité, validité, cohérence entre tables, cohérence temporelle. |
| `description` | VARCHAR | Libellé de la règle. |
| `gravite` | VARCHAR | Gravité : CRITIQUE (ligne inexploitable), MAJEURE (fausse un indicateur), MINEURE (exploitable avec réserve). |
| `traitement` | VARCHAR | Traitement : EXCLURE (quarantaine), CORRIGER (valeur corrigée) ou SIGNALER (conservée telle quelle). |
| `volume` | BIGINT | Nombre de lignes concernées par la règle. |
| `lignes_source` | BIGINT | Nombre de lignes de la source contrôlée. |
| `pct_lignes` | DOUBLE | Part des lignes de la source concernées, en %. |

### `qualite.referentiel_garanties`

Garanties autorisées par produit.

| Colonne | Type | Définition |
|---|---|---|
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `libelle` | VARCHAR | Libellé métier. |

### `qualite.regles_qualite`

Catalogue des règles de qualité : dimension, gravité et traitement (EXCLURE, CORRIGER, SIGNALER).

| Colonne | Type | Définition |
|---|---|---|
| `regle_id` | VARCHAR | Identifiant de la règle de qualité (préfixe = source : CLI, CTR, SIN, REG, AUD). |
| `entite` | VARCHAR | Source contrôlée par la règle. |
| `dimension` | VARCHAR | Dimension de qualité : complétude, unicité, validité, cohérence entre tables, cohérence temporelle. |
| `description` | VARCHAR | Libellé de la règle. |
| `gravite` | VARCHAR | Gravité : CRITIQUE (ligne inexploitable), MAJEURE (fausse un indicateur), MINEURE (exploitable avec réserve). |
| `traitement` | VARCHAR | Traitement : EXCLURE (quarantaine), CORRIGER (valeur corrigée) ou SIGNALER (conservée telle quelle). |

## Schéma `core`

Cœur : schéma en étoile.

### `core.client_rapprochement`

Passage de chaque identifiant client du CRM vers l'identifiant conservé après déduplication (clé : empreinte d'e-mail).

| Colonne | Type | Définition |
|---|---|---|
| `client_id_source` | INTEGER | Identifiant présent dans le CRM. |
| `client_id_retenu` | INTEGER | Identifiant conservé (survivant). |
| `est_doublon` | BOOLEAN | Vrai si la fiche a été fusionnée dans une autre. |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |

### `core.dim_client`

Un client par ligne après rapprochement des doublons. Historique de type 1 (valeur courante) ; l'historique est conservé par le snapshot snap_clients.

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant client conservé (clé). |
| `date_naissance` | DATE | Date de naissance, inconnue (NULL) si absente, sentinelle ou impossible (règles CLI_01 à CLI_03). |
| `age_extraction` | BIGINT | Âge en années révolues au 30/06/2025. |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `region` | VARCHAR | Code de région (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | BOOLEAN | Consentement à la prospection commerciale. |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'e-mail, clé de rapprochement des doublons. |
| `nb_fiches_fusionnees` | BIGINT | Nombre de fiches doublons rattachées à ce client. |
| `date_premiere_souscription` | DATE | Date d'effet du premier contrat du client. |
| `est_efface` | BOOLEAN | Vrai si les attributs personnels du client ont été effacés (droit à l'effacement, meta.effacements). |
| `anomalies_signalees` | VARCHAR[] | Règles de qualité signalées ou corrigées sur la fiche (non bloquantes). |

### `core.dim_contrat`

Un contrat valide par ligne. Attributs fixés à la souscription (type 0).

| Colonne | Type | Définition |
|---|---|---|
| `contrat_id` | INTEGER | Identifiant du contrat (clé). |
| `client_id` | INTEGER | Client conservé après rapprochement. |
| `segment_key` | VARCHAR | Segment de risque du contrat. |
| `produit` | VARCHAR | AUTO ou HABITATION. |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `franchise` | DOUBLE | Franchise du contrat, en euros. |
| `bonus_malus` | DOUBLE | Coefficient de bonus-malus (auto uniquement). |
| `puissance_cv` | DOUBLE | Puissance fiscale du véhicule en chevaux (auto uniquement). |
| `surface_m2` | DOUBLE | Surface du logement en m² (habitation uniquement). |
| `prime_annuelle` | DECIMAL(12,2) | Prime annuelle en euros (strictement positive). |
| `date_effet` | DATE | Début de couverture. |
| `date_resiliation` | DATE | Fin de couverture (vide si le contrat est en cours). |
| `date_fin_observation` | DATE | Dernier jour couvert et observé : résiliation ou 30/06/2025. |
| `est_resilie` | BOOLEAN | Vrai si le contrat a une date de résiliation. |
| `annee_souscription` | BIGINT | Année de la date d'effet (cohorte). |
| `jours_couverts` | BIGINT | Durée de couverture observée, bornes incluses. |
| `anomalies_signalees` | VARCHAR[] | Règles de qualité non bloquantes (CORRIGER, SIGNALER) relevées sur la ligne. |

### `core.dim_date`

Calendrier jour par jour, 2019 à 2025.

| Colonne | Type | Définition |
|---|---|---|
| `date_jour` | DATE | Jour (clé). |
| `annee` | BIGINT | Année civile. |
| `trimestre` | BIGINT | Trimestre (1 à 4). |
| `mois` | BIGINT | Premier jour du mois. |
| `annee_mois` | VARCHAR | Mois au format AAAA-MM. |
| `jour_semaine` | BIGINT | Jour de la semaine (1 = lundi, 7 = dimanche). |
| `est_apres_extraction` | BOOLEAN | Vrai après le 30/06/2025 : période non observée. |

### `core.dim_garantie`

Garanties par produit.

| Colonne | Type | Définition |
|---|---|---|
| `garantie_key` | VARCHAR | Clé produit\|garantie. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `libelle` | VARCHAR | Libellé métier de la garantie. |

### `core.dim_segment`

Segment de risque : combinaison produit × zone de risque × formule × canal.

| Colonne | Type | Définition |
|---|---|---|
| `segment_key` | VARCHAR | Clé du segment (empreinte MD5 des attributs). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |

### `core.fct_exposition`

Exposition. Grain : un contrat × une année civile. Base de toute fréquence (sinistres par année-police) et des primes acquises.

| Colonne | Type | Définition |
|---|---|---|
| `exposition_id` | VARCHAR | Clé contrat-année. |
| `contrat_id` | INTEGER | Contrat exposé. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `segment_key` | VARCHAR | Clé du segment (empreinte MD5 des attributs). |
| `annee` | BIGINT | Année civile. |
| `date_debut_periode` | DATE | Premier jour couvert dans l'année. |
| `date_fin_periode` | DATE | Dernier jour couvert dans l'année. |
| `jours_couverts` | BIGINT | Jours couverts dans l'année (bornes incluses). |
| `annees_police` | DOUBLE | Exposition en années-police : jours couverts / 365. |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle × jours couverts / 365. |
| `resilie_dans_annee` | BOOLEAN | Vrai si le contrat a été résilié pendant cette année. |
| `annee_complete` | BOOLEAN | Faux pour 2025, observée jusqu'au 30/06 seulement. |

### `core.fct_reglement`

Règlement. Grain : un paiement (paiement_id). Copies de livraison et paiements de sinistres en quarantaine exclus.

| Colonne | Type | Définition |
|---|---|---|
| `paiement_id` | INTEGER | Identifiant du paiement (clé). |
| `sinistre_id` | INTEGER | Sinistre réglé. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `segment_key` | VARCHAR | Clé du segment (empreinte MD5 des attributs). |
| `garantie_key` | VARCHAR | Garantie mise en jeu. |
| `date_paiement` | DATE | Date du paiement. |
| `montant` | DECIMAL(12,2) | Montant payé en euros. |
| `mois_livraison` | VARCHAR | Mois du fichier de la livraison retenue. |
| `nb_livraisons` | BIGINT | Nombre de fichiers ayant livré ce paiement (2 = livré en double). |
| `_fichier_source` | VARCHAR | Fichier d'origine de la ligne, relatif au dossier des sources. |
| `_numero_ligne` | INTEGER | Numéro de la ligne dans le fichier d'origine (1 = en-tête pour un CSV). |

### `core.fct_sinistre`

Sinistre. Grain : un sinistre valide, avec montants payés, réserve restante, délais et résultat d'audit.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre (clé). |
| `contrat_id` | INTEGER | Contrat sinistré. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `segment_key` | VARCHAR | Clé du segment (empreinte MD5 des attributs). |
| `garantie_key` | VARCHAR | Garantie mise en jeu. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `date_survenance` | DATE | Date de survenance du sinistre. |
| `date_declaration` | DATE | Date de déclaration du sinistre à l'assureur. |
| `annee_survenance` | BIGINT | Année de survenance du sinistre. |
| `statut` | VARCHAR | OUVERT, CLOTURE, REJETE ou SANS_SUITE. |
| `est_sans_suite` | BOOLEAN | Sinistre rejeté ou classé sans suite (aucun paiement). |
| `reserve_initiale` | DECIMAL(12,2) | Réserve ouverte à la déclaration. |
| `montant_paye` | DECIMAL(38,2) | Total des règlements valides. |
| `nb_reglements` | BIGINT | Nombre de paiements du sinistre. |
| `date_premier_reglement` | DATE | Date du premier paiement du sinistre. |
| `date_dernier_reglement` | DATE | Date du dernier paiement du sinistre (date de clôture de substitution). |
| `reserve_restante` | DECIMAL(38,2) | Pour un dossier ouvert : réserve initiale moins montants payés (minimum 0). |
| `charge_totale` | DECIMAL(38,2) | Montant payé + réserve restante. |
| `delai_declaration_j` | BIGINT | Jours entre survenance et déclaration (vide si déclaration antérieure à la survenance, règle SIN_06). |
| `delai_premier_reglement_j` | BIGINT | Jours entre déclaration et premier règlement. |
| `delai_cloture_j` | BIGINT | Pour un dossier clôturé : jours entre déclaration et dernier règlement (date de clôture absente des sources). |
| `est_audite` | BOOLEAN | Vrai si le dossier a été contrôlé par l'antifraude. |
| `date_audit` | DATE | Date de l'audit antifraude. |
| `fraude_confirmee` | BOOLEAN | Résultat de l'audit (vide si non audité). |
| `est_atypique` | BOOLEAN | Réserve initiale supérieure à 1 M€ (règle SIN_08). |
| `anomalies_signalees` | VARCHAR[] | Règles de qualité non bloquantes (CORRIGER, SIGNALER) relevées sur la ligne. |

## Schéma `snapshots`

Historique (type 2) des dimensions.

### `snapshots.snap_clients`

Historique (type 2) des attributs clients : une nouvelle version à chaque changement de région, CSP ou consentement lors d'une livraison du CRM.

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `date_naissance` | DATE | Date de naissance du client. |
| `age_extraction` | BIGINT | Âge en années révolues au 30/06/2025. |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `consent_marketing` | BOOLEAN | Consentement à la prospection commerciale (1 = oui). |
| `email_hash` | VARCHAR | Empreinte pseudonymisée de l'adresse e-mail, clé de rapprochement des doublons. |
| `nb_fiches_fusionnees` | BIGINT | Nombre de fiches doublons rattachées à ce client. |
| `date_premiere_souscription` | DATE | Date d'effet du premier contrat du client. |
| `est_efface` | BOOLEAN | Vrai si les attributs personnels du client ont été effacés (droit à l'effacement). |
| `anomalies_signalees` | VARCHAR[] | Règles de qualité non bloquantes (CORRIGER, SIGNALER) relevées sur la ligne. |
| `dbt_scd_id` | VARCHAR | Identifiant technique de la version (snapshot dbt). |
| `dbt_updated_at` | TIMESTAMP | Date de prise en compte de la version (snapshot dbt). |
| `dbt_valid_from` | TIMESTAMP | Début de validité de la version. |
| `dbt_valid_to` | TIMESTAMP | Fin de validité de la version (vide pour la version courante). |

## Schéma `marts`

Tables d'indicateurs lues par le dashboard et les notebooks.

### `marts.mart_clients`

Un client par ligne : produits détenus, primes acquises, sinistres payés, valeur observée (primes acquises − sinistres payés).

| Colonne | Type | Définition |
|---|---|---|
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `csp` | VARCHAR | Catégorie socioprofessionnelle. |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `nb_contrats` | BIGINT | Nombre de contrats. |
| `produits` | VARCHAR | Produits détenus par le client sur la période (AUTO, HABITATION ou AUTO+HABITATION). |
| `multi_detenteur` | BOOLEAN | Vrai si le client a détenu au moins un contrat auto et un contrat habitation. |
| `canaux` | VARCHAR | Canaux de distribution des contrats du client. |
| `cohorte` | BIGINT | Année de souscription (date d'effet du contrat, ou du premier contrat pour un client). |
| `client_actif` | BOOLEAN | Vrai si le client a au moins un contrat non résilié au 30/06/2025. |
| `annees_police` | DOUBLE | Exposition en années-police : jours couverts / 365. |
| `primes_acquises` | DOUBLE | Primes acquises par le client, 2020 au 30/06/2025. |
| `nb_sinistres` | BIGINT | Sinistres avec suite (ouverts ou clôturés) survenus dans l'année : base de la fréquence et du coût moyen. |
| `sinistres_payes` | DECIMAL(38,2) | Règlements payés sur les sinistres du client, 2020 au 30/06/2025. |
| `valeur_observee` | DOUBLE | Primes acquises moins sinistres payés, de 2020 au 30/06/2025 (réserves non déduites). |

### `marts.mart_contrat_annee`

Base d'analyse au grain contrat × année : exposition, primes acquises, résiliations et sinistres de l'année de survenance. Mesures additives.

| Colonne | Type | Définition |
|---|---|---|
| `exposition_id` | VARCHAR | Clé contrat-année. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `annee` | BIGINT | Année civile. |
| `annee_complete` | BOOLEAN | Faux pour 2025, observée jusqu'au 30/06 seulement. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `annee_souscription` | BIGINT | Année de la date d'effet (cohorte). |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `jours_couverts` | BIGINT | Durée de couverture observée, bornes incluses. |
| `annees_police` | DOUBLE | Exposition en années-police (jours couverts / 365). |
| `prime_acquise` | DOUBLE | Prime acquise sur la période couverte de l'année. |
| `nb_resiliations` | INTEGER | 1 si le contrat est résilié dans l'année. |
| `nb_sinistres_declares` | BIGINT | Sinistres survenus dans l'année, tous statuts. |
| `nb_sinistres` | BIGINT | Sinistres avec suite (ouverts ou clôturés) survenus dans l'année : base de la fréquence et du coût moyen. |
| `nb_sinistres_sans_suite` | BIGINT | Sinistres rejetés ou classés sans suite. |
| `nb_sinistres_atypiques` | BIGINT | Sinistres à réserve initiale supérieure à 1 M€ (règle SIN_08). |
| `montant_paye` | DECIMAL(38,2) | Règlements payés sur les sinistres de l'année. |
| `reserve_restante` | DECIMAL(38,2) | Réserves restantes des sinistres encore ouverts. |
| `charge` | DECIMAL(38,2) | Charge sinistres = payé + réserve restante. |
| `charge_hors_atypique` | DECIMAL(38,2) | Charge hors sinistre atypique (réserve > 1 M€, règle SIN_08). |

### `marts.mart_exploitation_chargements`

État de la chaîne par source (page Exploitation) : dernier chargement, volumes, rejets, échecs et fraîcheur des données.

| Colonne | Type | Définition |
|---|---|---|
| `source` | VARCHAR | Source de données : clients, contrats, sinistres, reglements ou audits. |
| `nb_fichiers` | BIGINT | Nombre de fichiers chargés pour la source. |
| `lignes_lues` | HUGEINT | Lignes de données lues dans le fichier. |
| `lignes_chargees` | HUGEINT | Lignes chargées dans la couche brute. |
| `lignes_rejetees` | HUGEINT | Lignes illisibles envoyées dans raw.rejets_ingestion. |
| `dernier_chargement` | TIMESTAMP | Horodatage du dernier chargement réussi. |
| `dernier_fichier` | VARCHAR | Dernier fichier (par ordre alphabétique) de la version chargée. |
| `dernier_passage` | TIMESTAMP | Dernière exécution ayant traité la source, chargement ou non. |
| `dernier_echec` | TIMESTAMP | Dernier chargement en échec (vide si aucun). |
| `date_metier_max` | DATE | Date métier la plus récente de la source (paiement, déclaration, effet, audit). |

### `marts.mart_exploitation_regles`

Volume par règle de qualité (page Exploitation), copie de qualite.bilan_regles.

| Colonne | Type | Définition |
|---|---|---|
| `regle_id` | VARCHAR | Identifiant de la règle de qualité (préfixe = source : CLI, CTR, SIN, REG, AUD). |
| `entite` | VARCHAR | Source contrôlée par la règle. |
| `dimension` | VARCHAR | Dimension de qualité : complétude, unicité, validité, cohérence entre tables, cohérence temporelle. |
| `description` | VARCHAR | Libellé de la règle. |
| `gravite` | VARCHAR | Gravité : CRITIQUE (ligne inexploitable), MAJEURE (fausse un indicateur), MINEURE (exploitable avec réserve). |
| `traitement` | VARCHAR | Traitement : EXCLURE (quarantaine), CORRIGER (valeur corrigée) ou SIGNALER (conservée telle quelle). |
| `volume` | BIGINT | Nombre de lignes concernées par la règle. |
| `lignes_source` | BIGINT | Nombre de lignes de la source contrôlée. |
| `pct_lignes` | DOUBLE | Part des lignes de la source concernées, en %. |

### `marts.mart_exploitation_tests`

Résultats des tests de la dernière exécution (page Exploitation). Vue sur meta.resultats_tests.

| Colonne | Type | Définition |
|---|---|---|
| `id_execution` | VARCHAR | Identifiant de l'exécution (ingestion ou dbt). |
| `genere_le` | TIMESTAMP | Horodatage de l'exécution des tests. |
| `outil` | VARCHAR | Outil ayant exécuté le test (dbt). |
| `nom` | VARCHAR | Nom du test. |
| `objet` | VARCHAR | Identifiant complet du test dans dbt. |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `echecs` | INTEGER | Nombre de lignes en échec renvoyées par le test. |
| `duree_s` | DOUBLE | Durée du traitement, en secondes. |
| `message` | VARCHAR | Message complémentaire (motif d'échec, fichier homonyme…). |

### `marts.mart_portefeuille_mensuel`

Suivi mensuel (page Portefeuille) : mois × produit × zone × canal × région ; primes acquises, années-police, contrats actifs, résiliations et sinistres du mois de survenance.

| Colonne | Type | Définition |
|---|---|---|
| `mois` | DATE | Premier jour du mois. |
| `annee` | BIGINT | Année civile. |
| `num_mois` | BIGINT | Numéro du mois (1 à 12). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `contrats_actifs` | BIGINT | Contrats couverts le dernier jour du mois (ou au 30/06/2025). |
| `annees_police` | DOUBLE | Exposition du mois en années-police. |
| `prime_acquise` | DOUBLE | Primes acquises dans le mois (prime annuelle × jours couverts dans le mois / 365). |
| `nb_resiliations` | BIGINT | Contrats résiliés dans le mois. |
| `nb_sinistres` | BIGINT | Sinistres avec suite (ouverts ou clôturés) survenus dans l'année : base de la fréquence et du coût moyen. |
| `nb_sinistres_sans_suite` | BIGINT | Sinistres rejetés ou classés sans suite. |
| `montant_paye` | DECIMAL(38,2) | Total des règlements valides. |
| `reserve_restante` | DECIMAL(38,2) | Pour un dossier ouvert : réserve initiale moins montants payés (minimum 0). |
| `charge` | DECIMAL(38,2) | Charge sinistres = payé + réserve restante. |
| `charge_hors_atypique` | DECIMAL(38,2) | Charge hors sinistre atypique (réserve > 1 M€, règle SIN_08). |

### `marts.mart_retention_clients`

Rétention client à un an depuis le 1er janvier 2021 à 2024, selon le nombre de produits détenus (1 ou 2).

| Colonne | Type | Définition |
|---|---|---|
| `date_reference` | DATE | Date de référence (1er janvier) de la mesure de rétention. |
| `nb_produits` | BIGINT | Nombre de produits différents détenus à la date de référence (1 ou 2). |
| `nb_clients` | BIGINT | Nombre de clients. |
| `nb_clients_retenus` | BIGINT | Clients ayant encore au moins un contrat actif un an après la date de référence. |

### `marts.mart_retention_contrats`

Rétention des contrats par cohorte de souscription, produit, détention de l'autre produit à la souscription et ancienneté (1 à 5 ans). Taux = nb_retenus / nb_contrats, valable seulement si cellule_complete.

| Colonne | Type | Définition |
|---|---|---|
| `cohorte` | BIGINT | Année de souscription (date d'effet du contrat, ou du premier contrat pour un client). |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `detenait_autre_produit` | BOOLEAN | Vrai si le client détenait déjà un contrat actif de l'autre produit à la date d'effet. |
| `anciennete_annees` | BIGINT | Ancienneté du contrat, en années révolues depuis la date d'effet. |
| `nb_contrats` | BIGINT | Nombre de contrats. |
| `nb_retenus` | BIGINT | Contrats non résiliés à l'anniversaire considéré. |
| `nb_observables` | BIGINT | Contrats dont l'anniversaire considéré est antérieur au 30/06/2025. |
| `cellule_complete` | BOOLEAN | Vrai si tous les contrats de la cellule ont atteint l'anniversaire avant le 30/06/2025. |

### `marts.mart_sinistres`

Un sinistre valide par ligne, enrichi des attributs du contrat, du client et de la garantie.

| Colonne | Type | Définition |
|---|---|---|
| `sinistre_id` | INTEGER | Identifiant du sinistre. |
| `contrat_id` | INTEGER | Identifiant du contrat. |
| `client_id` | INTEGER | Identifiant pseudonymisé du client (CRM). |
| `segment_key` | VARCHAR | Clé du segment (empreinte MD5 des attributs). |
| `garantie_key` | VARCHAR | Garantie mise en jeu. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `garantie` | VARCHAR | Garantie mise en jeu (RC, COLLISION, BRIS_GLACE, VOL, DEGAT_EAUX, INCENDIE, TEMPETE). |
| `date_survenance` | DATE | Date de survenance du sinistre. |
| `date_declaration` | DATE | Date de déclaration du sinistre à l'assureur. |
| `annee_survenance` | BIGINT | Année de survenance du sinistre. |
| `statut` | VARCHAR | Statut : OUVERT, CLOTURE, REJETE ou SANS_SUITE (sinistres) ; résultat d'un test (exploitation). |
| `est_sans_suite` | BOOLEAN | Sinistre rejeté ou classé sans suite (aucun paiement). |
| `reserve_initiale` | DECIMAL(12,2) | Réserve ouverte à la déclaration, en euros. |
| `montant_paye` | DECIMAL(38,2) | Total des règlements valides. |
| `nb_reglements` | BIGINT | Nombre de paiements du sinistre. |
| `date_premier_reglement` | DATE | Date du premier paiement du sinistre. |
| `date_dernier_reglement` | DATE | Date du dernier paiement du sinistre (date de clôture de substitution). |
| `reserve_restante` | DECIMAL(38,2) | Pour un dossier ouvert : réserve initiale moins montants payés (minimum 0). |
| `charge_totale` | DECIMAL(38,2) | Montant payé + réserve restante. |
| `delai_declaration_j` | BIGINT | Jours entre survenance et déclaration (vide si déclaration antérieure à la survenance, règle SIN_06). |
| `delai_premier_reglement_j` | BIGINT | Jours entre déclaration et premier règlement. |
| `delai_cloture_j` | BIGINT | Pour un dossier clôturé : jours entre déclaration et dernier règlement (date de clôture absente des sources). |
| `est_audite` | BOOLEAN | Vrai si le dossier a été contrôlé par l'antifraude. |
| `date_audit` | DATE | Date de l'audit antifraude. |
| `fraude_confirmee` | BOOLEAN | Résultat de l'audit : fraude confirmée (vide si non audité). |
| `est_atypique` | BOOLEAN | Réserve initiale supérieure à 1 M€ (règle SIN_08). |
| `anomalies_signalees` | VARCHAR[] | Règles de qualité non bloquantes (CORRIGER, SIGNALER) relevées sur la ligne. |
| `anciennete_contrat_j` | BIGINT | Jours entre la date d'effet du contrat et la survenance du sinistre. |
| `delai_audit_j` | BIGINT | Jours entre la déclaration et l'audit. |
| `montant_paye_avant_audit` | DECIMAL(38,2) | Montants payés sur le sinistre avant la date d'audit. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `annee_souscription` | BIGINT | Année de la date d'effet (cohorte). |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `libelle_garantie` | VARCHAR | Libellé métier de la garantie. |

### `marts.mart_technique`

Indicateurs agrégés par année, produit, zone, formule, canal, région et tranche d'âge. Fréquence = nb_sinistres / annees_police ; coût moyen = charge / nb_sinistres ; prime moyenne = prime_acquise / annees_police ; S/P = charge / prime_acquise ; taux de résiliation = nb_resiliations / annees_police.

| Colonne | Type | Définition |
|---|---|---|
| `annee` | BIGINT | Année civile. |
| `annee_complete` | BOOLEAN | Faux pour 2025, observée jusqu'au 30/06 seulement. |
| `produit` | VARCHAR | Produit : AUTO ou HABITATION. |
| `zone_risque` | INTEGER | Zone de risque tarifaire, de 1 (faible) à 5 (élevé). |
| `formule` | VARCHAR | Formule souscrite : ESSENTIELLE, CONFORT ou PREMIUM. |
| `canal_distribution` | VARCHAR | Canal de souscription : AGENT, COURTIER ou WEB. |
| `region` | VARCHAR | Code de la région de résidence (ex. IDF, ARA). |
| `tranche_age` | VARCHAR | 18-25, 26-35, 36-50, 51-65, 66+ ou Inconnu, calculée à la date d'extraction. |
| `nb_contrats_exposes` | BIGINT | Nombre de contrats couverts au moins un jour sur la période. |
| `annees_police` | DOUBLE | Exposition en années-police : jours couverts / 365. |
| `prime_acquise` | DOUBLE | Prime acquise : prime annuelle × jours couverts / 365. |
| `nb_resiliations` | HUGEINT | Contrats résiliés dans le mois. |
| `nb_sinistres_declares` | HUGEINT | Sinistres survenus dans l'année, tous statuts. |
| `nb_sinistres` | HUGEINT | Sinistres avec suite (ouverts ou clôturés) survenus dans l'année : base de la fréquence et du coût moyen. |
| `nb_sinistres_sans_suite` | HUGEINT | Sinistres rejetés ou classés sans suite. |
| `nb_sinistres_atypiques` | HUGEINT | Sinistres à réserve initiale supérieure à 1 M€ (règle SIN_08). |
| `montant_paye` | DECIMAL(38,2) | Total des règlements valides. |
| `reserve_restante` | DECIMAL(38,2) | Pour un dossier ouvert : réserve initiale moins montants payés (minimum 0). |
| `charge` | DECIMAL(38,2) | Charge sinistres = payé + réserve restante. |
| `charge_hors_atypique` | DECIMAL(38,2) | Charge hors sinistre atypique (réserve > 1 M€, règle SIN_08). |

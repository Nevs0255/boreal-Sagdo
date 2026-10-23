# Lignage d'un indicateur : le ratio S/P, de la source au graphique

Exemple suivi : le **S/P annuel** affiché sur la page Portefeuille du dashboard et dans le dossier (livrable 3). Le lignage complet et interactif de toutes les tables est consultable avec `make docs`, puis `dbt docs serve`.

```mermaid
flowchart LR
    subgraph Sources
        F1[contrats/contrats.csv<br/>prime_annuelle, dates]
        F2[sinistres/sinistres.jsonl<br/>réserve, statut, survenance]
        F3[reglements/reglements_AAAA_MM.csv<br/>64 fichiers, montant]
        F4[crm/clients.csv<br/>rattachement client]
    end
    subgraph raw[raw · copie fidèle]
        R1[raw.contrats]
        R2[raw.sinistres]
        R3[raw.reglements]
        R4[raw.clients]
    end
    subgraph prep[prep · typage et contrôles]
        S1[stg_contrats → int_contrats<br/>CTR_04 prime ≤ 0, CTR_05 dates]
        S2[stg_sinistres → int_sinistres<br/>SIN_05 hors couverture]
        S3[stg_reglements → int_reglements<br/>REG_01 doublon de livraison]
        S4[stg_clients → int_clients<br/>CLI_04 doublons]
    end
    subgraph core[core · schéma en étoile]
        D1[dim_contrat]
        E1[fct_exposition<br/>prime_acquise = prime × jours / 365]
        T1[fct_reglement]
        T2[fct_sinistre<br/>charge = payé + réserve restante]
    end
    subgraph marts
        M1[mart_portefeuille_mensuel<br/>Σ charge, Σ prime_acquise]
    end
    G[Dashboard · page Portefeuille<br/>S/P = Σ charge / Σ prime_acquise]

    F1 --> R1 --> S1 --> D1 --> E1 --> M1
    F2 --> R2 --> S2 --> T2
    F3 --> R3 --> S3 --> T1 --> T2 --> M1
    F4 --> R4 --> S4 --> D1
    M1 --> G
    Q[(quarantaine.q_*<br/>lignes écartées + motif)]
    S1 -.-> Q
    S2 -.-> Q
    S3 -.-> Q
```

| Étape | Objet | Transformation | Contrôle |
|---|---|---|---|
| 1 | `contrats.csv`, `sinistres.jsonl`, `reglements_*.csv`, `clients.csv` | Lecture, détection de l'encodage, du séparateur et des en-têtes (`pipeline/ingest.py`) | Journal d'ingestion, rejets de lecture, empreinte SHA-256 |
| 2 | `raw.*` | Copie fidèle en texte, avec fichier, ligne et chargement | `ingestion_sans_echec` |
| 3 | `prep.stg_*` | Typage des dates et des montants | Colonnes illisibles repérées |
| 4 | `prep.int_*` | 36 règles de qualité ; dédoublonnage des clients et des paiements | Quarantaine avec motif, `reconciliation_*` |
| 5 | `core.fct_exposition` | Prime acquise = prime annuelle × jours couverts / 365, par contrat et par année | `exposition_toujours_positive`, `exposition_egale_duree_contrat` |
| 6 | `core.fct_reglement`, `core.fct_sinistre` | Charge = règlements payés + réserve restante des dossiers ouverts | `montant_paye_egal_reglements`, `reconciliation_reglements_brut_coeur` |
| 7 | `marts.mart_portefeuille_mensuel` | Sommes par mois, produit, zone, canal et région | `mart_technique_reconcilie_coeur` (mêmes totaux que le cœur) |
| 8 | Dashboard (`dashboard/app.py`) et notebooks | S/P = Σ charge / Σ primes acquises (`analyse/indicateurs.py`, définition unique) | `tests/test_dashboard.py` |

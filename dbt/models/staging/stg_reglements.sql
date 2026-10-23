select
    try_cast(nullif(trim(paiement_id), '') as integer)         as paiement_id,
    try_cast(nullif(trim(sinistre_id), '') as integer)         as sinistre_id,
    try_cast(nullif(trim(date_paiement), '') as date)          as date_paiement,
    try_cast(nullif(trim(montant), '') as decimal(12, 2))      as montant,
    -- Mois de livraison déduit du nom de fichier (reglements_AAAA_MM.csv)
    regexp_extract(_fichier_source, 'reglements_(\d{4}_\d{2})', 1) as mois_livraison,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'reglements') }}

select
    try_cast(nullif(trim(contrat_id), '') as integer)          as contrat_id,
    try_cast(nullif(trim(client_id), '') as integer)           as client_id,
    nullif(trim(produit), '')                                   as produit,
    try_cast(nullif(trim(date_effet), '') as date)             as date_effet,
    try_cast(nullif(trim(date_resiliation), '') as date)       as date_resiliation,
    nullif(trim(formule), '')                                   as formule,
    nullif(trim(canal_distribution), '')                        as canal_distribution,
    try_cast(nullif(trim(zone_risque), '') as integer)         as zone_risque,
    try_cast(nullif(trim(franchise), '') as double)            as franchise,
    try_cast(nullif(trim(bonus_malus), '') as double)          as bonus_malus,
    try_cast(nullif(trim(puissance_cv), '') as double)         as puissance_cv,
    try_cast(nullif(trim(surface_m2), '') as double)           as surface_m2,
    try_cast(nullif(trim(prime_annuelle), '') as double)       as prime_annuelle,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'contrats') }}

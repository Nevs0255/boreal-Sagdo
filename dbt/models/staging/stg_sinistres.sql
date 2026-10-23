select
    try_cast(nullif(trim(sinistre_id), '') as integer)         as sinistre_id,
    try_cast(nullif(trim(contrat_id), '') as integer)          as contrat_id,
    try_cast(nullif(trim(date_survenance), '') as date)        as date_survenance,
    try_cast(nullif(trim(date_declaration), '') as date)       as date_declaration,
    nullif(trim(garantie), '')                                  as garantie,
    nullif(trim(statut), '')                                    as statut,
    try_cast(nullif(trim(reserve_initiale), '') as double)     as reserve_initiale,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'sinistres') }}

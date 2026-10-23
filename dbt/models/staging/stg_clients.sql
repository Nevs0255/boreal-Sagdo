-- Typage des clients. Les contrôles de qualité et la déduplication sont faits en couche cœur.
select
    try_cast(nullif(trim(client_id), '') as integer)                      as client_id,
    try_strptime(nullif(trim(date_naissance), ''), '%d/%m/%Y')::date      as date_naissance,
    nullif(trim(region), '')                                               as region,
    nullif(trim(csp), '')                                                  as csp,
    try_cast(nullif(trim(consent_marketing), '') as integer)              as consent_marketing,
    nullif(trim(email_hash), '')                                           as email_hash,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'clients') }}

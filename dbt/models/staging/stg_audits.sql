select
    try_cast(nullif(trim(sinistre_id), '') as integer)         as sinistre_id,
    try_cast(nullif(trim(date_audit), '') as date)             as date_audit,
    try_cast(nullif(trim(fraude_confirmee), '') as integer)    as fraude_confirmee,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'audits') }}

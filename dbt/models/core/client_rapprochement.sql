-- Table de passage : chaque identifiant client du CRM vers l'identifiant conservé.
select
    client_id         as client_id_source,
    client_id_retenu,
    client_id <> client_id_retenu as est_doublon,
    email_hash
from {{ ref('int_clients') }}
where rang_id = 1 and client_id is not null

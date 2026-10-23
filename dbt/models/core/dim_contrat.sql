-- Dimension contrat. Les attributs sont ceux de la souscription (type 0 : non historisés).
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

select
    contrat_id,
    client_id_retenu                                                   as client_id,
    md5(concat_ws('|', produit, zone_risque, formule, canal_distribution)) as segment_key,
    produit,
    formule,
    canal_distribution,
    zone_risque,
    franchise,
    bonus_malus,
    puissance_cv,
    surface_m2,
    prime_annuelle,
    date_effet,
    date_resiliation,
    -- Dernier jour couvert et observé (bornes incluses)
    least(coalesce(date_resiliation, {{ extraction }}), {{ extraction }}) as date_fin_observation,
    date_resiliation is not null                                       as est_resilie,
    year(date_effet)                                                   as annee_souscription,
    least(coalesce(date_resiliation, {{ extraction }}), {{ extraction }}) - date_effet + 1 as jours_couverts,
    anomalies                                                          as anomalies_signalees
from {{ ref('int_contrats') }}
where not est_exclu

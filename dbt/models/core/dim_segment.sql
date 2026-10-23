-- Segment de risque : combinaison produit × zone × formule × canal.
select distinct
    md5(concat_ws('|', produit, zone_risque, formule, canal_distribution)) as segment_key,
    produit,
    zone_risque,
    formule,
    canal_distribution
from {{ ref('int_contrats') }}
where not est_exclu

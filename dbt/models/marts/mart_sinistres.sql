-- Un sinistre valide par ligne avec les attributs de son contrat et de son client
-- (distribution des coûts, délais, audits).
select
    s.*,
    k.zone_risque,
    k.formule,
    k.canal_distribution,
    k.annee_souscription,
    c.region,
    c.tranche_age,
    g.libelle as libelle_garantie
from {{ ref('fct_sinistre') }} s
join {{ ref('dim_contrat') }} k using (contrat_id)
join {{ ref('dim_client') }} c on c.client_id = s.client_id
join {{ ref('dim_garantie') }} g using (garantie_key)

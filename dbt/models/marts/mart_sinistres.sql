-- Un sinistre valide par ligne avec les attributs de son contrat et de son client
-- (distribution des coûts, délais, audits).
with paye_avant_audit as (
    select r.sinistre_id, sum(r.montant) as montant_paye_avant_audit
    from {{ ref('fct_reglement') }} r
    join {{ ref('fct_sinistre') }} s using (sinistre_id)
    where s.est_audite and r.date_paiement < s.date_audit
    group by r.sinistre_id
)

select
    s.*,
    s.date_survenance - k.date_effet                       as anciennete_contrat_j,
    s.date_audit - s.date_declaration                      as delai_audit_j,
    coalesce(p.montant_paye_avant_audit, 0)               as montant_paye_avant_audit,
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
left join paye_avant_audit p using (sinistre_id)

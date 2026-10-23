-- Base d'analyse technique. Grain : un contrat × une année civile (identique à fct_exposition).
-- Les sinistres sont rattachés à leur année de survenance. Toutes les mesures sont additives :
-- n'importe quel regroupement donne des ratios exacts (somme des numérateurs / somme des dénominateurs).
with sinistres as (
    select
        contrat_id,
        annee_survenance                                            as annee,
        count(*)                                                    as nb_sinistres_declares,
        count(*) filter (where not est_sans_suite)                  as nb_sinistres,
        count(*) filter (where est_sans_suite)                      as nb_sinistres_sans_suite,
        count(*) filter (where est_atypique)                        as nb_sinistres_atypiques,
        sum(montant_paye)                                           as montant_paye,
        sum(reserve_restante)                                       as reserve_restante,
        sum(charge_totale)                                          as charge,
        sum(charge_totale) filter (where est_atypique)              as charge_atypique
    from {{ ref('fct_sinistre') }}
    group by all
)

select
    e.exposition_id,
    e.contrat_id,
    e.client_id,
    e.annee,
    e.annee_complete,
    k.produit,
    k.zone_risque,
    k.formule,
    k.canal_distribution,
    k.annee_souscription,
    c.region,
    c.tranche_age,
    e.jours_couverts,
    e.annees_police,
    e.prime_acquise,
    e.resilie_dans_annee::int                                       as nb_resiliations,
    coalesce(s.nb_sinistres_declares, 0)                            as nb_sinistres_declares,
    coalesce(s.nb_sinistres, 0)                                     as nb_sinistres,
    coalesce(s.nb_sinistres_sans_suite, 0)                          as nb_sinistres_sans_suite,
    coalesce(s.nb_sinistres_atypiques, 0)                           as nb_sinistres_atypiques,
    coalesce(s.montant_paye, 0)                                     as montant_paye,
    coalesce(s.reserve_restante, 0)                                 as reserve_restante,
    coalesce(s.charge, 0)                                           as charge,
    coalesce(s.charge, 0) - coalesce(s.charge_atypique, 0)          as charge_hors_atypique
from {{ ref('fct_exposition') }} e
join {{ ref('dim_contrat') }} k using (contrat_id)
join {{ ref('dim_client') }} c on c.client_id = e.client_id
left join sinistres s on s.contrat_id = e.contrat_id and s.annee = e.annee

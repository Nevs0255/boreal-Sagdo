-- Suivi mensuel du portefeuille pour le dashboard.
-- Grain : mois × produit × zone × canal × région. Mesures additives.
-- Sinistres rattachés à leur mois de survenance ; primes acquises et années-police au prorata
-- des jours couverts dans le mois ; contrats actifs = couverts le dernier jour observé du mois.
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with mois as (
    select m::date as debut_mois, (m + interval 1 month - interval 1 day)::date as fin_mois
    from generate_series(timestamp '2020-01-01', {{ extraction }}::timestamp, interval 1 month) as t(m)
),

couverture as (
    select
        m.debut_mois,
        k.contrat_id,
        k.client_id,
        k.produit,
        k.zone_risque,
        k.canal_distribution,
        k.prime_annuelle,
        k.date_resiliation,
        least(k.date_fin_observation, m.fin_mois) - greatest(k.date_effet, m.debut_mois) + 1 as jours,
        k.date_effet <= least(m.fin_mois, {{ extraction }}) and k.date_fin_observation >= least(m.fin_mois, {{ extraction }}) as actif_fin_mois
    from {{ ref('dim_contrat') }} k
    join mois m on k.date_effet <= m.fin_mois and k.date_fin_observation >= m.debut_mois
),

expositions as (
    select
        c.debut_mois, c.produit, c.zone_risque, c.canal_distribution, cl.region,
        count(*) filter (where c.actif_fin_mois)                                as contrats_actifs,
        sum(c.jours) / 365.0                                                    as annees_police,
        sum(c.prime_annuelle * c.jours / 365.0)                                 as prime_acquise,
        count(*) filter (where date_trunc('month', c.date_resiliation) = c.debut_mois) as nb_resiliations
    from couverture c
    join {{ ref('dim_client') }} cl on cl.client_id = c.client_id
    group by all
),

sinistres as (
    select
        date_trunc('month', s.date_survenance)::date as debut_mois,
        s.produit, k.zone_risque, k.canal_distribution, cl.region,
        count(*) filter (where not s.est_sans_suite)   as nb_sinistres,
        count(*) filter (where s.est_sans_suite)       as nb_sinistres_sans_suite,
        sum(s.montant_paye)                            as montant_paye,
        sum(s.reserve_restante)                        as reserve_restante,
        sum(s.charge_totale)                           as charge,
        sum(s.charge_totale) filter (where not s.est_atypique) as charge_hors_atypique
    from {{ ref('fct_sinistre') }} s
    join {{ ref('dim_contrat') }} k using (contrat_id)
    join {{ ref('dim_client') }} cl on cl.client_id = s.client_id
    group by all
)

select
    e.debut_mois                                    as mois,
    year(e.debut_mois)                              as annee,
    month(e.debut_mois)                             as num_mois,
    e.produit, e.zone_risque, e.canal_distribution, e.region,
    e.contrats_actifs,
    e.annees_police,
    e.prime_acquise,
    e.nb_resiliations,
    coalesce(s.nb_sinistres, 0)                     as nb_sinistres,
    coalesce(s.nb_sinistres_sans_suite, 0)          as nb_sinistres_sans_suite,
    coalesce(s.montant_paye, 0)                     as montant_paye,
    coalesce(s.reserve_restante, 0)                 as reserve_restante,
    coalesce(s.charge, 0)                           as charge,
    coalesce(s.charge_hors_atypique, 0)             as charge_hors_atypique
from expositions e
left join sinistres s using (debut_mois, produit, zone_risque, canal_distribution, region)

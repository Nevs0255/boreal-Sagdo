-- Indicateurs techniques agrégés. Grain : année × produit × zone × formule × canal × région × tranche d'âge.
-- Mesures additives : les ratios se recalculent à n'importe quel niveau d'agrégation.
select
    annee, annee_complete, produit, zone_risque, formule, canal_distribution, region, tranche_age,
    count(*)                       as nb_contrats_exposes,
    sum(annees_police)             as annees_police,
    sum(prime_acquise)             as prime_acquise,
    sum(nb_resiliations)           as nb_resiliations,
    sum(nb_sinistres_declares)     as nb_sinistres_declares,
    sum(nb_sinistres)              as nb_sinistres,
    sum(nb_sinistres_sans_suite)   as nb_sinistres_sans_suite,
    sum(nb_sinistres_atypiques)    as nb_sinistres_atypiques,
    sum(montant_paye)              as montant_paye,
    sum(reserve_restante)          as reserve_restante,
    sum(charge)                    as charge,
    sum(charge_hors_atypique)      as charge_hors_atypique
from {{ ref('mart_contrat_annee') }}
group by all

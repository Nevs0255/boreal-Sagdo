-- Fait exposition. Grain : un contrat × une année civile de couverture.
-- annees_police = jours couverts dans l'année / 365 ; prime acquise au prorata des jours couverts.
-- L'année {{ var('date_extraction')[:4] }} n'est observée que jusqu'au {{ var('date_extraction') }} (annee_complete = false).
with annees as (
    select
        k.*,
        unnest(generate_series(year(k.date_effet), year(k.date_fin_observation))) as annee
    from {{ ref('dim_contrat') }} k
),

bornes as (
    select
        *,
        greatest(date_effet, make_date(annee, 1, 1))          as date_debut_periode,
        least(date_fin_observation, make_date(annee, 12, 31)) as date_fin_periode
    from annees
)

select
    contrat_id || '-' || annee                              as exposition_id,
    contrat_id,
    client_id,
    segment_key,
    annee,
    date_debut_periode,
    date_fin_periode,
    date_fin_periode - date_debut_periode + 1               as jours_couverts,
    (date_fin_periode - date_debut_periode + 1) / 365.0     as annees_police,
    round(prime_annuelle * (date_fin_periode - date_debut_periode + 1) / 365.0, 2) as prime_acquise,
    est_resilie and year(date_resiliation) = annee          as resilie_dans_annee,
    annee < {{ var('date_extraction')[:4] }}                 as annee_complete
from bornes

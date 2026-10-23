-- Rétention client à un an, mesurée à des dates de référence (1er janvier) :
-- parmi les clients ayant au moins un contrat actif à la date de référence, part de ceux qui
-- ont encore au moins un contrat actif un an plus tard, selon le nombre de produits détenus.
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with dates_reference as (
    select make_date(a::int, 1, 1) as date_reference from range(2021, 2025) as t(a)
),

actifs as (
    select r.date_reference, k.client_id, count(distinct k.produit) as nb_produits
    from dates_reference r
    join {{ ref('dim_contrat') }} k
      on k.date_effet <= r.date_reference
     and coalesce(k.date_resiliation, {{ extraction }}) >= r.date_reference
    group by all
),

un_an_apres as (
    select distinct r.date_reference, k.client_id
    from dates_reference r
    join {{ ref('dim_contrat') }} k
      on k.date_effet <= r.date_reference + interval 1 year
     and coalesce(k.date_resiliation, {{ extraction }}) >= r.date_reference + interval 1 year
)

select
    a.date_reference,
    a.nb_produits,
    count(*)                              as nb_clients,
    count(u.client_id)                    as nb_clients_retenus
from actifs a
left join un_an_apres u using (date_reference, client_id)
group by all

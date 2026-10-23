-- Rétention empirique des contrats par cohorte annuelle de souscription et par produit.
-- Un contrat est « retenu » à l'ancienneté n s'il n'est pas résilié à son n-ième anniversaire.
-- Une cellule n'est complète que si TOUS les contrats de la cohorte ont atteint cet
-- anniversaire avant la date d'extraction (sinon la rétention serait biaisée).
-- detenait_autre_produit : le client détenait déjà un contrat actif de l'autre produit
-- à la date d'effet (multi-détention à la souscription, connue sans regarder le futur).
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with contrats as (
    select
        a.*,
        exists (
            select 1 from {{ ref('dim_contrat') }} b
            where b.client_id = a.client_id and b.produit <> a.produit
              and b.date_effet <= a.date_effet
              and coalesce(b.date_resiliation, {{ extraction }}) >= a.date_effet
        ) as detenait_autre_produit
    from {{ ref('dim_contrat') }} a
),

anniversaires as (
    select
        c.*,
        t.n as anciennete_annees,
        c.date_effet + to_years(t.n::int) as date_anniversaire
    from contrats c, range(1, 6) as t(n)
)

select
    annee_souscription                                   as cohorte,
    produit,
    detenait_autre_produit,
    anciennete_annees,
    count(*)                                             as nb_contrats,
    count(*) filter (where date_resiliation is null or date_resiliation > date_anniversaire) as nb_retenus,
    count(*) filter (where date_anniversaire <= {{ extraction }}) as nb_observables,
    max(date_anniversaire) <= {{ extraction }}           as cellule_complete
from anniversaires
group by all

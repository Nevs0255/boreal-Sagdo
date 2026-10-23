-- Réconciliation brut -> cœur : chaque paiement identifiable de la couche brute est présent
-- une et une seule fois dans le cœur, avec le même total (le test échoue s'il renvoie une ligne).
with brut as (
    select count(distinct paiement_id) as nb, sum(montant) as total
    from (
        select paiement_id, any_value(montant) as montant
        from {{ ref('stg_reglements') }}
        where paiement_id is not null
        group by paiement_id
    )
),
coeur as (
    select count(*) as nb, sum(montant) as total from {{ ref('fct_reglement') }}
)
select brut.nb as nb_brut, coeur.nb as nb_coeur, brut.total as total_brut, coeur.total as total_coeur
from brut, coeur
where brut.nb <> coeur.nb or brut.total <> coeur.total

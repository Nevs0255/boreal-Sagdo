-- Chaque ligne de règlement brute se retrouve soit dans le cœur, soit en quarantaine,
-- et les montants se réconcilient au centime (le test échoue s'il renvoie une ligne).
with brut as (
    select count(*) as nb, sum(try_cast(montant as decimal(12, 2))) as total from {{ source('raw', 'reglements') }}
),
coeur as (select count(*) as nb, sum(montant) as total from {{ ref('fct_reglement') }}),
quarantaine as (select count(*) as nb, coalesce(sum(montant), 0) as total from {{ ref('q_reglements') }})
select brut.nb, coeur.nb as nb_coeur, quarantaine.nb as nb_quarantaine, brut.total, coeur.total + quarantaine.total as total_reconcilie
from brut, coeur, quarantaine
where brut.nb <> coeur.nb + quarantaine.nb
   or brut.total <> coeur.total + quarantaine.total

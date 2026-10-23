-- Les marts restituent exactement les totaux du cœur (primes acquises, années-police, charge).
with mart as (
    select sum(prime_acquise) as primes, sum(annees_police) as ap, sum(charge) as charge, sum(nb_sinistres_declares) as nb
    from {{ ref('mart_technique') }}
),
coeur as (
    select
        (select sum(prime_acquise) from {{ ref('fct_exposition') }}) as primes,
        (select sum(annees_police) from {{ ref('fct_exposition') }}) as ap,
        (select sum(charge_totale) from {{ ref('fct_sinistre') }}) as charge,
        (select count(*) from {{ ref('fct_sinistre') }}) as nb
)
select * from mart, coeur
where abs(mart.primes - coeur.primes) > 0.01 or abs(mart.ap - coeur.ap) > 1e-6
   or mart.charge <> coeur.charge or mart.nb <> coeur.nb

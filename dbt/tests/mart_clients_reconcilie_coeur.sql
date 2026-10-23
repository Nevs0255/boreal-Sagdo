-- La valeur client totale égale primes acquises − sinistres payés du cœur.
select *
from (select sum(primes_acquises) as primes, sum(sinistres_payes) as payes from {{ ref('mart_clients') }}) m,
     (select (select sum(prime_acquise) from {{ ref('fct_exposition') }}) as primes,
             (select sum(montant) from {{ ref('fct_reglement') }}) as payes) c
where abs(m.primes - c.primes) > 0.01 or m.payes <> c.payes

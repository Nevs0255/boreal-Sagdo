-- Valeur observée par client : primes acquises moins sinistres payés, de 2020 au 30/06/2025.
-- Les réserves des dossiers ouverts ne sont pas déduites (valeur observée, pas projetée).
with expositions as (
    select client_id, sum(prime_acquise) as primes_acquises, sum(annees_police) as annees_police
    from {{ ref('fct_exposition') }}
    group by client_id
),

sinistres as (
    select client_id,
           count(*) filter (where not est_sans_suite) as nb_sinistres,
           sum(montant_paye)                           as sinistres_payes
    from {{ ref('fct_sinistre') }}
    group by client_id
),

contrats as (
    select
        client_id,
        count(*)                                        as nb_contrats,
        bool_or(produit = 'AUTO') and bool_or(produit = 'HABITATION') as multi_detenteur,
        string_agg(distinct produit, '+' order by produit) as produits,
        string_agg(distinct canal_distribution, '+' order by canal_distribution) as canaux,
        min(date_effet)                                 as date_premiere_souscription,
        bool_or(date_resiliation is null)               as client_actif
    from {{ ref('dim_contrat') }}
    group by client_id
)

select
    c.client_id,
    cl.region,
    cl.csp,
    cl.tranche_age,
    c.nb_contrats,
    c.produits,
    c.multi_detenteur,
    c.canaux,
    year(c.date_premiere_souscription)                  as cohorte,
    c.client_actif,
    e.annees_police,
    e.primes_acquises,
    coalesce(s.nb_sinistres, 0)                         as nb_sinistres,
    coalesce(s.sinistres_payes, 0)                      as sinistres_payes,
    e.primes_acquises - coalesce(s.sinistres_payes, 0)  as valeur_observee
from contrats c
join {{ ref('dim_client') }} cl using (client_id)
join expositions e using (client_id)
left join sinistres s using (client_id)

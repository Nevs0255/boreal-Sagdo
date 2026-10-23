-- Pour chaque source : lignes brutes = lignes du cœur + lignes en quarantaine.
with comptes as (
    select 'clients' as entite,
        (select count(*) from {{ source('raw', 'clients') }}) as brut,
        (select count(*) from {{ ref('dim_client') }}) as coeur,
        (select count(*) from {{ ref('q_clients') }}) as quarantaine
    union all select 'contrats',
        (select count(*) from {{ source('raw', 'contrats') }}),
        (select count(*) from {{ ref('dim_contrat') }}),
        (select count(*) from {{ ref('q_contrats') }})
    union all select 'sinistres',
        (select count(*) from {{ source('raw', 'sinistres') }}),
        (select count(*) from {{ ref('fct_sinistre') }}),
        (select count(*) from {{ ref('q_sinistres') }})
    union all select 'audits',
        (select count(*) from {{ source('raw', 'audits') }}),
        (select count(*) from {{ ref('fct_sinistre') }} where est_audite),
        (select count(*) from {{ ref('q_audits') }})
)
select * from comptes where brut <> coeur + quarantaine

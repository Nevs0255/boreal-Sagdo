-- Volume constaté par règle de qualité (0 compris), pour le dossier et la page Exploitation.
with violations as (
    select 'clients' as entite, unnest(anomalies) as regle_id from {{ ref('int_clients') }}
    union all select 'contrats', unnest(anomalies) from {{ ref('int_contrats') }}
    union all select 'sinistres', unnest(anomalies) from {{ ref('int_sinistres') }}
    union all select 'reglements', unnest(anomalies) from {{ ref('int_reglements') }}
    union all select 'audits', unnest(anomalies) from {{ ref('int_audits') }}
),

volumes_source as (
    select 'clients' as entite, count(*) as lignes_source from {{ ref('int_clients') }}
    union all select 'contrats', count(*) from {{ ref('int_contrats') }}
    union all select 'sinistres', count(*) from {{ ref('int_sinistres') }}
    union all select 'reglements', count(*) from {{ ref('int_reglements') }}
    union all select 'audits', count(*) from {{ ref('int_audits') }}
),

comptes as (
    select regle_id, count(*) as volume from violations group by regle_id
)

select
    r.regle_id,
    r.entite,
    r.dimension,
    r.description,
    r.gravite,
    r.traitement,
    coalesce(c.volume, 0) as volume,
    s.lignes_source,
    round(100.0 * coalesce(c.volume, 0) / s.lignes_source, 2) as pct_lignes
from {{ ref('regles_qualite') }} r
left join comptes c using (regle_id)
join volumes_source s on s.entite = r.entite
order by r.regle_id

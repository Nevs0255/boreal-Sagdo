-- Toute ligne en quarantaine porte un motif et reste traçable jusqu'à son fichier source.
select 'clients' as entite, _fichier_source, _numero_ligne from {{ ref('q_clients') }} where motif is null or _fichier_source is null
union all select 'contrats', _fichier_source, _numero_ligne from {{ ref('q_contrats') }} where motif is null or _fichier_source is null
union all select 'sinistres', _fichier_source, _numero_ligne from {{ ref('q_sinistres') }} where motif is null or _fichier_source is null
union all select 'reglements', _fichier_source, _numero_ligne from {{ ref('q_reglements') }} where motif is null or _fichier_source is null
union all select 'audits', _fichier_source, _numero_ligne from {{ ref('q_audits') }} where motif is null or _fichier_source is null

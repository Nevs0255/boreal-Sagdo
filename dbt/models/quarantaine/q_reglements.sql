-- Lignes écartées de la source reglements, retrouvables avec leur fichier, leur ligne et leur motif.
select
    i.*,
    (
        select string_agg(r.regle_id || ' : ' || r.description, ' | ' order by r.regle_id)
        from {{ ref('regles_qualite') }} r
        where list_contains(i.anomalies, r.regle_id) and r.traitement = 'EXCLURE'
    ) as motif
from {{ ref('int_reglements') }} i
where i.est_exclu

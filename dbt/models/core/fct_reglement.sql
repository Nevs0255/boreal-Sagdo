-- Fait règlement : un paiement par ligne (grain = paiement_id).
--
-- Chargement incrémental idempotent :
-- - à chaque exécution, on ne traite que les paiements touchés par un chargement
--   postérieur au dernier traitement (nouveau mois, ou mois rechargé) ;
-- - pour ces paiements, la version retenue est recalculée sur TOUTE la couche brute
--   (règle de survie : la première livraison, puis le plus petit numéro de ligne),
--   puis remplace l'éventuelle version existante (delete+insert sur paiement_id).
-- Rejouer un mois produit donc exactement le même résultat qu'un chargement complet.
{{ config(
    materialized='incremental',
    unique_key='paiement_id',
    incremental_strategy='delete+insert'
) }}

with brut as (
    select * from {{ ref('stg_reglements') }}
    where paiement_id is not null
),

{% if is_incremental() %}
touches as (
    select distinct paiement_id
    from brut
    where _date_chargement > (select coalesce(max(_maj_le), '1900-01-01'::timestamp) from {{ this }})
),
candidats as (
    select brut.* from brut join touches using (paiement_id)
),
{% else %}
candidats as (
    select * from brut
),
{% endif %}

classes as (
    select
        *,
        count(*) over (partition by paiement_id)              as nb_livraisons,
        max(_date_chargement) over (partition by paiement_id) as _maj_le,
        row_number() over (
            partition by paiement_id
            order by mois_livraison, _fichier_source, _numero_ligne
        ) as rang
    from candidats
)

select
    paiement_id,
    sinistre_id,
    date_paiement,
    montant,
    mois_livraison,
    nb_livraisons,
    _fichier_source,
    _numero_ligne,
    _maj_le
from classes
where rang = 1

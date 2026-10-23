{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with contrats as (
    select
        *,
        row_number() over (partition by contrat_id order by _numero_ligne) as rang_id
    from {{ ref('stg_contrats') }}
),

clients as (
    select client_id, client_id_retenu from {{ ref('int_clients') }} where rang_id = 1
),

survivants as (
    select client_id, est_exclu from {{ ref('int_clients') }} where rang_id = 1
),

enrichis as (
    select
        k.*,
        c.client_id_retenu,
        s.est_exclu as client_retenu_exclu
    from contrats k
    left join clients c on c.client_id = k.client_id
    left join survivants s on s.client_id = c.client_id_retenu
),

controles as (
    select
        *,
        {{ anomalies({
            'CTR_01': "rang_id > 1",
            'CTR_02': "contrat_id is null or client_id is null or date_effet is null or prime_annuelle is null
                       or franchise is null or len(colonnes_illisibles) > 0
                       or produit not in ('AUTO', 'HABITATION')
                       or formule not in ('ESSENTIELLE', 'CONFORT', 'PREMIUM')
                       or canal_distribution not in ('AGENT', 'COURTIER', 'WEB')
                       or zone_risque not between 1 and 5",
            'CTR_03': "client_id_retenu is null or client_retenu_exclu",
            'CTR_04': "prime_annuelle <= 0",
            'CTR_05': "date_resiliation < date_effet",
            'CTR_06': "date_resiliation = date_effet",
            'CTR_07': "(produit = 'AUTO' and (puissance_cv is null or bonus_malus is null))
                       or (produit = 'HABITATION' and surface_m2 is null)",
            'CTR_08': "date_effet > " ~ extraction,
        }) }} as anomalies
    from enrichis
)

select *, {{ est_exclu() }} as est_exclu
from controles

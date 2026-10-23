with audits as (
    select
        *,
        row_number() over (partition by sinistre_id order by date_audit, _numero_ligne) as rang_id
    from {{ ref('stg_audits') }}
),

sinistres as (
    select sinistre_id, date_declaration, est_exclu from {{ ref('int_sinistres') }} where rang_id = 1
),

controles as (
    select
        a.*,
        {{ anomalies({
            'AUD_01': "a.rang_id > 1",
            'AUD_02': "a.sinistre_id is null or a.date_audit is null or a.fraude_confirmee not in (0, 1)
                       or a.fraude_confirmee is null or len(a.colonnes_illisibles) > 0",
            'AUD_03': "s.sinistre_id is null or s.est_exclu",
            'AUD_04': "a.date_audit < s.date_declaration",
        }) }} as anomalies
    from audits a
    left join sinistres s using (sinistre_id)
)

select *, {{ est_exclu() }} as est_exclu
from controles

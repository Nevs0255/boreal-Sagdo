{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with sinistres as (
    select
        *,
        row_number() over (partition by sinistre_id order by _numero_ligne) as rang_id
    from {{ ref('stg_sinistres') }}
),

contrats as (
    select contrat_id, produit, date_effet, date_resiliation, est_exclu
    from {{ ref('int_contrats') }}
    where rang_id = 1
),

enrichis as (
    select
        s.*,
        k.contrat_id is not null as contrat_connu,
        k.est_exclu as contrat_exclu,
        k.produit,
        k.date_effet as contrat_date_effet,
        k.date_resiliation as contrat_date_resiliation,
        g.garantie is not null as garantie_compatible
    from sinistres s
    left join contrats k using (contrat_id)
    left join {{ ref('referentiel_garanties') }} g on g.produit = k.produit and g.garantie = s.garantie
),

controles as (
    select
        *,
        {{ anomalies({
            'SIN_01': "rang_id > 1",
            'SIN_02': "sinistre_id is null or contrat_id is null or date_survenance is null or date_declaration is null
                       or reserve_initiale is null or len(colonnes_illisibles) > 0
                       or statut not in ('OUVERT', 'CLOTURE', 'REJETE', 'SANS_SUITE')",
            'SIN_03': "not contrat_connu",
            'SIN_04': "contrat_connu and contrat_exclu",
            'SIN_05': "date_survenance < contrat_date_effet
                       or date_survenance > coalesce(contrat_date_resiliation, " ~ extraction ~ ")
                       or date_survenance > " ~ extraction,
            'SIN_06': "date_declaration < date_survenance",
            'SIN_07': "contrat_connu and not garantie_compatible",
            'SIN_08': "reserve_initiale > " ~ var('seuil_reserve_atypique'),
            'SIN_09': "statut in ('REJETE', 'SANS_SUITE') and reserve_initiale > 0",
        }) }} as anomalies
    from enrichis
)

select *, {{ est_exclu() }} as est_exclu
from controles

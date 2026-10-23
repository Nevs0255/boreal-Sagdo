-- Clients contrôlés et rapprochés.
-- Clé de rapprochement : empreinte d'e-mail (email_hash). Règle de survie : parmi les fiches
-- partageant une empreinte, on conserve celle qui porte des contrats, puis le plus petit
-- identifiant. Les autres fiches sont rattachées au survivant (client_id_retenu) et exclues.
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with clients as (
    select
        *,
        row_number() over (partition by client_id order by _numero_ligne) as rang_id
    from {{ ref('stg_clients') }}
),

premiere_souscription as (
    select client_id, min(date_effet) as date_premiere_souscription
    from {{ ref('stg_contrats') }}
    group by client_id
),

enrichis as (
    select
        c.*,
        p.date_premiere_souscription,
        e.client_id is not null as est_efface,
        case
            when e.client_id is not null then e.client_id_retenu
            when c.email_hash is null or c.client_id is null then c.client_id
            else first_value(c.client_id) over (
                partition by c.email_hash
                order by (p.client_id is not null) desc, c.client_id
            )
        end as client_id_retenu
    from clients c
    left join premiere_souscription p using (client_id)
    left join {{ source('meta', 'effacements') }} e on e.client_id = c.client_id
),

controles as (
    select
        *,
        {{ anomalies({
            'CLI_01': "date_naissance is null and not list_contains(colonnes_illisibles, 'date_naissance')",
            'CLI_02': "date_naissance < " ~ extraction ~ " - interval 120 year",
            'CLI_03': "date_naissance + interval 18 year > " ~ extraction,
            'CLI_04': "client_id_retenu <> client_id",
            'CLI_05': "rang_id > 1",
            'CLI_06': "not est_efface and (client_id is null or email_hash is null or len(colonnes_illisibles) > 0
                       or region not in ('ARA','BFC','BRE','COR','CVL','GES','HDF','IDF','NAQ','NOR','OCC','PACA','PDL')
                       or csp not in ('AGRICULTEUR','CADRE','EMPLOYE','ETUDIANT','INDEPENDANT','OUVRIER','RETRAITE','SANS_ACTIVITE')
                       or consent_marketing not in (0, 1))",
            'CLI_07': "date_naissance + interval 18 year > date_premiere_souscription
                       and date_naissance + interval 18 year <= " ~ extraction,
        }) }} as anomalies
    from enrichis
)

select
    *,
    -- Correction : une date sentinelle ou impossible devient inconnue (âge non calculable).
    case when list_has_any(anomalies, ['CLI_02', 'CLI_03']) then null else date_naissance end as date_naissance_corrigee,
    {{ est_exclu() }} as est_exclu
from controles

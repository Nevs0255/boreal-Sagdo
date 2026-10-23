-- Dimension client (une ligne par client conservé après rapprochement).
-- Historique : type 1 (valeur courante). La source ne livre qu'un instantané du CRM ;
-- l'historique des changements est constitué à partir de maintenant par le snapshot snap_clients.
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with fusions as (
    select client_id_retenu, count(*) - 1 as nb_fiches_fusionnees
    from {{ ref('client_rapprochement') }}
    group by client_id_retenu
)

select
    c.client_id,
    c.date_naissance_corrigee                                       as date_naissance,
    date_diff('year', c.date_naissance_corrigee, {{ extraction }})
        - case when strftime(c.date_naissance_corrigee, '%m-%d') > strftime({{ extraction }}, '%m-%d') then 1 else 0 end
                                                                     as age_extraction,
    {{ tranche_age("date_diff('year', c.date_naissance_corrigee, " ~ extraction ~ ")
        - case when strftime(c.date_naissance_corrigee, '%m-%d') > strftime(" ~ extraction ~ ", '%m-%d') then 1 else 0 end") }}
                                                                     as tranche_age,
    c.region,
    c.csp,
    c.consent_marketing = 1                                          as consent_marketing,
    c.email_hash,
    coalesce(f.nb_fiches_fusionnees, 0)                              as nb_fiches_fusionnees,
    c.date_premiere_souscription,
    c.est_efface,
    c.anomalies                                                      as anomalies_signalees
from {{ ref('int_clients') }} c
left join fusions f on f.client_id_retenu = c.client_id
where not c.est_exclu

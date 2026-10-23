-- Règlements contrôlés. Un paiement livré dans plusieurs fichiers mensuels garde sa première
-- livraison (mois le plus ancien, puis numéro de ligne) ; les copies suivantes sont écartées (REG_01).
{% set extraction = "date '" ~ var('date_extraction') ~ "'" %}

with reglements as (
    select
        *,
        row_number() over (
            partition by paiement_id
            order by mois_livraison, _fichier_source, _numero_ligne
        ) as rang_livraison,
        count(*) over (partition by paiement_id) as nb_livraisons
    from {{ ref('stg_reglements') }}
),

sinistres as (
    select sinistre_id, date_survenance, statut, est_exclu
    from {{ ref('int_sinistres') }}
    where rang_id = 1
),

enrichis as (
    select
        r.*,
        s.sinistre_id is not null as sinistre_connu,
        s.est_exclu as sinistre_exclu,
        s.date_survenance as sinistre_date_survenance,
        s.statut as sinistre_statut
    from reglements r
    left join sinistres s using (sinistre_id)
),

controles as (
    select
        *,
        {{ anomalies({
            'REG_01': "paiement_id is not null and rang_livraison > 1",
            'REG_02': "paiement_id is null or sinistre_id is null or date_paiement is null or montant is null
                       or len(colonnes_illisibles) > 0",
            'REG_03': "sinistre_id is not null and not sinistre_connu",
            'REG_04': "sinistre_connu and sinistre_exclu",
            'REG_05': "montant <= 0",
            'REG_06': "date_paiement < sinistre_date_survenance or date_paiement > " ~ extraction,
            'REG_07': "mois_livraison > strftime(" ~ extraction ~ ", '%Y_%m')",
            'REG_08': "sinistre_statut in ('REJETE', 'SANS_SUITE')",
        }) }} as anomalies
    from enrichis
)

select *, {{ est_exclu() }} as est_exclu
from controles

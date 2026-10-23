-- Fait sinistre. Grain : un sinistre. Montants payés et délais calculés depuis fct_reglement.
-- Les dates de clôture n'existent pas dans les sources : pour un sinistre clôturé, la date
-- du dernier règlement sert de date de clôture.
with paiements as (
    select
        sinistre_id,
        sum(montant)       as montant_paye,
        count(*)           as nb_reglements,
        min(date_paiement) as date_premier_reglement,
        max(date_paiement) as date_dernier_reglement
    from {{ ref('fct_reglement') }}
    group by sinistre_id
),

audits as (
    select sinistre_id, date_audit, fraude_confirmee = 1 as fraude_confirmee
    from {{ ref('int_audits') }}
    where not est_exclu
)

select
    s.sinistre_id,
    s.contrat_id,
    k.client_id,
    k.segment_key,
    k.produit || '|' || s.garantie                           as garantie_key,
    k.produit,
    s.garantie,
    s.date_survenance,
    s.date_declaration,
    year(s.date_survenance)                                  as annee_survenance,
    s.statut,
    s.statut in ('REJETE', 'SANS_SUITE')                     as est_sans_suite,
    s.reserve_initiale,
    coalesce(p.montant_paye, 0)                              as montant_paye,
    coalesce(p.nb_reglements, 0)                             as nb_reglements,
    p.date_premier_reglement,
    p.date_dernier_reglement,
    -- Réserve restante : uniquement pour un dossier encore ouvert
    case when s.statut = 'OUVERT' then greatest(s.reserve_initiale - coalesce(p.montant_paye, 0), 0) else 0 end
                                                             as reserve_restante,
    coalesce(p.montant_paye, 0)
        + case when s.statut = 'OUVERT' then greatest(s.reserve_initiale - coalesce(p.montant_paye, 0), 0) else 0 end
                                                             as charge_totale,
    case when not list_contains(s.anomalies, 'SIN_06') then s.date_declaration - s.date_survenance end
                                                             as delai_declaration_j,
    p.date_premier_reglement - s.date_declaration            as delai_premier_reglement_j,
    case when s.statut = 'CLOTURE' then p.date_dernier_reglement - s.date_declaration end
                                                             as delai_cloture_j,
    a.sinistre_id is not null                                as est_audite,
    a.date_audit,
    a.fraude_confirmee,
    list_contains(s.anomalies, 'SIN_08')                     as est_atypique,
    s.anomalies                                              as anomalies_signalees
from {{ ref('int_sinistres') }} s
join {{ ref('dim_contrat') }} k on k.contrat_id = s.contrat_id
left join paiements p on p.sinistre_id = s.sinistre_id
left join audits a on a.sinistre_id = s.sinistre_id
where not s.est_exclu

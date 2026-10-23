-- Fait règlement. Grain : un paiement (paiement_id), copies de livraison et paiements
-- de sinistres en quarantaine exclus (voir quarantaine.q_reglements).
select
    r.paiement_id,
    r.sinistre_id,
    s.contrat_id,
    k.client_id,
    k.segment_key,
    k.produit || '|' || s.garantie   as garantie_key,
    r.date_paiement,
    r.montant,
    r.mois_livraison,
    r.nb_livraisons,
    r._fichier_source,
    r._numero_ligne
from {{ ref('int_reglements') }} r
join {{ ref('int_sinistres') }} s on s.sinistre_id = r.sinistre_id and s.rang_id = 1
join {{ ref('dim_contrat') }} k on k.contrat_id = s.contrat_id
where not r.est_exclu

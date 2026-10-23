-- Le montant payé d'un sinistre égale la somme de ses règlements dans le cœur.
select s.sinistre_id, s.montant_paye, coalesce(sum(r.montant), 0) as total_reglements
from {{ ref('fct_sinistre') }} s
left join {{ ref('fct_reglement') }} r using (sinistre_id)
group by s.sinistre_id, s.montant_paye
having s.montant_paye <> coalesce(sum(r.montant), 0)

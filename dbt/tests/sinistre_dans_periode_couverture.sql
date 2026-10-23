-- Un sinistre du cœur survient pendant la couverture observée de son contrat.
select s.sinistre_id, s.date_survenance, k.date_effet, k.date_fin_observation
from {{ ref('fct_sinistre') }} s
join {{ ref('dim_contrat') }} k using (contrat_id)
where s.date_survenance < k.date_effet or s.date_survenance > k.date_fin_observation

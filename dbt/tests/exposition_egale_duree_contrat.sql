-- La somme des expositions annuelles d'un contrat égale sa durée de couverture observée.
select k.contrat_id, k.jours_couverts, sum(e.jours_couverts) as jours_exposes
from {{ ref('dim_contrat') }} k
left join {{ ref('fct_exposition') }} e using (contrat_id)
group by k.contrat_id, k.jours_couverts
having sum(e.jours_couverts) is distinct from k.jours_couverts

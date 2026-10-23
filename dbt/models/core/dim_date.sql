-- Calendrier jour par jour couvrant l'historique (2019-2025).
select
    d::date                                    as date_jour,
    year(d)                                    as annee,
    quarter(d)                                 as trimestre,
    month(d)                                   as mois,
    strftime(d, '%Y-%m')                       as annee_mois,
    isodow(d)                                  as jour_semaine,
    d::date > date '{{ var("date_extraction") }}' as est_apres_extraction
from generate_series(timestamp '2019-01-01', timestamp '2025-12-31', interval 1 day) as t(d)

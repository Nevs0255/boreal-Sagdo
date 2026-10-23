-- Toute ligne d'exposition couvre au moins un jour et au plus une année civile.
select * from {{ ref('fct_exposition') }}
where jours_couverts <= 0 or annees_police <= 0 or jours_couverts > 366 or prime_acquise <= 0

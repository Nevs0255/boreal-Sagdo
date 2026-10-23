{% set colonnes = {'paiement_id': 'integer', 'sinistre_id': 'integer', 'date_paiement': 'date',
                   'montant': 'decimal(12, 2)'} %}
select
    {% for col, type in colonnes.items() -%}
    {{ convertir(col, type) }} as {{ col }},
    {% endfor -%}
    {{ colonnes_illisibles(colonnes) }} as colonnes_illisibles,
    -- Mois de livraison déduit du nom de fichier (reglements_AAAA_MM.csv)
    regexp_extract(_fichier_source, 'reglements_(\d{4}_\d{2})', 1) as mois_livraison,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'reglements') }}

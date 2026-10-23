{% set colonnes = {'contrat_id': 'integer', 'client_id': 'integer', 'produit': 'texte', 'date_effet': 'date',
                   'date_resiliation': 'date', 'formule': 'texte', 'canal_distribution': 'texte',
                   'zone_risque': 'integer', 'franchise': 'double', 'bonus_malus': 'double',
                   'puissance_cv': 'double', 'surface_m2': 'double', 'prime_annuelle': 'decimal(12, 2)'} %}
select
    {% for col, type in colonnes.items() -%}
    {{ convertir(col, type) }} as {{ col }},
    {% endfor -%}
    {{ colonnes_illisibles(colonnes) }} as colonnes_illisibles,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'contrats') }}

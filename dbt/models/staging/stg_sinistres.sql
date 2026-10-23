{% set colonnes = {'sinistre_id': 'integer', 'contrat_id': 'integer', 'date_survenance': 'date',
                   'date_declaration': 'date', 'garantie': 'texte', 'statut': 'texte',
                   'reserve_initiale': 'decimal(12, 2)'} %}
select
    {% for col, type in colonnes.items() -%}
    {{ convertir(col, type) }} as {{ col }},
    {% endfor -%}
    {{ colonnes_illisibles(colonnes) }} as colonnes_illisibles,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'sinistres') }}

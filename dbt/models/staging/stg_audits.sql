{% set colonnes = {'sinistre_id': 'integer', 'date_audit': 'date', 'fraude_confirmee': 'integer'} %}
select
    {% for col, type in colonnes.items() -%}
    {{ convertir(col, type) }} as {{ col }},
    {% endfor -%}
    {{ colonnes_illisibles(colonnes) }} as colonnes_illisibles,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'audits') }}

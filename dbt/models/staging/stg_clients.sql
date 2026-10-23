-- Typage des clients, sans filtrage : les contrôles sont faits dans int_clients.
{% set colonnes = {'client_id': 'integer', 'date_naissance': 'date_fr', 'region': 'texte', 'csp': 'texte',
                   'consent_marketing': 'integer', 'email_hash': 'texte'} %}
select
    {% for col, type in colonnes.items() -%}
    {{ convertir(col, type) }} as {{ col }},
    {% endfor -%}
    {{ colonnes_illisibles(colonnes) }} as colonnes_illisibles,
    _fichier_source, _numero_ligne, _date_chargement
from {{ source('raw', 'clients') }}

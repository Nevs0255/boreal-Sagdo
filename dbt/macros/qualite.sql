-- Conversion texte -> type cible. 'date_fr' = JJ/MM/AAAA.
{% macro convertir(col, type) -%}
    {%- if type == 'date_fr' -%}
        try_strptime(nullif(trim({{ col }}), ''), '%d/%m/%Y')::date
    {%- elif type == 'texte' -%}
        nullif(trim({{ col }}), '')
    {%- else -%}
        try_cast(nullif(trim({{ col }}), '') as {{ type }})
    {%- endif -%}
{%- endmacro %}

-- Liste des colonnes renseignées en brut mais illisibles dans leur type cible.
{% macro colonnes_illisibles(colonnes) -%}
    list_filter([
    {%- for col, type in colonnes.items() %}
        case when nullif(trim({{ col }}), '') is not null and {{ convertir(col, type) }} is null then '{{ col }}' end{{ "," if not loop.last }}
    {%- endfor %}
    ], x -> x is not null)
{%- endmacro %}

-- Construit la liste des règles violées à partir de paires (règle, condition).
{% macro anomalies(regles) -%}
    list_filter([
    {%- for regle_id, condition in regles.items() %}
        case when coalesce({{ condition }}, false) then '{{ regle_id }}' end{{ "," if not loop.last }}
    {%- endfor %}
    ], x -> x is not null)
{%- endmacro %}

-- Vrai si au moins une des règles violées a pour traitement EXCLURE.
{% macro est_exclu(colonne='anomalies') -%}
    list_has_any({{ colonne }}, (select list(regle_id) from {{ ref('regles_qualite') }} where traitement = 'EXCLURE'))
{%- endmacro %}

-- Tranche d'âge métier.
{% macro tranche_age(age) -%}
    case
        when {{ age }} is null then 'Inconnu'
        when {{ age }} < 26 then '18-25'
        when {{ age }} < 36 then '26-35'
        when {{ age }} < 51 then '36-50'
        when {{ age }} < 66 then '51-65'
        else '66+'
    end
{%- endmacro %}

-- Utilise le schéma déclaré (prep, core, marts) tel quel, sans préfixe de cible.
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}

-- Garanties par produit (la garantie VOL existe en auto et en habitation).
select
    produit || '|' || garantie as garantie_key,
    produit,
    garantie,
    libelle
from {{ ref('referentiel_garanties') }}

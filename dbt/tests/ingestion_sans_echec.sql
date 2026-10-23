-- Le dernier passage de chaque fichier dans le journal n'est pas en échec.
select fichier, statut, message
from {{ source('meta', 'journal_ingestion') }}
qualify row_number() over (partition by fichier order by debut desc) = 1
  and statut = 'ECHEC'

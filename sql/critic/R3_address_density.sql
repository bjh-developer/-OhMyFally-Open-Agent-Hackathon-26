-- Critic, R3 address-density check: how many distinct ACRA entities are registered at the same block, street and postal code
-- as each supplier flagged by R3, plus the unit-level fields (to spot groups whose level/unit is missing).
-- Params: {{uens}} = comma-separated quoted UENs (validated by the Critic).
WITH t AS (
  SELECT uen, postal_code, upper(block) AS blk, upper(street_name) AS street, level_no, unit_no
  FROM ACRA_FILES.entities
  WHERE uen IN ({{uens}})
)
SELECT t.uen, t.level_no, t.unit_no, t.postal_code, count(DISTINCT e.uen) AS n_entities
FROM t
JOIN ACRA_FILES.entities e
  ON e.postal_code = t.postal_code AND upper(e.block) = t.blk AND upper(e.street_name) = t.street
GROUP BY t.uen, t.level_no, t.unit_no, t.postal_code

"""R5 preparation validation. All runtime source reads go through Zetaris."""
from __future__ import annotations

import json
import math

PAIRS_SQL = """SELECT DISTINCT a.tender_description, e.primary_ssic_description AS ssic_description
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN ACRA_FILES.entities e ON e.uen = x.uen
WHERE x.confidence >= 0.92
  AND length(trim(a.tender_description)) >= 10
  AND length(trim(e.primary_ssic_description)) >= 10
  AND lower(trim(a.tender_description)) NOT IN ('not applicable', 'not available')
  AND lower(trim(e.primary_ssic_description)) NOT IN ('not applicable', 'not available')"""


class R5PreparationError(RuntimeError):
    pass


def validate_scores(params: dict, pairs: list[dict]) -> None:
    if not params.get("prepared") or not params.get("model") or not isinstance(params.get("similarities"), list):
        raise R5PreparationError("R5 similarities are missing; run scripts/prepare_r5.py after seeding and resolving")
    threshold = params.get("max_similarity")
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise R5PreparationError("R5 similarity threshold is missing or invalid")
    scores = {}
    for row in params["similarities"]:
        key = (row["tender_description"], row["ssic_description"])
        value = float(row["similarity"])
        if key in scores or not math.isfinite(value) or not -1.000001 <= value <= 1.000001:
            raise R5PreparationError("R5 similarity preparation contains invalid or duplicate scores")
        scores[key] = value
    if any((row["tender_description"], row["ssic_description"]) not in scores for row in pairs):
        raise R5PreparationError("R5 similarities are stale or incomplete; rerun scripts/prepare_r5.py")


def require_prepared(run_sql, *, agency, date_from, date_to) -> list[str]:
    from .runner import render
    metadata = run_sql("SELECT params FROM gebiz_pg.rules WHERE flag_id = 'R5'")
    if len(metadata.rows) != 1:
        raise R5PreparationError("R5 rule configuration is missing")
    pairs = run_sql(render(PAIRS_SQL + "\nAND a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}",
                           agency=agency, date_from=date_from, date_to=date_to))
    validate_scores(json.loads(metadata.rows[0][0]), pairs.dicts())
    return [metadata.query_id, pairs.query_id]

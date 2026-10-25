#!/usr/bin/env python3
"""Evaluate model-led candidate decisions against a separately human-adjudicated gold set."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import terrafar_candidate_ledger as candidate_ledger
from terrafar_model_executor import atomic_private_json, safe_private_directory


GOLD_LABELS = {"relevant", "not_relevant"}
PREDICTIONS = {"relevant": "relevant", "not_relevant": "not_relevant"}


def _utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0


def load_gold(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("gold_reference_must_be_json_array")
    gold: dict[str, dict[str, Any]] = {}
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("gold_reference_row_must_be_object")
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.startswith("tcand-") or candidate_id in gold:
            raise ValueError("gold_reference_candidate_identity_missing_or_duplicated")
        if row.get("adjudicator_type") != "human" or not isinstance(row.get("adjudicator"), str) or not row["adjudicator"].strip():
            raise ValueError(f"gold_reference_requires_independent_human_adjudicator:{candidate_id}")
        if row.get("label") not in GOLD_LABELS or not _utc_timestamp(row.get("adjudicated_at")):
            raise ValueError(f"gold_reference_label_or_time_invalid:{candidate_id}")
        evidence = row.get("evidence")
        if (not isinstance(evidence, list) or not evidence
                or any(not isinstance(item, dict)
                       or not all(isinstance(item.get(key), str) and item[key].strip()
                                  for key in ("url", "claim", "quote", "locator"))
                       for item in evidence)):
            raise ValueError(f"gold_reference_requires_url_quote_and_locator:{candidate_id}")
        gold[candidate_id] = row
    return gold


def evaluate(ledger_path: Path, gold_path: Path | None = None,
             output_dir: Path | None = None) -> dict[str, Any]:
    ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
    if gold_path is None:
        report = {"format": "terrafar-independent-eval-v1", "status": "not_evaluable",
                  "reason": "no_independent_human_gold_file_supplied", "gold_count": 0,
                  "precision": None, "recall": None, "specificity": None,
                  "note": "Model self-review, generated tests, and task counts are not independent evaluation labels."}
    else:
        gold = load_gold(gold_path)
        cells = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        unresolved = 0
        missing_prediction = 0
        for candidate_id, reference in gold.items():
            task = ledger.get("tasks", {}).get(candidate_id)
            latest = task.get("review_history", [])[-1] if task and task.get("review_history") else None
            prediction = None
            if (latest and task and latest.get("candidate_fingerprint") == task.get("content_fingerprint")):
                finding = latest.get("finding") if isinstance(latest.get("finding"), dict) else {}
                relevance = finding.get("scope_relevance")
                evidence = latest.get("evidence") if isinstance(latest.get("evidence"), list) else []
                evidence_index = relevance.get("evidence_index") if isinstance(relevance, dict) else None
                evidence_bound = (isinstance(evidence_index, int) and 0 <= evidence_index < len(evidence)
                                  and isinstance(evidence[evidence_index], dict)
                                  and evidence[evidence_index].get("field") == "scope_relevance"
                                  and isinstance(evidence[evidence_index].get("quote"), str)
                                  and bool(evidence[evidence_index]["quote"].strip())
                                  and isinstance(evidence[evidence_index].get("page_content_sha256"), str))
                if evidence_bound:
                    evidence_bound = evidence[evidence_index]["page_content_sha256"] == finding.get("snapshot_sha256")
                if (isinstance(relevance, dict) and relevance.get("status") == "supported"
                        and evidence_bound):
                    prediction = PREDICTIONS.get(str(relevance.get("normalized_value", "")).casefold())
            if prediction is None:
                unresolved += 1
                missing_prediction += task is None
                continue
            actual = reference["label"]
            if prediction == "relevant" and actual == "relevant":
                cells["tp"] += 1
            elif prediction == "relevant":
                cells["fp"] += 1
            elif actual == "relevant":
                cells["fn"] += 1
            else:
                cells["tn"] += 1
        precision_den = cells["tp"] + cells["fp"]
        recall_den = cells["tp"] + cells["fn"]
        specificity_den = cells["tn"] + cells["fp"]
        report = {"format": "terrafar-independent-eval-v1",
                  "status": "scored" if precision_den and recall_den else "insufficient_scored_denominator",
                  "gold_count": len(gold), "scored_count": sum(cells.values()),
                  "unresolved_gold_count": unresolved, "gold_ids_missing_from_ledger": missing_prediction,
                  "confusion": cells,
                  "precision": cells["tp"] / precision_den if precision_den else None,
                  "recall": cells["tp"] / recall_den if recall_den else None,
                  "specificity": cells["tn"] / specificity_den if specificity_den else None,
                  "gold_source_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest(),
                  "metric_scope": "binary relevance among independently human-adjudicated items; duplicate and unresolved decisions are not forced into either class"}
    if output_dir:
        private = safe_private_directory(output_dir)
        atomic_private_json(private / "independent_eval.json", report)
        report["output_directory"] = str(private)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--gold")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = evaluate(Path(args.ledger).resolve(), Path(args.gold).resolve() if args.gold else None,
                      Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

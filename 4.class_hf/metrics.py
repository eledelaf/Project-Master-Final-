#!/usr/bin/env python3
"""
Evaluate protest/not-protest classifier against human labels in MongoDB.

Outputs:
- N
- TP, FP, TN, FN  (positive class = PROTEST)
- Accuracy, Precision, Recall, F1
- F0.5 (F-beta with beta=0.5)

It tries to auto-detect the human label field among common names.
It uses the model prediction primarily from hf_reason ("-> PROTEST"/"-> NOT_PROTEST"),
falling back to hf_label_name when hf_reason is missing.

You can optionally export a per-document CSV report.
"""

from __future__ import annotations

import re
import csv
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

from pymongo import MongoClient


# ----------------------------
# Config (edit these)
# ----------------------------
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"


# Your human-labelled collection (often "sample_texts" in your project)
EVAL_COLLECTION = "sample_texts"

# If you *know* the field name for the human label, set it here and leave AUTO_DETECT=True.
HUMAN_LABEL_FIELD = None  # e.g. "human_label_name" or "human_label"
AUTO_DETECT_HUMAN_FIELD = True

# Export per-doc report
EXPORT_CSV = True
CSV_PATH = "eval_report_protest_classifier.csv"


# ----------------------------
# Helpers
# ----------------------------
HUMAN_FIELD_CANDIDATES = [
    "human_label_name",
    "human_label",
    "gold_label_name",
    "gold_label",
    "manual_label_name",
    "manual_label",
    "true_label_name",
    "true_label",
    "label_name",
    "label",
    "is_protest_human",
    "human_is_protest",
]

def to_binary_label(val: Any) -> Optional[int]:
    """
    Convert various label formats to binary:
    PROTEST -> 1, NOT_PROTEST -> 0
    Returns None if it cannot interpret.
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)) and val in (0, 1):
        return int(val)
    if isinstance(val, str):
        s = val.strip().upper()
        # common strings
        if "NOT" in s and "PROTEST" in s:
            return 0
        if "PROTEST" in s:
            return 1
        if s in ("0", "NO", "FALSE"):
            return 0
        if s in ("1", "YES", "TRUE"):
            return 1
    return None

def get_human_label(doc: Dict[str, Any], human_field: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    """Return (binary_label, field_used)."""
    if human_field:
        return to_binary_label(doc.get(human_field)), human_field

    if not AUTO_DETECT_HUMAN_FIELD:
        return None, None

    for f in HUMAN_FIELD_CANDIDATES:
        if f in doc:
            y = to_binary_label(doc.get(f))
            if y is not None:
                return y, f
    return None, None

def parse_prediction_from_hf_reason(hf_reason: Any) -> Optional[int]:
    """
    Parse final decision from hf_reason if it contains '-> PROTEST' or '-> NOT_PROTEST'.
    """
    if not isinstance(hf_reason, str):
        return None
    m = re.search(r"->\s*(PROTEST|NOT[_\s]?PROTEST)\b", hf_reason, flags=re.IGNORECASE)
    if not m:
        return None
    outcome = m.group(1).upper().replace(" ", "_")
    return 1 if outcome == "PROTEST" else 0

def get_model_prediction(doc: Dict[str, Any]) -> Tuple[Optional[int], str]:
    """
    Prefer hf_reason arrow outcome (your threshold-based final decision),
    else fall back to hf_label_name.
    """
    y_pred = parse_prediction_from_hf_reason(doc.get("hf_reason"))
    if y_pred is not None:
        return y_pred, "hf_reason"

    # fallback
    y_pred = to_binary_label(doc.get("hf_label_name"))
    if y_pred is not None:
        return y_pred, "hf_label_name"

    # last fallback: hf_label could be 0/1 in some pipelines
    y_pred = to_binary_label(doc.get("hf_label"))
    if y_pred is not None:
        return y_pred, "hf_label"

    return None, "missing"

def safe_div(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0

def fbeta(precision: float, recall: float, beta: float) -> float:
    """
    F-beta score from precision/recall.
    beta < 1 weights precision more; beta > 1 weights recall more.
    """
    if precision == 0 and recall == 0:
        return 0.0
    b2 = beta * beta
    return (1 + b2) * precision * recall / (b2 * precision + recall)

@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

def update_confusion(conf: Confusion, y_true: int, y_pred: int) -> None:
    if y_true == 1 and y_pred == 1:
        conf.tp += 1
    elif y_true == 0 and y_pred == 1:
        conf.fp += 1
    elif y_true == 0 and y_pred == 0:
        conf.tn += 1
    elif y_true == 1 and y_pred == 0:
        conf.fn += 1

def main() -> None:
    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][EVAL_COLLECTION]

    # Pull only docs that *look* evaluable:
    # - must have some human label field
    # - must have either hf_reason or hf_label_name
    # (We still validate in code.)
    query = {
        "$or": [{"hf_reason": {"$exists": True}}, {"hf_label_name": {"$exists": True}}, {"hf_label": {"$exists": True}}],
    }

    projection = {
        "_id": 1,
        "title": 1,
        "paper": 1,
        "publish_date": 1,
        "hf_reason": 1,
        "hf_label_name": 1,
        "hf_label": 1,
    }
    # Also project all human label candidates so auto-detect can work
    for f in HUMAN_FIELD_CANDIDATES:
        projection[f] = 1
    if HUMAN_LABEL_FIELD:
        projection[HUMAN_LABEL_FIELD] = 1

    docs = list(col.find(query, projection))

    conf = Confusion()
    used_human_field_counts: Dict[str, int] = {}
    used_pred_field_counts: Dict[str, int] = {}

    rows_for_csv: List[Dict[str, Any]] = []

    n_total = 0
    n_used = 0
    n_skipped_no_human = 0
    n_skipped_no_pred = 0

    for doc in docs:
        n_total += 1

        y_true, human_field_used = get_human_label(doc, HUMAN_LABEL_FIELD)
        if y_true is None:
            n_skipped_no_human += 1
            continue

        y_pred, pred_source = get_model_prediction(doc)
        if y_pred is None:
            n_skipped_no_pred += 1
            continue

        n_used += 1
        used_human_field_counts[human_field_used] = used_human_field_counts.get(human_field_used, 0) + 1
        used_pred_field_counts[pred_source] = used_pred_field_counts.get(pred_source, 0) + 1

        update_confusion(conf, y_true, y_pred)

        if EXPORT_CSV:
            rows_for_csv.append({
                "url": doc.get("_id"),
                "title": doc.get("title"),
                "paper": doc.get("paper"),
                "publish_date": doc.get("publish_date"),
                "y_true": y_true,
                "y_pred": y_pred,
                "human_field_used": human_field_used,
                "pred_source": pred_source,
                "hf_label_name": doc.get("hf_label_name"),
                "hf_reason": doc.get("hf_reason"),
            })

    # Metrics
    tp, fp, tn, fn = conf.tp, conf.fp, conf.tn, conf.fn
    accuracy = safe_div(tp + tn, tp + tn + fp + fn)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = fbeta(precision, recall, beta=1.0)
    f05 = fbeta(precision, recall, beta=0.5)

    print("\n=== Evaluation summary (positive class = PROTEST) ===")
    print(f"Total docs scanned: {n_total}")
    print(f"Used in evaluation: {n_used}")
    print(f"Skipped (no human label): {n_skipped_no_human}")
    print(f"Skipped (no prediction fields): {n_skipped_no_pred}")

    print("\nHuman label fields used:")
    for k, v in sorted(used_human_field_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\nPrediction source used:")
    for k, v in sorted(used_pred_field_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\nConfusion matrix counts:")
    print(f"  TP: {tp}")
    print(f"  FP: {fp}")
    print(f"  TN: {tn}")
    print(f"  FN: {fn}")

    print("\nMetrics:")
    print(f"  Accuracy:  {accuracy:.3f}")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1:        {f1:.3f}")
    print(f"  F0.5:      {f05:.3f}")

    if EXPORT_CSV:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_for_csv[0].keys()) if rows_for_csv else [])
            if rows_for_csv:
                w.writeheader()
                w.writerows(rows_for_csv)
        print(f"\nSaved per-document report to: {CSV_PATH}")

if __name__ == "__main__":
    main()

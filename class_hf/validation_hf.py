import os
import sys
import subprocess
from pymongo.mongo_client import MongoClient
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
COLLECTION_NAME = "sample_texts"
#COLLECTION_NAME = "Texts"

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COLLECTION_NAME]


def compute_metrics(tp, fp, tn, fn):
    total = tp + fp + tn + fn

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    # F1
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    # F0.5  (beta = 0.5 -> beta^2 = 0.25)
    beta2 = 0.25
    denom = beta2 * precision + recall
    f05 = (
        (1 + beta2) * precision * recall / denom
        if denom
        else 0.0
    )

    return accuracy, precision, recall, f1, f05


def confusion_from_labels():
    """
    Confusion matrix using the *stored* hf_label in Mongo.
    """
    docs = list(col.find(
        {"human_label": {"$exists": True}, "hf_label": {"$exists": True}},
        {"human_label": 1, "hf_label": 1},
    ))

    tp = fp = tn = fn = 0
    for d in docs:
        h = d["human_label"]      # assume 1 = protest, 0 = not
        p = d["hf_label"]         # same convention
        if h == 1 and p == 1:
            tp += 1
        elif h == 0 and p == 1:
            fp += 1
        elif h == 0 and p == 0:
            tn += 1
        elif h == 1 and p == 0:
            fn += 1
    return tp, fp, tn, fn


def run_classifier_for_threshold(threshold: float):
    """
    Call run_hf.py with the given threshold to re-classify the sample_texts.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_hf_path = os.path.join(script_dir, "run_hf.py")

    cmd = [sys.executable, run_hf_path, "--threshold", str(threshold)]
    print(f"\n>>> Running classifier with threshold={threshold:.2f}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    # 0) Metrics for the CURRENT stored hf_label (whatever threshold was used last)
    tp, fp, tn, fn = confusion_from_labels()
    acc, prec, rec, f1, f05 = compute_metrics(tp, fp, tn, fn)

    print("=== Metrics for CURRENT hf_label (existing threshold) ===")
    print("TP, FP, TN, FN:", tp, fp, tn, fn)
    print(f"Accuracy:  {acc:.3f}")
    print(f"Precision: {prec:.3f}")
    print(f"Recall:    {rec:.3f}")
    print(f"F1:        {f1:.3f}")
    print(f"F0.5:      {f05:.3f}")

    # 1) Sweep thresholds and optimise F0.5
    best_t = None
    best_f05 = -1.0
    best_counts = None
    best_metrics = None

    # 0.05, 0.06, ..., 0.90
    thresholds = [round(0.05 + i * 0.01, 2) for i in range(0, 86)]

    print("\n=== Threshold sweep for F0.5 ===")
    for t in thresholds:
        # Re-classify sample_texts with this threshold
        run_classifier_for_threshold(t)

        # Compute metrics for this threshold
        tp, fp, tn, fn = confusion_from_labels()
        acc, prec, rec, f1, f05 = compute_metrics(tp, fp, tn, fn)

        print(
            f"t={t:.2f}  F0.5={f05:.3f}  P={prec:.3f}  R={rec:.3f}  "
            f"F1={f1:.3f}  Acc={acc:.3f}  (TP={tp}, FP={fp}, TN={tn}, FN={fn})"
        )

        if f05 > best_f05:
            best_f05 = f05
            best_t = t
            best_counts = (tp, fp, tn, fn)
            best_metrics = (acc, prec, rec, f1, f05)

    # 2) Report best threshold
    b_tp, b_fp, b_tn, b_fn = best_counts
    b_acc, b_prec, b_rec, b_f1, b_f05 = best_metrics

    print("\n=== Optimal threshold for F0.5 (by re-running run_hf) ===")
    print(f"Best protest_threshold: {best_t:.2f}")
    print("TP, FP, TN, FN:", b_tp, b_fp, b_tn, b_fn)
    print(f"Accuracy:  {b_acc:.3f}")
    print(f"Precision: {b_prec:.3f}")
    print(f"Recall:    {b_rec:.3f}")
    print(f"F1:        {b_f1:.3f}")
    print(f"F0.5:      {b_f05:.3f}")

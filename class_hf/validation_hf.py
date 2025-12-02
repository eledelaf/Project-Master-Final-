from pymongo.mongo_client import MongoClient


MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
COLLECTION_NAME = "sample_texts"

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COLLECTION_NAME]
"""
docs = list(col.find(
    {"human_label": {"$exists": True}, "hf_label": {"$exists": True}},
    {"human_label": 1, "hf_label": 1}
))
"""
docs = list(col.find(
    {
        "human_label": {"$exists": True},
        "hf_confidence": {"$exists": True},
    },
    {
        "human_label": 1,
        "hf_label": 1,
        "hf_confidence": 1,
    }
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

print("TP, FP, TN, FN:", tp, fp, tn, fn)

def compute_metrics(tp, fp, tn, fn):
    total = tp + fp + tn + fn

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    f05 = (1 + 0.5*0.5) * precision * recall / (0.5*0.5 * precision + recall) if (precision + recall) else 0.0

    return accuracy, precision, recall, f1, f05

#acc, prec, rec, f1, f05 = compute_metrics(tp, fp, tn, fn)


def confusion_for_threshold(docs, threshold: float):
    """
    Confusion matrix when we threshold the raw protest probability (hf_confidence).
    """
    tp = fp = tn = fn = 0
    for d in docs:
        h = d["human_label"]
        prob = float(d.get("hf_confidence", 0.0))  # P(PROTEST)
        p = 1 if prob >= threshold else 0

        if h == 1 and p == 1:
            tp += 1
        elif h == 0 and p == 1:
            fp += 1
        elif h == 0 and p == 0:
            tn += 1
        elif h == 1 and p == 0:
            fn += 1
    return tp, fp, tn, fn

def find_best_threshold_for_f05(docs, start=0.1, stop=0.9, step=0.01):
    """
    Sweep thresholds and return the one that maximises F0.5.
    """
    best_t = None
    best_f05 = -1.0
    best_metrics = None
    best_counts = None

    t = start
    while t <= stop + 1e-9:
        tp, fp, tn, fn = confusion_for_threshold(docs, t)
        acc, prec, rec, f1, f05 = compute_metrics(tp, fp, tn, fn)

        if f05 > best_f05:
            best_f05 = f05
            best_t = t
            best_metrics = (acc, prec, rec, f1, f05)
            best_counts = (tp, fp, tn, fn)

        t += step

    return best_t, best_f05, best_metrics, best_counts

def confusion_from_labels(docs):
    """
    Confusion matrix using the *stored* hf_label in Mongo.
    """
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

if __name__ == "__main__":
    # 1) Metrics for the CURRENT stored hf_label (whatever threshold you used)
    tp, fp, tn, fn = confusion_from_labels(docs)
    acc, prec, rec, f1, f05 = compute_metrics(tp, fp, tn, fn)

    print("=== Metrics for CURRENT hf_label (existing threshold) ===")
    print("TP, FP, TN, FN:", tp, fp, tn, fn)
    print(f"Accuracy:  {acc:.3f}")
    print(f"Precision: {prec:.3f}")
    print(f"Recall:    {rec:.3f}")
    print(f"F1:        {f1:.3f}")
    print(f"F0.5:      {f05:.3f}")

    # 2) Search for threshold that maximises F0.5 using hf_confidence
    best_t, best_f05, best_metrics, best_counts = find_best_threshold_for_f05(
        docs, start=0.1, stop=0.9, step=0.005
    )

    b_acc, b_prec, b_rec, b_f1, b_f05 = best_metrics
    b_tp, b_fp, b_tn, b_fn = best_counts

    print("\n=== Optimal threshold for F0.5 (using hf_confidence) ===")
    print(f"Best protest_threshold: {best_t:.3f}")
    print("TP, FP, TN, FN:", b_tp, b_fp, b_tn, b_fn)
    print(f"Accuracy:  {b_acc:.3f}")
    print(f"Precision: {b_prec:.3f}")
    print(f"Recall:    {b_rec:.3f}")
    print(f"F1:        {b_f1:.3f}")
    print(f"F0.5:      {b_f05:.3f}")
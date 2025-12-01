from pymongo.mongo_client import MongoClient

MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
COLLECTION_NAME = "sample_texts"

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COLLECTION_NAME]

docs = list(col.find(
    {"human_label": {"$exists": True}, "hf_label": {"$exists": True}},
    {"human_label": 1, "hf_label": 1}
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

    return accuracy, precision, recall, f1

acc, prec, rec, f1 = compute_metrics(tp, fp, tn, fn)

print(f"Accuracy:  {acc:.3f}")
print(f"Precision: {prec:.3f}")
print(f"Recall:    {rec:.3f}")
print(f"F1:        {f1:.3f}")
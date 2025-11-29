# classify_with_bert_mongo.py

from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from tqdm import tqdm

# ------------------- 1. MongoDB config -------------------

Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]
col = db["Texts"]

# ------------------- 2. Model config -------------------

MODEL_DIR = "./bert_protest_binary_final"  # folder saved by Trainer
MODEL_NAME_TAG = "distilbert_protest_v1"   # tag to store in Mongo

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

clf = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    truncation=True,
    max_length=512,
    padding=True
)

# ------------------- 3. Query docs to classify -------------------
# Only classify:
#   - url_candidate = True (news / politics sections)
#   - no existing bert_protest_label (so script is resumable)

query = {
    "url_candidate": True,
    "bert_protest_label": {"$exists": False}
}

projection = {
    "_id": 1,
    "title": 1,
    "text": 1,
    "url_candidate": 1
}

cursor = col.find(query, projection)

BATCH_SIZE = 32
updates = []
count = 0

print("Starting BERT classification on Mongo docs...")

batch_docs = []
for doc in cursor:
    batch_docs.append(doc)

    if len(batch_docs) >= BATCH_SIZE:
        # Classify this batch
        texts = []
        ids = []
        for d in batch_docs:
            title = d.get("title") or ""
            text = d.get("text") or ""
            combined = (title + " " + text).strip()
            if not combined:
                combined = title or text or ""
            texts.append(combined)
            ids.append(d["_id"])

        # Run BERT
        preds = clf(texts, batch_size=8)

        for _id, pred in zip(ids, preds):
            label_str = pred["label"]   # should be "protest" or "not_protest"
            score = float(pred["score"])

            # Convert to 0/1
            if label_str.lower() in ["1", "protest", "label_1"]:
                label_int = 1
            else:
                label_int = 0

            updates.append(
                UpdateOne(
                    {"_id": _id},
                    {
                        "$set": {
                            "bert_protest_label": label_int,
                            "bert_protest_score": score,
                            "bert_protest_model": MODEL_NAME_TAG,
                        }
                    }
                )
            )

        # Write batch to Mongo
        if updates:
            try:
                col.bulk_write(updates)
            except PyMongoError as e:
                print("Mongo error in bulk_write:", e)
            count += len(updates)
            print(f"Updated {count} documents so far...")
            updates = []
        batch_docs = []

# Flush last partial batch
if batch_docs:
    texts = []
    ids = []
    for d in batch_docs:
        title = d.get("title") or ""
        text = d.get("text") or ""
        combined = (title + " " + text).strip()
        if not combined:
            combined = title or text or ""
        texts.append(combined)
        ids.append(d["_id"])

    preds = clf(texts, batch_size=8)

    for _id, pred in zip(ids, preds):
        label_str = pred["label"]
        score = float(pred["score"])

        if label_str.lower() in ["1", "protest", "label_1"]:
            label_int = 1
        else:
            label_int = 0

        updates.append(
            UpdateOne(
                {"_id": _id},
                {
                    "$set": {
                        "bert_protest_label": label_int,
                        "bert_protest_score": score,
                        "bert_protest_model": MODEL_NAME_TAG,
                        }
                }
                
                )
            )
        

    if updates:
        try:
            col.bulk_write(updates)
        except PyMongoError as e:
            print("Mongo error in final bulk_write:", e)
        count += len(updates)

print(f"Finished. Total documents updated with BERT labels: {count}")

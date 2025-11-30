# run_hf.py
# Use Hugging Face classifier on the MongoDB sample set

import os
from typing import Dict, Any, List

from pymongo.mongo_client import MongoClient
from pymongo import UpdateOne
from pymongo.errors import PyMongoError
from tqdm import tqdm

from hf_class import classify_article_with_hf

# ----------------------------------------------------------------------
# 0. Configuration
# ----------------------------------------------------------------------

# Prefer to store your Mongo URI in an env var to avoid committing secrets:
#   export MONGO_URI="mongodb+srv://user:pass@cluster/dbname?retryWrites=true&w=majority"
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"

# Adjust these if your DB / collection names are different
DB_NAME = "ProjectMaster"
#COLLECTION_NAME = "Texts"
COLLECTION_NAME = "sample_texts"

# How many updates to send in one bulk_write
BATCH_SIZE = 20
Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"




# ----------------------------------------------------------------------
# 1. Main logic
# ----------------------------------------------------------------------

def main() -> None:
    # Connect to Mongo
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Query: sample set (90 docs) – assuming they all have human_label
    # and we only want to classify the ones we haven't touched with HF yet.
    query: Dict[str, Any] = {
        "human_label": {"$exists": True},
        "hf_label": {"$exists": False},
        "text": {"$exists": True, "$ne": None}
    }

    projection = {
        "_id": 1,
        "title": 1,
        "text": 1,
        "human_label": 1,
    }

    docs_cursor = col.find(query, projection)

    docs = list(docs_cursor)
    total = len(docs)
    print(f"Found {total} documents to classify with Hugging Face.")

    if total == 0:
        return

    batch_ops: List[UpdateOne] = []

    for doc in tqdm(docs):
        doc_id = doc["_id"]
        title = doc.get("title") or ""
        text = doc.get("text") or ""

        try:
            result = classify_article_with_hf(title, text)
        except Exception as e:
            print(f"[HF] Fatal error classifying doc {_short_id(doc_id)}: {e}")
            # Mark as failure, but don't crash the whole script
            update = UpdateOne(
                {"_id": doc_id},
                {
                    "$set": {
                        "hf_status": "error",
                        "hf_error_message": str(e),
                    }
                },
            )
            batch_ops.append(update)
        else:
            if result is None:
                # Too short or skipped
                update = UpdateOne(
                    {"_id": doc_id},
                    {
                        "$set": {
                            "hf_status": "failed_or_skipped",
                        }
                    },
                )
            else:
                update = UpdateOne(
                    {"_id": doc_id},
                    {
                        "$set": {
                            "hf_label": result["label"],
                            "hf_label_name": result["label_name"],
                            "hf_confidence": result["confidence"],
                            "hf_reason": result["reason"],
                            "hf_model": "facebook/bart-large-mnli-zero-shot",
                            "hf_status": "ok",
                        }
                    },
                )

            batch_ops.append(update)

        # Flush batch to Mongo
        if len(batch_ops) >= BATCH_SIZE:
            _flush_batch(col, batch_ops)
            batch_ops = []

    # Flush any remaining
    if batch_ops:
        _flush_batch(col, batch_ops)


def _flush_batch(col, batch_ops: List[UpdateOne]) -> None:
    try:
        result = col.bulk_write(batch_ops, ordered=False)
        # Optional: print some info
        # print(f"Bulk write: matched={result.matched_count}, modified={result.modified_count}")
    except PyMongoError as e:
        print(f"[Mongo] Error during bulk_write: {e}")


def _short_id(doc_id: Any) -> str:
    s = str(doc_id)
    return s if len(s) <= 40 else s[:37] + "..."


if __name__ == "__main__":
    main()

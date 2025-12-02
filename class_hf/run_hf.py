# run_hf.py
# Use Hugging Face classifier on the MongoDB sample set

from typing import Dict, Any, List
import argparse
import sys

from pymongo.mongo_client import MongoClient
from pymongo import UpdateOne
from pymongo.errors import PyMongoError
from tqdm import tqdm

from hf_class import classify_article_with_hf

MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"

DB_NAME = "ProjectMaster"
COLLECTION_NAME = "sample_texts"
#COLLECTION_NAME = "Texts"

BATCH_SIZE = 20


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.57,
        help="Protest threshold passed to classify_article_with_hf().",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protest_threshold = args.threshold
    print(f"[run_hf] Using protest_threshold={protest_threshold:.2f}")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Re-classify all docs that have text
    query: Dict[str, Any] = {
        "text": {"$exists": True, "$ne": None},
    }

    projection = {
        "_id": 1,
        "title": 1,
        "text": 1,
    }

    docs = list(col.find(query, projection))
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
            result = classify_article_with_hf(
                title,
                text,
                protest_threshold=protest_threshold,  # <<< key change
            )
        except Exception as e:
            print(f"[HF] Fatal error classifying doc {_short_id(doc_id)}: {e}")
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
                            "hf_status": "ok",
                        }
                    },
                )

            batch_ops.append(update)

        if len(batch_ops) >= BATCH_SIZE:
            _flush_batch(col, batch_ops)
            batch_ops = []

    if batch_ops:
        _flush_batch(col, batch_ops)


def _flush_batch(col, batch_ops: List[UpdateOne]) -> None:
    try:
        col.bulk_write(batch_ops, ordered=False)
    except PyMongoError as e:
        print(f"[Mongo] Error during bulk_write: {e}")


def _short_id(doc_id: Any) -> str:
    s = str(doc_id)
    return s if len(s) <= 40 else s[:37] + "..."


if __name__ == "__main__":
    main()

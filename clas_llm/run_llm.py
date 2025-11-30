import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm

from llm_classify import classify_article_with_llm

load_dotenv()

Mongo_uri = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
client = MongoClient(Mongo_uri)
db = client["ProjectMaster"]
#col = db["Texts"]  
col = db["sample_texts"]


def main():
    # Base query: only classify articles that:
    # - have text and title
    # - are already scraped (status == "done")
    # - don't have an llm_label yet
    query = {
        #"status": "done",
        "text": {"$exists": True, "$ne": None, "$ne": ""},
        "title": {"$exists": True, "$ne": None, "$ne": ""},
        "llm_label": {"$exists": False},
    }

    # Projection: only fetch what we need
    projection = {
        "_id": 1,        # this is your URL
        "title": 1,
        "text": 1,
    }

    # Get count (for progress bar)
    total_to_classify = col.count_documents(query)
    print(f"Found {total_to_classify} documents to classify with LLM.")

    cursor = col.find(query, projection)

    batch_size = 50
    bulk_ops = []

    try:
        for doc in tqdm(cursor, total=total_to_classify):
            _id = doc["_id"]          # URL string
            title = doc.get("title", "")
            text = doc.get("text", "")

            result = classify_article_with_llm(title, text)

            if result is None:
                # Either text too short or API failure; mark but don't label
                update = {
                    "$set": {
                        "llm_classification_status": "failed_or_skipped",
                        "llm_classification_timestamp": datetime.now(timezone.utc),
                    }
                }
            else:
                update = {
                    "$set": {
                        "llm_label": result["label"],           # 0 or 1
                        "llm_label_name": result["label_name"], # "PROTEST"/"NOT_PROTEST"
                        "llm_confidence": result["confidence"],
                        "llm_reason": result["reason"],
                        "llm_model": "gpt-4o-mini",
                        "llm_classification_status": "success",
                        "llm_classification_timestamp": datetime.now(timezone.utc),
                    }
                }

            bulk_ops.append(UpdateOne({"_id": _id}, update))

            if len(bulk_ops) >= batch_size:
                col.bulk_write(bulk_ops, ordered=False)
                bulk_ops = []

        # Flush remaining ops
        if bulk_ops:
            col.bulk_write(bulk_ops, ordered=False)

    finally:
        cursor.close()

    print("LLM classification completed.")


if __name__ == "__main__":
    main()


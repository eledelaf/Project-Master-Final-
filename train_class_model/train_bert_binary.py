import numpy as np
import pandas as pd

from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer,
)

# ------------------ 1. CONFIG ------------------

CSV_PATH = "sample_texts_with_candidate_refined_clean.csv"  # your file
TEXT_COL = "text"
TITLE_COL = "title"
LABEL_COL = "label"  # this is candidate_refined

MODEL_NAME = "distilbert-base-uncased"
OUTPUT_DIR = "./bert_protest_binary"

# ------------------ 2. LOAD + CLEAN CSV ------------------

# Read CSV (default header row is fine)
df = pd.read_csv(CSV_PATH)

# Drop old 'candidate' column if present 
if "candidate" in df.columns:
    df = df.drop(columns=["candidate"])

# Ensure 'candidate_refined' exists
if "candidate_refined" not in df.columns:
    raise ValueError("Column 'candidate_refined' not found in CSV.")

# Convert candidate_refined (True/False or 0/1) -> int 0/1
df["candidate_refined"] = df["candidate_refined"].astype(int)

# Create 'label' column for BERT (0/1)
df[LABEL_COL] = df["candidate_refined"]

# Optional: drop rows with missing text/title (to avoid weird errors)
df[TEXT_COL] = df[TEXT_COL].fillna("")
df[TITLE_COL] = df[TITLE_COL].fillna("")

print("First few cleaned rows:")
print(df[[TEXT_COL, TITLE_COL, LABEL_COL]].head())

# ------------------ 3. CONVERT TO HF DATASET + SPLIT ------------------

dataset = Dataset.from_pandas(df, preserve_index=False)

# Train/validation/test split: 80/10/10
dataset = dataset.train_test_split(test_size=0.2, seed=42)
test_valid = dataset["test"].train_test_split(test_size=0.5, seed=42)
dataset["validation"] = test_valid["test"]
dataset["test"] = test_valid["train"]

print(dataset)

# ------------------ 4. TOKENIZER + PREPROCESSING ------------------

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def preprocess_function(examples):
    titles = examples.get(TITLE_COL, [""] * len(examples[TEXT_COL]))
    texts = examples[TEXT_COL]
    combined = [ (t or "") + " " + (x or "") for t, x in zip(titles, texts) ]
    return tokenizer(
        combined,
        truncation=True,
        max_length=512,
    )

encoded_dataset = dataset.map(preprocess_function, batched=True)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# ------------------ 5. METRICS ------------------
# This function tells Hugging Face how to evaluate the model.
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary"
    )

    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

# ------------------ 6. MODEL + TRAINER ------------------

num_labels = 2
id2label = {0: "not_protest", 1: "protest"}
label2id = {"not_protest": 0, "protest": 1}

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label2id,
)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=20,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=encoded_dataset["train"],
    eval_dataset=encoded_dataset["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# ------------------ 7. TRAIN ------------------

trainer.train()

# ------------------ 8. EVALUATE ON TEST ------------------

metrics = trainer.evaluate(encoded_dataset["test"])
print("Test metrics:", metrics)

# ------------------ 9. SAVE FINAL MODEL ------------------

final_dir = OUTPUT_DIR + "_final"
trainer.save_model(final_dir)
tokenizer.save_pretrained(final_dir)
print(f"Final model saved to: {final_dir}")

# ------------------ 10. ERROR ANALYSIS: FALSE POSITIVES / FALSE NEGATIVES ------------------

import pandas as pd
import numpy as np

# 1) Get the raw (non-tokenized) test split and the encoded test split
test_raw = dataset["test"]               # original fields: title, text, label, ...
test_encoded = encoded_dataset["test"]   # tokenized version used by the model

# 2) Predict on the test set
pred_output = trainer.predict(test_encoded)
logits = pred_output.predictions
true_labels = pred_output.label_ids
pred_labels = np.argmax(logits, axis=-1)

# 3) Build a DataFrame with useful info
df_test = pd.DataFrame({
    "_id": test_raw["_id"],
    "title": test_raw["title"],
    "text": test_raw["text"],
    "true_label": true_labels,
    "pred_label": pred_labels,
})

# 4) False positives: model says "protest" (1) but true label is 0
false_pos = df_test[(df_test["true_label"] == 0) & (df_test["pred_label"] == 1)]

# 5) False negatives: model says "not protest" (0) but true label is 1
false_neg = df_test[(df_test["true_label"] == 1) & (df_test["pred_label"] == 0)]

print("\nNumber of false positives:", len(false_pos))
print("Number of false negatives:", len(false_neg))

print("\n--- Sample false positives (model thought they were protests, but labels say no) ---")
for idx, row in false_pos.head(5).iterrows():
    print(f"\nURL: {row['_id']}")
    print("TITLE:", row["title"])
    print("TRUE LABEL:", row["true_label"], "PRED:", row["pred_label"])

print("\n--- Sample false negatives (real protests that the model missed) ---")
for idx, row in false_neg.head(5).iterrows():
    print(f"\nURL: {row['_id']}")
    print("TITLE:", row["title"])
    print("TRUE LABEL:", row["true_label"], "PRED:", row["pred_label"])

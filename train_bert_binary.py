import numpy as np
import pandas as pd

# ------------------ 1. CONFIG ------------------

CSV_PATH = "sample_texts_with_candidate_refined.csv"  # your file
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
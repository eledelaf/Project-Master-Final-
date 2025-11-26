import os
import numpy as np
from dataclasses import dataclass
import pandas as pd
from datasets import load_dataset, ClassLabel

# -------- 1. Config --------

CSV_PATH = "sample_texts_with_labels.csv"  # change if needed
TEXT_COL = "text"          # column with full article text
TITLE_COL = "title"        # we will concatenate title + text
LABEL_COL = "label"        # 0 = not protest, 1 = protest

MODEL_NAME = "distilbert-base-uncased"  # smaller, faster BERT-like model

# -------- 2. Load dataset --------

# Expecting a CSV with at least: title, text, label
dataset = load_dataset("csv", data_files={"data": CSV_PATH})["data"]

# Ensure labels are integers 0/1
if LABEL_COL not in dataset.column_names:
    raise ValueError(f"Column '{LABEL_COL}' not found in CSV. Please add it as 0/1 labels.")

# Cast label column to ClassLabel for nicer handling
unique_labels = sorted(set(dataset[LABEL_COL]))
num_labels = len(unique_labels)
print("Unique labels:", unique_labels)

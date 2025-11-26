import os
import numpy as np
from dataclasses import dataclass
import pandas as pd

# -------- 1. Config --------

CSV_PATH = "sample_texts_with_labels.csv"  # change if needed
TEXT_COL = "text"          # column with full article text
TITLE_COL = "title"        # we will concatenate title + text
LABEL_COL = "label"        # 0 = not protest, 1 = protest

MODEL_NAME = "distilbert-base-uncased"  # smaller, faster BERT-like model

df = pd.read_csv(CSV_PATH)
print(df.head())
print(df.columns)
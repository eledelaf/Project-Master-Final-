# hf_classify.py
# Zero-shot PROTEST / NOT_PROTEST classifier using Hugging Face transformers

import os
from typing import Optional, Dict, Any

from transformers import pipeline

# Load a zero-shot classification pipeline
# (this will download the model the first time you run it)
_zero_shot_classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"  # robust English NLI model
)

LABELS = ["PROTEST", "NOT_PROTEST"]

SYSTEM_PROMPT = (
    "Decide if the MAIN FOCUS of the article is a concrete protest event "
    "(demonstration, strike, rally, march, etc.) or not.\n"
    "Return one of the labels: PROTEST, NOT_PROTEST."
)
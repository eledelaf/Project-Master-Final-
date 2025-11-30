# hf_classify.py
# Zero-shot PROTEST / NOT_PROTEST classifier using Hugging Face transformers

from typing import Optional, Dict, Any

from transformers import pipeline

# Load a zero-shot classification pipeline ONCE (global)
# This will download the model the first time you run it.
_zero_shot_classifier = pipeline(
    task="zero-shot-classification",
    model="facebook/bart-large-mnli"
)

LABELS = ["PROTEST", "NOT_PROTEST"]

SYSTEM_PROMPT = (
    "Decide if the MAIN FOCUS of the article is a concrete protest event "
    "(demonstration, strike, rally, march, blockade, occupation, strike, etc.) "
    "or something else.\n\n"
    "If the main focus is a specific protest event, label it PROTEST.\n"
    "Otherwise, label it NOT_PROTEST."
)

def classify_article_with_hf(
    title: str,
    text: str,
    max_chars: int = 4000,
) -> Optional[Dict[str, Any]]:
    """
    Classify an article as PROTEST / NOT_PROTEST using zero-shot NLI.

    Returns:
      {
        "label": 1 or 0,
        "label_name": "PROTEST" or "NOT_PROTEST",
        "confidence": float,
        "reason": str
      }
    or None if the text is too short.
    """

    # Skip very short texts (likely bad scrapes)
    if not text or len(text.strip()) < 200:
        return None

    truncated_text = text[:max_chars]

    sequence = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Title: {title}\n\n"
        f"Article:\n{truncated_text}"
    )

    result = _zero_shot_classifier(
        sequence,
        candidate_labels=LABELS,
        hypothesis_template="This article is about {}."
    )

    # result["labels"] sorted by score desc
    top_label_name = result["labels"][0]
    score = float(result["scores"][0])

    label_int = 1 if top_label_name == "PROTEST" else 0

    return {
        "label": label_int,
        "label_name": top_label_name,
        "confidence": score,
        "reason": (
            f"Zero-shot classification predicted {top_label_name} "
            f"with score {score:.3f} using facebook/bart-large-mnli."
        ),
    }

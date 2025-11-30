# hf_class.py
# Zero-shot PROTEST / NOT_PROTEST classifier using Hugging Face transformers

from typing import Optional, Dict, Any
from transformers import pipeline

# Load a zero-shot classification pipeline ONCE (global)
_zero_shot_classifier = pipeline(
    task="zero-shot-classification",
    model="facebook/bart-large-mnli"
)

# Natural-language labels instead of weird tokens like "NOT_PROTEST"
CANDIDATE_LABELS = [
    "a concrete real-world protest event in the UK",
    "something else (no specific protest event in the UK)",
]

def classify_article_with_hf(
    title: str,
    text: str,
    max_chars: int = 4000,
    min_length: int = 200,
    protest_threshold: float = 0.70,
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
    if not text or len(text.strip()) < min_length:
        return None

    truncated_text = text[:max_chars]

    sequence = f"Title: {title}\n\nArticle:\n{truncated_text}"

    result = _zero_shot_classifier(
        sequence,
        candidate_labels=CANDIDATE_LABELS,
        hypothesis_template="The main focus of this article is {}.",
        multi_label=False,
    )

    top_label = result["labels"][0]
    score = float(result["scores"][0])

    is_protest = (
        top_label.startswith("a concrete real-world protest event")
        and score >= protest_threshold
    )

    label_int = 1 if is_protest else 0
    label_name = "PROTEST" if is_protest else "NOT_PROTEST"

    return {
        "label": label_int,
        "label_name": label_name,
        "confidence": score,
        "reason": (
            f"Zero-shot classification top label='{top_label}' "
            f"score={score:.3f}, threshold={protest_threshold} "
            f"-> {label_name}"
        ),
    }

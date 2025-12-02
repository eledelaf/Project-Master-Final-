# hf_class.py
from typing import Optional, Dict, Any
from transformers import pipeline

_zero_shot_classifier = pipeline(
    task="zero-shot-classification",
    model="facebook/bart-large-mnli"
)

CANDIDATE_LABELS = [
    "a concrete real-world protest event ",
    "something else (no specific protest event )",
]

def classify_article_with_hf(
    title: str,
    text: str,
    max_chars: int = 4000,
    min_length: int = 200,
    protest_threshold: float = 0.57,
) -> Optional[Dict[str, Any]]:
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

    labels = result["labels"]
    scores = result["scores"]

    protest_label = CANDIDATE_LABELS[0]
    protest_index = labels.index(protest_label)
    protest_score = float(scores[protest_index])  # <-- ALWAYS P(PROTEST)

    is_protest = protest_score >= protest_threshold

    label_int = 1 if is_protest else 0
    label_name = "PROTEST" if is_protest else "NOT_PROTEST"

    return {
        "label": label_int,
        "label_name": label_name,
        "confidence": protest_score,  # <-- now: P(PROTEST)
        "reason": (
            f"Zero-shot P(PROTEST)={protest_score:.3f}, "
            f"threshold={protest_threshold} -> {label_name}"
        ),
    }

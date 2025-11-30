import os
import json
import time
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
import openai  # for exception classes

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

SYSTEM_INSTRUCTIONS = """
You are a classifier for news articles about protests.

You must decide if the article's MAIN FOCUS is a concrete protest event
(demonstration, march, rally, strike, riot, blockade, occupation, picket, etc.)
or if protests are only mentioned in passing.

Labeling rules:

- 1 = PROTEST:
  The article’s main focus is a collective, public action in which people express
  political or social claims. The article should describe the event itself
  (who, where, why, what happened), or its very immediate unfolding
  (clashes, arrests, dispersal, numbers of participants, etc.).

- 0 = NOT_PROTEST:
  The article mainly concerns elite statements, scandals, normal politics,
  commentary, analysis, or other topics. Protests may be mentioned only
  briefly, as background, or hypothetically.

Borderline guidance:
- Opinion or analysis pieces ABOUT protests, but not describing a specific
  concrete event, are usually NOT_PROTEST.
- Articles that list many unrelated things (e.g. daily briefs, roundups)
  are NOT_PROTEST unless a single concrete protest event clearly dominates.
- If it is ambiguous whether the main focus is a concrete protest event,
  lean towards 0 = NOT_PROTEST.

You must output STRICT JSON with keys:
- "label": integer 1 or 0
- "label_name": "PROTEST" or "NOT_PROTEST"
- "confidence": float between 0 and 1
- "reason": short text explanation (1-3 sentences)
"""

def classify_article_with_llm(
    title: str,
    text: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Call the LLM to classify a single article as PROTEST/NOT_PROTEST.

    Returns a dict like:
      {"label": 1, "label_name": "PROTEST", "confidence": 0.92, "reason": "..."}
    or None if it fails.
    """

    # Short-circuit if text is too short / empty
    if not text or len(text.strip()) < 200:
        # You can choose to return None or treat very-short items as NOT_PROTEST.
        return None

    # Truncate very long texts so tokens don't explode (adjust as needed)
    max_chars = 4000
    truncated_text = text[:max_chars]

    article_input = f"""
Title: {title}

Article text:
\"\"\"{truncated_text}\"\"\"

Decide if this article is PROTEST (1) or NOT_PROTEST (0) following the rules.
Return ONLY a JSON object with keys: label, label_name, confidence, reason.
"""

    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model=model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=article_input,
                response_format={"type": "json_object"},
                temperature=0.0,  # deterministic
            )

            # responses.create has a handy helper:
            raw_text = response.output_text  # JSON string
            result = json.loads(raw_text)

            # Basic sanity checks
            if "label" not in result or "label_name" not in result:
                raise ValueError(f"Missing keys in LLM output: {result}")

            # Force types / values just in case
            label = int(result["label"])
            if label not in (0, 1):
                raise ValueError(f"Invalid label value: {label}")

            result["label"] = label
            result["label_name"] = "PROTEST" if label == 1 else "NOT_PROTEST"

            # Coerce confidence
            try:
                conf = float(result.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            result["confidence"] = max(0.0, min(1.0, conf))

            return result

        except (openai.RateLimitError, openai.APIConnectionError) as e:
            # Simple backoff and retry
            wait_seconds = 5 * (attempt + 1)
            print(f"[LLM] Rate/connection error: {e}. Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)

        except Exception as e:
            print(f"[LLM] Error classifying article: {e}")
            # If JSON parsing etc fails, retry once or twice, then give up
            time.sleep(2)

    print("[LLM] Failed after retries, returning None.")
    return None

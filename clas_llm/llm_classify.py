# export OPENAI_API_KEY="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"
import os
import json
import time
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI  # NEW

# Load variables from .env if present
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Set it as an env var (export OPENAI_API_KEY=\"...\") "
        "or in a .env file."
    )

# New-style client
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_INSTRUCTIONS = """
You are a classifier for news articles about protests.

You must decide if the article's MAIN FOCUS is a concrete protest event
(demonstration, march, rally, strike, riot, blockade, occupation, picket, etc.)
or if protests are only mentioned in passing.

Labeling rules:

- 1 = PROTEST:
  The article’s main focus is a collective, public action in which people
  express political or social claims. The article should describe the event
  itself (who, where, why, what happened), or its very immediate unfolding
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


def _extract_json(raw_text: str) -> Dict[str, Any]:
    """
    Try to parse JSON from the model output.
    If the model accidentally adds extra text around the JSON,
    we take the substring between the first '{' and the last '}'.
    """
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = raw_text[start:end + 1]
            return json.loads(json_str)
        raise


def classify_article_with_llm(
    title: str,
    text: str,
    model: str = "gpt-4o-mini",  # change model name if needed
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Call the LLM (chat completion) to classify a single article.

    Returns a dict:
      {"label": 1, "label_name": "PROTEST",
       "confidence": 0.92, "reason": "..."}
    or None if it fails or text is too short.
    """

    if not text or len(text.strip()) < 200:
        # Too short / likely bad scrape -> skip
        return None

    max_chars = 4000
    truncated_text = text[:max_chars]

    user_prompt = f"""
Title: {title}

Article text:
\"\"\"{truncated_text}\"\"\"

Decide if this article is PROTEST (1) or NOT_PROTEST (0)
following the rules in the system instructions.

Return ONLY a JSON object with keys:
  "label", "label_name", "confidence", "reason".
"""

    for attempt in range(max_retries):
        try:
            # Use the new client-style chat completions API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,  # deterministic
            )

            # New-style response object
            raw_text = response.choices[0].message.content
            result = _extract_json(raw_text)

            if "label" not in result or "label_name" not in result:
                raise ValueError(f"Missing keys in LLM output: {result}")

            label = int(result["label"])
            if label not in (0, 1):
                raise ValueError(f"Invalid label value: {label}")

            result["label"] = label
            result["label_name"] = "PROTEST" if label == 1 else "NOT_PROTEST"

            # Normalise confidence
            try:
                conf = float(result.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            result["confidence"] = max(0.0, min(1.0, conf))

            # Clean up reason
            reason = (result.get("reason") or "").strip()
            result["reason"] = reason

            return result

        except Exception as e:
            wait_seconds = 5 * (attempt + 1)
            print(f"[LLM] Error classifying article (attempt {attempt+1}): {e}")
            print(f"      Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)

    print("[LLM] Failed after retries, returning None.")
    return None

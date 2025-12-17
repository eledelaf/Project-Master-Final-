#!/usr/bin/env python3
"""
Plot publication date vs sentiment (VADER compound) with a rolling mean and 95% CI band,
plus shaded COVID-19 period(s).

Usage:
  python plot_sentiment_time.py

Before running, set your MongoDB URI securely, e.g. in your terminal:
  export MONGO_URI="mongodb+srv://USER:PASSWORD@HOST/?retryWrites=true&w=majority"

Then adjust DB_NAME / COLLECTION_NAME below if needed.
"""

import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient


# ----------------------------
# Config (edit these)
# ----------------------------
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
COLLECTION_NAME = "Texts"

# Filter: keep only protest-labelled articles (recommended for your thesis question).
# If you want ALL articles, set PROTEST_ONLY = False.
PROTEST_ONLY = True

# Rolling window for trend line (time-based window, not a fixed number of points)
ROLLING_WINDOW = "30D"  # e.g., "30D" or "90D" or "60D"

# Compute a simple 95% CI band around the rolling mean (mean ± 1.96 * SE)
SHOW_CI_BAND = True

# Define COVID period(s) to shade (edit to match your methodology)
COVID_PERIODS = [
    # WHO declared COVID-19 a pandemic: 2020-03-11
    # UK legal restrictions largely ended: 2022-02-24
    {"start": "2020-03-11", "end": "2022-02-24", "label": "COVID-19 period"},
]

# Output
OUT_DIR = Path("figures")
OUT_FILE = OUT_DIR / "sentiment_over_time.png"


def load_sentiment_from_mongo() -> pd.DataFrame:
    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI is not set. Export it in your shell, e.g.\n"
            "  export MONGO_URI='mongodb+srv://USER:PASSWORD@HOST/?retryWrites=true&w=majority'\n"
            "Or set it directly in the script (not recommended)."
        )

    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][COLLECTION_NAME]

    query = {
        "publish_date": {"$exists": True},
        "sentiment.compound": {"$exists": True},
    }
    if PROTEST_ONLY:
        query["hf_label_name"] = "PROTEST"

    projection = {
        "_id": 0,
        "publish_date": 1,
        "paper": 1,
        "sentiment.compound": 1,
    }

    docs = list(col.find(query, projection))
    df = pd.DataFrame(docs)

    if df.empty:
        raise RuntimeError(
            "Query returned 0 documents.\n"
            "Check DB_NAME / COLLECTION_NAME, and whether your docs have:\n"
            "- publish_date\n"
            "- sentiment.compound\n"
            + ("- hf_label_name == 'PROTEST'\n" if PROTEST_ONLY else "")
        )

    df = df.rename(columns={"sentiment": "sentiment_obj"})
    # sentiment_obj is a dict, we only projected sentiment.compound, so it becomes {'compound': ...}
    df["compound"] = df["sentiment_obj"].apply(lambda d: d.get("compound") if isinstance(d, dict) else None)

    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    df["compound"] = pd.to_numeric(df["compound"], errors="coerce")

    df = df.dropna(subset=["publish_date", "compound"]).sort_values("publish_date")
    return df


def plot_sentiment_over_time(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Article-level series
    s = df.set_index("publish_date")["compound"].sort_index()

    # Rolling statistics (time-based window)
    roll_mean = s.rolling(ROLLING_WINDOW).mean()

    if SHOW_CI_BAND:
        roll_std = s.rolling(ROLLING_WINDOW).std()
        roll_n = s.rolling(ROLLING_WINDOW).count()
        roll_se = roll_std / (roll_n ** 0.5)
        ci_low = roll_mean - 1.96 * roll_se
        ci_high = roll_mean + 1.96 * roll_se
    else:
        ci_low = ci_high = None

    fig, ax = plt.subplots(figsize=(12, 5))

    # Scatter (article-level)
    ax.scatter(
        df["publish_date"],
        df["compound"],
        s=8,
        alpha=0.08,  # low alpha to avoid a blob
        linewidths=0,
    )

    # Rolling mean line
    ax.plot(roll_mean.index, roll_mean.values, linewidth=2)

    # CI band
    if SHOW_CI_BAND:
        ax.fill_between(ci_low.index, ci_low.values, ci_high.values, alpha=0.15)

    # Neutral line
    ax.axhline(0, linewidth=1, linestyle="--")

    # Shade COVID periods
    for p in COVID_PERIODS:
        start = pd.to_datetime(p["start"])
        end = pd.to_datetime(p["end"])
        ax.axvspan(start, end, alpha=0.12)
        # Put label near the top of the shaded region
        ax.text(
            start + (end - start) * 0.02,
            ax.get_ylim()[1] * 0.95,
            p.get("label", "COVID"),
            fontsize=9,
            va="top",
        )

    title = "Publication date vs sentiment (VADER compound)"
    if PROTEST_ONLY:
        title += " — PROTEST articles only"
    ax.set_title(title)

    ax.set_xlabel("Publication date")
    ax.set_ylabel("Sentiment (compound)")

    # Tight layout and save
    fig.tight_layout()
    fig.savefig(OUT_FILE, dpi=300)
    print(f"Saved: {OUT_FILE.resolve()}")

    plt.show()


def main():
    df = load_sentiment_from_mongo()
    print("Loaded rows:", len(df))
    print("Date range:", df["publish_date"].min().date(), "to", df["publish_date"].max().date())
    plot_sentiment_over_time(df)


if __name__ == "__main__":
    main()

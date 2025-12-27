#!/usr/bin/env python3
"""
Overall sentiment (VADER compound), not split by paper.

Creates:
A) Time series: monthly mean compound (overall).
B1) Overall distribution: violin + boxplot of compound.
B2) COVID angle: distributions faceted by period (pre/during/post).

Usage:
  export MONGO_URI="mongodb+srv://USER:PASSWORD@HOST/?retryWrites=true&w=majority"
  python plot_sentiment_overall.py
"""

import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient

# ----------------------------
# Config
# ---------------------------- 
MONGO_URI = "mongodb+srv://eledelaf:Ly5BX57aSXIzJVde@articlesprotestdb.bk5rtxs.mongodb.net/?retryWrites=true&w=majority&appName=ArticlesProtestDB"
DB_NAME = "ProjectMaster"
COLLECTION_NAME = "Texts"

# Filter: keep only protest-labelled articles.
PROTEST_ONLY = True

# Monthly aggregation frequency for time series
MONTH_FREQ = "MS"  # month-start; alternative: "M" for month-end

# Optional: drop very short texts / junk if you want (set None to disable)
MIN_TEXT_CHARS = None  # e.g. 80

# Define periods for the COVID comparison
# WHO pandemic declaration 2020-03-11
# Most UK legal restrictions ended 2022-02-24 (your chosen cutoff)
PERIODS = [
    {"name": "Pre-COVID",  "start": None,         "end": "2020-03-10"},
    {"name": "COVID",      "start": "2020-03-11", "end": "2022-02-24"},
    {"name": "Post-COVID", "start": "2022-02-25", "end": None},
]

# Output
OUT_DIR = Path("7.2figures")
OUT_A = OUT_DIR / "sentiment_monthly_mean_overall.png"
OUT_B1 = OUT_DIR / "sentiment_distribution_overall.png"
OUT_B2 = OUT_DIR / "sentiment_distribution_by_period.png"


def _require_env():
    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI is not set.\n"
            "Set it in your shell, e.g.\n"
            "  export MONGO_URI='mongodb+srv://USER:PASSWORD@HOST/?retryWrites=true&w=majority'"
        )


def load_df() -> pd.DataFrame:
    _require_env()

    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][COLLECTION_NAME]

    query = {
        "publish_date": {"$exists": True},
        "sentiment.compound": {"$exists": True},
    }
    if PROTEST_ONLY:
        query["hf_label_name"] = "PROTEST"
    if MIN_TEXT_CHARS is not None:
        query["text"] = {"$exists": True}

    projection = {
        "_id": 0,
        "publish_date": 1,
        "sentiment.compound": 1,
    }
    if MIN_TEXT_CHARS is not None:
        projection["text"] = 1

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

    # sentiment becomes {'compound': ...} due to projection path
    df = df.rename(columns={"sentiment": "sentiment_obj"})
    df["compound"] = df["sentiment_obj"].apply(
        lambda d: d.get("compound") if isinstance(d, dict) else None
    )

    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    df["compound"] = pd.to_numeric(df["compound"], errors="coerce")

    keep_cols = ["publish_date", "compound"]
    if MIN_TEXT_CHARS is not None and "text" in df.columns:
        df["text_len"] = df["text"].astype(str).str.len()
        df = df[df["text_len"] >= MIN_TEXT_CHARS]
        keep_cols.append("text_len")

    df = df.dropna(subset=["publish_date", "compound"]).sort_values("publish_date")
    return df[keep_cols].copy()


def add_period(df: pd.DataFrame) -> pd.DataFrame:
    def assign(d: pd.Timestamp) -> str:
        for p in PERIODS:
            start = pd.to_datetime(p["start"]) if p["start"] else None
            end = pd.to_datetime(p["end"]) if p["end"] else None
            ok_start = True if start is None else (d >= start)
            ok_end = True if end is None else (d <= end)
            if ok_start and ok_end:
                return p["name"]
        return "Other"

    df2 = df.copy()
    df2["period"] = df2["publish_date"].apply(assign)
    return df2


def plot_monthly_mean(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    monthly = (
        df.groupby(pd.Grouper(key="publish_date", freq=MONTH_FREQ))["compound"]
          .mean()
          .reset_index()
          .rename(columns={"publish_date": "month"})
          .sort_values("month")
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(monthly["month"], monthly["compound"], linewidth=2)
    ax.axhline(0, linewidth=1, linestyle="--")
    ax.set_ylim(-1, 1)

    title = "Monthly mean sentiment (VADER compound) — overall"
    if PROTEST_ONLY:
        title += " — PROTEST articles only"
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean compound")

    fig.tight_layout()
    fig.savefig(OUT_A, dpi=300)
    print(f"Saved: {OUT_A.resolve()}")
    plt.show()


def plot_distribution_overall(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = df["compound"].dropna().values

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.violinplot([data], showextrema=False)
    ax.boxplot([data], widths=0.15, showfliers=False)

    ax.axhline(0, linewidth=1, linestyle="--")
    ax.set_ylim(-1, 1)

    ax.set_xticks([1])
    ax.set_xticklabels(["Overall"])

    title = "Sentiment distribution (VADER compound) — overall"
    if PROTEST_ONLY:
        title += " — PROTEST articles only"
    ax.set_title(title)

    ax.set_ylabel("Compound")

    fig.tight_layout()
    fig.savefig(OUT_B1, dpi=300)
    print(f"Saved: {OUT_B1.resolve()}")
    plt.show()


def plot_distribution_by_period(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    dfp = add_period(df)
    period_names = [p["name"] for p in PERIODS]
    dfp = dfp[dfp["period"].isin(period_names)].copy()

    data = [dfp.loc[dfp["period"] == per, "compound"].dropna().values for per in period_names]

    fig, ax = plt.subplots(figsize=(max(9, 1.6 * len(period_names)), 4))

    ax.violinplot(data, showextrema=False)
    ax.boxplot(data, widths=0.25, showfliers=False)

    ax.axhline(0, linewidth=1, linestyle="--")
    ax.set_ylim(-1, 1)

    ax.set_xticks(range(1, len(period_names) + 1))
    ax.set_xticklabels(period_names, rotation=20, ha="right")

    title = "Sentiment by period (VADER compound)"
    if PROTEST_ONLY:
        title += " — PROTEST articles only"
    ax.set_title(title)

    ax.set_xlabel("Period")
    ax.set_ylabel("Compound")

    fig.tight_layout()
    fig.savefig(OUT_B2, dpi=300)
    print(f"Saved: {OUT_B2.resolve()}")
    plt.show()


def main():
    df = load_df()

    print("Loaded rows:", len(df))
    print("Date range:", df["publish_date"].min().date(), "to", df["publish_date"].max().date())
    print("Mean compound:", float(df["compound"].mean()))
    print("Median compound:", float(df["compound"].median()))

    plot_monthly_mean(df)
    plot_distribution_overall(df)
    plot_distribution_by_period(df)


if __name__ == "__main__":
    main()

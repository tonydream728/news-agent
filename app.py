from __future__ import annotations

import json
import os
from typing import Any

from flask import Flask, render_template, request

from news_fetcher import load_keywords


app = Flask(__name__)


def load_json(path: str, fallback: Any) -> Any:
    if not os.path.exists(path):
        return fallback
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.route("/")
def index():
    selected_category = request.args.get("category", "all")
    keywords_config = load_keywords("keywords.yml")
    today_articles = load_json("data/news_today.json", [])
    history_articles = load_json("data/news_7d_history.json", [])
    report = load_json("data/daily_report.json", {})

    today_report = report.get("sections", {}).get("today", {})
    history_report = report.get("sections", {}).get("history_7d", {})

    today_articles = _filter_category(today_articles, selected_category)
    history_articles = _filter_category(history_articles, selected_category)

    today_report = _filter_report(today_report, today_articles, selected_category)
    history_report = _filter_report(history_report, history_articles, selected_category)

    return render_template(
        "index.html",
        keywords_config=keywords_config,
        selected_category=selected_category,
        today_articles=today_articles,
        history_articles=history_articles,
        today_report=today_report,
        history_report=history_report,
        report=report,
    )


def _filter_category(articles: list[dict[str, Any]], selected_category: str) -> list[dict[str, Any]]:
    normalized_articles = [article for article in articles if isinstance(article, dict)]
    if selected_category == "all":
        return normalized_articles
    return [article for article in normalized_articles if selected_category in article.get("categories", [])]


def _filter_report(
    report: dict[str, Any],
    filtered_articles: list[dict[str, Any]],
    selected_category: str,
) -> dict[str, Any]:
    if not isinstance(report, dict):
        return {
            "layer_1_keyword_news": filtered_articles,
            "layer_2_ai_filtering": [],
            "layer_3_daily_brief": [],
            "layer_4_content_ideas": [],
            "layer_5_trend_analysis": {},
        }

    if selected_category == "all":
        return report

    filtered_ids = {article.get("id") for article in filtered_articles if isinstance(article, dict)}
    copied = dict(report)
    copied["layer_1_keyword_news"] = filtered_articles
    copied["layer_2_ai_filtering"] = [
        item
        for item in report.get("layer_2_ai_filtering", [])
        if isinstance(item, dict) and item.get("id") in filtered_ids
    ]
    copied["layer_3_daily_brief"] = [
        item
        for item in report.get("layer_3_daily_brief", [])
        if isinstance(item, dict) and item.get("id") in filtered_ids
    ]
    return copied


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

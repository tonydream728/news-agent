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
    articles = load_json("data/news.json", [])
    report = load_json("data/daily_report.json", {})

    if selected_category != "all":
        filtered_articles = [
            article for article in articles if selected_category in article.get("categories", [])
        ]
    else:
        filtered_articles = articles

    filtered_ids = {article.get("id") for article in filtered_articles}
    ai_items = report.get("layer_2_ai_filtering", [])
    if selected_category != "all":
        ai_items = [item for item in ai_items if item.get("id") in filtered_ids]

    return render_template(
        "index.html",
        keywords_config=keywords_config,
        selected_category=selected_category,
        articles=filtered_articles,
        ai_items=ai_items,
        report=report,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

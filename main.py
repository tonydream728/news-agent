from __future__ import annotations

from news_fetcher import fetch_news, load_keywords
from report_writer import write_daily_markdown, write_json
from summarizer import build_daily_report, enrich_articles


def main() -> None:
    keywords_config = load_keywords("keywords.yml")
    articles = fetch_news(keywords_config)
    enriched_articles = enrich_articles(articles)
    report = build_daily_report(enriched_articles)

    write_json("data/news.json", enriched_articles)
    write_json("data/daily_report.json", report)
    write_daily_markdown("daily_report.md", report)

    print(f"Generated {len(enriched_articles)} articles.")
    print("Updated data/news.json, data/daily_report.json, and daily_report.md.")


if __name__ == "__main__":
    main()

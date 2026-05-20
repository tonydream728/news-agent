from __future__ import annotations

from datetime import datetime, timedelta, timezone

from news_fetcher import fetch_news, load_keywords
from report_writer import write_daily_markdown, write_json
from summarizer import build_daily_report, enrich_articles


TAIPEI_TZ = timezone(timedelta(hours=8))


def main() -> None:
    keywords_config = load_keywords("keywords.yml")
    now_local = datetime.now(TAIPEI_TZ)
    today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    history_start_local = today_start_local - timedelta(days=7)

    now_utc = now_local.astimezone(timezone.utc)
    today_start_utc = today_start_local.astimezone(timezone.utc)
    history_start_utc = history_start_local.astimezone(timezone.utc)

    today_articles = enrich_articles(
        fetch_news(
            keywords_config,
            start_at=today_start_utc,
            end_at=now_utc + timedelta(minutes=5),
            period="today",
        )
    )
    history_articles = enrich_articles(
        fetch_news(
            keywords_config,
            start_at=history_start_utc,
            end_at=today_start_utc,
            period="history_7d",
        )
    )

    today_report = build_daily_report(
        today_articles,
        period_name="today",
        period_label="當日最新新聞",
        start_at=today_start_local.isoformat(),
        end_at=now_local.isoformat(),
    )
    history_report = build_daily_report(
        history_articles,
        period_name="history_7d",
        period_label="近七日歷史新聞",
        start_at=history_start_local.isoformat(),
        end_at=today_start_local.isoformat(),
    )

    combined_report = {
        "generated_at": now_local.isoformat(),
        "timezone": "Asia/Taipei",
        "sections": {
            "today": today_report,
            "history_7d": history_report,
        },
    }

    write_json("data/news_today.json", today_articles)
    write_json("data/news_7d_history.json", history_articles)
    write_json("data/news.json", {"today": today_articles, "history_7d": history_articles})
    write_json("data/daily_report.json", combined_report)
    write_daily_markdown("daily_report.md", combined_report)

    print(f"Generated {len(today_articles)} today articles.")
    print(f"Generated {len(history_articles)} history articles.")
    print("Updated two-section news data and daily_report.md.")


if __name__ == "__main__":
    main()

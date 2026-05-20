from __future__ import annotations

import hashlib
import math
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from urllib.parse import quote_plus

import feedparser
import yaml


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"


def load_keywords(path: str = "keywords.yml") -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    normalized: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            normalized[key] = {"label": key, "keywords": value}
        else:
            normalized[key] = {
                "label": value.get("label", key),
                "keywords": value.get("keywords", []),
            }
    return normalized


def fetch_news(
    keywords_config: dict[str, dict[str, Any]],
    max_items_per_keyword: Optional[int] = None,
    lookback_days: Optional[int] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    period: str = "latest",
) -> list[dict[str, Any]]:
    max_items = max_items_per_keyword or int(os.getenv("NEWS_AGENT_MAX_ITEMS_PER_KEYWORD", "5"))
    now = datetime.now(timezone.utc)

    if start_at is None:
        days = lookback_days or int(os.getenv("NEWS_AGENT_LOOKBACK_DAYS", "1"))
        start_at = now - timedelta(days=days)
    else:
        days = max(1, math.ceil((now - start_at).total_seconds() / 86400))

    if end_at is None:
        end_at = now + timedelta(minutes=5)

    start_at = _as_utc(start_at)
    end_at = _as_utc(end_at)

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for category_key, category in keywords_config.items():
        label = category["label"]
        for keyword in category["keywords"]:
            feed_url = GOOGLE_NEWS_RSS.format(query=quote_plus(f"{keyword} when:{days}d"))
            parsed = feedparser.parse(feed_url)
            entries = parsed.entries[:max_items]

            for entry in entries:
                article = _entry_to_article(entry, category_key, label, keyword, period)
                published_at = _published_datetime(article["published_at"])
                if published_at < start_at or published_at >= end_at:
                    continue

                dedupe_key = article["url"] or article["title"]
                if dedupe_key in seen:
                    _append_keyword_match(articles, dedupe_key, category_key, label, keyword)
                    continue
                seen.add(dedupe_key)
                articles.append(article)

    if not articles:
        articles = build_sample_articles(keywords_config, period=period, published_at=start_at)

    return sorted(articles, key=lambda item: item.get("published_at", ""), reverse=True)


def _entry_to_article(
    entry: Any,
    category_key: str,
    category_label: str,
    keyword: str,
    period: str,
) -> dict[str, Any]:
    title = getattr(entry, "title", "未命名新聞")
    url = getattr(entry, "link", "")
    source = "Google News"

    if hasattr(entry, "source") and getattr(entry.source, "title", None):
        source = entry.source.title

    published_at = _parse_time(getattr(entry, "published", None) or getattr(entry, "updated", None))
    article_id = hashlib.sha1(f"{period}|{title}|{url}".encode("utf-8")).hexdigest()[:16]

    return {
        "id": article_id,
        "period": period,
        "title": title,
        "source": source,
        "published_at": published_at,
        "url": url,
        "matched_keywords": [keyword],
        "categories": [category_key],
        "category_labels": [category_label],
        "raw_summary": getattr(entry, "summary", ""),
    }


def _append_keyword_match(
    articles: list[dict[str, Any]],
    dedupe_key: str,
    category_key: str,
    category_label: str,
    keyword: str,
) -> None:
    for article in articles:
        if (article["url"] or article["title"]) != dedupe_key:
            continue
        if keyword not in article["matched_keywords"]:
            article["matched_keywords"].append(keyword)
        if category_key not in article["categories"]:
            article["categories"].append(category_key)
        if category_label not in article["category_labels"]:
            article["category_labels"].append(category_label)
        return


def _parse_time(value: Optional[str]) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, AttributeError):
        return datetime.now(timezone.utc).isoformat()


def _published_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.now(timezone.utc)
    return _as_utc(parsed)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_sample_articles(
    keywords_config: dict[str, dict[str, Any]],
    period: str = "latest",
    published_at: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    published = _as_utc(published_at or datetime.now(timezone.utc)).isoformat()
    samples: list[dict[str, Any]] = []
    for category_key, category in keywords_config.items():
        keyword = category["keywords"][0] if category["keywords"] else category["label"]
        title = f"{category['label']}觀察：{keyword}帶動餐飲市場新話題"
        samples.append(
            {
                "id": hashlib.sha1(f"sample-{period}-{category_key}".encode("utf-8")).hexdigest()[:16],
                "period": period,
                "title": title,
                "source": "Sample News",
                "published_at": published,
                "url": "https://example.com/news-agent-sample",
                "matched_keywords": [keyword],
                "categories": [category_key],
                "category_labels": [category["label"]],
                "raw_summary": f"這是一則示範新聞，用來呈現 {category['label']} 的五層情報分析資料。",
                "sample": True,
            }
        )
    return samples

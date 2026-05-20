from __future__ import annotations

import re
from collections import Counter
from typing import Any


CATEGORY_LABELS = [
    "競品異動",
    "行銷靈感",
    "市場情報",
    "品牌監控",
    "世界料理趨勢",
    "精釀啤酒",
    "會員經濟",
]

HIGH_VALUE_TERMS = [
    "開幕",
    "展店",
    "合作",
    "新品",
    "活動",
    "會員",
    "精釀",
    "啤酒",
    "餐酒",
    "趨勢",
    "社群",
    "品牌",
    "市場",
    "料理",
]


def enrich_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [enrich_article(article) for article in articles]


def enrich_article(article: dict[str, Any]) -> dict[str, Any]:
    title = article.get("title", "")
    raw_summary = _clean_text(article.get("raw_summary", ""))
    category_labels = article.get("category_labels", [])
    matched_keywords = article.get("matched_keywords", [])

    score = _score_article(title, raw_summary, matched_keywords, category_labels)
    classification = _choose_classification(title, raw_summary, category_labels)

    article["ai"] = {
        "worth_reading": score >= 3,
        "score": score,
        "reason": _build_reason(score, matched_keywords, classification),
        "classification": classification,
        "summary_zh": _build_summary(title, raw_summary, category_labels),
        "abv_value": _build_abv_value(title, classification, matched_keywords),
    }
    return article


def build_daily_report(
    articles: list[dict[str, Any]],
    period_name: str = "today",
    period_label: str = "當日最新新聞",
    start_at: str | None = None,
    end_at: str | None = None,
) -> dict[str, Any]:
    top_articles = sorted(
        [article for article in articles if article.get("ai", {}).get("worth_reading")],
        key=lambda item: item.get("ai", {}).get("score", 0),
        reverse=True,
    )[:5]

    if len(top_articles) < 5:
        for article in sorted(articles, key=lambda item: item.get("ai", {}).get("score", 0), reverse=True):
            if article not in top_articles:
                top_articles.append(article)
            if len(top_articles) == 5:
                break

    category_counts = Counter()
    high_score_count = 0
    for article in articles:
        for label in article.get("category_labels", []):
            category_counts[label] += 1
        if article.get("ai", {}).get("score", 0) >= 4:
            high_score_count += 1

    hot_terms = _extract_hot_terms(articles)
    content_ideas = _build_content_ideas(top_articles or articles)

    return {
        "generated_at": _generated_at(),
        "period": {
            "name": period_name,
            "label": period_label,
            "start_at": start_at,
            "end_at": end_at,
        },
        "layer_1_keyword_news": articles,
        "layer_2_ai_filtering": [
            {
                "id": article["id"],
                "title": article["title"],
                "source": article["source"],
                "published_at": article["published_at"],
                "url": article["url"],
                "matched_keywords": article["matched_keywords"],
                "category_labels": article["category_labels"],
                **article["ai"],
            }
            for article in articles
        ],
        "layer_3_daily_brief": [
            {
                "id": article["id"],
                "title": article["title"],
                "source": article["source"],
                "url": article["url"],
                "score": article["ai"]["score"],
                "summary_zh": article["ai"]["summary_zh"],
                "abv_impact": article["ai"]["abv_value"],
            }
            for article in top_articles
        ],
        "layer_4_content_ideas": content_ideas,
        "layer_5_trend_analysis": {
            "category_counts": dict(category_counts),
            "high_score_news_count": high_score_count,
            "hot_terms": hot_terms,
            "trend_judgement": _build_trend_judgement(category_counts, hot_terms),
            "weekly_actions": _build_weekly_actions(category_counts, hot_terms),
        },
    }


def _score_article(title: str, raw_summary: str, matched_keywords: list[str], category_labels: list[str]) -> int:
    text = f"{title} {raw_summary}"
    score = 2
    score += min(2, sum(1 for term in HIGH_VALUE_TERMS if term.lower() in text.lower()))
    if any(label in ["競品異動", "品牌監控", "精釀啤酒", "會員經濟"] for label in category_labels):
        score += 1
    if len(matched_keywords) >= 2:
        score += 1
    return max(1, min(5, score))


def _choose_classification(title: str, raw_summary: str, category_labels: list[str]) -> str:
    text = f"{title} {raw_summary}"
    if category_labels:
        return category_labels[0]
    for label in CATEGORY_LABELS:
        if label[:2] in text:
            return label
    return "市場情報"


def _build_reason(score: int, matched_keywords: list[str], classification: str) -> str:
    keywords = "、".join(matched_keywords[:3]) if matched_keywords else "追蹤關鍵字"
    if score >= 4:
        return f"命中 {keywords}，且與「{classification}」高度相關，值得優先閱讀。"
    if score == 3:
        return f"命中 {keywords}，可作為「{classification}」的輔助觀察。"
    return f"命中 {keywords}，但目前訊號較弱，可低優先追蹤。"


def _build_summary(title: str, raw_summary: str, category_labels: list[str]) -> str:
    cleaned = raw_summary or title
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 120:
        cleaned = cleaned[:117] + "..."
    category = "、".join(category_labels) if category_labels else "市場情報"
    return f"這則新聞聚焦於「{title}」，可放在 {category} 脈絡下觀察。{cleaned}"


def _build_abv_value(title: str, classification: str, matched_keywords: list[str]) -> str:
    keyword_hint = "、".join(matched_keywords[:2]) if matched_keywords else "相關議題"
    mapping = {
        "競品異動": "可用來追蹤同業展店、活動包裝與產品組合，協助 ABV 調整檔期與店型定位。",
        "行銷靈感": "可延伸為社群貼文、短影音或節慶活動主題，協助 ABV 提高內容新鮮度。",
        "市場情報": "可作為 ABV 評估餐飲需求、消費情緒與商圈變化的參考。",
        "品牌監控": "可協助 ABV 掌握品牌被討論的情境，及早回應口碑與搜尋需求。",
        "世界料理趨勢": "可支援 ABV 菜單故事、主題餐期與跨國料理溝通角度。",
        "精釀啤酒": "可協助 ABV 強化啤酒選品、酒款教育與餐酒搭配內容。",
        "會員經濟": "可用於優化會員分眾、回訪誘因與 LINE 推播策略。",
    }
    return f"{mapping.get(classification, mapping['市場情報'])}本則可從「{keyword_hint}」切入。"


def _extract_hot_terms(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms: list[str] = []
    stop_words = {"Google", "News", "Sample", "https", "com", "html"}
    for article in articles:
        text = f"{article.get('title', '')} {' '.join(article.get('matched_keywords', []))}"
        terms.extend(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9-]{2,}", text))

    counter = Counter(term for term in terms if term not in stop_words)
    return [{"term": term, "count": count} for term, count in counter.most_common(10)]


def _build_content_ideas(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    ideas: list[dict[str, str]] = []
    seed_articles = articles[:5]
    while len(seed_articles) < 5 and articles:
        seed_articles.append(articles[len(seed_articles) % len(articles)])

    for index, article in enumerate(seed_articles[:5], start=1):
        title = article.get("title", "今日餐飲趨勢")
        classification = article.get("ai", {}).get("classification", "市場情報")
        ideas.append(
            {
                "id": f"idea-{index}",
                "source_title": title,
                "fb_ig_angle": f"用「{title}」包裝成一則趨勢觀察，邀請粉絲留言分享自己的餐酒經驗。",
                "reels_shorts_script": f"開場 3 秒提出問題：最近大家都在聊什麼 {classification}？接著用 3 個畫面帶出 ABV 的菜色、酒款與情境。",
                "line_push_angle": f"以會員專屬提醒切入：本週精選一個與「{classification}」相關的餐酒體驗或活動。",
                "seo_title": f"{classification}趨勢怎麼看？從「{title}」看餐酒館內容與選品機會",
            }
        )
    return ideas


def _build_trend_judgement(category_counts: Counter, hot_terms: list[dict[str, Any]]) -> str:
    if not category_counts:
        return "今日新聞量偏低，建議先累積更多資料後再判斷趨勢。"
    top_category, count = category_counts.most_common(1)[0]
    top_terms = "、".join(item["term"] for item in hot_terms[:3]) or "餐飲市場"
    return f"今日以「{top_category}」聲量最高，共 {count} 則；熱門詞集中在 {top_terms}，代表內容可圍繞消費場景、選品與活動溝通展開。"


def _build_weekly_actions(category_counts: Counter, hot_terms: list[dict[str, Any]]) -> list[str]:
    top_category = category_counts.most_common(1)[0][0] if category_counts else "市場情報"
    top_term = hot_terms[0]["term"] if hot_terms else "餐酒趨勢"
    return [
        f"本週安排一則「{top_category}」主題貼文，連結 ABV 的實際菜色、酒款或門市活動。",
        f"針對「{top_term}」製作短影音腳本，讓店內體驗變成可分享的內容資產。",
        "把高分新聞轉成 LINE 分眾推播素材，測試會員回訪與訂位反應。",
    ]


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return re.sub(r"\s+", " ", value).strip()


def _generated_at() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()

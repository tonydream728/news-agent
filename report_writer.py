from __future__ import annotations

import json
import os
from typing import Any


def ensure_data_dir(path: str = "data") -> None:
    os.makedirs(path, exist_ok=True)


def write_json(path: str, payload: Any) -> None:
    ensure_data_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def write_daily_markdown(path: str, report: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# ABV 每日五層情報報告")
    lines.append("")
    lines.append(f"產生時間：{report.get('generated_at', '')}")
    lines.append(f"時區：{report.get('timezone', 'Asia/Taipei')}")
    lines.append("")

    sections = report.get("sections")
    if sections:
        _append_section(lines, "當日最新新聞", sections.get("today", {}))
        _append_section(lines, "昨日往前七日歷史新聞", sections.get("history_7d", {}))
    else:
        _append_section(lines, "每日情報", report)

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def _append_section(lines: list[str], title: str, report: dict[str, Any]) -> None:
    period = report.get("period", {})
    lines.append(f"## {title}")
    if period.get("start_at") and period.get("end_at"):
        lines.append(f"資料區間：{period['start_at']} 至 {period['end_at']}")
    lines.append("")

    lines.append("### 第一層：關鍵字新聞列表")
    for article in report.get("layer_1_keyword_news", []):
        lines.append(f"- [{article['title']}]({article['url']})")
        lines.append(f"  - 來源：{article['source']}")
        lines.append(f"  - 日期：{article['published_at']}")
        lines.append(f"  - 命中關鍵字：{'、'.join(article.get('matched_keywords', []))}")
    lines.append("")

    lines.append("### 第二層：AI 智能篩選")
    for item in report.get("layer_2_ai_filtering", []):
        lines.append(f"- {item['title']}")
        lines.append(f"  - 是否值得閱讀：{'是' if item['worth_reading'] else '否'}")
        lines.append(f"  - 評分：{item['score']} / 5")
        lines.append(f"  - 分類：{item['classification']}")
        lines.append(f"  - 理由：{item['reason']}")
    lines.append("")

    lines.append("### 第三層：戰情報告")
    for index, item in enumerate(report.get("layer_3_daily_brief", []), start=1):
        lines.append(f"#### {index}. {item['title']}")
        lines.append(f"- 摘要：{item['summary_zh']}")
        lines.append(f"- 對 ABV 的可能影響：{item['abv_impact']}")
        lines.append(f"- 原文：{item['url']}")
        lines.append("")

    lines.append("### 第四層：社群內容靈感池")
    for idea in report.get("layer_4_content_ideas", []):
        lines.append(f"#### {idea['source_title']}")
        lines.append(f"- FB/IG 貼文角度：{idea['fb_ig_angle']}")
        lines.append(f"- Reels/Shorts 腳本方向：{idea['reels_shorts_script']}")
        lines.append(f"- LINE 推播角度：{idea['line_push_angle']}")
        lines.append(f"- SEO 文章題目：{idea['seo_title']}")
        lines.append("")

    trend = report.get("layer_5_trend_analysis", {})
    lines.append("### 第五層：企業級輿情/趨勢分析")
    lines.append("#### 各分類新聞數量")
    for category, count in trend.get("category_counts", {}).items():
        lines.append(f"- {category}：{count}")
    lines.append(f"- 高分新聞數量：{trend.get('high_score_news_count', 0)}")
    lines.append("")
    lines.append("#### 熱門詞")
    for term in trend.get("hot_terms", []):
        lines.append(f"- {term['term']}：{term['count']}")
    lines.append("")
    lines.append(f"#### 趨勢判斷\n{trend.get('trend_judgement', '')}")
    lines.append("")
    lines.append("#### ABV 可行動建議")
    for action in trend.get("weekly_actions", []):
        lines.append(f"- {action}")
    lines.append("")

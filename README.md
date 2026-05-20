# News Agent

Python + Flask 新聞追蹤 Dashboard，依照 `keywords.yml` 抓取新聞，產出五層情報架構報告，並提供可用瀏覽器閱讀的 Dashboard。

## 功能

- 依照 `keywords.yml` 關鍵字抓取新聞
- 每次執行 `main.py` 後輸出：
  - `data/news.json`
  - `data/daily_report.json`
  - `daily_report.md`
- Flask Dashboard 顯示五層情報：
  1. 關鍵字新聞列表
  2. AI 智能篩選
  3. 每日戰情報告
  4. 社群內容靈感池
  5. 輿情與趨勢分析
- 支援左側分類選單與手機版閱讀

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 設定關鍵字

編輯 `keywords.yml`：

```yml
competitors:
  label: 競品異動
  keywords:
    - 啤酒餐廳
    - 精釀酒吧
```

每個分類需要：

- `label`：顯示名稱
- `keywords`：要追蹤的關鍵字清單

## 產生每日情報

```bash
python3 main.py
```

執行後會更新：

- `data/news.json`
- `data/daily_report.json`
- `daily_report.md`

如果 RSS 抓取失敗，系統會產生示範資料，方便你先確認 Dashboard 與流程。

## 啟動網頁 Dashboard

```bash
python3 app.py
```

開啟瀏覽器：

```text
http://127.0.0.1:5000
```

可以用網址參數篩選分類：

```text
http://127.0.0.1:5000?category=craft_beer
```

## 專案結構

```text
news-agent/
├── README.md
├── requirements.txt
├── .env.example
├── keywords.yml
├── main.py
├── app.py
├── news_fetcher.py
├── summarizer.py
├── report_writer.py
├── data/
│   └── news.json
├── templates/
│   └── index.html
├── static/
│   └── style.css
└── .github/workflows/daily-news.yml
```

## GitHub Actions

`.github/workflows/daily-news.yml` 會每日執行 `python main.py`。如需把報告 commit 回 repo，可在 workflow 中加入 commit/push 步驟。

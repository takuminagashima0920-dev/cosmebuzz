"""
CosmeBuzz GitHub Pages 日次更新スクリプト
beauty_trends/data/ のバックアップJSONからindex.htmlを生成してgit push
"""

from __future__ import annotations

import json
import glob
import os
import re
import subprocess
from datetime import datetime
from html import escape
from urllib.parse import quote


BACKUP_DIR = os.path.expanduser("~/beauty_trends/data")
SITE_DIR = os.path.expanduser("~/cosmebuzz-site")
INDEX_PATH = os.path.join(SITE_DIR, "index.html")
GH_BIN = os.path.expanduser("~/bin/gh")

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def get_latest_backup():
    """最新のバックアップJSONを取得"""
    pattern = os.path.join(BACKUP_DIR, "backup_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print("❌ バックアップファイルが見つかりません")
        return None
    latest = files[-1]
    print(f"📄 最新バックアップ: {os.path.basename(latest)}")
    return latest


def load_backup(path):
    """バックアップJSONを読み込み"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_price(price):
    """価格をフォーマット（¥1,280形式）"""
    try:
        p = int(price)
        if p <= 0:
            return ""
        return f"&yen;{p:,}"
    except (ValueError, TypeError):
        return ""


_RAKUTEN_NOISE = {
    "大容量", "美容", "日本製", "デイリー", "メンズにも", "ランキング",
    "プレゼント", "ギフト", "送料無料", "ポイント", "即納", "国内正規品",
    "正規品", "公式", "限定", "セール", "SALE", "スパセ", "お買い物マラソン",
    "スーパーSALE", "楽天スーパーSALE", "ZZ", "SS", "FS",
}


def clean_product_name(name, max_len=35):
    """楽天等のSEOキーワード羅列商品名を整理"""
    # 【...】ブラケットを除去
    name = re.sub(r'【[^】]*】', '', name)
    # [...] ブラケットを除去（ブランド名[XX]パターンは保持）
    name = re.sub(r'\[[^\]]{8,}\]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # ノイズワード除去
    words = [w for w in name.split() if w not in _RAKUTEN_NOISE]
    # 類似ワード除去（共通部分文字列3文字以上を含むワードは2回目以降除去）
    kept = []
    for w in words:
        is_dup = False
        for prev in kept:
            if len(w) >= 3 and len(prev) >= 3:
                for i in range(len(w) - 2):
                    if w[i:i+3] in prev:
                        is_dup = True
                        break
            if is_dup:
                break
        if not is_dup:
            kept.append(w)
    name = " ".join(kept)
    if len(name) > max_len:
        name = name[:max_len - 1] + "…"
    return name


def sanitize_url(url):
    """URLスキームをhttp/httpsのみ許可"""
    if not url:
        return ""
    url = url.strip()
    if url.startswith(("http://", "https://")):
        return url
    return ""


def make_rakuten_search_url(product_name):
    """楽天商品名から検索URLを生成（URLなし時のフォールバック）"""
    # 短いキーワードを抽出（最初の主要ワード）
    keywords = re.sub(r'【[^】]*】|\[[^\]]*\]', '', product_name)
    keywords = re.sub(r'\s+', ' ', keywords).strip()
    # 先頭30文字程度のキーワードで検索
    words = keywords.split()[:4]
    query = " ".join(words)
    return f"https://search.rakuten.co.jp/search/mall/{quote(query)}/"


def format_date(dt_str):
    """日時文字列から表示用日付を生成"""
    try:
        dt = datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        dt = datetime.now()
    weekday = WEEKDAY_JA[dt.weekday()]
    return f"{dt.year}年{dt.month}月{dt.day}日（{weekday}）のトレンド", dt.strftime("%Y-%m-%d")


def build_ec_items_html(ec_sales):
    """EC セール情報のHTMLを生成"""
    if not ec_sales:
        return '      <div class="ec-item"><div class="ec-product-name" style="color: var(--text-secondary); text-align: center; padding: 16px 0;">本日のセール情報はありません</div></div>'

    platform_map = {
        "楽天市場": ("rakuten", "楽天市場"),
        "Amazon": ("amazon", "Amazon"),
        "Qoo10": ("qoo10", "Qoo10"),
    }

    items_html = []
    for item in ec_sales:
        site = item.get("site", "")
        platform_key, badge_text = platform_map.get(site, ("rakuten", site))

        raw_name = item.get("product_name", "")
        product_name = escape(clean_product_name(raw_name))

        sale_price = item.get("sale_price", 0)
        original_price = item.get("original_price", 0)
        discount_rate = item.get("discount_rate", 0)

        # discount表示（型安全）
        discount_html = ""
        try:
            dr = int(str(discount_rate).replace("%", "").replace("％", ""))
            if dr > 0:
                discount_html = f'          <span class="ec-discount">-{dr}% OFF</span>'
        except (ValueError, TypeError):
            dr = 0
        if not discount_html:
            try:
                op = int(original_price)
                sp = int(sale_price)
                if op > 0 and sp > 0 and op > sp:
                    rate = round((1 - sp / op) * 100)
                    if rate > 0:
                        discount_html = f'          <span class="ec-discount">-{rate}% OFF</span>'
            except (ValueError, TypeError):
                pass

        # 価格行
        price_html = f'<span class="ec-price">{format_price(sale_price)}</span>'
        orig_fmt = format_price(original_price)
        if orig_fmt and format_price(sale_price) and orig_fmt != format_price(sale_price):
            price_html += f'\n            <span class="ec-original-price">{orig_fmt}</span>'

        # URL（スキーム検証 + 楽天フォールバック）
        url = sanitize_url(item.get("url", ""))
        if not url and platform_key == "rakuten" and raw_name:
            url = make_rakuten_search_url(raw_name)
        open_tag = f'<a href="{escape(url)}" target="_blank" rel="noopener" style="text-decoration:none; color:inherit;">' if url else ""
        close_tag = "</a>" if url else ""

        # ソースバッジ
        source = item.get("source", "")
        if source == "rakuten_api":
            source_badge = '<span class="source-badge source-badge-api">API</span>'
        else:
            source_badge = '<span class="source-badge source-badge-ai">AI検索</span>'

        items_html.append(f"""      {open_tag}<div class="ec-item" data-platform="{platform_key}">
        <div class="ec-item-header">
          <span class="ec-badge ec-badge-{platform_key}">{escape(badge_text)}{source_badge}</span>
{discount_html}
        </div>
        <div class="ec-product-name">{product_name}</div>
        <div class="ec-price-row">
          {price_html}
        </div>
      </div>{close_tag}""")

    return "\n\n".join(items_html)


def _normalize_rating(rating):
    """rating値を正規化（★を除去して数値のみに）"""
    s = escape(str(rating).replace("★", "").replace("☆", "").strip())
    return s if s else ""


def _parse_ingredient_tags(ing_str):
    """成分文字列をタグリストに分割"""
    tags = []
    if ing_str:
        for ing in re.split(r"[、,/・]+", str(ing_str)):
            # 括弧内の役割説明を分離
            m = re.match(r'^([^（(]+)[（(]([^）)]+)[）)]$', ing.strip())
            if m:
                tags.append((m.group(1).strip(), m.group(2).strip()))
            else:
                t = ing.strip()
                if t and len(t) < 30:
                    tags.append((t, ""))
    return tags


def build_ingredient_items_html(ingredients):
    """成分比較のHTMLを生成"""
    if not ingredients:
        return '      <div class="ingredient-pair"><div class="ingredient-summary" style="text-align: center;">本日の成分比較データはありません</div></div>'

    pairs_html = []
    for item in ingredients:
        category = escape(item.get("category", ""))
        petit_name = escape(item.get("petit_name", ""))
        petit_price = format_price(item.get("petit_price", 0))
        petit_rating = _normalize_rating(item.get("petit_rating", ""))
        depa_name = escape(item.get("depa_name", ""))
        depa_price = format_price(item.get("depa_price", 0))
        depa_rating = _normalize_rating(item.get("depa_rating", ""))
        summary = escape(item.get("summary", ""))

        # 新フィールド
        similarity_score = item.get("similarity_score", 0)
        why_similar = escape(item.get("why_similar", ""))
        can_replace = escape(item.get("can_replace", ""))
        shared_ingredients = item.get("shared_ingredients", "")
        petit_unique = item.get("petit_unique", "")
        depa_unique = item.get("depa_unique", "")

        # 類似度バー + 代替判定バッジ
        similarity_html = ""
        if similarity_score > 0:
            bar_color = "#4ECDC4" if similarity_score >= 70 else "#FFCC00" if similarity_score >= 40 else "#FF6B6B"
            similarity_html = f"""        <div class="ingredient-similarity">
          <div class="similarity-header">
            <span class="similarity-label">成分類似度</span>
            <span class="similarity-score" style="color: {bar_color};">{similarity_score}%</span>
          </div>
          <div class="similarity-bar-bg">
            <div class="similarity-bar" style="width: {similarity_score}%; background: {bar_color};"></div>
          </div>
        </div>"""

        # 代替可能性バッジ
        replace_html = ""
        if can_replace:
            if "ほぼ" in can_replace:
                badge_cls = "replace-high"
            elif "部分" in can_replace:
                badge_cls = "replace-mid"
            else:
                badge_cls = "replace-low"
            replace_html = f'          <span class="replace-badge {badge_cls}">{can_replace}</span>'

        # 共通成分タグ（役割付き）
        shared_tags = _parse_ingredient_tags(shared_ingredients)
        shared_tags_html = "\n".join(
            f'          <span class="ingredient-tag tag-shared">{escape(name)}<span class="tag-role">{escape(role)}</span></span>'
            if role else f'          <span class="ingredient-tag tag-shared">{escape(name)}</span>'
            for name, role in shared_tags[:4]
        )

        # 固有成分タグ
        petit_tags = _parse_ingredient_tags(petit_unique)
        depa_tags = _parse_ingredient_tags(depa_unique)
        unique_tags_html = ""
        if petit_tags or depa_tags:
            petit_unique_html = "".join(
                f'<span class="ingredient-tag tag-petitpra">{escape(name)}</span>'
                for name, _ in petit_tags[:2]
            )
            depa_unique_html = "".join(
                f'<span class="ingredient-tag tag-depacos">{escape(name)}</span>'
                for name, _ in depa_tags[:2]
            )
            unique_tags_html = f"""        <div class="ingredient-unique-row">
          <div class="unique-group"><span class="unique-label label-petitpra">固有</span>{petit_unique_html}</div>
          <div class="unique-group"><span class="unique-label label-depacos">固有</span>{depa_unique_html}</div>
        </div>"""

        # フォールバック: 新フィールドがない場合は旧方式の成分タグ
        if not shared_tags_html and not unique_tags_html:
            petit_ingredients = item.get("petit_ingredients", "")
            depa_ingredients = item.get("depa_ingredients", "")
            seen = []
            for ing_str in [petit_ingredients, depa_ingredients]:
                if ing_str:
                    for ing in re.split(r"[、,/・\s]+", str(ing_str)):
                        ing = ing.strip()
                        if ing and len(ing) < 20 and ing not in seen:
                            seen.append(ing)
            shared_tags_html = "\n".join(
                f'          <span class="ingredient-tag tag-shared">{escape(t)}</span>'
                for t in seen[:6]
            )

        # 成分解説（why_similar）
        analysis_html = ""
        if why_similar:
            analysis_html = f"""        <div class="ingredient-analysis">
          <div class="analysis-label">なぜ似ている？</div>
          <div class="analysis-text">{why_similar}</div>
        </div>"""

        pairs_html.append(f"""      <div class="ingredient-pair" data-category="{escape(category.lower())}">
        <div class="ingredient-pair-header">
          <div class="ingredient-category">{category}</div>
{replace_html}
        </div>
{similarity_html}
        <div class="ingredient-vs-grid">
          <div class="ingredient-product">
            <span class="ingredient-label label-petitpra">プチプラ</span>
            <div class="ingredient-product-name">{petit_name}</div>
            <div class="ingredient-product-price price-petitpra">{petit_price}</div>
            <div class="ingredient-product-rating"><span class="star">&#x2605;</span> {petit_rating}</div>
          </div>
          <div class="ingredient-vs-divider">
            <div class="vs-circle">VS</div>
          </div>
          <div class="ingredient-product">
            <span class="ingredient-label label-depacos">デパコス</span>
            <div class="ingredient-product-name">{depa_name}</div>
            <div class="ingredient-product-price price-depacos">{depa_price}</div>
            <div class="ingredient-product-rating"><span class="star">&#x2605;</span> {depa_rating}</div>
          </div>
        </div>
        <div class="ingredient-tags-section">
          <div class="tags-label">共通成分</div>
          <div class="ingredient-tags">
{shared_tags_html}
          </div>
        </div>
{unique_tags_html}
{analysis_html}
        <div class="ingredient-summary">
          {summary}
        </div>
      </div>""")

    return "\n\n".join(pairs_html)


def build_trend_items_html(trends):
    """Google検索トレンドのHTMLを生成"""
    if not trends:
        return '      <div class="trend-item"><div class="trend-keyword" style="color: var(--text-secondary);">本日のトレンドデータはありません</div></div>'

    max_score = max((t.get("score", 0) for t in trends), default=100) or 100

    items_html = []
    for i, trend in enumerate(trends[:5], 1):
        keyword = escape(trend.get("keyword", ""))
        score = trend.get("score", 0)
        bar_width = round(score / max_score * 100)
        rank_class = ' trend-rank-1' if i == 1 else ''

        items_html.append(f"""      <div class="trend-item" data-rank="{i}">
        <span class="trend-rank{rank_class}">{i}</span>
        <div class="trend-content">
          <div class="trend-keyword">{keyword}</div>
          <div class="trend-bar-container">
            <div class="trend-bar" style="width: {bar_width}%;"></div>
          </div>
        </div>
        <span class="trend-score">{score}</span>
      </div>""")

    return "\n\n".join(items_html)


def update_html(data, dt_str):
    """index.htmlの動的部分を更新"""
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 日付更新
    date_display, date_attr = format_date(dt_str)
    html = re.sub(
        r'<div class="header-date" id="report-date"[^>]*>.*?</div>',
        f'<div class="header-date" id="report-date" data-date="{date_attr}">{date_display}</div>',
        html
    )

    # EC セール
    ec_html = build_ec_items_html(data.get("ec_sales", []))
    html = re.sub(
        r'(<!-- \[DYNAMIC: ec-items\] Start -->\s*<div id="ec-items">)(.*?)(</div>\s*<!-- \[DYNAMIC: ec-items\] End -->)',
        rf'\1\n\n{ec_html}\n\n    \3',
        html,
        flags=re.DOTALL
    )

    # 成分比較
    ingredient_html = build_ingredient_items_html(data.get("ingredient_comparison", []))
    html = re.sub(
        r'(<!-- \[DYNAMIC: ingredient-items\] Start -->\s*<div id="ingredient-items">)(.*?)(</div>\s*<!-- \[DYNAMIC: ingredient-items\] End -->)',
        rf'\1\n\n{ingredient_html}\n\n    \3',
        html,
        flags=re.DOTALL
    )

    # Google トレンド
    trend_html = build_trend_items_html(data.get("search_trends", []))
    html = re.sub(
        r'(<!-- \[DYNAMIC: trend-items\] Start -->\s*<div id="trend-items">)(.*?)(</div>\s*<!-- \[DYNAMIC: trend-items\] End -->)',
        rf'\1\n\n{trend_html}\n\n    \3',
        html,
        flags=re.DOTALL
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ index.html 更新完了")


ARCHIVE_PATH = os.path.join(SITE_DIR, "archive.html")


def collect_archive_pairs():
    """全バックアップから成分比較データを収集（日付別、重複除去）"""
    pattern = os.path.join(BACKUP_DIR, "backup_*.json")
    files = sorted(glob.glob(pattern))

    # 日付ごとに最新のバックアップのみ使う
    date_files = {}
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        dt = data.get("datetime", "")[:10]
        if dt:
            date_files[dt] = (f, data)

    all_pairs = []
    seen_keys = set()
    for dt in sorted(date_files.keys(), reverse=True):
        _, backup = date_files[dt]
        items = backup.get("data", {}).get("ingredient_comparison", [])
        for item in items:
            # 重複チェック（商品名ペアで判定）
            key = (item.get("petit_name", ""), item.get("depa_name", ""))
            if key[0] and key[1] and key not in seen_keys:
                seen_keys.add(key)
                item["_date"] = dt
                all_pairs.append(item)

    return all_pairs


def build_archive_html(pairs):
    """アーカイブページのHTMLを生成"""
    # カテゴリ一覧
    categories = []
    for p in pairs:
        cat = p.get("category", "")
        if cat and cat not in categories:
            categories.append(cat)

    # フィルターボタン
    filter_html = '        <button class="filter-btn active" data-cat="all">すべて</button>\n'
    for cat in categories:
        filter_html += f'        <button class="filter-btn" data-cat="{escape(cat)}">{escape(cat)}</button>\n'

    # ペアカード
    cards_html = []
    for item in pairs:
        category = escape(item.get("category", ""))
        petit_name = escape(item.get("petit_name", ""))
        petit_price = format_price(item.get("petit_price", 0))
        petit_rating = _normalize_rating(item.get("petit_rating", ""))
        depa_name = escape(item.get("depa_name", ""))
        depa_price = format_price(item.get("depa_price", 0))
        depa_rating = _normalize_rating(item.get("depa_rating", ""))
        summary = escape(item.get("summary", ""))
        date_str = item.get("_date", "")

        similarity_score = item.get("similarity_score", 0)
        why_similar = escape(item.get("why_similar", ""))
        can_replace = escape(item.get("can_replace", ""))
        shared_ingredients = item.get("shared_ingredients", "")

        # 類似度バー
        sim_html = ""
        if similarity_score > 0:
            bar_color = "#4ECDC4" if similarity_score >= 70 else "#FFCC00" if similarity_score >= 40 else "#FF6B6B"
            sim_html = f"""<div class="arc-similarity">
            <span class="arc-sim-label">類似度</span>
            <div class="arc-sim-bar-bg"><div class="arc-sim-bar" style="width:{similarity_score}%;background:{bar_color};"></div></div>
            <span class="arc-sim-score" style="color:{bar_color};">{similarity_score}%</span>
          </div>"""

        # 代替バッジ
        replace_html = ""
        if can_replace:
            if "ほぼ" in can_replace:
                badge_cls = "replace-high"
            elif "部分" in can_replace:
                badge_cls = "replace-mid"
            else:
                badge_cls = "replace-low"
            replace_html = f'<span class="arc-replace {badge_cls}">{can_replace}</span>'

        # 共通成分
        shared_html = ""
        if shared_ingredients:
            tags = _parse_ingredient_tags(shared_ingredients)
            if tags:
                tag_spans = " ".join(
                    f'<span class="arc-tag">{escape(n)}</span>' for n, _ in tags[:4]
                )
                shared_html = f'<div class="arc-shared">{tag_spans}</div>'

        # 解説
        analysis_html = ""
        if why_similar:
            analysis_html = f'<div class="arc-why">{why_similar}</div>'

        cards_html.append(f"""      <div class="arc-card" data-category="{escape(category)}">
        <div class="arc-header">
          <span class="arc-category">{category}</span>
          {replace_html}
        </div>
        {sim_html}
        <div class="arc-vs">
          <div class="arc-product">
            <span class="arc-label arc-label-petit">プチプラ</span>
            <div class="arc-name">{petit_name}</div>
            <div class="arc-price arc-price-petit">{petit_price}</div>
          </div>
          <div class="arc-vs-mark">VS</div>
          <div class="arc-product">
            <span class="arc-label arc-label-depa">デパコス</span>
            <div class="arc-name">{depa_name}</div>
            <div class="arc-price arc-price-depa">{depa_price}</div>
          </div>
        </div>
        {shared_html}
        {analysis_html}
        <div class="arc-summary">{summary}</div>
        <div class="arc-date">{date_str}</div>
      </div>""")

    cards_joined = "\n\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="コスメバズ 成分比較アーカイブ — プチプラvsデパコスの成分類似度を検証した全記録">
  <meta property="og:title" content="成分比較アーカイブ | コスメバズ">
  <meta property="og:description" content="成分類似度でコスメの&quot;激似&quot;を検証。過去の全比較データを一覧で。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://takuminagashima0920-dev.github.io/cosmebuzz/archive.html">
  <meta property="og:locale" content="ja_JP">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧬</text></svg>">
  <title>成分比較アーカイブ | コスメバズ</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans', sans-serif;
      background: #1C1C24;
      color: #FFFFFF;
      min-height: 100vh;
    }}
    .container {{ max-width: 480px; margin: 0 auto; padding: 20px 16px; }}

    .page-header {{
      text-align: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }}
    .page-title {{
      font-size: 1.3rem;
      font-weight: 700;
      background: linear-gradient(135deg, #4ECDC4, #45B7AA);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .page-tagline {{
      font-size: 0.68rem;
      color: #AAAAAA;
      margin-top: 4px;
      letter-spacing: 0.06em;
    }}
    .page-stats {{
      font-size: 0.7rem;
      color: #888;
      margin-top: 8px;
    }}
    .page-stats strong {{ color: #4ECDC4; }}
    .back-link {{
      display: inline-block;
      margin-top: 10px;
      font-size: 0.7rem;
      color: #DC8C9E;
      text-decoration: none;
    }}
    .back-link:hover {{ text-decoration: underline; }}

    /* Filter */
    .filter-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 16px;
    }}
    .filter-btn {{
      font-size: 0.62rem;
      padding: 4px 10px;
      border-radius: 12px;
      border: 1px solid rgba(78,205,196,0.2);
      background: transparent;
      color: #AAAAAA;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn.active, .filter-btn:hover {{
      background: rgba(78,205,196,0.15);
      color: #4ECDC4;
      border-color: rgba(78,205,196,0.4);
    }}

    /* Card */
    .arc-card {{
      background: #282830;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 12px;
      border: 1px solid rgba(255,255,255,0.04);
    }}
    .arc-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .arc-category {{
      font-size: 0.65rem;
      font-weight: 600;
      color: #4ECDC4;
      letter-spacing: 0.06em;
      padding-left: 8px;
      border-left: 3px solid #4ECDC4;
    }}
    .arc-replace {{
      font-size: 0.55rem;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 4px;
    }}
    .replace-high {{ background: rgba(107,203,119,0.15); color: #6BCB77; border: 1px solid rgba(107,203,119,0.3); }}
    .replace-mid {{ background: rgba(255,204,0,0.12); color: #FFCC00; border: 1px solid rgba(255,204,0,0.25); }}
    .replace-low {{ background: rgba(255,107,107,0.12); color: #FF6B6B; border: 1px solid rgba(255,107,107,0.25); }}

    .arc-similarity {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .arc-sim-label {{ font-size: 0.55rem; color: #888; white-space: nowrap; }}
    .arc-sim-bar-bg {{
      flex: 1;
      height: 4px;
      background: rgba(255,255,255,0.08);
      border-radius: 2px;
      overflow: hidden;
    }}
    .arc-sim-bar {{ height: 100%; border-radius: 2px; }}
    .arc-sim-score {{ font-size: 0.75rem; font-weight: 700; white-space: nowrap; }}

    .arc-vs {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      gap: 8px;
      align-items: start;
      margin-bottom: 10px;
    }}
    .arc-product {{ text-align: center; }}
    .arc-label {{
      font-size: 0.55rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 4px;
      letter-spacing: 0.08em;
    }}
    .arc-label-petit {{ background: rgba(107,203,119,0.15); color: #6BCB77; border: 1px solid rgba(107,203,119,0.25); }}
    .arc-label-depa {{ background: rgba(255,107,107,0.15); color: #FF6B6B; border: 1px solid rgba(255,107,107,0.25); }}
    .arc-name {{ font-size: 0.72rem; font-weight: 500; line-height: 1.3; margin-bottom: 3px; }}
    .arc-price {{ font-size: 0.8rem; font-weight: 700; }}
    .arc-price-petit {{ color: #6BCB77; }}
    .arc-price-depa {{ color: #FF6B6B; }}
    .arc-vs-mark {{
      display: flex;
      align-items: center;
      padding-top: 16px;
      font-size: 0.55rem;
      font-weight: 700;
      color: #4ECDC4;
    }}

    .arc-shared {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-bottom: 8px;
    }}
    .arc-tag {{
      font-size: 0.58rem;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(78,205,196,0.1);
      color: #4ECDC4;
      border: 1px solid rgba(78,205,196,0.15);
    }}

    .arc-why {{
      font-size: 0.68rem;
      color: #AAAAAA;
      line-height: 1.5;
      padding: 8px 10px;
      background: rgba(78,205,196,0.04);
      border-radius: 6px;
      border: 1px solid rgba(78,205,196,0.08);
      margin-bottom: 8px;
    }}

    .arc-summary {{
      font-size: 0.7rem;
      color: #FFFFFF;
      line-height: 1.5;
      padding: 8px 10px;
      background: rgba(78,205,196,0.06);
      border-radius: 6px;
      border-left: 3px solid #4ECDC4;
      font-weight: 500;
    }}

    .arc-date {{
      font-size: 0.55rem;
      color: #666;
      text-align: right;
      margin-top: 6px;
    }}

    .footer {{
      text-align: center;
      padding: 24px 0 16px;
      border-top: 1px solid rgba(255,255,255,0.04);
      margin-top: 16px;
    }}
    .footer-brand {{
      font-size: 0.8rem;
      font-weight: 600;
      background: linear-gradient(135deg, #DC8C9E, #F0B0C0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .footer-tagline {{ font-size: 0.58rem; color: #888; margin-top: 4px; }}
  </style>
</head>
<body>
<div class="container">

  <div class="page-header">
    <div class="page-title">&#x1F9EC; 成分比較アーカイブ</div>
    <div class="page-tagline">成分類似度でコスメの"激似"を検証</div>
    <div class="page-stats"><strong>{len(pairs)}</strong> ペア / <strong>{len(categories)}</strong> カテゴリ収録</div>
    <a href="index.html" class="back-link">&larr; トップに戻る</a>
  </div>

  <div class="filter-bar">
{filter_html}
  </div>

{cards_joined}

  <footer class="footer">
    <div class="footer-brand">&#x1F484; コスメバズ | CosmeBuzz</div>
    <div class="footer-tagline">成分類似度でコスメの"激似"を検証</div>
  </footer>

</div>

<script>
document.querySelectorAll('.filter-btn').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    this.classList.add('active');
    var cat = this.getAttribute('data-cat');
    document.querySelectorAll('.arc-card').forEach(function(card) {{
      if (cat === 'all' || card.getAttribute('data-category') === cat) {{
        card.style.display = '';
      }} else {{
        card.style.display = 'none';
      }}
    }});
  }});
}});
</script>

</body>
</html>"""


def update_archive():
    """成分比較アーカイブページを生成"""
    pairs = collect_archive_pairs()
    if not pairs:
        print("ℹ️ アーカイブ対象の成分比較データなし")
        return

    html = build_archive_html(pairs)
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ archive.html 更新完了（{len(pairs)}ペア）")


def git_push():
    """git commit & push"""
    env = os.environ.copy()
    env["PATH"] = os.path.expanduser("~/bin") + ":" + env.get("PATH", "")

    try:
        subprocess.run(["git", "add", "index.html", "archive.html"], cwd=SITE_DIR, check=True, env=env)

        # 変更があるか確認
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=SITE_DIR, env=env
        )
        if result.returncode == 0:
            print("ℹ️ index.htmlに変更なし、pushスキップ")
            return

        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(
            ["git", "commit", "-m", f"Daily update: {today}"],
            cwd=SITE_DIR, check=True, env=env
        )
        subprocess.run(
            ["git", "push"],
            cwd=SITE_DIR, check=True, env=env
        )
        print("✅ GitHub Pages 更新完了")
    except subprocess.CalledProcessError as e:
        print(f"❌ git操作エラー: {e}")


def main():
    """メイン処理"""
    print("🌐 CosmeBuzz サイト更新開始...")

    backup_path = get_latest_backup()
    if not backup_path:
        return

    backup = load_backup(backup_path)
    data = backup.get("data", {})
    dt_str = backup.get("datetime", "")

    update_html(data, dt_str)
    update_archive()
    git_push()

    print("🎉 完了!")


if __name__ == "__main__":
    main()

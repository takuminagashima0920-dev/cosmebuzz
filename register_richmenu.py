"""
CosmeBuzz リッチメニュー登録スクリプト
LINE Messaging APIでリッチメニューを作成・画像アップロード・デフォルト設定
"""

from __future__ import annotations

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.env"))

TOKEN = os.getenv("LINE_COSMEBUZZ_ACCESS_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_JSON = {**HEADERS, "Content-Type": "application/json"}

# --- リッチメニュー定義 ---
# 画像: 2500x1686 (4分割 2x2)
# 各エリアサイズ: 1250x843

RICHMENU_BODY = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "コスメバズ メインメニュー",
    "chatBarText": "メニュー",
    "areas": [
        {
            # 左上: 今日の美容トレンド → GitHub Pages
            "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
            "action": {
                "type": "uri",
                "label": "今日の美容トレンド",
                "uri": "https://takuminagashima0920-dev.github.io/cosmebuzz/"
            }
        },
        {
            # 右上: @cosme ランキング → @cosme外部リンク
            "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
            "action": {
                "type": "uri",
                "label": "@cosme ランキング",
                "uri": "https://www.cosme.net/ranking/"
            }
        },
        {
            # 左下: 感想・要望 → Google Form (プレースホルダー、後で更新)
            "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "uri",
                "label": "感想・要望",
                "uri": "https://forms.gle/placeholder"
            }
        },
        {
            # 右下: 友達に紹介 → LINE Share
            "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "uri",
                "label": "友達に紹介",
                "uri": "https://line.me/R/nv/recommendOA/@093zjaly"
            }
        }
    ]
}

IMAGE_PATH = os.path.expanduser("~/cosmebuzz-site/richmenu.png")


def create_richmenu():
    """リッチメニューを作成"""
    print("1/4 リッチメニュー作成中...")
    r = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=HEADERS_JSON,
        json=RICHMENU_BODY
    )
    if r.status_code != 200:
        print(f"❌ リッチメニュー作成失敗: {r.status_code} {r.text}")
        return None
    richmenu_id = r.json().get("richMenuId")
    print(f"   ✅ richMenuId: {richmenu_id}")
    return richmenu_id


def upload_image(richmenu_id):
    """リッチメニュー画像をアップロード"""
    print("2/4 画像アップロード中...")
    with open(IMAGE_PATH, "rb") as f:
        r = requests.post(
            f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content",
            headers={**HEADERS, "Content-Type": "image/png"},
            data=f
        )
    if r.status_code != 200:
        print(f"❌ 画像アップロード失敗: {r.status_code} {r.text}")
        return False
    print("   ✅ 画像アップロード完了")
    return True


def set_default(richmenu_id):
    """デフォルトリッチメニューに設定"""
    print("3/4 デフォルトメニューに設定中...")
    r = requests.post(
        f"https://api.line.me/v2/bot/user/all/richmenu/{richmenu_id}",
        headers=HEADERS
    )
    if r.status_code != 200:
        print(f"❌ デフォルト設定失敗: {r.status_code} {r.text}")
        return False
    print("   ✅ デフォルトメニュー設定完了")
    return True


def verify():
    """設定確認"""
    print("4/4 設定確認中...")
    r = requests.get(
        "https://api.line.me/v2/bot/user/all/richmenu",
        headers=HEADERS
    )
    if r.status_code == 200:
        menu_id = r.json().get("richMenuId", "")
        print(f"   ✅ 現在のデフォルトメニュー: {menu_id}")
        return True
    else:
        print(f"   ⚠️ 確認失敗: {r.status_code}")
        return False


def main():
    print("🎨 コスメバズ リッチメニュー登録")
    print("=" * 50)

    # 1. リッチメニュー作成
    richmenu_id = create_richmenu()
    if not richmenu_id:
        return

    # 2. 画像アップロード
    if not upload_image(richmenu_id):
        return

    # 3. デフォルト設定
    if not set_default(richmenu_id):
        return

    # 4. 確認
    verify()

    print("=" * 50)
    print("🎉 リッチメニュー登録完了！")
    print(f"   richMenuId: {richmenu_id}")
    print()
    print("📝 TODO: Google Form作成後にURLを更新してください")
    print(f"   現在の「感想・要望」URL: https://forms.gle/placeholder")


if __name__ == "__main__":
    main()

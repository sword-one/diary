# -*- coding: utf-8 -*-
"""楽天ブックスの売れ筋から ranking.json を作る。

閲覧者がアクセスするたびにAPIを叩くのではなく、**公開前に1回だけ**取得して
静的なJSONにする。アプリIDが外に出ず、表示も速い。

アプリIDの置き場所（どちらでもよい）
    1. tools/.rakuten-id というファイルに1行で書く（.gitignore 済み）
    2. 環境変数 RAKUTEN_APP_ID

使い方（mockup/ で）
    python tools/fetch-ranking.py

月に1回くらい流せば十分。流したあと gen-meta.py も実行すること。
"""
import io, os, sys, json, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))
JST = timezone(timedelta(hours=9))
API = "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404"

# 楽天ブックスのジャンル。ORBITの惑星に近いものを選んである。
# ジャンルIDは BooksGenre/Search で調べられる
GENRES = [
    ("001012", "ビジネス・経済・就職"),
    ("001004", "人文・思想・社会"),
]

HITS = 20            # 1ジャンルあたり何冊取るか
KEEP = 12            # ページに出す冊数


def app_id():
    p = os.path.join(TOOLS, ".rakuten-id")
    if os.path.exists(p):
        v = io.open(p, encoding="utf-8").read().strip()
        if v:
            return v
    v = os.environ.get("RAKUTEN_APP_ID", "").strip()
    if v:
        return v
    sys.exit(
        "アプリIDが見つかりません。\n"
        "  tools/.rakuten-id に1行で貼るか、環境変数 RAKUTEN_APP_ID に入れてください。\n"
        "  発行: https://webservice.rakuten.co.jp/")


def fetch(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ORBIT/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def my_books():
    """自分が書いた記事と、本棚にある本。ランキングと重なったら印をつける。"""
    mine = {}
    idx = io.open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    import re
    for m in re.finditer(r"title: '(.*?)',\s*\n\s*author:.*?\n\s*cover:.*?\n\s*url: '(.*?)'", idx):
        mine[m.group(1)] = m.group(2)
    shelf = []
    d = r"C:\Users\山口PC\Desktop\私の本棚"
    if os.path.isdir(d):
        shelf = [f[:-4] for f in os.listdir(d) if f.endswith(".pdf")]
    return mine, shelf


def norm(t):
    """突き合わせ用。記号と空白を落とす"""
    for c in " 　・（）()［］[]【】「」『』:：/／,、.。-ー―":
        t = t.replace(c, "")
    return t


def main():
    aid = app_id()
    affid = ""
    p = os.path.join(TOOLS, ".rakuten-affiliate-id")
    if os.path.exists(p):
        affid = io.open(p, encoding="utf-8").read().strip()

    mine, shelf = my_books()
    shelf_n = [norm(x) for x in shelf]
    mine_n = {norm(k): v for k, v in mine.items()}

    rows, seen = [], set()
    for gid, gname in GENRES:
        q = {"applicationId": aid, "booksGenreId": gid,
             "sort": "sales", "hits": HITS, "formatVersion": 2}
        if affid:
            q["affiliateId"] = affid
        try:
            d = fetch(q)
        except Exception as e:
            print("  ! %s(%s) の取得に失敗: %s" % (gname, gid, e))
            continue
        items = d.get("Items", [])
        print("  %s … %d件" % (gname, len(items)))
        for it in items:
            isbn = (it.get("isbn") or "").strip()
            title = (it.get("title") or "").strip()
            if not title or isbn in seen:
                continue
            seen.add(isbn)
            n = norm(title)
            read = next((v for k, v in mine_n.items() if k and (k in n or n in k)), None)
            on_shelf = any(s and (s in n or n in s) for s in shelf_n)
            rows.append({
                "isbn": isbn,
                "title": title,
                "author": (it.get("author") or "").strip(),
                "publisher": (it.get("publisherName") or "").strip(),
                "cover": it.get("largeImageUrl") or it.get("mediumImageUrl") or "",
                "url": it.get("affiliateUrl") or it.get("itemUrl") or "",
                "genre": gname,
                "article": read,          # 記事があればそのURL
                "shelf": on_shelf,        # 本棚にあるか
            })
        time.sleep(1.2)      # 連続アクセスを避ける

    rows = rows[:KEEP]
    out = {
        "updated": datetime.now(JST).strftime("%Y-%m-%d"),
        "source": "楽天ブックス（売れ筋順）",
        "credit": "Supported by 楽天ウェブサービス",
        "affiliate": bool(affid),
        "items": rows,
    }
    p = os.path.join(HERE, "ranking.json")
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("ranking.json に %d冊 書きました（記事あり %d / 本棚にあり %d）" % (
        len(rows), sum(1 for r in rows if r["article"]),
        sum(1 for r in rows if r["shelf"])))


if __name__ == "__main__":
    print("楽天ブックスから取得:")
    main()

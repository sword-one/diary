# -*- coding: utf-8 -*-
"""楽天ブックスの売れ筋から ranking.json を作る。

閲覧者がアクセスするたびにAPIを叩くのではなく、**公開前に1回だけ**取得して
静的なJSONにする。アプリIDが外に出ず、表示も速い。

アプリIDの置き場所
    tools/rakuten-id.txt            ← ふつうはこれ。メモ帳で開いて貼るだけ
    tools/.rakuten-id               ← どちらでもよい
    環境変数 RAKUTEN_APP_ID          ← どちらでもよい

使い方（mockup/ で）
    python tools/fetch-ranking.py

月に1回くらい流せば十分。流したあと gen-meta.py も実行すること。
"""
import io, os, sys, json, time, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))
JST = timezone(timedelta(hours=9))
# 2026年の刷新でドメインが変わり、accessKey と Referer が必須になった。
# 旧 app.rakuten.co.jp は停止済み。
API_HOSTS = [
    # 2026年の刷新後の正式URL（公式ドキュメント）
    "https://openapi.rakuten.co.jp/services/api/BooksBook/Search/20170404",
]
REFERER = "https://sword-one.github.io/diary/"

# 楽天ブックスのジャンル。ORBITの惑星に近いものを選んである。
# ジャンルIDは BooksGenre/Search で調べられる
GENRES = [
    # ORBITの惑星に対応するジャンル。IDは BooksGenre/Search で確認した（2026-10-25）。
    # ※ 親ジャンル（001006 など）だと資格テキストや図鑑が上位を占める。
    #   下位ジャンルまで指定しないと、このサイトに関係ない本ばかりになる
    ("001006009", "自己啓発"),              # 習慣・生き方・心
    ("001006007", "マネジメント・人材管理"),  # 伝え方・チーム
    ("001008003", "心理学"),                # 心・意識
]

HITS = 10            # 1ジャンルあたり何冊取るか
KEEP = 15            # ページに出す冊数

ISSUE = "https://webservice.rakuten.co.jp/"


def read_id(*names):
    """# で始まる行・空行・プレースホルダは飛ばして、最初の中身を返す。
       Windowsではドット始まりのファイルが作りにくいので .txt でも読む"""
    for n in names:
        path = os.path.join(TOOLS, n)
        if not os.path.exists(path):
            continue
        for line in io.open(path, encoding="utf-8-sig").read().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "ここに" not in line:
                return line
    return ""


def access_key():
    v = read_id("rakuten-access-key.txt", ".rakuten-access-key")
    if not v:
        v = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
    if v:
        return v
    print("アクセスキーがまだ入っていません。")
    print("  tools/rakuten-access-key.txt を開いて貼ってください。")
    sys.exit(1)


def app_id():
    v = read_id("rakuten-id.txt", ".rakuten-id")
    if not v:
        v = os.environ.get("RAKUTEN_APP_ID", "").strip()
    if v:
        return v
    print("アプリIDがまだ入っていません。")
    print("  tools/rakuten-id.txt を開いて、いちばん下の行をIDに書き換えて保存してください。")
    print("  発行: " + ISSUE)
    sys.exit(1)


def fetch(params, key):
    """新仕様のホストから順に試す。どれで通ったかを返す。
       accessKey はログに残らないようヘッダーで送る"""
    last = None
    for host in API_HOSTS:
        url = host + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "User-Agent": "ORBIT/1.0",
            "Referer": REFERER,
            "Origin": REFERER.rstrip("/"),
            "accessKey": key,
        })
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8")), host
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            last = "HTTP %s  %s" % (e.code, body)
        except Exception as e:
            last = str(e)
    raise RuntimeError(last)


def my_books():
    """自分が記事にした本と、本棚にある本。ランキングと重なったら印をつける。"""
    mine = {}
    idx = io.open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    pat = r"title: '(.*?)',\s*\n\s*author:.*?\n\s*cover:.*?\n\s*url: '(.*?)'"
    for m in re.finditer(pat, idx):
        mine[m.group(1)] = m.group(2)
    shelf = []
    d = os.path.join(os.path.expanduser("~"), "Desktop", "私の本棚")
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
    akey = access_key()
    affid = read_id("rakuten-affiliate-id.txt", ".rakuten-affiliate-id")

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
            d, used = fetch(q, akey)
            print("    (%s)" % used.split("/")[2])
        except Exception as e:
            print("  ! %s(%s) の取得に失敗" % (gname, gid))
            print("    %s" % e)
            continue
        items = d.get("Items", [])
        print("  %s … %d件" % (gname, len(items)))
        for it in items:
            isbn = (it.get("isbn") or "").strip()
            title = (it.get("title") or "").strip()
            if not title or (isbn and isbn in seen):
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

    if not rows:
        print("1冊も取れませんでした。アプリIDかジャンルIDを確認してください。")
        sys.exit(1)

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
    if not affid:
        print("※ アフィリエイトIDは未設定。ふつうのリンクになります")


if __name__ == "__main__":
    print("楽天ブックスから取得:")
    main()

# -*- coding: utf-8 -*-
"""style.css などのリンクに版番号を付け直す。

ブラウザは style.css をURLで覚えるので、中身を変えてもURLが同じだと
古いものを使い続ける。特にLINEのアプリ内ブラウザで強く効く。
URLの末尾に ?v=<日時> を付けておけば、変えたときだけ必ず読み直される。

使い方（mockup/ で）:
    python tools/bump-assets.py

CSSやJSを触ったら必ず実行する。記事を出すときは gen-meta.py と両方。
"""
import io, os, re, glob
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))
VER = datetime.now(JST).strftime("%Y%m%d%H%M")

# 版番号を付ける対象（自分のサイト内のものだけ）。
# 中身を差し替えてもファイル名が同じものは、ここに足す。
# 書影や記事のヒーロー画像は、差し替えるとき名前も変える前提なので入れない。
TARGETS = ["style.css", "img/pepe.webp"]

n = 0
for path in sorted(glob.glob(os.path.join(HERE, "*.html"))):
    name = os.path.basename(path)
    s = io.open(path, encoding="utf-8").read()
    before = s
    for t in TARGETS:
        # href= と src= の両方、/diary/ 付きも、既に版番号があるものも拾う
        s = re.sub(r'((?:href|src)="(?:/diary/)?%s)(\?v=\d+)?"' % re.escape(t),
                   lambda m: m.group(1) + "?v=" + VER + '"', s)
    if s != before:
        io.open(path, "w", encoding="utf-8", newline="").write(s)
        print("  " + name)
        n += 1

print("版番号 %s を %d ファイルに付けました" % (VER, n))

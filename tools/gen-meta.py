# -*- coding: utf-8 -*-
"""記事HTMLから sitemap.xml / feed.xml を作る。

記事そのものを唯一の情報源にしてある。
別の一覧ファイルを持つと必ずズレるので、og: タグと本文から拾う。

使い方（mockup/ で）:
    python tools/gen-meta.py

記事を足したら必ず実行する。
"""
import io, os, re, glob, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://sword-one.github.io/diary"
TITLE = "ORBIT"
DESC = "仕事をする上で、生きていく上で。人間関係やコミュニケーションのこと、毎日の仕事が少し進めやすくなること。そういう本を選んで、一冊ずつお届けします。"
JST = timezone(timedelta(hours=9))

# 一覧に入れないもの（トップ・エラーページ・転送用の残骸）
SKIP = {"index.html", "404.html"}


def meta(html, prop, attr="property"):
    m = re.search(r'<meta\s+%s="%s"\s+content="(.*?)"' % (attr, re.escape(prop)),
                  html, re.S)
    return m.group(1).strip() if m else None


def collect():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "*.html"))):
        name = os.path.basename(path)
        if name in SKIP:
            continue
        html = io.open(path, encoding="utf-8").read()
        # meta refresh だけの転送用スタブは飛ばす
        if "http-equiv=\"refresh\"" in html:
            continue
        url = meta(html, "og:url")
        if not url:
            continue
        date = None
        m = re.search(r'class="by-meta">\s*(\d{4})\.(\d{2})\.(\d{2})', html)
        if m:
            date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            9, 0, 0, tzinfo=JST)
        kicker = re.search(r'<span class="kicker">(.*?)</span>', html, re.S)
        catch = re.search(r'<p class="catch">(.*?)</p>', html, re.S)
        sub = re.search(r'<p class="catch-sub">(.*?)</p>', html, re.S)
        strip = lambda t: re.sub(r"<[^>]+>", "", t).strip() if t else ""
        out.append({
            "file": name,
            "url": url,
            "title": meta(html, "og:title") or "",
            "desc": meta(html, "og:description") or "",
            "image": meta(html, "og:image") or "",
            "date": date,
            "cat": strip(kicker.group(1)) if kicker else "",
            "catch": strip(catch.group(1)) if catch else "",
            "sub": strip(sub.group(1)) if sub else "",
        })
    out.sort(key=lambda a: (a["date"] or datetime(1970, 1, 1, tzinfo=JST)), reverse=True)
    return out


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def write(name, body):
    p = os.path.join(HERE, name)
    io.open(p, "w", encoding="utf-8", newline="\n").write(body)
    print("  " + name)


def main():
    arts = collect()
    if not arts:
        sys.exit("記事が1本も見つかりませんでした")
    newest = arts[0]["date"] or datetime.now(JST)

    # ---- sitemap.xml
    rows = ['<url><loc>%s/</loc><lastmod>%s</lastmod>'
            '<changefreq>weekly</changefreq><priority>1.0</priority></url>'
            % (SITE, newest.strftime("%Y-%m-%d"))]
    for a in arts:
        rows.append('<url><loc>%s</loc><lastmod>%s</lastmod>'
                    '<changefreq>monthly</changefreq><priority>0.8</priority></url>'
                    % (esc(a["url"]),
                       (a["date"] or newest).strftime("%Y-%m-%d")))
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "\n".join(rows) + "\n</urlset>\n")

    # ---- robots.txt
    write("robots.txt",
          "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    # ---- feed.xml（RSS 2.0）
    items = []
    for a in arts:
        d = a["date"] or newest
        body = a["catch"]
        if a["sub"]:
            body += " " + a["sub"]
        items.append(
            "    <item>\n"
            "      <title>%s</title>\n"
            "      <link>%s</link>\n"
            "      <guid isPermaLink=\"true\">%s</guid>\n"
            "      <pubDate>%s</pubDate>\n"
            "      <category>%s</category>\n"
            "      <description>%s</description>\n"
            "    </item>"
            % (esc(a["title"]), esc(a["url"]), esc(a["url"]),
               d.strftime("%a, %d %b %Y %H:%M:%S +0900"),
               esc(a["cat"].split("　")[-1]), esc(body or a["desc"])))
    write("feed.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
          '  <channel>\n'
          '    <title>%s</title>\n'
          '    <link>%s/</link>\n'
          '    <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>\n'
          '    <description>%s</description>\n'
          '    <language>ja</language>\n'
          '    <lastBuildDate>%s</lastBuildDate>\n'
          '%s\n'
          '  </channel>\n'
          '</rss>\n'
          % (esc(TITLE), SITE, SITE, esc(DESC),
             newest.strftime("%a, %d %b %Y %H:%M:%S +0900"),
             "\n".join(items)))

    print("記事 %d本から生成しました" % len(arts))
    for a in arts:
        print("  - %s  %s" % ((a["date"] or newest).strftime("%Y-%m-%d"), a["title"]))


if __name__ == "__main__":
    print("生成:")
    main()

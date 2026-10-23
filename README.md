# ソードワンダイアリー

株式会社ソードワンの山口ひかりが、読んだ本と、そこで考えたことを書いています。

公開: GitHub Pages

## 構成

```
index.html        記事一覧
01-coaching.html  #01 新 コーチングが人を活かす
style.css         全ページ共通
img/              画像
```

## 新しい記事を追加するとき

1. `01-coaching.html` を複製して `02-xxxx.html` にする
2. 本文と OGP（`og:title` / `og:description` / `og:url`）を書き換える
3. `index.html` の「記事」に1件足して、「これから」から該当行を消す

書き方・デザインの決まりは `../CLAUDE.md` を参照。

## 注意

- 各ページの OGP に `https://example.com` が入っている。**公開URLが決まったら全ファイルを置換すること。**
  `og:image` は絶対URLでないとLINEでカード表示されない
- 書影は各出版社に帰属。縮小のみで改変しない

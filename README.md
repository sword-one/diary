# ソードワンダイアリー

仕事をする上で、生きていく上で。人間関係やコミュニケーションのこと、毎日の仕事が少し進めやすくなること。そういう本を選んで、週に一冊ずつお届けします。

公開: https://sword-one.github.io/diary/

## 構成

```
index.html        記事一覧
coaching.html     新 コーチングが人を活かす
power.html        パワーか、フォースか 改訂版
style.css         全ページ共通
img/              画像
```

## ファイル名のルール

**URLに番号を入れない。** 配信の順番を入れ替えてもURLが変わらないようにするため。

- 書名から短く取る（`coaching.html` `power.html` `peptalk.html`）
- 似た書名の本が来たら、区別できる語を足す
  （例: 旧版の『コーチングが人を活かす』を扱うなら `coaching-old.html`）
- 記事中の「#01」「#02」は**表示だけ**。入れ替えたらそこだけ手で直す

## 新しい記事を追加するとき

1. `coaching.html` を複製して `<書名>.html` にする
2. 本文を書き換える
3. **OGPを3つとも書き換える**（`og:title` / `og:description` / `og:url`）
4. ヒーロー画像とヒーローの `alt`、書影、Amazonリンクを差し替える
5. `index.html` の「記事」に1件足し、「これから」から該当行を消す
6. `git add -A && git commit && git push` → 2〜3分でPagesに反映

書き方・デザインの決まりは `../CLAUDE.md` を参照。

## 注意

- 公開URL: https://sword-one.github.io/diary/
  `og:image` は絶対URLでないとLINEでカード表示されない
- **このフォルダに置いた時点で公開される。** 一覧に載せなくてもURLを知れば読める。
  書きかけの記事は `../下書き/` に置き、配信の直前にここへ移す
- 書影は各出版社に帰属。縮小のみで改変しない

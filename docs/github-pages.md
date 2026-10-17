# GitHub Pages での公開

## 現在の公開方式

現在は Settings > Pages の「Deploy from a branch」で、`main` ブランチのリポジトリ直下から公開されています。ゲームの URL は `https://caitakenchikuclub.github.io/ClaudeGame005/www/` です。

リポジトリ直下の `index.html` は `www/` に転送するだけのページです。そのため `https://caitakenchikuclub.github.io/ClaudeGame005/` を開いてもゲームが表示されます。

この方式では README や `docs/`、`tools/` も公開されます。秘密情報は置かない運用なので実害はありません。

## GitHub Actions 方式への切り替え（任意）

`www/` だけを公開し、URL を `/ClaudeGame005/` 直下にしたい場合は、所有者が次の2つを行います。

1. Settings > Pages の Source を「GitHub Actions」に変更する
2. Settings > Secrets and variables > Actions の Variables に `PAGES_VIA_ACTIONS` を `true` で追加する

すると `.github/workflows/pages.yml` のデプロイジョブが有効になり、`main` への push ごとに `www/` が公開されます。変数を設定しない間は、push 時にチェックだけが実行されます。

## サブパス配信の注意点

公開URLが `/ClaudeGame005/` 配下になるため、`/` で始まる絶対パスはドメイン直下を指してしまい読み込みに失敗します。すべて相対パスで記述し、`npm test` で検出できるようにしています。

`fetch()` で譜面や音源を読む場合も `fetch('charts/song1.json')` のように相対パスで書きます。JS モジュールから基準を明示したいときは `new URL('../charts/song1.json', import.meta.url)` を使います。

リポジトリ直下と `www/` の `.nojekyll` は、Jekyll 処理によって `_` で始まるファイルが除外されるのを防ぐためのものです。直下のものはブランチ公開用、`www/` のものは Actions 公開用です。

## 将来の課題

Service Worker を導入する場合、スコープは `/ClaudeGame005/` になるため、登録時のパスも相対で指定します（[offline.md](offline.md) 参照）。

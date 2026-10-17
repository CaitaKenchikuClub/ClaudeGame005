# GitHub Pages での公開

## 公開方式

ゲーム本体を `www/` に置き、GitHub Actions（`.github/workflows/pages.yml`）で `www/` だけを公開します。

ブランチから直接公開する方式は公開元に「リポジトリ直下」か「`/docs`」しか選べず、Capacitor の慣例である `www/` と両立しにくいため、Actions 方式を採用しました。リポジトリ直下を公開すると README やツール類まで公開される問題も避けられます。

## 所有者が行う設定

Settings > Pages を開き、Build and deployment の Source を「GitHub Actions」に変更します。その後 `main` に push するか、Actions タブから「Check and deploy to GitHub Pages」を手動実行すると公開されます。

公開URLは `https://caitakenchikuclub.github.io/ClaudeGame005/` になる見込みです。Source を「Deploy from a branch」にした場合、このワークフローのデプロイは失敗するので注意してください。

## サブパス配信の注意点

公開URLが `/ClaudeGame005/` 配下になるため、`/` で始まる絶対パスはドメイン直下を指してしまい読み込みに失敗します。すべて相対パスで記述し、`npm test` で検出できるようにしています。

`fetch()` で譜面や音源を読む場合も `fetch('charts/song1.json')` のように相対パスで書きます。JS モジュールから基準を明示したいときは `new URL('../charts/song1.json', import.meta.url)` を使います。

`www/.nojekyll` は Jekyll 処理によって `_` で始まるファイルが除外されるのを防ぐためのものです。

## 将来の課題

Service Worker を導入する場合、スコープは `/ClaudeGame005/` になるため、登録時のパスも相対で指定します（[offline.md](offline.md) 参照）。

# ClaudeGame005

ブラウザで遊べるリズムゲームです。現在は GitHub Pages での公開を想定し、将来は Capacitor で Android などのスマートフォンアプリとして配布する予定です。

現時点ではゲーム本体は未実装です。タイトル画面と仮のプレイ画面を行き来できる、起動用の土台だけがあります。この土台は画面サイズへの追従、タッチ入力、音声アンロックを備えています。

## 技術スタック

ビルド工程のない素の HTML / CSS / JavaScript（ES Modules）で構成しています。ランタイムの依存ライブラリはありません。Node.js（18 以上）はローカル確認用サーバーと静的チェックにのみ使います。

## ファイル構成

| パス | 役割 |
| --- | --- |
| `index.html` | リポジトリ直下を公開した場合に `www/` へ転送するページ |
| `www/` | 公開されるゲーム本体。GitHub Pages の公開対象であり、将来 Capacitor の `webDir` にもなる |
| `www/index.html` | エントリーポイント |
| `www/css/` | スタイル |
| `www/js/main.js` | JavaScript のエントリーポイント |
| `tools/serve.mjs` | ローカル確認用の静的サーバー（サブパス配信を再現） |
| `tools/check.mjs` | 相対パス・参照切れ・外部URL参照を検出するチェック |
| `.github/workflows/pages.yml` | push 時のチェックと GitHub Pages へのデプロイ |
| `docs/` | 設計メモ（公開・アプリ化・オフライン・広告） |

## 起動方法

```sh
npm start
```

`http://localhost:8080/ClaudeGame005/` を開くと、サブパス配下での動作を確認できます。ポートは `PORT=3000 npm start` のように変更できます。

## テスト

```sh
npm test
```

`www/` 内の HTML・CSS・JS を走査し、ルート相対パス（`/` で始まるパス）、存在しないファイルへの参照、外部URLへの参照があればエラーにします。

## 開発ルール

リソースの参照は必ず相対パスで書きます（`/css/style.css` ではなく `css/style.css`）。サブパス配信と Capacitor の両方で壊れないようにするためです。

CDN やWebフォントなど外部URLからの読み込みは行わず、必要なファイルは `www/` 内に同梱します。オフライン対応の前提になります。

変更は原則として `main` ブランチへ直接コミットします。APIキーなどの秘密情報はコミットしません。

## GitHub Pages での公開

現在は `main` ブランチのリポジトリ直下から公開されています。ゲームは https://caitakenchikuclub.github.io/ClaudeGame005/www/ で遊べます。直下の `index.html` が `www/` へ転送します。`www/` だけを公開する GitHub Actions 方式への切り替え手順は [docs/github-pages.md](docs/github-pages.md) を参照してください。

## 今後の設計メモ

[docs/capacitor.md](docs/capacitor.md) にアプリ化、[docs/offline.md](docs/offline.md) にオフライン対応、[docs/ads.md](docs/ads.md) に広告導入の課題と方針をまとめています。

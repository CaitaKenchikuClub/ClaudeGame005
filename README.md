# ClaudeGame005

ブラウザで遊べるリズムゲームです。現在は GitHub Pages での公開を想定し、将来は Capacitor で Android などのスマートフォンアプリとして配布する予定です。

現時点ではゲーム本体は未実装で、画面サイズ追従・タッチ入力・音声アンロックだけを備えた起動用の土台があります。

## 技術スタック

ビルド工程のない素の HTML / CSS / JavaScript（ES Modules）で構成しています。ランタイムの依存ライブラリはありません。Node.js（18 以上）はローカル確認用サーバーと静的チェックにのみ使います。

## ファイル構成

| パス | 役割 |
| --- | --- |
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

`http://localhost:8080/ClaudeGame005/` を開くと、GitHub Pages と同じサブパス構成で動作を確認できます。ポートは `PORT=3000 npm start` のように変更できます。

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

リポジトリ所有者が Settings > Pages の Source を「GitHub Actions」に設定すると、`main` への push ごとに `www/` が公開されます。設定前はデプロイジョブがスキップされ、チェックのみ実行されます。詳細は [docs/github-pages.md](docs/github-pages.md) を参照してください。

## 今後の設計メモ

[docs/capacitor.md](docs/capacitor.md) にアプリ化、[docs/offline.md](docs/offline.md) にオフライン対応、[docs/ads.md](docs/ads.md) に広告導入の課題と方針をまとめています。

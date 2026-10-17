// 依存ライブラリなしのローカル確認用静的サーバー。
// GitHub Pages のサブパス配信を再現するため、www/ を /ClaudeGame005/ 配下で配信する。
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';

const ROOT = resolve('www');
const BASE = '/ClaudeGame005/';
const PORT = Number(process.env.PORT) || 8080;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.m4a': 'audio/mp4',
  '.wav': 'audio/wav',
};

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/' || url.pathname === BASE.slice(0, -1)) {
    res.writeHead(302, { Location: BASE }).end();
    return;
  }
  if (!url.pathname.startsWith(BASE)) {
    res.writeHead(404).end('Not Found');
    return;
  }
  let path = normalize(join(ROOT, decodeURIComponent(url.pathname.slice(BASE.length))));
  if (path !== ROOT && !path.startsWith(ROOT + sep)) {
    res.writeHead(403).end('Forbidden');
    return;
  }
  try {
    if ((await stat(path)).isDirectory()) path = join(path, 'index.html');
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': TYPES[extname(path)] || 'application/octet-stream' }).end(body);
  } catch {
    res.writeHead(404).end('Not Found');
  }
}).listen(PORT, () => {
  console.log(`http://localhost:${PORT}${BASE}`);
});

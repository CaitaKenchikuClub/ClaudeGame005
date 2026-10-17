// 依存ライブラリなしの静的チェック。
// GitHub Pages のサブパス配信・Capacitor・オフライン対応を壊しやすい記述を検出する。
import { readdir, readFile, access } from 'node:fs/promises';
import { dirname, extname, join, relative, resolve } from 'node:path';

const ROOT = resolve('www');
const errors = [];
const warnings = [];

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(p)));
    else out.push(p);
  }
  return out;
}

async function exists(p) {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

const files = await walk(ROOT);
if (!files.some((f) => relative(ROOT, f) === 'index.html')) errors.push('www/index.html がありません');

const REF = /(?:src|href)\s*=\s*["']([^"']+)["']|url\(\s*["']?([^"')]+)["']?\s*\)|import\s+(?:[^'"]*from\s+)?["']([^"']+)["']/g;

for (const file of files) {
  if (!['.html', '.css', '.js', '.mjs'].includes(extname(file))) continue;
  const text = await readFile(file, 'utf8');
  const rel = relative(process.cwd(), file);
  for (const m of text.matchAll(REF)) {
    const ref = m[1] || m[2] || m[3];
    if (/^(data:|#|mailto:|javascript:)/.test(ref)) continue;
    // JS のテンプレート文字列（img/t_${key}.jpg など）は実行時に決まるので静的には確かめない
    if (ref.includes('${')) continue;
    // 'img/s_' + key のように文字列連結で組み立てるパスも実行時に決まるので確かめない
    if (/^\s*\+/.test(text.slice(m.index + m[0].length))) continue;
    // Google Fonts はオフラインだと読めないが、代わりのフォントで表示は崩れないので警告にとどめる
    if (/^https:\/\/fonts\.(googleapis|gstatic)\.com/.test(ref)) {
      warnings.push(`${rel}: Google Fonts はオンライン時のみ読み込まれます（オフラインでは代替フォント）: ${ref}`);
      continue;
    }
    if (/^(https?:)?\/\//.test(ref)) {
      errors.push(`${rel}: 外部URLを参照しています（オフラインで動作しません）: ${ref}`);
      continue;
    }
    if (ref.startsWith('/')) {
      errors.push(`${rel}: ルート相対パスはサブパス配信で壊れます。相対パスにしてください: ${ref}`);
      continue;
    }
    const target = resolve(dirname(file), ref.split(/[?#]/)[0]);
    if (!(await exists(target))) errors.push(`${rel}: 参照先が存在しません: ${ref}`);
  }
}

if (warnings.length) console.warn(warnings.join("\n"));
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${files.length} ファイルをチェックしました`);

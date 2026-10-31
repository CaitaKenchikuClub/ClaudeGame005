"""使い方: python3 tools/charts/densify.py www/game/index.html 曲のkey 難易度 音源.mp3
長押しを短くし、ノーツの少ない区間を拍に合わせたタップで埋める（指定した曲・難易度だけ）。"""
import sys, json, random
sys.path.insert(0, __import__('os').path.dirname(__file__))
from onset import load, envelope, strength, SR
from gen import check, LANES
from create import rms_curve
html, key, diff, audio = sys.argv[1:5]
s = open(html).read(); i = s.index('const SONGS = '); j = s.index('\n', i)
SONGS = json.loads(s[i + 14:j].rstrip(';')); x = [x for x in SONGS if x['key'] == key][0]
beat, off = x['beat'], x['offset']; ch = [list(n) for n in x['charts'][diff]]
y = load(audio); env = envelope(y); rms, rw = rms_curve(y); import numpy as np; loud = np.median(rms)
audible = lambda t: 0 <= int(t / rw) < len(rms) and rms[int(t / rw)] > loud * .08
rnd = random.Random(key + diff + 'densify')
before = len(ch)
# 1) 長押しは2拍まで
MAXH = 2 * beat
for k, n in enumerate(ch):
    if n[2] in ('hold', 'hflick') and n[3] - n[0] > MAXH + .01:
        ch[k] = [n[0], n[1], 'flick' if n[2] == 'hflick' else 'tap']
# 2) 1拍より空いている所を、拍（と音のある8分）で埋める
def busy_until(t):
    return max([n[3] if len(n) > 3 else n[0] for n in ch if n[0] <= t + 1e-6], default=-9)
events = sorted(ch, key=lambda n: n[0])
add = []
for a, b in zip(events, events[1:]):
    start = a[3] if len(a) > 3 else a[0]
    if b[0] - start <= .9 * beat: continue
    k0 = int(np.ceil((start + beat * .45 - off) / (beat / 2)))
    t = off + k0 * beat / 2
    last = start
    while t < b[0] - beat * .45:
        on_beat = abs(((t - off) / beat) - round((t - off) / beat)) < 1e-3
        st = strength(env, t, .03)
        if audible(t) and (on_beat or st >= .12) and t - last >= beat / 2 - 1e-3:
            add.append(round(t, 4)); last = t
        t += beat / 2
for t in add:
    prev = max([n for n in ch if n[0] < t], key=lambda n: n[0], default=None)
    pl = prev[1] if prev else 2
    opts = [l for l in range(LANES) if l != pl and abs(l - pl) <= 2
            and not any(m[1] == l and (abs(m[0] - t) < .3 or (len(m) > 3 and m[0] - .05 <= t <= m[3] + .12)) for m in ch)
            and not any(len(m) > 3 and m[0] < t <= m[3] + .05 for m in ch if m[1] != l and False)]
    holding = [m for m in ch if len(m) > 3 and m[0] - .05 <= t <= m[3] + .05]
    if holding and len(holding) >= 1 and any(abs(m[0] - t) < .01 for m in ch): continue
    if not opts: continue
    ch.append([t, rnd.choice(opts), 'tap'])
ch.sort(key=lambda n: (n[0], n[1]))
errs = check(ch, diff)
print(f'{key} {diff}: {before} -> {len(ch)} notes (+{len(ch)-before}), holds max {max(n[3]-n[0] for n in ch if len(n)>3):.2f}s, issues {len(errs)}', errs[:3])
ts = sorted({n[0] for n in ch}); print('largest gaps now', sorted([round(b - a, 2) for a, b in zip(ts, ts[1:])])[-6:])
import collections; cnt = collections.Counter(int(n[0] // 4) for n in ch); print('notes per 4s', [cnt.get(k, 0) for k in range(int(x['dur'] // 4) + 1)])
x['charts'][diff] = ch
s = s[:i] + 'const SONGS = ' + json.dumps(SONGS, ensure_ascii=False, separators=(',', ':')) + ';' + s[j:]
open(html, 'w').write(s)

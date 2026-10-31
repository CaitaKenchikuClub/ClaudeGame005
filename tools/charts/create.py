"""使い方: python3 tools/charts/tempo.py 曲.mp3 でテンポを調べ、python3 tools/charts/create.py 曲.mp3 BPM 最初の拍の秒 種(任意の文字) 出力.json
新しい曲の譜面を音から作る（EASY / NORMAL / HARD / EXTRA）。
テンポの格子（16分）の上で音の立ち上がりが強い位置を選び、難易度ごとの密度・最短間隔に合わせる。
レーンは近くを行き来するように動かし、長押し・フリック・同時押しを既存曲と同じくらいの割合で混ぜる。"""
import sys, json, random, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from onset import load, envelope, strength, SR, HOP
from gen import check, LANES

CFG = {  # 1秒あたりのノーツ数、最短間隔、使う刻み、長押し・フリック・同時押しの割合、同時押しの間隔
  'easy':   dict(thr=.12, nps=.98, gap=.45, sub=4, hold=.09, flick=.07, chord=0,    cgap=99),
  'normal': dict(thr=.07, nps=2.55, gap=.2, sub=2, hold=.06, flick=.09, chord=.012, cgap=7),
  'hard':   dict(thr=.06, nps=3.4, gap=.15, sub=2, hold=.05, flick=.10, chord=.02,  cgap=4),
  'extra':  dict(thr=.05, nps=4.75, gap=.1, sub=2, hold=.04, flick=.11, chord=.04, cgap=3),
}

def rms_curve(y, win=.2):
    n = int(SR * win); m = len(y) // n
    return np.sqrt((y[:m * n].reshape(m, n) ** 2).mean(axis=1)), win

def local_peak(env, t, w=.025):
    c = int((t * SR - 512) / HOP); k = int(w * SR / HOP)
    a, b = max(0, c - k), min(len(env), c + k + 1)
    j = a + int(np.argmax(env[a:b])); return (j * HOP + 512) / SR

def make(y, env, bpm, off, dur, diff, seed):
    cfg = CFG[diff]; rnd = random.Random(f'{seed}-{diff}')
    beat = 60 / bpm; q = beat / 4
    rms, rw = rms_curve(y); loud = np.median(rms)
    def audible(t): i = int(t / rw); return 0 <= i < len(rms) and rms[i] > loud * .18
    # 格子の候補
    cands = []
    k = 0
    while off + k * q < dur - .6:
        t = off + k * q
        if t > .5 and audible(t):
            st = strength(env, t, .03)
            w = 1.3 if k % 16 == 0 else 1.15 if k % 4 == 0 else 1.0
            if k % cfg['sub'] == 0: cands.append((st * w, t, k, st))
            # EXTRA はテンポが遅めの曲だけ、強い音の16分も使う（素早い2連になる）
            elif diff == 'extra' and q >= .1 and st >= .45: cands.append((st * .75, t, k, st))
        k += 1
    active = sum(1 for c in cands if c[2] % cfg['sub'] == 0) * (q * cfg['sub'])
    want = int(cfg['nps'] * min(active, dur))
    cands.sort(reverse=True)
    picked = []
    for sc, t, k, st in cands:
        if len(picked) >= want or st < cfg['thr']: break
        if any(abs(t - p[0]) < cfg['gap'] - 1e-6 for p in picked): continue
        picked.append((t, k, st))
    picked.sort()
    # 実際の音の立ち上がりに合わせ直す
    notes = [[round(local_peak(env, t), 4), None, 'tap', st, k] for t, k, st in picked]
    # レーン：近くを行き来する
    lane = 2
    for i, n in enumerate(notes):
        gap = n[0] - notes[i - 1][0] if i else 9
        if diff == 'easy':
            opts = [l for l in range(LANES) if l != lane or gap > .9]
            wts = [1.6 if 1 <= l <= 3 else .8 for l in opts]
            wts = [w / (1 + abs(l - lane) * .4) for w, l in zip(wts, opts)]
        else:
            opts = [l for l in range(LANES) if (l != lane or gap > .45) and abs(l - lane) <= (2 if gap < .25 else 4)]
            wts = [1 / (1 + abs(abs(l - lane) - 1.2)) for l in opts]
        lane = rnd.choices(opts, wts)[0]; n[1] = lane
    # 長押し：次のノーツまで間があって音が強い所
    holds = 0; nh = int(len(notes) * cfg['hold'])
    order = sorted(range(len(notes) - 1), key=lambda i: -notes[i][3])
    for i in order:
        if holds >= nh: break
        n, nx = notes[i], notes[i + 1]
        g = nx[0] - n[0]
        if g < max(2 * beat, .7) or n[2] != 'tap': continue
        end = round(nx[0] - max(beat / 2, .22), 4)
        if end - n[0] < .35: continue
        n[2] = 'hold'; n.append(end); holds += 1
    # 一部の長押しは最後にフリック
    for n in notes:
        if n[2] == 'hold' and rnd.random() < .35: n[2] = 'hflick'
    # フリック：強い音で、次まで少し間がある所
    nf = int(len(notes) * cfg['flick']); fl = 0
    order = sorted(range(len(notes)), key=lambda i: -notes[i][3] * (1.2 if notes[i][4] % 8 == 0 else 1))
    for i in order:
        if fl >= nf: break
        n = notes[i]
        if n[2] != 'tap': continue
        nxt = notes[i + 1][0] - n[0] if i + 1 < len(notes) else 9
        if nxt < max(beat * .9, .25): continue
        n[2] = 'flick'; fl += 1
    out = [[n[0], n[1], n[2]] + ([n[5]] if n[2] in ('hold', 'hflick') else []) for n in notes]
    # 同時押し：特に強いアクセントの所だけ、間隔をあけて
    nc = int(len(out) * cfg['chord']); ct = []
    strong = sorted([n for n in notes if n[2] == 'tap'], key=lambda n: -n[3])
    for n in strong:
        if len(ct) >= nc: break
        t = n[0]
        if any(abs(c - t) < cfg['cgap'] for c in ct): continue
        if any(0 < abs(m[0] - t) < cfg['gap'] for m in out): continue
        if any(m[2] in ('hold', 'hflick') and m[0] - .05 <= t <= m[3] + .1 for m in out): continue
        lanes = [l for l in range(LANES) if abs(l - n[1]) >= 2 and not any(m[1] == l and abs(m[0] - t) < .3 for m in out)]
        if not lanes: continue
        out.append([t, rnd.choice(lanes), 'tap']); ct.append(t)
    out.sort(key=lambda n: (n[0], n[1]))
    # 同じレーンが近すぎる所は外す（念のため）
    fixed = []
    for n in out:
        if any(m[1] == n[1] and abs(m[0] - n[0]) < .1 for m in fixed): continue
        if any(m[2] in ('hold', 'hflick') and m[1] == n[1] and m[0] + .01 < n[0] <= m[3] + .05 for m in fixed): continue
        fixed.append(n)
    return fixed

def preview(y, off, bpm, dur, length=15):
    rms, rw = rms_curve(y, .5); w = int(length / rw)
    sc = [rms[i:i + w].mean() for i in range(len(rms) - w)]
    i = int(np.argmax(sc)); t = i * rw
    bar = 60 / bpm * 4; t = off + round((t - off) / bar) * bar
    t = max(0, min(t, dur - length - .5)); return [round(t, 3), round(t + length, 3)]

if __name__ == '__main__':
    path, bpm, off, seed = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    y = load(path); env = envelope(y); dur = len(y) / SR
    charts = {d: make(y, env, bpm, off, dur, d, seed) for d in CFG}
    res = {'charts': charts, 'preview': preview(y, off, bpm, dur), 'dur': round(dur, 2)}
    for d, c in charts.items():
        kinds = {}
        for n in c: kinds[n[2]] = kinds.get(n[2], 0) + 1
        tc = {}
        for n in c: tc[round(n[0], 3)] = tc.get(round(n[0], 3), 0) + 1
        print(f'{d:7s} {len(c):4d} notes  {len(c)/dur:.2f}/s  {kinds}  chords {sum(1 for v in tc.values() if v > 1)}  issues {len(check(c, d))}')
    print('preview', res['preview'])
    json.dump(res, open(sys.argv[5], 'w'))

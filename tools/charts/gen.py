"""使い方: git show 5389c50:www/game/index.html > old.html && python3 tools/charts/gen.py old.html （元になる旧EXTRAはこの版にある）
今の EXTRA から新しい HARD（間引き）と新しい EXTRA（追加）を作る。
音の立ち上がり（オンセット）の強さを手がかりに、
HARD は弱い位置のノーツを抜き、EXTRA は音が鳴っている空きの位置にノーツと同時押しを足す。"""
import sys, json, random, collections
sys.path.insert(0, __import__('os').path.dirname(__file__))
from onset import load, envelope, strength, load_songs

HTML = 'www/game/index.html'
AUDIO = 'www/game/audio/'
LANES = 5
HARD_CUT = .19   # HARD は今の EXTRA から約19%減らす
EXTRA_ADD = .22  # EXTRA は今の EXTRA から約22%増やす
CHORD_MAX = .045 # そのうち同時押しは元のノーツ数の4.5%まで
CHORD_GAP = 3.0  # 足す同時押しどうしは3秒以上あける
MIN_GAP = .118   # 足すノーツは前後のノーツとこれ以上あける

def unit_of(ch):
    ts = sorted({round(n[0], 4) for n in ch})
    gaps = [round(b - a, 2) for a, b in zip(ts, ts[1:]) if b - a > .09]
    c = collections.Counter(gaps).most_common(1)[0][0]
    near = [b - a for a, b in zip(ts, ts[1:]) if abs((b - a) - c) < .02]
    return sum(near) / len(near)

def holds_at(ch, t, pad=.06):
    return [n for n in ch if n[2] in ('hold', 'hflick') and n[0] - pad <= t <= n[3] + pad]

def busy_lane(ch, t, lane, near=.1):
    for n in ch:
        if n[1] != lane: continue
        if abs(n[0] - t) < near: return True
        if n[2] in ('hold', 'hflick') and n[0] - .06 <= t <= n[3] + .12: return True
    return False

def make_hard(ch, env, u):
    ch = sorted([list(n) for n in ch], key=lambda n: (n[0], n[1]))
    target = int(len(ch) * HARD_CUT)
    removed = set()
    # 同時押しの片方を半分ほど外す（弱いほうから）
    groups = collections.defaultdict(list)
    for i, n in enumerate(ch): groups[round(n[0], 3)].append(i)
    chords = [g for g in groups.values() if len(g) > 1]
    chords.sort(key=lambda g: strength(env, ch[g[0]][0]))
    for g in chords[:len(chords) // 2]:
        taps = [i for i in g if ch[i][2] == 'tap']
        if taps: removed.add(taps[-1])
    # 細かい連打の中の、音が弱いタップを抜く（続けて2つは抜かない）
    times = [n[0] for n in ch]
    cand = []
    for i, n in enumerate(ch):
        if n[2] != 'tap' or i in removed: continue
        prev = max([times[k] for k in range(i) if times[k] < n[0] - .01], default=-9)
        nxt = min([times[k] for k in range(i + 1, len(ch)) if times[k] > n[0] + .01], default=99)
        if n[0] - prev < 1.35 * u and nxt - n[0] < 1.35 * u:
            cand.append((strength(env, n[0]), i))
    cand.sort()
    for _, i in cand:
        if len(removed) >= target: break
        if (i - 1) in removed or (i + 1) in removed: continue
        removed.add(i)
    return [n for i, n in enumerate(ch) if i not in removed]

def pick_lane(ch, t, avoid, rnd, around):
    opts = []
    for l in range(LANES):
        if busy_lane(ch, t, l): continue
        cost = abs(l - around) + (3 if l in avoid else 0) + rnd.random() * .8
        opts.append((cost, l))
    return min(opts)[1] if opts else None

def make_extra(ch, env, u, seed):
    rnd = random.Random(seed)
    ch = sorted([list(n) for n in ch], key=lambda n: (n[0], n[1]))
    want = int(len(ch) * EXTRA_ADD)
    chord_budget = int(len(ch) * CHORD_MAX)
    steps = [u] + ([u / 2] if u / 2 >= .104 else [])
    # 1) 空いている所で音が鳴っている位置にノーツを足す
    ts = sorted({round(n[0], 4) for n in ch})
    cands = []
    for a, b in zip(ts, ts[1:]):
        for q in steps:
            k = 1
            while a + k * q < b - .6 * q:
                t = a + k * q
                gap_ok = min(t - a, b - t) >= (MIN_GAP if q == u else .104)
                st0 = strength(env, t)
                if gap_ok and (q == u or st0 >= .55):
                    cands.append((st0, round(t, 4), a, b))
                k += 1
    cands.sort(reverse=True)
    added = 0
    for st, t, a, b in cands:
        if added >= want - int(len(ch) * 0) - chord_budget or st < .3: break
        if any(abs(n[0] - t) < .104 for n in ch): continue
        if len(holds_at(ch, t)) >= 1 and any(abs(n[0] - t) < .2 for n in ch if n[2] not in ('hold', 'hflick')): continue
        la = [n[1] for n in ch if abs(n[0] - a) < .01]; lb = [n[1] for n in ch if abs(n[0] - b) < .01]
        around = (sum(la + lb) / len(la + lb)) if (la + lb) else 2
        lane = pick_lane(ch, t, set(la + lb), rnd, around)
        if lane is None: continue
        ch.append([t, lane, 'tap']); ch.sort(key=lambda n: (n[0], n[1])); added += 1
    # 2) 強いアクセントのタップを同時押しにする
    singles = []
    groups = collections.Counter(round(n[0], 3) for n in ch)
    for n in ch:
        if n[2] == 'tap' and groups[round(n[0], 3)] == 1 and not holds_at(ch, n[0]):
            singles.append((strength(env, n[0]), n))
    singles.sort(key=lambda x: -x[0])
    chord_ts = []
    for st, n in singles:
        if added >= want or len(chord_ts) >= chord_budget: break
        t = n[0]
        if any(abs(c - t) < CHORD_GAP for c in chord_ts): continue
        if any(0 < abs(m[0] - t) < MIN_GAP for m in ch if m is not n): continue
        mirror = LANES - 1 - n[1]
        lane = pick_lane(ch, t, {n[1], n[1] - 1, n[1] + 1}, rnd, mirror if mirror != n[1] else (0 if n[1] > 2 else 4))
        if lane is None or abs(lane - n[1]) < 2: continue
        ch.append([t, lane, 'tap']); ch.sort(key=lambda m: (m[0], m[1])); added += 1; chord_ts.append(t)
    return ch

def check(ch, name):
    errs = []
    ch = sorted(ch, key=lambda n: (n[0], n[1]))
    seen = set()
    for n in ch:
        k = (round(n[0], 3), n[1])
        if k in seen: errs.append(('dup', n))
        seen.add(k)
        for h in ch:
            if h is n or h[1] != n[1] or h[2] not in ('hold', 'hflick'): continue
            if h[0] + .01 < n[0] <= h[3] + .05: errs.append(('in-hold', n, h))
        fingers = len({m[1] for m in ch if abs(m[0] - n[0]) < .01}) + len([h for h in ch if h[2] in ('hold', 'hflick') and h[0] + .01 < n[0] <= h[3] + .05])
        if fingers > 2: errs.append(('3fingers', n))
    lanes = collections.defaultdict(list)
    for n in ch: lanes[n[1]].append(n[0])
    for l, ts in lanes.items():
        for a, b in zip(ts, ts[1:]):
            if b - a < .1: errs.append(('jack', l, a, b))
    return errs

if __name__ == '__main__':
    s, i, j, SONGS = load_songs(sys.argv[1] if len(sys.argv) > 1 else HTML)
    out = {}
    for x in SONGS:
        env = envelope(load(AUDIO + x['id'] + '.mp3'))
        old = x['charts']['extra']; u = unit_of(old)
        hard = make_hard(old, env, u)
        extra = make_extra(old, env, u, seed=x['id'])
        r = lambda c: [[round(n[0], 4), n[1], n[2]] + ([round(n[3], 4)] if len(n) > 3 else []) for n in sorted(c, key=lambda n: (n[0], n[1]))]
        out[x['id']] = {'hard': r(hard), 'extra': r(extra)}
        e_old, e_h, e_x = check(old, 'old'), check(hard, 'hard'), check(extra, 'extra')
        print(f"{x['key']:8s} u={u:.3f}  normal {len(x['charts']['normal'])}  old-extra {len(old)} ({len(old)/x['dur']:.2f}/s)  HARD {len(hard)} ({len(hard)/x['dur']:.2f}/s)  EXTRA {len(extra)} ({len(extra)/x['dur']:.2f}/s)  issues old/hard/extra {len(e_old)}/{len(e_h)}/{len(e_x)}")
        for e in (e_x[:4] if len(e_x) > len(e_old) else []): print('   ', e)
    json.dump(out, open('new_charts.json', 'w'))

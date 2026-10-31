import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from onset import load, envelope, SR, HOP
FPS = SR/HOP
def tempo(env, lo=70, hi=200):
    e = env - env.mean()
    ac = np.correlate(e, e, mode='full')[len(e)-1:]
    best=None
    for bpm in np.arange(lo, hi, .05):
        lag = 60/bpm*FPS
        # 1,2,4拍ぶんの相関の合計（倍・半分のテンポに引っぱられにくくする）
        sc = sum(np.interp(lag*k, np.arange(len(ac)), ac) for k in (1,2,4)) / 3
        if best is None or sc > best[0]: best=(sc,bpm)
    return best[1]
def phase(env, bpm):
    beat = 60/bpm; n = len(env)/FPS
    best=None
    for off in np.arange(0, beat, .002):
        ts = np.arange(off, n, beat); idx = ((ts*SR-512)/HOP).astype(int); idx=idx[(idx>=0)&(idx<len(env))]
        sc = env[idx].mean()
        if best is None or sc>best[0]: best=(sc,off)
    return best[1], best[0]
if __name__=='__main__':
    for f in sys.argv[1:]:
        y=load(f); env=envelope(y)
        b=tempo(env); off,sc=phase(env,b)
        # 2倍・半分のテンポで拍の上の強さを比べる
        alt={k: phase(env,b*k)[1] for k in (.5,1,2)}
        print(f, 'bpm %.2f beat %.4f offset %.3f onbeat %.2f'%(b,60/b,off,sc), 'alt', {k:round(v,2) for k,v in alt.items()}, 'mean env %.2f'%env.mean())

import numpy as np, subprocess, json
SR=22050; HOP=128
def load(path):
    raw=subprocess.run(['ffmpeg','-v','quiet','-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32)
def envelope(y):
    N=1024; win=np.hanning(N); n=(len(y)-N)//HOP
    frames=np.lib.stride_tricks.as_strided(y,shape=(n,N),strides=(y.strides[0]*HOP,y.strides[0]))
    S=np.log1p(100*np.abs(np.fft.rfft(frames*win,axis=1)))
    flux=np.maximum(0,np.diff(S,axis=0)).sum(axis=1)
    flux=np.concatenate([[0],flux])
    flux-= np.convolve(flux,np.ones(31)/31,mode='same')  # 局所平均を引く
    flux=np.maximum(flux,0); flux/= (np.percentile(flux,99)+1e-9)
    return flux  # frame k の時刻 = (k*HOP + N/2)/SR
def strength(env,t,win=0.035):
    c=int((t*SR-512)/HOP); w=int(win*SR/HOP)
    a=max(0,c-w); b=min(len(env),c+w+1)
    return float(env[a:b].max()) if b>a else 0.0
def load_songs(html):
    s=open(html).read(); i=s.index('const SONGS = '); j=s.index('\n',i)
    return s, i, j, json.loads(s[i+len('const SONGS = '):j].rstrip(';'))

import json, numpy as np
D=json.load(open('data.json')); Hs=np.load('Hs.npy'); Hc=np.load('Hcourt.npy')
N=1043
NORM=np.array([[1/960.,0,0],[0,1/540.,0],[0,0,1]])
W2S=[]
for i in range(N):
    M=NORM @ np.linalg.inv(Hs[i]) @ Hc        # world(m) -> normalised screen
    M=M/M[2,2]
    W2S.append([round(float(v),8) for v in M.flatten()[:8]])
out=dict(fps=60, n=N, dur=round(N/60.,3), impacts=D['impacts'], w2s=W2S, players={})
for s in ['near','far']:
    p=D['players'][s]
    out['players'][s]=dict(
        name=p['name'], mass=p['mass'],
        speed=[round(v,2) for v in p['speed']],
        acc=[round(v,1) for v in p['acc']],
        wx=[round(v,2) for v in p['wx']], wy=[round(v,2) for v in p['wy']],
        dist=[round(v,1) for v in p['dist']],
        hr=[round(v,1) for v in p['hr']],
        kcal=[round(v,2) for v in p['kcal']],
        box=[[round(b[0]/960,4),round(b[1]/540,4),round(b[2]/960,4),round(b[3]/540,4)] for b in p['box']],
        coverage=p['coverage'], heat=p['heat'],
        peak_speed=p['peak_speed'], avg_speed=p['avg_speed'], peak_acc=p['peak_acc'],
        total_dist=p['total_dist'], total_kcal=p['total_kcal'], peak_hr=p['peak_hr'])
json.dump(out,open('build/data.json','w'),separators=(',',':'))
import os; print('%.0f KB'%(os.path.getsize('build/data.json')/1024))
# sanity: project the four court corners at frame 0 and 800
for i in [0,800]:
    M=np.array(W2S[i]+[1.0]).reshape(3,3)
    for w in [(-5.485,-11.885),(5.485,11.885)]:
        v=M@np.array([w[0],w[1],1.0]); v/=v[2]
        print(i,w,'->',np.round(v[:2],3))

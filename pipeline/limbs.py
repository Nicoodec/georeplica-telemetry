import json,numpy as np,cv2
from scipy.signal import medfilt,savgol_filter
P=json.load(open('pose_raw.json')); D=json.load(open('build/data.json'))
Hc=np.load('Hcourt.npy'); Hci=np.linalg.inv(Hc)
N=1043; W,H=1920.,1080.
# analysis space was 960x540; normalised coords are shared
NOSE,LS,RS,LE,RE,LW,RW,LH,RH,LK,RK,LA,RA=range(13)
def ang(a,b,c):
    v1=a-b; v2=c-b
    n=(np.linalg.norm(v1)*np.linalg.norm(v2))
    if n<1e-6: return np.nan
    return float(np.degrees(np.arccos(np.clip(np.dot(v1,v2)/n,-1,1))))
out={}
for side in ['near','far']:
    seq=P[side]
    K=np.full((N,13,2),np.nan); C=np.zeros((N,13))
    last=None
    for i,p in enumerate(seq[:N]):
        if p is None:
            if last is not None: K[i]=last
            continue
        a=np.array(p)
        K[i]=a[:,:2]; C[i]=a[:,2]
        last=K[i]
    # fill leading gaps
    for j in range(13):
        for d in range(2):
            v=K[:,j,d]; idx=np.where(~np.isnan(v))[0]
            if len(idx)==0: v[:]=0; continue
            v[:idx[0]]=v[idx[0]]; v[idx[-1]+1:]=v[idx[-1]]
            nan=np.isnan(v)
            if nan.any(): v[nan]=np.interp(np.flatnonzero(nan),np.flatnonzero(~nan),v[~nan])
            K[:,j,d]=savgol_filter(medfilt(v,5),11,2)
    # ---- metrics in real units ----
    fy=np.array(D['players'][side]['box'])[:,1]+np.array(D['players'][side]['box'])[:,3]  # norm foot y
    fy_px=fy*540.0                       # analysis-space pixels
    stature_px=0.2289*fy_px+13.37        # calibrated apparent height of a 1.85 m player
    m_per_px=1.85/np.maximum(stature_px,6.0)
    kx=K[:,:,0]*960.0; ky=K[:,:,1]*540.0   # to analysis pixels
    knee=np.array([np.nanmean([ang(np.array([kx[i,LH],ky[i,LH]]),np.array([kx[i,LK],ky[i,LK]]),np.array([kx[i,LA],ky[i,LA]])),
                               ang(np.array([kx[i,RH],ky[i,RH]]),np.array([kx[i,RK],ky[i,RK]]),np.array([kx[i,RA],ky[i,RA]]))])
                   for i in range(N)])
    # stance width on the ground, via the court homography (ankles are on the ground)
    la=cv2.perspectiveTransform(np.stack([kx[:,LA],ky[:,LA]],1).reshape(-1,1,2).astype(np.float32),Hci).reshape(-1,2)
    ra=cv2.perspectiveTransform(np.stack([kx[:,RA],ky[:,RA]],1).reshape(-1,1,2).astype(np.float32),Hci).reshape(-1,2)
    stance=np.hypot(la[:,0]-ra[:,0],la[:,1]-ra[:,1])
    stance=savgol_filter(np.clip(stance,0,3.2),15,2)
    # racket-arm extension: longest shoulder->wrist distance, in metres
    dL=np.hypot(kx[:,LW]-kx[:,LS],ky[:,LW]-ky[:,LS]); dR=np.hypot(kx[:,RW]-kx[:,RS],ky[:,RW]-ky[:,RS])
    reach=np.maximum(dL,dR)*m_per_px
    reach=savgol_filter(np.clip(reach,0,1.5),15,2)
    # centre of mass height: hip midpoint above the ankle line
    hipy=(ky[:,LH]+ky[:,RH])/2; anky=np.maximum(ky[:,LA],ky[:,RA])
    com=np.clip((anky-hipy)*m_per_px,0,1.6)
    com=savgol_filter(com,15,2)
    knee=savgol_filter(np.nan_to_num(knee,nan=np.nanmedian(knee)),15,2)
    out[side]=dict(
      kp=[[ [int(round(K[i,j,0]*4000)),int(round(K[i,j,1]*4000))] for j in range(13)] for i in range(0,N,2)],
      conf=[round(float(C[i].mean()),2) for i in range(0,N,2)],
      knee=[round(float(v),1) for v in knee],
      stance=[round(float(v),3) for v in stance],
      reach=[round(float(v),3) for v in reach],
      com=[round(float(v),3) for v in com])
    print('%-5s rodilla %.0f-%.0f deg | apertura %.2f-%.2f m | alcance %.2f-%.2f m | CdM %.2f-%.2f m | conf %.2f'%(
      side,np.percentile(knee,5),np.percentile(knee,95),np.percentile(stance,5),np.percentile(stance,95),
      np.percentile(reach,5),np.percentile(reach,95),np.percentile(com,5),np.percentile(com,95),C.mean()))
json.dump(out,open('limbs.json','w'),separators=(',',':'))
import os;print('limbs.json %.0f KB'%(os.path.getsize('limbs.json')/1024))

import json, numpy as np
T=json.load(open('tracks.json')); S=json.load(open('screen.json')); IMP=json.load(open('impacts.json'))
N=1043; FPS=60.0; DT=1/FPS
MASS={'near':82.0,'far':85.0}          # kg, listed playing weights
out={'fps':FPS,'n':N,'impacts':IMP,'players':{}}

for side,name in [('near','Dimitrov'),('far','Nadal')]:
    d=T[side]
    sp=np.array(d['speed']); acc=np.array(d['acc'])
    wx=np.array(d['wx']); wy=np.array(d['wy']); dist=np.array(d['dist'])
    m=MASS[side]
    # --- metabolic model: horizontal running incl. acceleration cost (di Prampero style) ---
    # equivalent slope from horizontal acceleration
    g=9.81
    a_h=np.gradient(sp,DT)
    ES=np.clip(a_h/g,-0.45,0.45)                       # equivalent slope
    EM=np.sqrt(ES**2+1)                                # equivalent mass factor
    Cr=(155.4*ES**5-30.4*ES**4-43.3*ES**3+46.3*ES**2+19.5*ES+3.6)*EM   # J/kg/m
    P=np.clip(Cr*sp,0,None)*m                          # W
    P=P+m*1.3                                          # resting/postural baseline
    kJ=np.cumsum(P)*DT/1000.0
    kcal=kJ/4.184                                      # Cr is already a metabolic cost
    # --- heart-rate: first-order lag toward a load-driven target ---
    HRrest,HRmax=58.0,195.0
    METs=np.clip(P/m/1.222,1.0,None)                   # 1 MET = 3.5 mlO2/kg/min = 1.222 W/kg
    HRR=np.clip((METs-1.0)/(15.0-1.0),0.0,1.0)         # %HR reserve, METmax~15 for elite
    tgt=HRrest+(HRmax-HRrest)*np.clip(0.34+0.72*HRR,0,1.0)
    hr=np.empty(N); hr[0]=118.0; tau=14.0
    for i in range(1,N):
        k=DT/(tau if tgt[i]>hr[i-1] else tau*2.4)      # slower recovery than onset
        hr[i]=hr[i-1]+(tgt[i]-hr[i-1])*k
    # --- court coverage: fraction of singles court within 1.6 m of a visited point ---
    gx=np.arange(-5.0,5.01,0.5); gy=np.arange(-12.5,12.51,0.5)
    GX,GY=np.meshgrid(gx,gy)
    half=(GY>0) if side=='near' else (GY<0)
    pts=np.stack([wx,wy],1)[::3]
    dmin=np.full(GX.shape,9e9)
    for p in pts:
        dmin=np.minimum(dmin,np.hypot(GX-p[0],GY-p[1]))
    cov=float((dmin[half]<1.6).mean())
    # --- heatmap grid 34 x 40 over that player's half (+ run-off) ---
    HX=np.linspace(-8.0,8.0,41); HY=(np.linspace(0,15.0,34) if side=='near' else np.linspace(-15.0,0,34))
    H=np.zeros((33,40))
    ix=np.clip(np.digitize(wx,HX)-1,0,39); iy=np.clip(np.digitize(wy,HY)-1,0,32)
    for a,b in zip(iy,ix): H[a,b]+=1
    from scipy.ndimage import gaussian_filter
    H=gaussian_filter(H,1.6); H=H/H.max() if H.max()>0 else H
    out['players'][side]=dict(
        name=name, mass=m,
        speed=[round(float(v),3) for v in sp],
        acc=[round(float(v),3) for v in acc],
        wx=[round(float(v),3) for v in wx], wy=[round(float(v),3) for v in wy],
        dist=[round(float(v),2) for v in dist],
        hr=[round(float(v),1) for v in hr],
        kcal=[round(float(v),3) for v in kcal],
        power=[round(float(v),1) for v in P],
        box=[[round(c,1) for c in b] for b in S[side]['box']],
        foot=[[round(c,1) for c in b] for b in S[side]['foot']],
        coverage=round(cov,3),
        heat=[[round(float(v),3) for v in r] for r in H],
        peak_speed=round(float(sp.max()),2), avg_speed=round(float(sp.mean()),2),
        peak_acc=round(float(acc.max()),2), total_dist=round(float(dist[-1]),1),
        total_kcal=round(float(kcal[-1]),1), peak_hr=round(float(hr.max()),0))
    print('%-9s dist %.1f m  peak %.2f m/s  cov %.0f%%  kcal %.1f  HRpeak %.0f'%(
        name,dist[-1],sp.max(),cov*100,kcal[-1],hr.max()))
json.dump(out,open('data.json','w'))
import os; print('data.json %.0f KB'%(os.path.getsize('data.json')/1024))

import json, numpy as np, cv2
from scipy.signal import medfilt, savgol_filter
from scipy.ndimage import maximum_filter1d
T=json.load(open('tracks_raw.json')); Hc=np.load('Hcourt.npy'); Hci=np.linalg.inv(Hc)
FPS=60.0; dt=1/FPS
def i2w(p): return cv2.perspectiveTransform(np.float32(p).reshape(-1,1,2),Hci).reshape(-1,2)

def jac(fx,fy):
    """local metres-per-pixel 2x2 Jacobian of image->world at (fx,fy)"""
    p0=i2w([[fx,fy]])[0]; px=i2w([[fx+1,fy]])[0]; py=i2w([[fx,fy+1]])[0]
    return np.stack([px-p0,py-p0],axis=1)   # columns: d(world)/d(px), d(world)/d(py)

def rts(z, R, q):
    """constant-acceleration RTS smoother. z:(n,2) R:(n,2,2) q: jerk PSD"""
    n=len(z)
    F=np.eye(6)
    for i,(p,v,a) in enumerate([(0,1,2),(3,4,5)]):
        F[p,v]=dt; F[p,a]=0.5*dt*dt; F[v,a]=dt
    # white-noise-jerk process noise
    Q1=np.array([[dt**5/20,dt**4/8,dt**3/6],[dt**4/8,dt**3/3,dt**2/2],[dt**3/6,dt**2/2,dt]])*q
    Q=np.zeros((6,6)); Q[:3,:3]=Q1; Q[3:,3:]=Q1
    H=np.zeros((2,6)); H[0,0]=1; H[1,3]=1
    x=np.zeros(6); x[0],x[3]=z[0]
    P=np.eye(6)*np.array([4,25,100,4,25,100])
    xf=np.zeros((n,6)); Pf=np.zeros((n,6,6)); xp=np.zeros((n,6)); Pp=np.zeros((n,6,6))
    for k in range(n):
        if k>0: x=F@x; P=F@P@F.T+Q
        xp[k]=x; Pp[k]=P
        S=H@P@H.T+R[k]; K=P@H.T@np.linalg.inv(S)
        x=x+K@(z[k]-H@x); P=(np.eye(6)-K@H)@P
        xf[k]=x; Pf[k]=P
    xs=xf.copy()
    for k in range(n-2,-1,-1):
        C=Pf[k]@F.T@np.linalg.inv(Pp[k+1])
        xs[k]=xf[k]+C@(xs[k+1]-xp[k+1])
    return xs

out={}
for side,spx in [('near',2.6),('far',1.6)]:
    B=T[side]; n=len(B)
    fx=medfilt(np.array([b['fx'] for b in B]),5); fy=medfilt(np.array([b['fy'] for b in B]),5)
    HP=(0.2289,13.37)   # unified stature line, both players
    from scipy.ndimage import minimum_filter1d
    ex0=medfilt(np.array([b['ex0'] for b in B]),5); ex1=medfilt(np.array([b['ex1'] for b in B]),5)
    ey0=medfilt(np.array([b['ey0'] for b in B]),5); ey1=medfilt(np.array([b['ey1'] for b in B]),5)
    K=13
    X0=savgol_filter(minimum_filter1d(ex0,K),17,2); X1=savgol_filter(maximum_filter1d(ex1,K),17,2)
    Y0=savgol_filter(minimum_filter1d(ey0,K),17,2); Y1=savgol_filter(maximum_filter1d(ey1,K),17,2)
    # apparent stature at this depth, from court calibration
    prior_h=HP[0]*fy+HP[1]
    # the head/torso top is the reliable edge (thick, high contrast); thin legs are not.
    # derive the feet from the head downwards, and take whichever extent is larger.
    bot_from_head=Y0+prior_h*0.97
    bybot=np.maximum.reduce([Y1,fy,bot_from_head])+prior_h*0.04
    bh=np.maximum(bybot-Y0,prior_h*1.02)
    cxb=(X0+X1)/2.0
    bw=np.clip(X1-X0,bh*0.50,bh*1.70)
    Z=i2w(np.stack([fx,fy],1))
    R=np.zeros((n,2,2))
    for k in range(n):
        J=jac(fx[k],fy[k]); R[k]=J@np.diag([spx**2,spx**2])@J.T + np.eye(2)*1e-4
    xs=rts(Z,R,q=8.0)
    W=xs[:,[0,3]]; V=xs[:,[1,4]]; A=xs[:,[2,5]]
    sp=np.hypot(V[:,0],V[:,1]); acc=np.hypot(A[:,0],A[:,1])
    dist=np.concatenate([[0],np.cumsum(np.hypot(np.diff(W[:,0]),np.diff(W[:,1])))])
    # reproject smoothed world back to image for pixel-perfect overlay
    IP=cv2.perspectiveTransform(np.float32(W).reshape(-1,1,2),Hc).reshape(-1,2)
    out[side]=dict(fx=IP[:,0].tolist(),fy=IP[:,1].tolist(),
                   bw=bw.tolist(),bh=bh.tolist(),cxb=cxb.tolist(),bybot=bybot.tolist(),
                   wx=W[:,0].tolist(),wy=W[:,1].tolist(),
                   speed=sp.tolist(),acc=acc.tolist(),dist=dist.tolist())
    print('%-5s speed med %.2f p95 %.2f max %.2f | dist %.1f m | acc p95 %.1f max %.1f | mean %.2f'%(
        side,np.median(sp),np.percentile(sp,95),sp.max(),dist[-1],np.percentile(acc,95),acc.max(),sp.mean()))
json.dump(out,open('tracks.json','w'))

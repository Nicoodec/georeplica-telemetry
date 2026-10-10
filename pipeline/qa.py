import cv2,numpy as np,json
cv2.setNumThreads(2)
Hs=np.load('Hs.npy'); bg=cv2.imread('bg.png'); Hc=np.load('Hcourt.npy'); Hci=np.linalg.inv(Hc)
S=json.load(open('screen.json')); T=json.load(open('tracks.json'))
GFX=np.full((540,960),255,np.uint8)
for r in [(438,537,65,285),(0,44,0,215),(448,517,290,655)]: GFX[r[0]:r[1],r[2]:r[3]]=0
bgb=cv2.GaussianBlur(bg,(3,3),0); ONE=np.full((540,960),255,np.uint8)
res={'near':[], 'far':[]}
for i in range(0,1043,6):
    f=cv2.imread('work/fr_%04d.jpg'%(i+1))
    w=cv2.warpPerspective(f,Hs[i],(960,540))
    gm=cv2.warpPerspective(GFX,Hs[i],(960,540),flags=cv2.INTER_NEAREST)
    vm=cv2.erode(cv2.warpPerspective(ONE,Hs[i],(960,540),flags=cv2.INTER_NEAREST),np.ones((9,9),np.uint8))
    d=np.max(cv2.absdiff(cv2.GaussianBlur(w,(3,3),0),bgb),axis=2).astype(np.uint8)
    d=cv2.erode(d,np.ones((3,3),np.uint8))
    m=cv2.threshold(d,28,255,cv2.THRESH_BINARY)[1]
    m=cv2.bitwise_and(cv2.bitwise_and(m,gm),vm)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab,st,ce=cv2.connectedComponentsWithStats(m)
    for side in ['near','far']:
        fx,fy=T[side]['fx'][i],T[side]['fy'][i]          # ref-space smoothed foot
        best=None;bd=1e9
        for k in range(1,n):
            x,y,bw,bh,a=st[k]
            if a<40: continue
            cx,cy=ce[k][0], y+bh
            dd=((cx-fx)**2+(cy-fy)**2)**.5
            if dd<bd: bd=dd;best=k
        if best is None or bd>45: res[side].append(None); continue
        ys,xs=np.nonzero(lab==best)
        # map component pixels ref->screen, test against displayed screen box
        P=cv2.perspectiveTransform(np.float32(np.stack([xs,ys],1)).reshape(-1,1,2),
                                   np.linalg.inv(Hs[i])).reshape(-1,2)
        bx,by,bw2,bh2=S[side]['box'][i]
        inside=((P[:,0]>=bx)&(P[:,0]<=bx+bw2)&(P[:,1]>=by)&(P[:,1]<=by+bh2)).mean()
        res[side].append(float(inside))
for side in ['near','far']:
    v=[x for x in res[side] if x is not None]
    print('%-5s n=%d  coverage mean %.3f  p05 %.3f  min %.3f  frames<0.80: %d  unmatched: %d'%(
        side,len(v),np.mean(v),np.percentile(v,5),min(v),sum(1 for x in v if x<0.80),
        sum(1 for x in res[side] if x is None)))
json.dump(res,open('qa.json','w'))

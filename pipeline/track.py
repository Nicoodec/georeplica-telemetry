import cv2, numpy as np, json
cv2.setNumThreads(2)
Hs=np.load('Hs.npy'); bg=cv2.imread('bg.png'); Hc=np.load('Hcourt.npy')
Hci=np.linalg.inv(Hc); N=len(Hs)
GFX=np.full((540,960),255,np.uint8)
for r in [(438,537,65,285),(0,44,0,215),(448,517,290,655)]: GFX[r[0]:r[1],r[2]:r[3]]=0
bgb=cv2.GaussianBlur(bg,(3,3),0)
ONE=np.full((540,960),255,np.uint8)

def w2i(p): return cv2.perspectiveTransform(np.float32(p).reshape(-1,1,2),Hc).reshape(-1,2)
def i2w(p): return cv2.perspectiveTransform(np.float32(p).reshape(-1,1,2),Hci).reshape(-1,2)

def frame_blobs(i):
    f=cv2.imread('work/fr_%04d.jpg'%(i+1))
    w=cv2.warpPerspective(f,Hs[i],(960,540))
    gm=cv2.warpPerspective(GFX,Hs[i],(960,540),flags=cv2.INTER_NEAREST)
    vm=cv2.warpPerspective(ONE,Hs[i],(960,540),flags=cv2.INTER_NEAREST)
    vm=cv2.erode(vm,np.ones((9,9),np.uint8))
    d=np.max(cv2.absdiff(cv2.GaussianBlur(w,(3,3),0),bgb),axis=2).astype(np.uint8)
    d=cv2.erode(d,np.ones((3,3),np.uint8))
    m=cv2.threshold(d,28,255,cv2.THRESH_BINARY)[1]
    m=cv2.bitwise_and(m,gm); m=cv2.bitwise_and(m,vm)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,ce=cv2.connectedComponentsWithStats(m)
    cands=[]
    for k in range(1,n):
        x,y,bw,bh,a=st[k]
        if a<40 or bh<8: continue
        fill=a/float(bw*bh); ar=bw/float(bh)
        if fill<0.20 or ar>2.8 or ar<0.15: continue
        ys,xs=np.nonzero(lab[y:y+bh,x:x+bw]==k)
        ys=ys+y; xs=xs+x
        # robust box: percentiles reject shadow spikes / racket tips
        x0,x1=np.percentile(xs,[1,99]); y0,y1=np.percentile(ys,[1,99])
        ex0,ex1,ey0,ey1=float(xs.min()),float(xs.max()),float(ys.min()),float(ys.max())
        band=ys>=(y1-max(3,0.18*(y1-y0)))
        fx=float(np.median(xs[band])) if band.sum() else float((x0+x1)/2)
        fy=float(y1)
        wx,wy=i2w([[fx,fy]])[0]
        if abs(wx)>11.0 or wy<-23.0 or wy>17.0: continue
        if fy<86: continue
        px=w[y:y+bh,x:x+bw]; msk=(lab[y:y+bh,x:x+bw]==k)
        col=px[msk].mean(axis=0) if msk.sum() else np.zeros(3)
        cands.append(dict(fx=fx,fy=fy,x=float(x0),y=float(y0),w=float(x1-x0),h=float(y1-y0),
                          ex0=ex0,ey0=ey0,ex1=ex1,ey1=ey1,
                          a=int(a),wx=float(wx),wy=float(wy),
                          b=float(col[0]),g=float(col[1]),r=float(col[2])))
    return cands

allc=[]
for i in range(N):
    allc.append(frame_blobs(i))
    if i%100==0: print('f',i,flush=True)
json.dump(allc,open('cands.json','w'))
print('DONE',flush=True)

import os,json,numpy as np,cv2
os.environ.setdefault('YOLO_VERBOSE','False')
from ultralytics import YOLO
cv2.setNumThreads(1)
S=json.load(open('build/data.json'))
model=YOLO('mdl/yolo11n-pose.pt')
cap=cv2.VideoCapture('src.mp4')
N=1043
# COCO-17 -> keep 13 (drop eyes/ears)
KEEP=[0,5,6,7,8,9,10,11,12,13,14,15,16]
out={'near':[], 'far':[]}
f=0
while f<N:
    ok,img=cap.read()
    if not ok: break
    H,W=img.shape[:2]
    for side in ['near','far']:
        bx,by,bw,bh=S['players'][side]['box'][f]
        x0,y0,x1,y1=bx*W,by*H,(bx+bw)*W,(by+bh)*H
        mx,my=(x1-x0)*0.55,(y1-y0)*0.30
        cx0=int(max(0,x0-mx));cy0=int(max(0,y0-my))
        cx1=int(min(W,x1+mx));cy1=int(min(H,y1+my))
        crop=img[cy0:cy1,cx0:cx1]
        if crop.size==0: out[side].append(None); continue
        sc=max(1.0,320.0/max(1,crop.shape[0]))
        big=cv2.resize(crop,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
        r=model.predict(big,imgsz=320,conf=0.15,verbose=False,device='cpu')[0]
        if r.keypoints is None or len(r.keypoints.data)==0: out[side].append(None); continue
        # pick the detection whose box area is largest
        k=int(np.argmax([b[2]*b[3] for b in r.boxes.xywh.cpu().numpy()])) if len(r.boxes) else 0
        kp=r.keypoints.data[k].cpu().numpy()      # (17,3) x,y,conf
        pts=[]
        for i in KEEP:
            x,y,c=kp[i]
            pts.append([round(float(cx0+x/sc)/W,5), round(float(cy0+y/sc)/H,5), round(float(c),2)])
        out[side].append(pts)
    f+=1
    if f%100==0: print('pose',f,flush=True)
json.dump(out,open('pose_raw.json','w'))
ok={s:sum(1 for p in out[s] if p) for s in out}
print('DONE',ok,flush=True)

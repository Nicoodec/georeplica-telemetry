import json, numpy as np, cv2
T=json.load(open('tracks.json')); Hs=np.load('Hs.npy'); N=len(Hs)
out={}
for s in ['near','far']:
    d=T[s]; pts=[]; box=[]
    for i in range(N):
        Hi=np.linalg.inv(Hs[i])     # ref -> screen
        p=cv2.perspectiveTransform(np.float32([[[d['fx'][i],d['fy'][i]]]]),Hi).reshape(2)
        # box corners in ref, mapped to screen, then axis-aligned
        w,h=d['bw'][i],d['bh'][i]; cx=d['cxb'][i]; yb=d['bybot'][i]
        c=np.float32([[cx-w/2,yb-h],[cx+w/2,yb-h],[cx+w/2,yb],[cx-w/2,yb]]).reshape(-1,1,2)
        cs=cv2.perspectiveTransform(c,Hi).reshape(-1,2)
        x0,y0=cs.min(0); x1,y1=cs.max(0)
        pts.append([round(float(p[0]),2),round(float(p[1]),2)])
        box.append([round(float(x0),1),round(float(y0),1),round(float(x1-x0),1),round(float(y1-y0),1)])
    out[s]=dict(foot=pts,box=box)
json.dump(out,open('screen.json','w'))
print('ok',N)

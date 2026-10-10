import cv2,numpy as np,re
im=cv2.imread('/root/.claude/uploads/1cd7bf5d-9512-5cab-be98-cba56a9b2b32/2f018dfb-image.png')
U=3
big=cv2.GaussianBlur(cv2.resize(im,None,fx=U,fy=U,interpolation=cv2.INTER_CUBIC),(5,5),0)
b,g,r=[big[:,:,i].astype(int) for i in range(3)]
blue=(((b>90)&(b-r>50)&(b-g>30))*255).astype(np.uint8)
white=(((r>95)&(g>95)&(b>95)&(abs(b-r)<60))*255).astype(np.uint8)
k=np.ones((3,3),np.uint8)
blue=cv2.morphologyEx(blue,cv2.MORPH_CLOSE,k); white=cv2.morphologyEx(white,cv2.MORPH_CLOSE,k)

def trace(mask):
    cs,_=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    out=[]
    for c in cs:
        if cv2.contourArea(c)<18*U*U: continue
        a=cv2.approxPolyDP(c,0.7,True).reshape(-1,2).astype(float)
        if len(a)>=3: out.append(a)
    return out
PB,PW=trace(blue),trace(white)
def bbox(ps):
    A=np.vstack(ps); return A[:,0].min(),A[:,1].min(),A[:,0].max(),A[:,1].max()
bx0,by0,bx1,by1=bbox(PB); wx0,wy0,wx1,wy1=bbox(PW)
def emit(ps,ox,oy,s):
    return "".join('<path d="M%s Z"/>'%(" L".join("%.2f,%.2f"%((p[0]-ox)*s,(p[1]-oy)*s) for p in a))+"\n" for a in ps)

# ---- 1) faithful stacked lockup, normalised to a 1000-unit width
X0,Y0=min(bx0,wx0),min(by0,wy0); X1,Y1=max(bx1,wx1),max(by1,wy1)
s=1000.0/(X1-X0); Hh=(Y1-Y0)*s
svg=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 %.1f" role="img" aria-label="geoReplica.ai">\n'%Hh
 +'<g fill="var(--logo-mark,#0079F5)" fill-rule="evenodd">\n'+emit(PB,X0,Y0,s)+'</g>\n'
 +'<g fill="var(--logo-text,#ECE9F3)" fill-rule="evenodd">\n'+emit(PW,X0,Y0,s)+'</g>\n</svg>\n')
open('build/logo.svg','w').write(svg)

# ---- 2) horizontal bar lockup: mark left, wordmark right, both optically sized
H=100.0
sb=H/(by1-by0)                      # mark fills the bar height
sw=(H*0.52)/(wy1-wy0)               # wordmark at 52% of it
gap=H*0.26
markW=(bx1-bx0)*sb; wordW=(wx1-wx0)*sw; wordH=(wy1-wy0)*sw
tot=markW+gap+wordW
def emit2(ps,ox,oy,s,dx,dy):
    return "".join('<path d="M%s Z"/>'%(" L".join("%.2f,%.2f"%((p[0]-ox)*s+dx,(p[1]-oy)*s+dy) for p in a))+"\n" for a in ps)
bar=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.1f %.1f" role="img" aria-label="geoReplica.ai">\n'%(tot,H)
 +'<g fill="var(--logo-mark,#0079F5)" fill-rule="evenodd">\n'+emit2(PB,bx0,by0,sb,0,0)+'</g>\n'
 +'<g fill="var(--logo-text,#ECE9F3)" fill-rule="evenodd">\n'
 +emit2(PW,wx0,wy0,sw,markW+gap,(H-wordH)/2)+'</g>\n</svg>\n')
open('build/logo-bar.svg','w').write(bar)
import os
print('logo.svg      %.1f KB  viewBox 1000x%.0f'%(os.path.getsize('build/logo.svg')/1024,Hh))
print('logo-bar.svg  %.1f KB  viewBox %.0fx%.0f  (texto al %.0f%% de la altura)'%(
  os.path.getsize('build/logo-bar.svg')/1024,tot,H,wordH))

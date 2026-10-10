import cv2, numpy as np
cv2.setNumThreads(2)
Hs=np.load('Hs.npy'); N=len(Hs)
acc=[]; valid=np.zeros((540,960),np.float32)
for i in range(0,N,7):
    g=cv2.imread('work/fr_%04d.jpg'%(i+1))
    w=cv2.warpPerspective(g,Hs[i],(960,540))
    vm=cv2.warpPerspective(np.full((540,960),1,np.uint8),Hs[i],(960,540))
    valid+=vm
    acc.append(w)
A=np.array(acc)
bg=np.median(A,axis=0).astype(np.uint8)
cv2.imwrite('bg.png',bg)
np.save('valid.npy',(valid>len(acc)*0.5).astype(np.uint8))
print('bg built from',len(acc),'frames')

import cv2, numpy as np, glob
cv2.setNumThreads(2)
fs = sorted(glob.glob('work/fr_*.jpg'))
N=len(fs)
ref = cv2.imread(fs[0], cv2.IMREAD_GRAYSCALE)
M = np.full(ref.shape, 255, np.uint8)
M[440:535, 70:280]=0; M[0:42,0:210]=0; M[450:515,295:650]=0
det = cv2.ORB_create(nfeatures=1500, fastThreshold=12)
kp0,de0 = det.detectAndCompute(ref,M)
matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
Hs=[np.eye(3)]
for i in range(1,N):
    g=cv2.imread(fs[i],cv2.IMREAD_GRAYSCALE)
    kp,de=det.detectAndCompute(g,M)
    if de is None or len(kp)<20: Hs.append(Hs[-1]); continue
    mt=matcher.knnMatch(de,de0,k=2)
    good=[m for m,n in mt if m.distance<0.78*n.distance]
    if len(good)<25: Hs.append(Hs[-1]); continue
    src=np.float32([kp[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst=np.float32([kp0[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    Hm,inl=cv2.findHomography(src,dst,cv2.RANSAC,3.0)
    Hs.append(Hm if Hm is not None else Hs[-1])
    if i%150==0: print(i,len(good),flush=True)
np.save('Hs.npy',np.array(Hs)); print('DONE',len(Hs),flush=True)

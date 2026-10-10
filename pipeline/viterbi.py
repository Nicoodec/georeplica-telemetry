import json, numpy as np
C=json.load(open('cands.json')); N=len(C)
PRI={'near':dict(hs=(0.1461,17.12),hsig=14.6,col=np.array([136,138,144.]),csig=np.array([16,13,12.]),sel=lambda b:b['wy']>0),
     'far' :dict(hs=(0.1531,14.85),hsig=6.7, col=np.array([81,72,71.]),  csig=np.array([12,11,8.]), sel=lambda b:b['wy']<0)}

def unary(b,P):
    hexp=P['hs'][0]*b['fy']+P['hs'][1]
    cs=min(((b['h']-hexp)/P['hsig'])**2,12)
    col=np.array([b['b'],b['g'],b['r']])
    cc=min(np.sum(((col-P['col'])/(P['csig']*2.0))**2),12)
    ca=max(0.0,1.5-np.log1p(b['a'])/4.0)*2.0   # mild preference for substantial blobs
    return cs+cc+ca

def run(side):
    P=PRI[side]
    idx=[]; cand=[]
    for i in range(N):
        s=[b for b in C[i] if P['sel'](b)]
        if s: idx.append(i); cand.append(s)
    M=len(cand)
    cost=[np.array([unary(b,P) for b in cand[0]])]
    bp=[np.zeros(len(cand[0]),int)]
    for t in range(1,M):
        dt=max(1,idx[t]-idx[t-1])
        prev=np.array([[b['wx'],b['wy']] for b in cand[t-1]])
        cur =np.array([[b['wx'],b['wy']] for b in cand[t]])
        D=np.linalg.norm(cur[:,None,:]-prev[None,:,:],axis=2)/dt      # m per frame
        T=np.minimum((D/0.14)**2,20000.0)
        tot=T+cost[-1][None,:]
        bi=np.argmin(tot,axis=1); best=tot[np.arange(len(cur)),bi]
        u=np.array([unary(b,P) for b in cand[t]])
        cost.append(best+u); bp.append(bi)
    path=[int(np.argmin(cost[-1]))]
    for t in range(M-1,0,-1): path.append(int(bp[t][path[-1]]))
    path=path[::-1]
    tr={}
    for t,k in enumerate(path):
        b=cand[t][k]; tr[idx[t]]=b
    return tr

out={}
for side in ['near','far']:
    tr=run(side)
    # fill gaps by linear interpolation in world coords
    ks=sorted(tr); full=[]
    for i in range(N):
        if i in tr: full.append(tr[i]); continue
        lo=max([k for k in ks if k<i],default=None); hi=min([k for k in ks if k>i],default=None)
        if lo is None: full.append(dict(tr[hi],interp=1))
        elif hi is None: full.append(dict(tr[lo],interp=1))
        else:
            a=(i-lo)/(hi-lo); A,B=tr[lo],tr[hi]
            full.append({k:(A[k]+(B[k]-A[k])*a if isinstance(A[k],(int,float)) else A[k]) for k in A}|{'interp':1})
    out[side]=full
    sp=np.array([[b['wx'],b['wy']] for b in full])
    d=np.linalg.norm(np.diff(sp,axis=0),axis=1)*60
    print(side,'median speed %.2f m/s  p95 %.2f  max %.2f'%(np.median(d),np.percentile(d,95),d.max()))
json.dump(out,open('tracks_raw.json','w'))
print('ok')

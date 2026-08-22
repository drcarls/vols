import json, numpy as np, random, math, statistics
from collections import Counter
nat=json.load(open('data/national_walmart.json'))
def clus(S,cols,y,gkey):
    n=len(S); g=[r[gkey] for r in S]; gs=sorted(set(g))
    D=np.column_stack([[1.0 if r[gkey]==c else 0.0 for r in S] for c in gs[1:]]) if len(gs)>1 else np.zeros((n,0))
    X=np.column_stack([np.ones(n)]+cols+[D])
    beta,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@beta
    k=np.linalg.matrix_rank(X); XtXi=np.linalg.pinv(X.T@X)
    meat=np.zeros((X.shape[1],)*2)
    for c in gs:
        idx=[i for i,r in enumerate(S) if r[gkey]==c]
        v=X[idx].T@res[idx]; meat+=np.outer(v,v)
    G=len(gs); V=XtXi@meat@XtXi*((G/(G-1))*((n-1)/max(n-k,1)) if G>1 else 1)
    return beta, np.sqrt(np.diag(V)), G
for st in ('TX','CA'):
    S=[r for r in nat if r['state']==st and r.get('county')]
    y=np.array([r['price'] for r in S])
    H=np.array([(r.get('hisp') or 0) for r in S]); B=np.array([r['black'] for r in S],float)
    I=np.array([r['inc'] for r in S])/1000; P=np.log(np.array([r['pop'] for r in S],float))
    # (1) no FE
    X=np.column_stack([np.ones(len(S)),H,B,I,P])
    bt,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@bt; dof=len(S)-X.shape[1]
    se=np.sqrt(np.diag(np.linalg.pinv(X.T@X))*(res@res/dof))
    print(f"\n{st}  n={len(S)}  counties={len({r['county'] for r in S})}")
    print(f"  no FE, plain SE      : %Hisp={bt[1]:+.5f}(t{bt[1]/se[1]:+.2f})  %Black={bt[2]:+.5f}(t{bt[2]/se[2]:+.2f})")
    b2,s2,G=clus(S,[H,B,I,P],y,'county')
    print(f"  county FE, cluster SE: %Hisp={b2[1]:+.5f}(t{b2[1]/s2[1]:+.2f})  %Black={b2[2]:+.5f}(t{b2[2]/s2[2]:+.2f})   G={G}")
    # within-county permutation of %Hisp
    rng=np.random.default_rng(7); cts=sorted({r['county'] for r in S})
    idxby={c:[i for i,r in enumerate(S) if r['county']==c] for c in cts}
    def refit(h):
        D=np.column_stack([[1.0 if r['county']==c else 0.0 for r in S] for c in cts[1:]])
        X=np.column_stack([np.ones(len(S)),h,B,I,P,D])
        bb,*_=np.linalg.lstsq(X,y,rcond=None); return bb[1]
    obs=refit(H); null=[]
    for _ in range(2000):
        hp=H.copy()
        for c in cts:
            ii=idxby[c]; hp[ii]=rng.permutation(hp[ii])
        null.append(refit(hp))
    null=np.array(null)
    print(f"  within-county permutation on %Hisp: obs={obs:+.5f}  two-sided p={np.mean(np.abs(null)>=abs(obs)):.4f}")
    # how concentrated are Hispanic ZIPs by county?
    hi=[r for r in S if (r.get('hisp') or 0)>=50]; lo=[r for r in S if (r.get('hisp') or 0)<=20]
    ch=Counter(r['county'] for r in hi); cl=Counter(r['county'] for r in lo)
    print(f"  high-Hisp ZIPs (n={len(hi)}) top counties: {ch.most_common(5)}")
    print(f"  low-Hisp  ZIPs (n={len(lo)}) top counties: {cl.most_common(5)}")
    ov=set(ch)&set(cl)
    print(f"  counties containing BOTH tails: {len(ov)} of {len(set(ch)|set(cl))}")

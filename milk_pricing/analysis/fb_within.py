import json, numpy as np
from collections import Counter
nat=json.load(open('data/national_walmart.json'))
sc=json.load(open('data/sc_walmart_official.json')); scmap={r['zip']:r for r in sc}
rows=[]
for r in nat:
    rr=dict(r)
    if r['state']=='SC' and r['zip'] in scmap: rr['price']=scmap[r['zip']]['price']
    rows.append(rr)
for st in ('SC','LA','MS','AR','NC','AL'):
    S=[r for r in rows if r['state']==st and r.get('county') and r['geo']=='rural']
    if len(S)<25: print(st,"too small"); continue
    y=np.array([r['price'] for r in S]); B=np.array([r['black'] for r in S],float)
    I=np.array([r['inc'] for r in S])/1000; P=np.log(np.array([r['pop'] for r in S],float))
    X=np.column_stack([np.ones(len(S)),B,I,P])
    bt,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@bt
    se=np.sqrt(np.diag(np.linalg.pinv(X.T@X))*(res@res/(len(S)-4)))
    cts=sorted({r['county'] for r in S})
    multi=[c for c in cts if sum(1 for r in S if r['county']==c)>1]
    nin=sum(1 for r in S if r['county'] in multi)
    hi=Counter(r['county'] for r in S if r['black']>=30); lo=Counter(r['county'] for r in S if r['black']<=10)
    print(f"{st}: rural n={len(S)}  counties={len(cts)}  ZIPs in multi-ZIP counties={nin}"
          f"  |  no-FE %Black={bt[1]:+.5f}(t{bt[1]/se[1]:+.2f})"
          f"  |  counties w/ BOTH tails={len(set(hi)&set(lo))} of {len(set(hi)|set(lo))}")
    if len(multi)>=3 and nin>=20:
        M=[r for r in S if r['county'] in multi]
        ym=np.array([r['price'] for r in M])
        D=np.column_stack([[1.0 if r['county']==c else 0.0 for r in M] for c in multi[1:]])
        Xm=np.column_stack([np.ones(len(M)),[r['black'] for r in M],
                            np.array([r['inc'] for r in M])/1000,
                            np.log(np.array([r['pop'] for r in M],float)),D])
        bb,*_=np.linalg.lstsq(Xm,ym,rcond=None); rr2=ym-Xm@bb
        k=np.linalg.matrix_rank(Xm)
        sem=np.sqrt(np.diag(np.linalg.pinv(Xm.T@Xm))*(rr2@rr2/max(len(M)-k,1)))
        print(f"      within-county (n={len(M)}, {len(multi)} counties): %Black={bb[1]:+.5f}(t{bb[1]/sem[1]:+.2f})")

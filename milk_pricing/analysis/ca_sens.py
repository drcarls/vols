import json, numpy as np
from collections import Counter
nat=json.load(open('data/national_walmart.json'))
A={z:v["whole"] for z,v in json.load(open('data/aldi_pooled.json')).items() if v.get("whole")}
meta={r['zip']:r for r in nat}
def clean_counties(st,minz=6):
    S=[z for z in A if meta.get(z,{}).get('state')==st]
    cnt=Counter(meta[z]['county'] for z in S)
    f=Counter(meta[z]['county'] for z in S if abs(A[z]-2.19)<0.005)
    return {c for c,n in cnt.items() if n>=minz and f.get(c,0)==0}
def sample(st):
    good=clean_counties(st)
    return [meta[z] for z in A if meta.get(z,{}).get('state')==st and meta[z]['county'] in good]
CA=sample('CA')

def fit(S,yf,seed_perm=None,rng=None):
    """county FE, cluster-robust on county. returns (beta_black, t_black)"""
    n=len(S); cts=sorted({r['county'] for r in S})
    blk=np.array([r['black'] for r in S],float)
    if rng is not None:  # permute %Black within county
        blk=blk.copy()
        for c in cts:
            idx=[i for i,r in enumerate(S) if r['county']==c]
            blk[idx]=rng.permutation(blk[idx])
    cols=[np.array([(r['hisp'] or 0) for r in S]), blk,
          np.array([r['inc'] for r in S])/1000, np.array([r['pop'] for r in S])/1000]
    CD=np.column_stack([[1.0 if r['county']==c else 0.0 for r in S] for c in cts[1:]])
    X=np.column_stack([np.ones(n)]+cols+[CD])
    y=np.array([yf(r) for r in S])
    beta,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@beta
    k=np.linalg.matrix_rank(X); XtXi=np.linalg.pinv(X.T@X)
    cidx=[cts.index(r['county']) for r in S]; meat=np.zeros((X.shape[1],)*2)
    for g in set(cidx):
        idx=[i for i,s in enumerate(cidx) if s==g]
        v=X[idx].T@res[idx]; meat+=np.outer(v,v)
    G=len(set(cidx))
    V=XtXi@meat@XtXi*((G/(G-1))*((n-1)/max(n-k,1)))
    se=np.sqrt(np.diag(V))
    return beta[2], beta[2]/se[2]

YA=lambda r:A[r['zip']]; YS=lambda r:r['price']-A[r['zip']]
b=[r['black'] for r in CA]
print("CA metro pctBlack distribution: n={} median={:.1f} p75={:.1f} p90={:.1f} max={:.1f} n>=20pct:{} n>=30pct:{}".format(
    len(b),np.median(b),np.percentile(b,75),np.percentile(b,90),max(b),sum(x>=20 for x in b),sum(x>=30 for x in b)))

print("\nLeave-out sensitivity (SAME clustered county-FE model), dropping the N highest-%Black ZIPs:")
order=sorted(range(len(CA)),key=lambda i:-CA[i]['black'])
for N in (0,1,2,3,4,5,8,10):
    keep=[CA[i] for i in range(len(CA)) if i not in set(order[:N])]
    ba,ta=fit(keep,YA); bs,ts=fit(keep,YS)
    print(f"  drop {N:>2}: n={len(keep):>3}  Aldi %Black={ba:+.5f}(t{ta:+.2f})   spread %Black={bs:+.5f}(t{ts:+.2f})")

print("\nLeave-one-county-out (drop each county entirely):")
for c in sorted({r['county'] for r in CA}):
    keep=[r for r in CA if r['county']!=c]
    ba,ta=fit(keep,YA); bs,ts=fit(keep,YS)
    print(f"  minus {c:<16} n={len(keep):>3}  Aldi %Black={ba:+.5f}(t{ta:+.2f})   spread %Black={bs:+.5f}(t{ts:+.2f})")

print("\nWithin-county permutation test on %Black (Aldi price), 5000 draws:")
rng=np.random.default_rng(11)
obs,_=fit(CA,YA)
null=[fit(CA,YA,rng=rng)[0] for _ in range(5000)]
null=np.array(null)
print(f"  observed {obs:+.5f}   two-sided p={np.mean(np.abs(null)>=abs(obs)):.4f}   one-sided(neg) p={np.mean(null<=obs):.4f}")
obs2,_=fit(CA,YS)
rng=np.random.default_rng(11)
null2=np.array([fit(CA,YS,rng=rng)[0] for _ in range(5000)])
print(f"  spread observed {obs2:+.5f}   two-sided p={np.mean(np.abs(null2)>=abs(obs2)):.4f}")

print("\nHow much Aldi price variation is there in CA metros?")
vals=[A[r['zip']] for r in CA]
print("  unique Aldi prices:",sorted(Counter(vals).items())[:12])
print("  n distinct =",len(set(vals)))
hi=[r for r in CA if r['black']>=20]
print("\nThe high-%Black CA ZIPs:")
for r in sorted(hi,key=lambda r:-r['black']):
    print(f"  {r['zip']} {r['county']:<14} %B={r['black']:.1f} inc=${r['inc']:,} WM=${r['price']:.2f} Aldi=${A[r['zip']]:.2f}")

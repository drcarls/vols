import json, numpy as np, statistics, math
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
def reg(S,label,terms):
    n=len(S); cts=sorted({r['county'] for r in S})
    cols=[]; names=[]
    for f,nm in terms: cols.append(np.array([f(r) for r in S])); names.append(nm)
    cols.append(np.array([r['inc'] for r in S])/1000); names.append("income $k")
    cols.append(np.array([r['pop'] for r in S])/1000); names.append("pop k")
    CD=np.column_stack([[1.0 if r['county']==c else 0.0 for r in S] for c in cts[1:]]) if len(cts)>1 else np.zeros((n,0))
    print(f"\n{label}   n={n}, counties={len(cts)}")
    for yf,ynm in ((lambda r:r['price'],'Walmart'),(lambda r:A[r['zip']],'Aldi'),
                   (lambda r:r['price']-A[r['zip']],'spread')):
        y=np.array([yf(r) for r in S])
        X=np.column_stack([np.ones(n)]+cols+[CD])
        beta,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@beta
        k=np.linalg.matrix_rank(X); XtXi=np.linalg.pinv(X.T@X)
        cidx=[cts.index(r['county']) for r in S]; meat=np.zeros((X.shape[1],)*2)
        for g in set(cidx):
            idx=[i for i,s in enumerate(cidx) if s==g]
            v=X[idx].T@res[idx]; meat+=np.outer(v,v)
        G=len(set(cidx))
        V=XtXi@meat@XtXi*((G/(G-1))*((n-1)/max(n-k,1)) if G>1 else 1)
        se=np.sqrt(np.diag(V)); t=beta/se
        parts=" ".join(f"{names[i]}={beta[i+1]:+.5f}(t{t[i+1]:+.2f})" for i in range(len(terms)))
        print(f"   {ynm:<9} {parts}")
H=(lambda r:(r['hisp'] or 0),"%Hisp"); B=(lambda r:r['black'],"%Black")
TX=sample('TX'); CA=sample('CA')
print(f"TX clean-county ZIPs: {len(TX)}  counties: {sorted({r['county'] for r in TX})}")
print(f"CA clean-county ZIPs: {len(CA)}  counties: {sorted({r['county'] for r in CA})}")
reg(TX,"TEXAS metros — county FE, SE clustered on county",[H,B])
reg(CA,"CALIFORNIA metros — county FE, SE clustered on county",[H,B])
reg(TX+CA,"TX + CA metros pooled — county FE",[H,B])
print("\n=== same, WITHOUT county FE (between-metro, for contrast) ===")
def reg_nofe(S,label,terms):
    n=len(S); cols=[]; names=[]
    for f,nm in terms: cols.append(np.array([f(r) for r in S])); names.append(nm)
    cols.append(np.array([r['inc'] for r in S])/1000); names.append("inc")
    cols.append(np.array([r['pop'] for r in S])/1000); names.append("pop")
    y=np.array([r['price']-A[r['zip']] for r in S])
    X=np.column_stack([np.ones(n)]+cols)
    beta,*_=np.linalg.lstsq(X,y,rcond=None); res=y-X@beta; dof=n-X.shape[1]
    se=np.sqrt(np.diag(np.linalg.pinv(X.T@X))*(res@res/dof)); t=beta/se
    print(f"   {label:<28} spread: "+" ".join(f"{names[i]}={beta[i+1]:+.5f}(t{t[i+1]:+.2f})" for i in range(len(terms))))
reg_nofe(TX,"TX metros no FE",[H,B]); reg_nofe(CA,"CA metros no FE",[H,B])

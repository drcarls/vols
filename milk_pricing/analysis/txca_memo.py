import json, math, statistics, random
nat=json.load(open('data/national_walmart.json'))
def uni(st,geo): return [r for r in nat if r['state']==st and r['geo']==geo]
def match(U,key,hi,lo):
    B=[r for r in U if (r.get(key) or 0)>=hi]; W=[r for r in U if (r.get(key) or 0)<=lo]
    if len(B)<5 or len(W)<3: return None
    pairs=[]
    for h in B:
        best=None;bd=None
        for c in W:
            d=(abs(c['inc']-h['inc'])/10000.0)**2+(abs(math.log(c['pop'])-math.log(h['pop'])))**2
            if bd is None or d<bd: bd=d;best=c
        if best: pairs.append((h,best))
    if len(pairs)<5: return None
    d=[h['price']-c['price'] for h,c in pairs]
    m=statistics.mean(d); sd=statistics.stdev(d)
    return len(pairs),len(W),m,(m/(sd/math.sqrt(len(d))) if sd else 0.0)
def perm(U,key,hi,lo,t0,trials=3000,seed=83):
    rng=random.Random(seed)
    nB=sum(1 for r in U if (r.get(key) or 0)>=hi); nW=sum(1 for r in U if (r.get(key) or 0)<=lo)
    ge=n=0
    for _ in range(trials):
        sh=U[:]; rng.shuffle(sh)
        fB=sh[:nB]; fW=sh[nB:nB+nW]
        pairs=[]
        for h in fB:
            best=None;bd=None
            for c in fW:
                d=(abs(c['inc']-h['inc'])/10000.0)**2+(abs(math.log(c['pop'])-math.log(h['pop'])))**2
                if bd is None or d<bd: bd=d;best=c
            if best: pairs.append((h,best))
        if len(pairs)<5: continue
        e=[h['price']-c['price'] for h,c in pairs]
        if statistics.stdev(e)==0: continue
        n+=1
        if statistics.mean(e)/(statistics.stdev(e)/math.sqrt(len(e)))>=t0: ge+=1
    return ge/max(1,n)
print("Memo's matched-pair design (income + log-pop NN matching, one-sided permutation p), Walmart-only")
print(f"{'state':<6}{'geo':<7}{'contrast':<24}{'pairs':>6}{'ctrl':>6}{'gap $/gal':>11}{'t':>7}{'perm p':>9}")
for st in ('TX','CA'):
    for geo in ('rural','urban'):
        U=uni(st,geo)
        for key,hi,lo,lbl in (('black',30,10,'Black>=30% vs <=10%'),('hisp',50,20,'Hispanic>=50% vs <=20%')):
            r=match(U,key,hi,lo)
            if not r:
                nB=sum(1 for x in U if (x.get(key) or 0)>=hi)
                print(f"{st:<6}{geo:<7}{lbl:<24}{'— untestable (only %d ZIPs in high tail)'%nB}")
                continue
            n,w,m,t=r
            p=perm(U,key,hi,lo,t)
            print(f"{st:<6}{geo:<7}{lbl:<24}{n:>6}{w:>6}{m:>+11.3f}{t:>7.2f}{p:>9.4f}")

import rowify,glob,re,json,uextract as U
PCT=re.compile(r'^\(?\s*-?\d+(\.\d+)?\s*%\s*\)?$')
def pnum(t):
    t=t.strip().replace('（','(').replace('）',')').replace(' ','')
    neg=t.startswith('(')
    t=t.strip('()').replace('%','')
    try: v=float(t)
    except: return None
    return -v if neg else v
def fnum(t):
    t=t.replace('$','').replace(',','').replace(' ','')
    try: return float(t)
    except: return None
CASH=re.compile(r'(?i)^(cash and money funds?|short[- ]?term investments?|money markets?(?: funds?)?|cash)\s*[-–—]?\s*\(?(\d+(?:\.\d+)?)\s*%')
out={}
for f in sorted(glob.glob('ncsr/*')):
    y=int(f.split('/')[-1][:4])
    T=[U.fixnum(c.strip()) for row in rowify.rows(f) for c in row if c.strip()]
    bs=[x for x in U.blocks(T) if x[2]=='growth']
    lo,hi=(bs[0][0],bs[-1][1]+60) if bs else (0,len(T))
    fund=bench=None
    for k,t in enumerate(T):
        if not re.search(r'(?i)^average annual (total )?returns',t): continue
        seg=T[k:k+30]
        for j,x in enumerate(seg):
            if re.fullmatch(r'(?i)upright growth fund\s*\*?',x.strip()) and fund is None:
                v=[pnum(z) for z in seg[j+1:j+7] if PCT.match(z.replace('（','(').replace('）',')'))]
                if v: fund=v[0]
            if re.search(r'(?i)^s ?& ?p 500',x.strip()) and bench is None:
                v=[pnum(z) for z in seg[j+1:j+7] if PCT.match(z.replace('（','(').replace('）',')'))]
                if v: bench=v[0]
        if fund is not None: break
    cash=0.0
    for t in T[lo:hi]:
        m=CASH.match(t)
        if m: cash+=float(m.group(2))
    # shares outstanding + NAV within growth section
    sh=nav=None
    for k in range(lo,min(hi+120,len(T))):
        t=T[k]
        m=re.search(r'(?i)based on ([\d,]+(?:\.\d+)?) shares outstanding',t)
        if m and sh is None: sh=fnum(m.group(1))
        if re.search(r'(?i)^(net asset value|net asset value, redemption|offering and redemption price)',t) and nav is None:
            v=fnum(T[k+1]) if k+1<len(T) else None
            if v and 0.2<v<200: nav=v
        if re.fullmatch(r'(?i)shares outstanding',t.strip()) and sh is None:
            for z in T[k+1:k+4]:
                v=fnum(z)
                if v and v>1000: sh=v; break
    out[y]={'ret1':fund,'spx1':bench,'cash_pct':round(cash,2),'shares':sh,'nav':nav}
    print(y,out[y])
json.dump(out,open('up_perf.json','w'),indent=1)

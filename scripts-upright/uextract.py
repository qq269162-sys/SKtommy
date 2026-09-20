import re,glob,json,statistics,rowify

NUM=re.compile(r'^\(?\$?\s*-?[\d,]+(?:\.\d+)?\)?\*?$')
INT=re.compile(r'^\$?\s*[\d,]{1,12}\*?$')
DASH=re.compile(r'^[-_\s–—]+$')
HDRWORDS=r'(?:schedule of investments?|statement of investment in securities|portfolio of investments?|portfolio holdings)'
HDR=re.compile(r'(?i)^%s(?:\s*[-–,]?\s*(?:as of\s*)?(?:september 30,? ?(?:19|20)\d\d|\d\d/\d\d/(?:19|20)\d\d))?\s*\$?$'%HDRWORDS)
DATE=re.compile(r'(?i)(september 30,? ?(19|20)\d\d|as of ?\d\d/\d\d/(19|20)\d\d)')
STOP=re.compile(r'(?i)^(statements? of assets|statements? of operations|notes to financial|financial highlights|report of independent|availability of quarterly|item \d)')
CLASS=re.compile(r'(?i)^(common stocks?|preferred stocks?|equities|short[- ]?term investments?|corporate bonds?|money markets?( funds?)?|warrants?|rights|exchange[- ]traded funds?|mutual funds?|closed[- ]end|bonds?|convertible|options?|u\.?s\.? government|investment compan|real estate investment)\b')
SEC=re.compile(r'^(.{2,60}?)\s*[-–—−]\s*\(?-?(\d+(?:\.\d+)?)\s*%\)?\s*$')
SEC2=re.compile(r'^(.{2,60}?)\s+\(?-?(\d+(?:\.\d+)?)\s*%\)?\s*$')
BAD=re.compile(r'(?i)^(total|net assets|other assets|liabilities|see accompanying|the accompanying|cost |sub-?total|grand total|percentages? |industries are categor|adr - )')
FUND=re.compile(r'(?i)upright\s+(growth\s*(?:and|&)\s*income|growth|assets?\s+allocation\s*plus)\s*fund')

def fixnum(t):
    t=re.sub(r'(\d)\.\s+(\d)',r'\1.\2',t)
    t=re.sub(r'(\d),\s+(\d)',r'\1,\2',t)
    return t

def num(s):
    s=s.strip().replace('$','').replace(',','').replace('*','').strip()
    neg=s.startswith('(')
    try: v=float(s.strip('()'))
    except: return None
    return -v if neg else v

def label_of(m):
    g=re.sub(r'\s+',' ',m.group(1)).lower()
    if 'income' in g: return 'growth_income'
    if 'alloc' in g: return 'allocation'
    return 'growth'

def label_for(T,k):
    for j in range(k,max(0,k-40),-1):
        m=FUND.search(T[j])
        if m: return label_of(m)
    return 'growth'

def blocks(T):
    hs=[k for k,t in enumerate(T)
        if HDR.match(t) and '\u2026' not in t and '..' not in t
        and (DATE.search(t) or any(DATE.search(x) for x in T[k+1:k+6]))
        and any(re.search(r'(?i)shares|quantity|description|fair value|market value',x) for x in T[k+1:k+8])]
    out=[]
    for n,k in enumerate(hs):
        end=hs[n+1] if n+1<len(hs) else len(T)
        for j in range(k+3,end):
            if STOP.match(T[j]): end=j; break
        out.append((k,end,label_for(T,k)))
    return out

def grouped(T,i,b,layout):
    """return (holdings, consumed) for a k-grouped run starting at i."""
    for k in range(1,5):
        if i+3*k>b: break
        A=T[i:i+k]; B=T[i+k:i+2*k]; C=T[i+2*k:i+3*k]
        if layout=='A':
            names,ints=A,B
        else:
            names,ints=B,A
        if all(not NUM.match(x) and not DASH.match(x) and len(x)>2
               and not SEC.match(x) and not SEC2.match(x) and not BAD.match(x) for x in names) \
           and all(INT.match(x) for x in ints) and all(NUM.match(x) for x in C):
            return [[names[j],num(ints[j]),num(C[j])] for j in range(k)],3*k
    return None,0

def scan(T,a,b,layout):
    hold=[]; sector=''; klass=''; i=a+1; pct={}
    while i<b:
        t=T[i]
        if DASH.match(t): i+=1; continue
        m=(SEC.match(t) or SEC2.match(t)) if not NUM.match(t) else None
        if m:
            nm=m.group(1).strip(); p=float(m.group(2))
            if BAD.match(nm): i+=1; continue
            if CLASS.match(nm): klass=nm.upper(); pct[('K',klass)]=p
            else: sector=nm; pct[('S',sector)]=p
            i+=1; continue
        if BAD.match(t):
            if hold and re.match(r'(?i)^total (net assets|investments)',t): break
            i+=1; continue
        g,used=grouped(T,i,b,layout)
        if g and any(BAD.match(n) for n,_,_ in g): g=None
        if g:
            for n,sh,v in g: hold.append([n,sh,v,sector,klass])
            i+=used; continue
        i+=1
    return hold,pct

def parse(path):
    T=[fixnum(c.strip()) for row in rowify.rows(path) for c in row if c.strip()]
    bs=[x for x in blocks(T) if x[2]=='growth']
    if not bs: return None
    keep=[]
    for a,b,_ in bs:
        hA,_=scan(T,a,b,'A'); hB,_=scan(T,a,b,'B')
        sA=sum(x[2] for x in hA); sB=sum(x[2] for x in hB)
        if sA==sB: lay='A' if len(hA)>=len(hB) else 'B'
        else: lay='A' if sA>sB else 'B'
        h,p=scan(T,a,b,lay)
        if len(h)>=3: keep.append((a,b,lay,h,p))
    if not keep: return None
    hold=[]; pct={}
    for a,b,lay,h,p in keep: hold+=h; pct.update(p)
    span=(keep[0][0],keep[-1][1])
    ktot={}; stot={}
    for n,sh,v,sec,kl in hold:
        if kl: ktot[kl]=ktot.get(kl,0)+v
        if sec: stot[sec]=stot.get(sec,0)+v
    total=sum(x[2] for x in hold)
    kpct=sum(p for (kd,n),p in pct.items() if kd=='K')
    classed=sum(v for n,sh,v,sec,kl in hold if kl)
    net=None; how=''
    if kpct>80 and kpct<125 and total>0 and classed/total>0.97:
        net=total/(kpct/100); how='class-sum'
    if net is None:
        est=[stot[n]/(p/100) for (kd,n),p in pct.items() if kd=='S' and n in stot and p>0.2]
        if est: net=statistics.median(est); how='sector-median'
    est=[]
    rep=None
    lim=len(T)
    for j in range(span[1],len(T)):
        m=FUND.search(T[j])
        if m and label_of(m)!='growth': lim=j; break
    for j in range(span[0],lim):
        if re.match(r'(?i)^(total net assets|net assets)\s*[-–]?\s*(100(\.0+)?\s*%)?\s*\$?$',T[j].strip()):
            for x in T[j+1:j+4]:
                v=num(x)
                if v and v>10000: rep=v; break
            if rep: break
    if rep and net and 0.75<rep/net<1.33: net=rep; how+='+rep'
    elif rep and not net: net=rep; how='rep'
    return {'rows':hold,'net':net,'net_reported':rep,'how':how,
            'classpct':{n:p for (kd,n),p in pct.items() if kd=='K'},'nblocks':len(keep)}

if __name__=='__main__':
    res={}
    for f in sorted(glob.glob('ncsr/*')):
        y=f.split('/')[-1][:4]
        r=parse(f)
        if not r or not r['rows']: print(y,'NOT FOUND'); continue
        res[y]=r
        s=sum(x[2] for x in r['rows'])
        print('%s n=%3d blk=%d sum=%11.0f net=%11s rep=%11s cover=%s %-14s| %s'%(
            y,len(r['rows']),r['nblocks'],s,
            '%.0f'%r['net'] if r['net'] else '-', '%.0f'%r['net_reported'] if r['net_reported'] else '-',
            '%.3f'%(s/r['net']) if r['net'] else '-',
            r['how'],', '.join('%s %.1f%%'%(k[:18],v) for k,v in list(r['classpct'].items())[:4])))
    json.dump(res,open('up_ncsr.json','w'),indent=1)

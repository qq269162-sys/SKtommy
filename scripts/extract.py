import re,glob,json,rowify

NUM=re.compile(r'^\(?\$?\s*-?[\d,]+(?:\.\d+)?\)?$')
def num(s):
    s=s.strip().replace('$','').replace(',','').strip()
    neg=s.startswith('(')
    try: v=float(s.strip('()'))
    except: return None
    return -v if neg else v

EMHDR=re.compile(r'(Schedules? of investments|Statements? of net assets)',re.I)
FUND=re.compile(r'(Emerging Market\w*|Global Value|International Value Equity|International Small Cap|International Equity|Focus Global Growth)',re.I)
COUNTRY=re.compile(r'[—–−-]\s*\(?\d+\.\d+\s*%')
SKIP=re.compile(r'^(Total|Subtotal|Number|Shares|Principal|Value|Common Stock|Preferred Stock|Rights|Warrant|Participation Note|Short-Term|Repurchase|Money Market|Securit|Exchange-Traded|Limited Partnership|Convertible|Corporate|Table of Contents|Schedule|Statement|See accompanying|amount|Net Asset|Components|Summary of|The following|Δ$|†$|\*$|\(continue)',re.I)

def sections(rows):
    hdrs=[]
    for i,x in enumerate(rows):
        s=' '.join(x)
        if len(s)<220 and EMHDR.search(s):
            ctx=s+' || '+' | '.join(' '.join(y) for y in rows[i+1:i+3])
            m=FUND.search(ctx)
            if m: hdrs.append((i,m.group(1).lower()))
            continue
        if len(s)<140 and FUND.search(s) and i+1<len(rows) and re.search(r'Number of\s*shares|Number of Value',' '.join(rows[i+1]),re.I):
            hdrs.append((i,FUND.search(s).group(1).lower()))
    hdrs.sort()
    return hdrs

def em_span(rows):
    h=sections(rows)
    start=None;end=len(rows)
    for i,(idx,f) in enumerate(h):
        if 'emerging' in f:
            start=idx
            for jdx,g in h[i+1:]:
                if 'emerging' not in g: end=jdx;break
            break
    return start,end

def extract(path):
    rows=rowify.rows(path)
    st,en=em_span(rows)
    if st is None: return None
    hold=[];pending='';net=None;tvs=None;ctrys=[];curpct=None;curctry=''
    HARD=re.compile(r'(Statements? of assets and liabilities|Statements? of operations|Financial highlights|Report of independent registered)',re.I)
    for i in range(st+1,en):
        c=rows[i];s=' '.join(c)
        if HARD.search(s) and hold: break
        mc=re.match(r'^([A-Z][A-Za-z\./ &\'-]{2,40})\s*[\u2014\u2013\u2212-]\s*(\d+\.\d+)\s*%',s)
        if mc and not re.match(r'(Common|Preferred|Total|Short|Securit|Rights|Warrant|Participation|Exchange|Convertible|Money|Repurchase|Limited|Corporate)',mc.group(1)):
            curpct=(mc.group(1).strip(),float(mc.group(2)),len(hold));curctry=mc.group(1).strip()
        m=re.match(r'^Total [Vv]alue of [Ss]ecurities\s*[—–−-]\s*([\d.]+)%',s)
        if m:
            v=[num(x) for x in c if NUM.match(x)]
            v=[q for q in v if q and q>1e6]
            if v: tvs=(v[-1],float(m.group(1)))
        m2=re.match(r'^(Net [Aa]ssets [Aa]pplicable|Total net assets|TOTAL NET ASSETS)',s)
        if m2:
            v=[num(x) for x in c if NUM.match(x)]
            v=[q for q in v if q and q>1e6]
            if v and hold: net=v[-1];break
        c=[x for x in c if not re.fullmatch(r'[*\u2020#@\u00a9\u0394=~o\u00b0^\u00b6\u00a7\'\"\u2264\u2265+<>!]{1,4}',x.strip())]
        txt=[x for x in c if not NUM.match(x) and x.strip() not in ('$',')','(','%')]
        nums=[num(x) for x in c if NUM.match(x)]
        if len(txt)==1 and len(nums)>=2:
            name=(pending+' '+txt[0]).strip();pending=''
            if not SKIP.match(name) and not COUNTRY.search(name) and len(name)<80:
                hold.append([name,nums[0],nums[-1],curctry])
        elif len(txt)==0 and len(nums)>=2 and pending and not SKIP.match(pending):
            hold.append([pending,nums[0],nums[-1],curctry]);pending=''
        elif len(txt)==1 and not nums:
            t=txt[0]
            if COUNTRY.search(t) or SKIP.match(t) or len(t)>70 or '(continued)' in t: pending=''
            else: pending=(pending+' '+t).strip()
        elif len(txt)==0 and len(nums)==1 and curpct and nums[0]>0:
            ctrys.append((curpct[0],curpct[1],nums[0]));curpct=None;pending=''
        else: pending=''
    if ctrys:
        import statistics
        ests=[v/(p/100) for _,p,v in ctrys if p>0.05]
        if ests: tvs=tvs or None; net_c=statistics.median(ests)
        else: net_c=None
    else: net_c=None
    if net is None and net_c: net=net_c
    if net is None and tvs: net=tvs[0]/(tvs[1]/100)
    for h in hold:
        n=re.sub(r'[\s*†#@©Δ=~°¶§≤≥]+$','',h[0])
        n=re.sub(r'^[\s*†#@©Δ=~°¶§≤≥]+','',n)
        h[0]=re.sub(r'^.*\(continued\)\s*','',n).strip()
    return {'rows':hold,'net':net,'tvs':tvs,'net_ctry':net_c,'ctrys':ctrys}

if __name__=='__main__':
    res={}
    for f in sorted(glob.glob('ncsr/*.htm')):
        y=f.split('/')[-1][:4]
        r=extract(f)
        if not r or not r['rows']: print(y,'NOT FOUND');continue
        tot=sum(x[2] for x in r['rows'])
        res[y]=r
        print(y,'n=%3d'%len(r['rows']),'sum=%13.0f'%tot,'net=%13.0f'%(r['net'] or 0),'netC=%13.0f'%(r['net_ctry'] or 0),'ncty=%3d'%len(r['ctrys']),('cover=%.3f'%(tot/r['net'])) if r['net'] else '')
    json.dump(res,open('ncsr_em.json','w'),indent=1)

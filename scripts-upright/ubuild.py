import rowify,glob,re,json,uextract as U
from collections import defaultdict

def pn(t):
    t=t.strip().replace('（','(').replace('）',')')
    t=re.sub(r'\s*\*+$','',t); t=re.sub(r'\s*\d\.?$','',t)
    neg='(' in t
    t=t.strip('()%').replace('%','').replace('(','').replace(')','').strip()
    try: v=float(t)
    except: return None
    return -abs(v) if neg else v
def fn(t):
    t=t.replace('$','').replace(',','').replace(' ','')
    try: return float(t)
    except: return None

RET=defaultdict(list); NAV=defaultdict(list)
for f in sorted(glob.glob('ncsr/*')):
    y=int(f.split('/')[-1][:4])
    T=[U.fixnum(c.strip()) for row in rowify.rows(f) for c in row if c.strip()]
    marks=[k for k,t in enumerate(T) if re.search(r'(?i)^upright growth fund\s*(class a)?$',t.strip())
           and any(re.search(r'(?i)financial highlights',T[j]) for j in range(k,min(k+3,len(T))))]
    multi=any(re.search(r'(?i)upright (growth\s*(and|&)\s*income|assets? allocation plus) fund',t) for t in T)
    mk=(marks[-1] if marks else 0) if multi else 0
    win=len(T)
    for k in range(mk,min(mk+win,len(T))):
        if re.match(r'(?i)^total return',T[k].strip()):
            v=[]
            for x in T[k+1:k+9]:
                p=pn(x)
                if p is None: break
                v.append(p)
            for j,p in enumerate(v): RET[y-j].append(p)
            break
    for k in range(mk,min(mk+win,len(T))):
        if re.search(r'(?i)^net assets,? (at )?end of (period|year)',T[k]):
            v=[]
            for x in T[k+1:k+9]:
                p=fn(x)
                if p is None: break
                v.append(p)
            for j,p in enumerate(v): NAV[y-j].append(p*1000)
            break

nc=json.load(open('up_ncsr.json'))
perf=json.load(open('up_perf.json'))
def consensus(d,y):
    v=d.get(y)
    if not v: return None
    v=sorted(v); return v[len(v)//2]

years=list(range(1999,2026))
size={}
for y in years:
    rep=nc.get(str(y),{}).get('net')
    hl=consensus(NAV,y)
    size[y]= rep if rep else hl
    if rep and hl and abs(rep-hl)/rep>0.02: size[y]=rep
ret={y:consensus(RET,y) for y in years}

# ---- holdings ----
SUF=[r'\(\d\)',r'\bADRF?\b',r'\bAdrf?\b',r'\bADR\b',r'\bGDR\b',r'\bInc\.?\b',r'\bIncorporated\b',r'\bCorp\.?\b',r'\bCorporation\b',r'\bCompany\b',
     r'\bCo\.?\b',r'\bLtd\.?\b',r'\bLimited\b',r'\bplc\b',r'\bN\.?V\.?\b',r'\bS\.?A\.?\b',r'\bL\.?P\.?\b',
     r'\bClass [A-Z]\b',r'\bCl [A-Z]\b',r'\bThe\b',r'\bSAA\b',r'\*+',r'\bHoldings?\b$',r'\bTrust\b$',r'&']
ALIAS={
 'apple':'Apple','apple computer':'Apple','himax technologies':'Himax Technologies',
 'taiwan semiconductr':'TSMC','taiwan semiconductor manu':'TSMC','taiwan semiconductor':'TSMC',
 'teva pharm inds':'Teva Pharmaceutical','teva pharmaceutical inds':'Teva Pharmaceutical',
 'lannet':'Lannett','lannett':'Lannett','elan p l c':'Elan','elan':'Elan',
 'sandisk':'SanDisk','pacificare health systems':'PacifiCare Health','andrx group':'Andrx',
 'biovail':'Biovail','pfizer':'Pfizer','coach':'Coach','sunedison':'SunEdison',
 'genworth financial':'Genworth','odyssey healthcare':'Odyssey Healthcare','boeing':'Boeing',
 'scientific-atlanta':'Scientific-Atlanta','scientific atlanta':'Scientific-Atlanta',
 'alibaba group holding':'Alibaba','computer associates international':'Computer Associates',
 'taiwan semiconductor manufacturing':'TSMC','silicon motion technology':'Silicon Motion',
 'silcon motion technology':'Silicon Motion','teva pharmaceutical industries':'Teva Pharmaceutical',
 'plug power':'Plug Power','abbvie':'AbbVie','mylan':'Mylan','viatris':'Viatris',
 'bausch health cos':'Bausch Health','bausch health companies':'Bausch Health','valeant pharmaceuticals international':'Bausch Health',
 'amgen':'Amgen','bank of america':'Bank of America','dell':'Dell','microsoft':'Microsoft',
 'nvidia':'NVIDIA','ase technology holding':'ASE Technology','advanced semiconductor engineering':'ASE Technology',
 'alphabet':'Alphabet','google':'Alphabet','metlife':'MetLife','brighthouse financial':'Brighthouse Financial',
 'corning':'Corning','vishay intertechnology':'Vishay','au optronics':'AU Optronics',
 'manitowoc':'Manitowoc','general electric':'General Electric','starbucks':'Starbucks',
 'unitedhealth group':'UnitedHealth','aflac':'Aflac','a f l a c':'Aflac','whirlpool':'Whirlpool',
 'bed bath beyond':'Bed Bath & Beyond','bed bath and beyond':'Bed Bath & Beyond',
 'bhp billiton':'BHP','dow chemical':'Dow','dowdupont':'DowDuPont','dupont de nemours':'DuPont',
 'steelcase':'Steelcase','johnson controls international':'Johnson Controls','cvs health':'CVS Health',
 'mosaic':'Mosaic','adient':'Adient','canadian solar':'Canadian Solar','first solar':'First Solar',
 'genetech':'Genentech','genentech':'Genentech','biogen':'Biogen','millennium pharmaceutical':'Millennium Pharma',
 'intel':'Intel','micron technology':'Micron','applied materials':'Applied Materials','broadcom':'Broadcom',
 'cisco systems':'Cisco','juniper networks':'Juniper','oracle':'Oracle','emc mass':'EMC',
 'network appliance':'NetApp','motorola':'Motorola','nokia':'Nokia','general motors':'General Motors',
 'continental airlines':'Continental Airlines','lsi logic':'LSI Logic','genesis microchip':'Genesis Microchip',
 'united microelectronics':'UMC','himax technologies inc':'Himax Technologies',
}
ETF=re.compile(r'(?i)(direxion|proshares|proshs|invesco|ishares|spdr|etf|exchange[- ]traded|ultrashort|ultrashrt|bull 3x|bear)')
MMF=re.compile(r'(?i)(money market|money fund|repurchase agreement|government portfolio|institutional class|treasury|fidelity gov|cash management|short[- ]term investments?|federal home loan)')
def norm(n):
    s=n
    s=re.sub(r'\s*\*+','',s)
    for p in SUF: s=re.sub(p,' ',s)
    s=re.sub(r'[,\.]+',' ',s); s=re.sub(r'\s+',' ',s).strip(' -,')
    k=s.lower().strip()
    if k in ALIAS: return ALIAS[k]
    for a,v in ALIAS.items():
        if k==a or k.startswith(a+' '): return v
    return s

rows=[]
for y in sorted(nc):
    fy=int(y); d=nc[y]; net=d['net']
    for name,sh,v,sec,kl in d['rows']:
        kind='ETF' if ETF.search(name) else ('MMF' if MMF.search(name) or MMF.search(kl or '') else 'STOCK')
        rows.append({'fy':fy,'raw':name,'issuer':norm(name),'shares':sh,'value':v,
                     'pct':100*v/net,'sector':sec,'kind':kind})
json.dump({'size':size,'ret':ret,'rows':rows},open('up_all.json','w'))
print('years size:',{y:round((size[y] or 0)/1e6,2) for y in years})
print('returns   :',{y:ret[y] for y in years})
agg=defaultdict(float)
for r in rows:
    if r['kind']=='STOCK': agg[(r['fy'],r['issuer'])]+=r['pct']
for fy in sorted({r['fy'] for r in rows}):
    t=sorted([(k[1],v) for k,v in agg.items() if k[0]==fy],key=lambda x:-x[1])[:6]
    print(fy,'top:',' | '.join('%s %.1f'%(n,v) for n,v in t))

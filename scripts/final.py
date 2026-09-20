import json,csv,re
from collections import defaultdict
rows=json.load(open('all_rows.json'))
nc=json.load(open('ncsr_em.json'))
np_=json.load(open('nport_em.json'))
years=sorted({r['fy'] for r in rows})

net={}
for y in years:
    k=[d for d in np_ if int(d[:4])==y]
    net[y]=float(np_[k[0]]['netAssets']) if k else nc[str(y)]['net']

# issuer aggregation
agg=defaultdict(float); val=defaultdict(float)
for r in rows:
    agg[(r['fy'],r['issuer'])]+=r['pct']; val[(r['fy'],r['issuer'])]+=r['value']
top={y:sorted([(k[1],v,val[k]) for k,v in agg.items() if k[0]==y],key=lambda x:-x[1]) for y in years}

with open('top10_by_year.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','rank','issuer','pct_of_net_assets','market_value_usd','source'])
    for y in years:
        src='N-PORT' if y>=2019 else 'N-CSR'
        for i,(n,p,v) in enumerate(top[y][:10],1):
            w.writerow([f'{y}-11-30',i,n,round(p,2),round(v),src])

with open('holdings_all_years.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','issuer','security_as_filed','shares','market_value_usd','pct_of_net_assets','country','source'])
    for r in sorted(rows,key=lambda x:(x['fy'],-x['pct'])):
        w.writerow([f"{r['fy']}-11-30",r['issuer'],r['raw'],r['shares'],round(r['value']),round(r['pct'],4),r['country'],r['src']])

CTRY=defaultdict(float)
for r in rows: CTRY[(r['fy'],r['country'] or 'Unclassified')]+=r['pct']
with open('country_weights.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','country_as_filed','pct_of_net_assets'])
    for y in years:
        for (yy,c),p in sorted(CTRY.items(),key=lambda x:-x[1]):
            if yy==y: w.writerow([f'{y}-11-30',c,round(p,2)])

SEMI={'TSMC','SK Hynix','Samsung Electronics','MediaTek','Micron','SK Square','Hon Hai Precision','Samsung C&T'}
CORE={'TSMC','SK Hynix','SK Square','Samsung Electronics','MediaTek','Micron'}
with open('fund_summary.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','net_assets_usd','line_items','issuers','top1_pct','top5_pct','top10_pct','top10_hhi','korea_taiwan_pct','china_hk_pct','semis_memory_pct'])
    for y in years:
        t=top[y]; n10=sum(p for _,p,_ in t[:10])
        kt=sum(p for (yy,c),p in CTRY.items() if yy==y and re.fullmatch(r'Republic of Korea|South Korea|Korea|KR|Taiwan|TW',c))
        ch=sum(p for (yy,c),p in CTRY.items() if yy==y and re.fullmatch(r'China/Hong Kong|China|Hong Kong|CN|HK',c))
        semi=sum(p for n,p,_ in t if n in CORE)
        hhi=sum(p*p for _,p,_ in t[:10])
        w.writerow([f'{y}-11-30',round(net[y]),len([r for r in rows if r['fy']==y]),len(t),
                    round(t[0][1],2),round(sum(p for _,p,_ in t[:5]),2),round(n10,2),round(hhi,1),
                    round(kt,2),round(ch,2),round(semi,2)])
print(open('fund_summary.csv').read())

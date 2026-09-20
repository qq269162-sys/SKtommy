import json,csv
from collections import defaultdict
rows=json.load(open('all_rows.json'))
years=sorted({r['fy'] for r in rows})
M={'Republic of Korea':'KR','South Korea':'KR','KR':'KR','Korea':'KR',
   'Taiwan':'TW','TW':'TW',
   'China/Hong Kong':'CN','China':'CN','Hong Kong':'CN','CN':'CN','HK':'CN',
   'India':'IN','IN':'IN','Brazil':'BR','BR':'BR','Russia':'RU','RU':'RU','Russian Federation':'RU'}
def reg(c): return M.get(c,'OT')
net={}
sm=list(csv.DictReader(open('fund_summary.csv')))
for r in sm: net[int(r['fiscal_year_end'][:4])]=r
agg=defaultdict(float)
for r in rows: agg[(r['fy'],r['issuer'])]+=r['pct']
top={y:sorted([(k[1],round(v,2)) for k,v in agg.items() if k[0]==y],key=lambda x:-x[1])[:10] for y in years}
appear=defaultdict(int); mx=defaultdict(float)
for y in years:
    for n,p in top[y]: appear[n]+=1; mx[n]=max(mx[n],p)
sel=[n for n in appear if appear[n]>=3 or mx[n]>=5]
first={n:min(y for y in years if any(k==n for k,_ in top[y])) for n in sel}
sel.sort(key=lambda n:(first[n],-mx[n]))
heat=[{'name':n,'v':[round(agg.get((y,n),0),2) for y in years]} for n in sel]
ctry=defaultdict(float)
for r in rows: ctry[(r['fy'],reg(r['country']))]+=r['pct']
regions=['KR','TW','CN','IN','BR','RU','OT']
cser={g:[round(ctry.get((y,g),0),2) for y in years] for g in regions}
val=defaultdict(float)
for r in rows: val[(r['fy'],r['issuer'])]+=r['value']
out={'years':years,
 'net':[round(float(net[y]['net_assets_usd'])/1e9,2) for y in years],
 'top1':[float(net[y]['top1_pct']) for y in years],
 'top5':[float(net[y]['top5_pct']) for y in years],
 'top10':[float(net[y]['top10_pct']) for y in years],
 'semis':[float(net[y]['semis_memory_pct']) for y in years],
 'issuers':[int(net[y]['issuers']) for y in years],
 'heat':heat,'regions':regions,'cser':cser,
 'tables':{str(y):[[n,p,round(val[(y,n)]/1e6)] for n,p in top[y]] for y in years}}
json.dump(out,open('payload.json','w'),separators=(',',':'))
print(len(json.dumps(out)),'bytes'); print(cser['KR'][-4:],cser['CN'][-4:],cser['OT'][:3])

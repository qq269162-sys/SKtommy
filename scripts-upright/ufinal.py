import json,csv,re
from collections import defaultdict
D=json.load(open('up_all.json'))
size={int(k):v for k,v in D['size'].items()}
ret={int(k):v for k,v in D['ret'].items()}
rows=D['rows']
years=sorted(size)
hy=sorted({r['fy'] for r in rows})

agg=defaultdict(float); val=defaultdict(float); kind={}
for r in rows:
    if r['kind']!='STOCK': continue
    agg[(r['fy'],r['issuer'])]+=r['pct']; val[(r['fy'],r['issuer'])]+=r['value']
top={y:sorted([(k[1],v,val[k]) for k,v in agg.items() if k[0]==y],key=lambda x:-x[1]) for y in hy}
perf=json.load(open('up_perf.json'))
CASH={int(k):(v.get('cash_pct') or 0) for k,v in perf.items()}
mix=defaultdict(float)
for r in rows: mix[(r['fy'],r['kind'])]+=r['pct']

# growth of 10k + flows
g=10000.0; cum={}
for y in years:
    g*= (1+ret[y]/100.0); cum[y]=g
flow={}
for i,y in enumerate(years):
    if i==0: flow[y]=None; continue
    p=size[years[i-1]]
    flow[y]= size[y]-p*(1+ret[y]/100.0)

with open('up_fund_summary.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','net_assets_usd','total_return_pct','implied_net_flow_usd',
        'growth_of_10000','equity_pct','etf_pct','cash_mmkt_pct','stock_line_items','top1_pct','top5_pct','top10_pct'])
    for y in years:
        t=top.get(y,[])
        w.writerow([f'{y}-09-30',round(size[y]) if size[y] else '',ret[y],
                    round(flow[y]) if flow.get(y) is not None else '',round(cum[y]),
                    round(mix.get((y,'STOCK'),0),2) or '', round(mix.get((y,'ETF'),0),2) or '',
                    round(max(CASH.get(y,0),mix.get((y,'MMF'),0)),2) or '',
                    len([r for r in rows if r['fy']==y and r['kind']=='STOCK']) or '',
                    round(t[0][1],2) if t else '', round(sum(x[1] for x in t[:5]),2) if t else '',
                    round(sum(x[1] for x in t[:10]),2) if t else ''])

with open('up_top10_by_year.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','rank','issuer','pct_of_net_assets','market_value_usd'])
    for y in hy:
        for i,(n,p,v) in enumerate(top[y][:10],1):
            w.writerow([f'{y}-09-30',i,n,round(p,2),round(v)])

with open('up_holdings_all_years.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['fiscal_year_end','issuer','security_as_filed','type','sector_as_filed','shares','market_value_usd','pct_of_net_assets'])
    for r in sorted(rows,key=lambda x:(x['fy'],-x['pct'])):
        w.writerow([f"{r['fy']}-09-30",r['issuer'],r['raw'],r['kind'],r['sector'],r['shares'],round(r['value']),round(r['pct'],3)])

appear=defaultdict(int); mx=defaultdict(float)
for y in hy:
    for n,p,v in top[y][:10]: appear[n]+=1; mx[n]=max(mx[n],p)
sel=[n for n in appear if appear[n]>=4 or mx[n]>=8]
first={n:min(y for y in hy if any(k==n for k,_,_ in top[y][:10])) for n in sel}
sel.sort(key=lambda n:(first[n],-mx[n]))
payload={'years':years,'hy':hy,
 'size':[round((size[y] or 0)/1e6,2) for y in years],
 'ret':[ret[y] for y in years],
 'cum':[round(cum[y]) for y in years],
 'flow':[round(flow[y]/1e6,2) if flow.get(y) is not None else None for y in years],
 'stock':[round(mix.get((y,'STOCK'),0),1) for y in hy],
 'etf':[round(mix.get((y,'ETF'),0),1) for y in hy],
 'cash':[round(max(CASH.get(y,0),mix.get((y,'MMF'),0)),1) for y in hy],
 'top1':[round(top[y][0][1],1) if top[y] else 0 for y in hy],
 'top5':[round(sum(x[1] for x in top[y][:5]),1) for y in hy],
 'top10':[round(sum(x[1] for x in top[y][:10]),1) for y in hy],
 'nstock':[len([r for r in rows if r['fy']==y and r['kind']=='STOCK']) for y in hy],
 'heat':[{'name':n,'v':[round(agg.get((y,n),0),1) for y in hy]} for n in sel],
 'tables':{str(y):[[n,round(p,2),round(v/1000)] for n,p,v in top[y][:10]] for y in hy}}
json.dump(payload,open('up_payload.json','w'),separators=(',',':'))
print(open('up_fund_summary.csv').read())
print('heat rows',len(sel),[h['name'] for h in payload['heat']])
print('payload',len(json.dumps(payload)))

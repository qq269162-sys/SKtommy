import json,re,csv
EXCL=re.compile(r'(Federal Home Loan Bank|Federal Farm Credit|Federal National Mortgage|US Treasury|U.S. Treasury|Collateral|Repurchase Agreement|Money Market|Ultrashort|Discount Note|Treasury|Cash Management|Fixed Income Clearing|Mellon GSL|Government Portfolio|Liquid Assets|Investment Compan|Time Deposit|Lehman .*LEPO|CW 1[0-9] LEPO)',re.I)

SUF=[r'\bADR\b',r'\bGDR\b',r'\b144A\b',r'\bNVDR\b',r'\bClass [A-Z]\b',r'\bPreference\b',r'\bPreferred\b',
     r'\bSponsored\b',r'\bCo Ltd\b',r'\bLtd\b',r'\bInc\b',r'\bSA\b',r'\bCorp\b',r'\bPLC\b',r'\bPT\b',
     r'\bHolding Ltd\b',r'\(London International Exchange\)',r'\(Regulation S\)',r'\d+\.\d+%',r'\bNew\b$',
     r'\bRights?\b',r'\bWarrants?\b',r'\bPartly Paid\b',r'\bunsponsored\b']
ALIAS={
 'taiwan semiconductor manufacturing':'TSMC','tsmc':'TSMC','taiwan semiconductor':'TSMC',
 'samsung electronics':'Samsung Electronics','samsung electronics pref':'Samsung Electronics',
 'sk hynix':'SK Hynix','sk square':'SK Square','sk telecom':'SK Telecom','sk holdings':'SK Holdings',
 'reliance industries':'Reliance Industries','alibaba group holding':'Alibaba','alibaba group':'Alibaba',
 'tencent holdings':'Tencent','kweichow moutai':'Kweichow Moutai','wuliangye yibin':'Wuliangye Yibin',
 'mediatek':'MediaTek','micron technology':'Micron','jd.com':'JD.com','pdd holdings':'PDD Holdings',
 'baidu':'Baidu','baidu.com':'Baidu','samsung c&t':'Samsung C&T','china mobile':'China Mobile',
 'petroleo brasileiro':'Petrobras','petrobras':'Petrobras','gazprom':'Gazprom','lukoil':'LUKOIL',
 'cia vale do rio doce':'Vale','vale':'Vale','hon hai precision industry':'Hon Hai Precision',
 'b2w cia digital':'B2W / Americanas','b2w cia global do varejo':'B2W / Americanas','b2w digital':'B2W / Americanas',
 'avon products':'Avon Products','archer-daniels-midland':'Archer-Daniels-Midland','yahoo!':'Yahoo!','yahoo':'Yahoo!',
 'china unicom hong kong':'China Unicom','china unicom':'China Unicom','china telecom':'China Telecom',
 'centrais eletricas brasileiras':'Eletrobras','grupo televisa':'Grupo Televisa',
 'kb financial group':'KB Financial','uni-president china holdings':'Uni-President China',
 'cia de minas buenaventura':'Buenaventura','tambang batubara bukit asam':'Bukit Asam',
 'naspers':'Naspers','sohu.com':'Sohu.com','sina':'SINA','hyundai motor':'Hyundai Motor',
 'cnooc':'CNOOC','banco do brasil':'Banco do Brasil','itau unibanco holding':'Itau Unibanco',
 'fibria celulose':'Fibria Celulose','hypermarcas':'Hypermarcas','brasil foods':'BRF',
 'china petroleum & chemical':'Sinopec','sinopec':'Sinopec','petrochina':'PetroChina',
 'gerdau':'Gerdau','coal india':'Coal India','ternium':'Ternium','turkiye garanti bankasi':'Garanti Bank',
 'lg corp':'LG Corp','shinhan financial group':'Shinhan Financial','kcc':'KCC',
 'standard bank group':'Standard Bank','iqiyi':'iQIYI','netease':'NetEase','infosys':'Infosys',
 'cia brasileira de distribuicao grupo pao de acucar':'GPA (Pao de Acucar)',
 'cresud':'Cresud','ypf':'YPF','mercadolibre':'MercadoLibre','arcos dorados holdings':'Arcos Dorados',
 'irsa inversiones y representaciones':'IRSA','grupo clarin':'Grupo Clarin','pampa energia':'Pampa Energia',
 'aes tiete':'AES Tiete','indus towers':'Indus Towers','bharti airtel':'Bharti Airtel',
 'kunlun energy':'Kunlun Energy','industrial & commercial bank of china':'ICBC',
 'china construction bank':'CCB','bank of china':'Bank of China','china life insurance':'China Life',
 'huaneng power international':'Huaneng Power','first pacific':'First Pacific',
 'cia siderurgica nacional':'CSN','magnitogorsk iron & steel works':'MMK','mmc norilsk nickel':'Norilsk Nickel',
 'surgutneftegas':'Surgutneftegas','rosneft oil':'Rosneft','sberbank of russia':'Sberbank','sberbank':'Sberbank',
 'chunghwa telecom':'Chunghwa Telecom','taiwan mobile':'Taiwan Mobile','quanta computer':'Quanta',
 'largan precision':'Largan','catcher technology':'Catcher','delta electronics':'Delta Electronics',
}
def norm(n):
    s=n
    s=re.sub(r'\s*\(continued\)\s*','',s)
    for p in SUF: s=re.sub(p,' ',s,flags=re.I)
    s=re.sub(r'[,\.]+$','',s)
    s=re.sub(r'\s+',' ',s).strip(' -–—,')
    k=s.lower().strip()
    if k in ALIAS: return ALIAS[k]
    for a,v in ALIAS.items():
        if k.startswith(a+' ') or k==a: return v
    return s

rows=[]
nc=json.load(open('ncsr_em.json'))
CMAP={}
for y in sorted(nc):
    for name,sh,val,cty in nc[y]['rows']:
        if cty: CMAP[(int(y),norm(name))]=cty
for y in sorted(nc):
    if int(y)>2018: continue
    r=nc[y]; net=r['net']
    for name,sh,val,cty in r['rows']:
        if EXCL.search(name): continue
        rows.append({'fy':int(y),'src':'N-CSR','raw':name,'issuer':norm(name),'shares':sh,'value':val,'pct':100*val/net,'country':cty})
np=json.load(open('nport_em.json'))
for rd in sorted(np):
    y=int(rd[:4]); net=float(np[rd]['netAssets'])
    for h in np[rd]['holdings']:
        nm=h.get('title') or h.get('name')
        if EXCL.search(nm): continue
        iss=norm(nm)
        rows.append({'fy':y,'src':'N-PORT','raw':nm,'issuer':iss,'shares':float(h.get('balance') or 0),
                     'value':float(h['valUSD']),'pct':float(h['pctVal']),'country':CMAP.get((y,iss),h.get('invCountry',''))})
json.dump(rows,open('all_rows.json','w'))
# aggregate
from collections import defaultdict
agg=defaultdict(float); ctry={}
for r in rows:
    agg[(r['fy'],r['issuer'])]+=r['pct']
    if r['country']: ctry[r['issuer']]=r['country']
years=sorted({r['fy'] for r in rows})
top={}
for y in years:
    t=sorted([(k[1],v) for k,v in agg.items() if k[0]==y],key=lambda x:-x[1])
    top[y]=t[:15]
json.dump({str(k):v for k,v in top.items()},open('top15.json','w'),indent=1)
for y in years:
    print('==',y,'top10 sum=%.1f%%'%sum(v for _,v in top[y][:10]))
    print('   '+' | '.join('%s %.2f'%(n,v) for n,v in top[y][:10]))

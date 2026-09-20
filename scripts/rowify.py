import re,html
def rows(path):
    t=open(path,encoding='utf-8',errors='replace').read()
    t=re.sub(r'(?is)<(script|style).*?</\1>',' ',t)
    t=re.sub(r'(?i)</t[dh]>','\x01',t)
    t=re.sub(r'(?i)</tr>','\x02',t)
    t=re.sub(r'(?i)<br[^>]*>',' ',t)
    t=re.sub(r'(?i)</p>','\x02',t)
    t=re.sub(r'<[^>]+>',' ',t)
    t=html.unescape(t)
    t=t.replace('\xa0',' ')
    out=[]
    for line in t.split('\x02'):
        cells=[re.sub(r'\s+',' ',c).strip() for c in line.split('\x01')]
        cells=[c for c in cells if c!='']
        if cells: out.append(cells)
    return out

"""Turn measured floors into game metadata; no work state is written here.
decks.py's fixed Y samples omit narrow tips. Extend constant floors only where
the deck VXK independently proves top-floor cells exist; keep their true Z.
"""
from pathlib import Path
import hashlib, json, struct, zlib
ROOT=Path(__file__).resolve().parent/'deck_meta_20261014'

def main():
    lines=[]; report=[]
    for line in (ROOT/'measured.tsv').read_text(encoding='utf-8').splitlines():
        part,name,body=line.split('\t')
        m=json.loads(body); code=m['deck']; path=ROOT/(code+'.vxk')
        raw=path.read_bytes(); b=zlib.decompress(raw,-15); n=struct.unpack_from('<I',b,4)[0]
        off=8+n; nc=(len(b)-off)//4102
        co=struct.unpack_from('<%dH'%(nc*3),b,off); off+=nc*6
        floor=[list(map(int,s.split(':'))) for s in m['floor'].split(',')]
        z=floor[0][1]
        if any(p[1]!=z for p in floor): raise RuntimeError('Only audited flat decks can extend tips')
        xs=[]
        for i in range(nc):
            cx,cy,cz=co[3*i:3*i+3]
            if not cz*16<=z-1<(cz+1)*16:continue
            block=b[off+i*4096:off+(i+1)*4096]; k0=((z-1)&15)*256
            xs.extend(cx*16+(k&15) for k in range(k0,k0+256) if block[k])
        if not xs:raise RuntimeError('No supporting floor cells')
        original=m['floor']; m['floor']=f'{min(xs)}:{z},{max(xs)}:{z}'
        if code=='weather':m['name']='露天甲板'
        lines.append('\t'.join((part,name,json.dumps(m,ensure_ascii=False,separators=(',',':')))))
        report.append({'deck':code,'vxkSha256':hashlib.sha256(raw).hexdigest(),'measuredFloor':original,'appliedFloor':m['floor'],'basis':'actual cells at floor-1; narrow tips included for labeling, not asserted walkable'})
    (ROOT/'applied.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

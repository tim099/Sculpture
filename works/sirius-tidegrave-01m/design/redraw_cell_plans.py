"""Repair only drawing rasters from frozen design lists. No sculpture CLI mutations."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from build_structure import sheet,cli,BASE
from build_decks import draw_plan
def read(name):
    source=ROOT/(name+'.vox.txt')
    if not source.read_text(encoding='utf-8-sig').strip():
        if not name.startswith('deck_'):raise RuntimeError(name+' empty design input')
        # Idempotent stamp overwrote the old file with a zero-cell delta.
        # Export actual deck geometry rather than treating that delta as a full design.
        source=ROOT/(name+'_drawing_input.list')
        cli(op='export',work=BASE+'-deck-'+name[5:],format='list',links='none',out=source)
    a=np.zeros((800,241,200),np.uint8)
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        if not line or line.startswith('#'):continue
        x,y,z,c=map(int,line.split(','));a[x,y,z]=c
    if not a.any():raise RuntimeError(name+' has no occupied drawing cells')
    return a,source
def main():
    report=[]
    for name in ('skeleton','shell')+tuple('deck_'+s for s in ('lower','upper','weather','quarter','poop','forecastle')):
        a,source=read(name)
        if name in ('skeleton','shell'):sheet(a,name);projection=a.max(axis=1).T[::-1]
        else:draw_plan(a,name);projection=a.max(axis=2).T[::-1]
        pixels=np.array(Image.open(ROOT/(name+'_cell_plan.png')))
        expected=np.empty_like(pixels);expected[:]=(16,38,48)
        # Independent integer palette contract: floor(channel*255/max), no uint8 multiplication.
        for c in np.unique(projection):
            if c:
                c=int(c);expected[projection==c]=[((c>>5)&7)*255//7,((c>>2)&7)*255//7,(c&3)*255//3]
        different=int(np.count_nonzero(np.any(pixels!=expected,axis=2)))
        report.append({'name':name,'source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'sourceKind':'frozen stage design' if name in ('skeleton','shell') else 'current deck CLI export; old design list was a zero-cell delta',
          'pixelsDifferent':different,'pngSha256':hashlib.sha256((ROOT/(name+'_cell_plan.png')).read_bytes()).hexdigest()})
        if different:raise RuntimeError(name+' palette mismatch')
    (ROOT/'verify_cell_plan_palette.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()

"""Exact fit corrections, with expected old colors guarding each carve."""
import json
from build_structure import cli,get_actual,ROOT,BASE
from build_decks import ASSEMBLY
def carve(work,items,label):
    if not items:return
    f=ROOT/(label+'.vox.txt');f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(items.items())),encoding='utf-8')
    cli(op='carvevox',work=work,voxels=f,at='0,0,0',expect_pixels=len(items))
bow=get_actual(BASE+'-bowsprit')
f=ROOT/'fit_without_bowsprit.list.txt';cli(op='export',work=ASSEMBLY,format='list',hide_links='bowsprit',out=f)
other={tuple(map(int,l.split(',')[:3])) for l in f.read_text(encoding='utf-8-sig').splitlines() if l and not l.startswith('#')}
duplicate={q:c for q,c in bow.items() if q in other};carve(BASE+'-bowsprit',duplicate,'bowsprit_overlap_remove')
hull=get_actual(BASE);tiny={q:c for q,c in hull.items() if 598<=q[0]<=606 and q[1] in (108,132) and q[2]==133}
neighbours=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
if any(tuple(q[i]+d[i] for i in range(3)) in other and tuple(q[i]+d[i] for i in range(3)) not in tiny for q in tiny for d in neighbours):raise RuntimeError('reported fragments not detached')
carve(BASE,tiny,'chase_detached_remove')
(ROOT/'verify_structure_fit.json').write_text(json.dumps({'bowsprit_overlap_removed':len(duplicate),'detached_hull_cells_removed':len(tiny),'reason':'cylinder root touched existing deck; exact gun-port cut freed two 9-cell shell strips'},indent=2)+'\n',encoding='utf-8')
cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
print('fit corrected',len(duplicate),len(tiny))

import numpy as np,json
from build_structure import cli,get_actual,ROOT,BASE
from build_decks import stamp,ASSEMBLY
from build_rig import linevox
name=BASE+'-ornament';old=get_actual(name);a=np.zeros((800,241,240),np.uint8)
for q,c in old.items():a[q]=c
for y in (96,102,138,144):linevox(a,(101,y,165),(101,y,183),1.3,218)
for q,c in old.items():
    m=(q[0],240-q[1],q[2])
    if m not in old:a[m]=c
for q,c in old.items():a[q]=c
f=ROOT/'without_ornament.list.txt';cli(op='export',work=ASSEMBLY,format='list',hide_links='海蝕裝飾',out=f)
for l in f.read_text(encoding='utf-8-sig').splitlines():
    if l and not l.startswith('#'):
        x,y,z,c=map(int,l.split(','))
        if z<240:a[x,y,z]=0
stamp(name,a,'ornament_root_correction')
cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
print('finials rooted; ornament mirrored')

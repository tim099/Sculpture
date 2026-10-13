import math,json
from draft_general import P,CY,width,top
from build_structure import cli,ROOT
from build_decks import ASSEMBLY
from build_rig import anchor,rope
for M in P['masts']:
    for sg,side in [(-1,'P'),(1,'S')]:
        for j,dx in enumerate((-20,0,20)):
            x=M['x']+dx;z=top(x);y=CY+sg*math.floor(width(x,z)-1)
            anchor(ASSEMBLY,f'{M["id"]}-chain-{side}{j}',(x,y,z))
cli(op='work',sub='sail',work=ASSEMBLY,name='jib',free='clew')
rope('jib.sheet-S','sail:jib/clew','fore-chain-S1','running/sheets',.4,1,'#9f9673')
rope('mizzen-lateen.sheet-P','sail:mizzen-lateen/clew','mizzen-chain-P0','running/sheets',.4,1,'#9f9673')
f=ROOT/'rig_meta_correction.tsv';f.write_text('rope\tjib.sheet-S\t'+json.dumps({'kind':'sheet','sail':'jib'})+'\nrope\tmizzen-lateen.sheet-P\t'+json.dumps({'kind':'sheet','sail':'mizzen-lateen'})+'\n',encoding='utf-8')
cli(op='work',sub='meta',work=ASSEMBLY,file=f)
cli(op='work',sub='ropes',work=ASSEMBLY)
print('rig: chain anchors on bulwark tops; jib/lateen sheets added')

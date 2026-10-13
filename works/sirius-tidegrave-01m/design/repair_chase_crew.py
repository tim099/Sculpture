"""Support bow gun crews using the real game's existing stand/blocked rules."""
import json,math
import numpy as np
from build_structure import cli,get_actual,ROOT,BASE
from build_decks import ensure,stamp,ASSEMBLY
from build_guns import composed,conflicts
from build_rig import anchor
original=get_actual(BASE+'-chase-tube');sources={}
for tier,shift,pivz in [('low',4,4),('high',20,20)]:
    name=BASE+'-chase-tube-'+tier;ensure(name,'潮墓號｜'+tier+'艏砲與木托');cli(op='work',sub='update',work=name,meters_per_voxel=.05)
    a=np.zeros((800,241,200),np.uint8)
    for (x,y,z),c in original.items():a[x,y,z+shift]=c
    for x in range(10,15):
        for y in range(2,6):
            for z in range(shift+7):
                if a[x,y,z]==0:a[x,y,z]=109
    stamp(name,a,'chase_'+tier+'_pedestal')
    for k,q in {'muzzle':(12,60,12+shift),'breech':(12,3,12+shift),'cascabel':(12,2,12+shift),'train':(12,3,3),'eye-aft':(7,10,12+shift),'eye-fwd':(17,10,12+shift)}.items():anchor(name,k,q)
    sources[tier]=(name,a,pivz)
positions=[(585.5,103.5,119),(585.5,92.5,127),(585.5,114.5,127),
           (585.5,137.5,119),(585.5,126.5,127),(585.5,148.5,127)]
occ=composed();hull=get_actual(BASE);remove=set()
for i,at in enumerate(positions):
    tier='low' if i in (0,3) else 'high';name,a,pz=sources[tier]
    vox=np.array([[*q,int(a[tuple(q)])] for q in np.argwhere(a>0)])
    hit=conflicts(vox,(12.5,0,pz),at,.5,-90,occ);remove.update(q for q in hit if q in hull)
    invalid=hit-set(hull)
    if invalid:raise RuntimeError(f'gun {i} hits non-hull {len(invalid)}')
f=ROOT/'chase_crew_fit_cut.vox.txt';f.write_text(''.join(f'{x},{y},{z},{hull[(x,y,z)]}\n' for x,y,z in sorted(remove)),encoding='utf-8')
if remove:cli(op='carvevox',work=BASE,voxels=f,at='0,0,0',expect_pixels=len(remove))
occ=composed();cradle=BASE+'-chase-cradle';old=get_actual(cradle);a=np.zeros((800,241,200),np.uint8)
for q,c in old.items():a[q]=c
for x in range(582,603):
    for y in range(82,159):
        if (x,y,116) not in occ:a[x,y,116]=109
stamp(cradle,a,'chase_operator_platform')
for i,at in enumerate(positions):
    tier='low' if i in (0,3) else 'high';name,a,pz=sources[tier]
    cli(op='work',sub='model',work=BASE+'-deck-weather',name='chase-'+str(i+1),source_work=name,pivot=f'12.5,0,{pz}',at=','.join(map(str,at)),scale=.5,rotate='0,0,-90',meta='{"kind":"gun","gun":"18chase"}',overwrite=1)
(ROOT/'chase_crew_design.json').write_text(json.dumps({'positions':positions,'layout':'lower one / upper two, widened operator spacing; existing stand rules need crew space','platform':[582,602,82,158,116],'hull_cut':len(remove),'source_z_shift':{'low':4,'high':20},'all_model_bases_z':117},indent=2)+'\n',encoding='utf-8')
print('chase operator geometry adjusted',len(remove))

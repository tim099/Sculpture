import json
from pathlib import Path
import numpy as np
from scipy import ndimage
W=Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m');O=Path(__file__).parent
state=set(); snapshots={}
for p in sorted((W/'events').rglob('*.json')):
    e=json.loads(p.read_text())
    state.update(tuple(v[:3]) for v in e.get('placed_colored',[]))
    state.update(tuple(v) for v in e.get('placed_voxels',[]))
    state.difference_update(tuple(v) for v in e.get('carved_voxels',[]))
    if p.name.startswith('231407'):snapshots['stage2_ports']=state.copy()
snapshots['current_base']=state
r={}
for label,points in snapshots.items():
    solid=np.zeros((541,161,52),bool)
    for x,y,z in points:
        if 90<=x<=630 and 40<=y<=200 and z<52:solid[x-90,y-40,z]=True
    air=~solid;seed=np.zeros_like(air)
    seed[0,:,:]=air[0,:,:];seed[-1,:,:]=air[-1,:,:];seed[:,0,:]=air[:,0,:];seed[:,-1,:]=air[:,-1,:];seed[:,:,0]=air[:,:,0]
    # No top seed: test immersion volume with water surface at z=52.
    wet=ndimage.binary_propagation(seed,mask=air)
    q=(350-90,120-40,40)
    r[label]={'waterline_plane':52,'seed_boundaries':'x90/x630/y40/y200/z0; no top seed','interior_probe':[350,120,40],'probe_is_air':bool(air[q]),'exterior_water_reaches_interior':bool(wet[q]),'sealed_submerged_air_cells':int((air&~wet).sum())}
(O/'water_flood.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))

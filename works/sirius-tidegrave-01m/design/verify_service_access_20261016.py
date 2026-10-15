"""Verify exact author geometry delta, preserved rig, physical clearance and export."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,'D:/Unity/Valhalla/Blockside/VoxelKit')
from build_structure import cli,BASE
from voxel_export import unpack

OUT=ROOT/'service_access_20261016'
FINAL=ROOT/'delivery/tidegrave_import_20261016.vxk'

def run():
    ah,av=unpack((ROOT/'delivery/tidegrave_import_20261015.vxk').read_bytes())
    bh,bv=unpack(FINAL.read_bytes())
    a={tuple(map(int,v[:3])):int(v[3]) for v in av}
    b={tuple(map(int,v[:3])):int(v[3]) for v in bv}
    p=json.loads((OUT/'plan.json').read_text('utf8'))
    removed={q:a[q] for q in a.keys()-b.keys()}
    added={q:b[q] for q in b.keys()-a.keys()}
    assert removed=={tuple(v[:3]):v[3] for v in p['cuts']}
    assert added=={tuple(v[:3]):v[3] for v in p['additions']}
    assert all(a[q]==b[q] for q in a.keys()&b.keys())
    assert ah['rig']==bh['rig'],'Sail/rope/model geometry or fastening changed'
    assert min(q[2] for q in removed.keys()|added.keys())>52
    for x in range(574,582):
        for y in list(range(94,104))+list(range(137,147)):
            assert all((x,y,z) not in b for z in range(117,135))
    # Independent integer checksum, not the exporter implementation.
    v=bv.astype(np.uint64)
    mix=(v[:,0]*73856093)&0xffffffff
    for j,k in [(1,19349663),(2,83492791),(3,2654435761)]:mix^=(v[:,j]*k)&0xffffffff
    assert int(mix.sum()&np.uint64(0xffffffff))==bh['checksum']
    cli(op='export',work=BASE+'-assembly',format='list',out=OUT/'actual_body.list')
    actual=np.loadtxt(OUT/'actual_body.list',comments='#',delimiter=',',dtype=np.int32,encoding='utf-8-sig')
    order=lambda q:q[np.lexsort((q[:,2],q[:,1],q[:,0]))]
    assert np.array_equal(order(actual),order(bv))
    # Restore only our overwritten tracked intermediate scratch list.
    tracked='works/'+BASE+'/design/current.list.txt'
    (ROOT/'current.list.txt').write_bytes(subprocess.check_output(['git','show','HEAD:'+tracked],cwd=ROOT.parents[2]))
    report={'sha256':hashlib.sha256(FINAL.read_bytes()).hexdigest(),'bytes':FINAL.stat().st_size,
            'voxels':len(b),'checksum':f"{bh['checksum']:08x}",'removed':len(removed),'added':len(added),
            'all_original_rig_exact_same':True,'waterline_and_below_voxels_unchanged':True,
            'symmetric_service_portals_clear':True,'cli_list_voxel_color_differences':0,
            'counts':{k:len(bh['rig'][k]) for k in ('ropes','sails','models','meshes')}}
    (OUT/'geometry_report.json').write_text(json.dumps(report,indent=2),'utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()

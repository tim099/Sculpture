"""Cross-check VXK decoding against an independent CLI list and a tamper control."""
import sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,'D:/Unity/Valhalla/ArtGallery/VoxelKit')
from build_structure import cli,BASE
from voxel_export import unpack
VXK=ROOT.parent.parent/(BASE+'-assembly')/'exports/tidegrave_preview.vxk'
def ordered(a):return a[np.lexsort((a[:,2],a[:,1],a[:,0]))]
def checksum_scalar(a):
    value=0
    for x,y,z,c in a.tolist():
        value=(value+(((x*73856093)&0xffffffff)^((y*19349663)&0xffffffff)^((z*83492791)&0xffffffff)^((c*2654435761)&0xffffffff)))&0xffffffff
    return value
def main():
    source=VXK.read_bytes();header,decoded=unpack(source)
    path=ROOT/'delivery_source.list';cli(op='export',work=BASE+'-assembly',format='list',out=path)
    actual=np.loadtxt(path,delimiter=',',comments='#',dtype=np.int32,ndmin=2,encoding='utf-8-sig')
    a,b=ordered(actual),ordered(decoded)
    if a.shape!=b.shape or not np.array_equal(a,b):raise RuntimeError('VXK/list voxel or color mismatch')
    if np.any(np.all(a[1:,:3]==a[:-1,:3],axis=1)):raise RuntimeError('Duplicate voxel coordinates')
    chk=checksum_scalar(actual)
    if chk!=header['checksum']:raise RuntimeError('Independent checksum mismatch')
    bad=b.copy();bad[0,3]=1 if bad[0,3]!=1 else 2
    changed=int(np.count_nonzero(np.any(a!=bad,axis=1)))
    badchk=checksum_scalar(bad)
    if changed!=1 or badchk==chk:raise RuntimeError('Tamper control did not detect change')
    rig=header['rig'];counts={k:len(rig[k]) for k in ('ropes','sails','models','meshes')}
    counts['parts']=len(header['parts'])
    if counts!={'ropes':300,'sails':10,'models':116,'meshes':19,'parts':17}:raise RuntimeError('Rig/part preservation mismatch')
    decks=[p for p in header['parts'] if p.get('meta',{}).get('kind')=='deck']
    if len(decks)!=6:raise RuntimeError('Expected six game deck metadata records')
    delivery=ROOT/'delivery';delivery.mkdir(exist_ok=True)
    output=delivery/'tidegrave_candidate_20261014.vxk';output.write_bytes(source)
    report={'observedAtUtc':datetime.now(timezone.utc).isoformat(),'source':str(VXK),'delivery':str(output),
      'sha256':hashlib.sha256(source).hexdigest(),'bytes':len(source),'voxels':len(actual),'checksum':f'{chk:08x}',
      'voxelAndColorDifferences':0,'negativeControlChangedVoxels':changed,'negativeControlChecksum':f'{badchk:08x}',
      'counts':counts,'metadata':{'sailsWithMeta':sum(bool(s.get('meta')) for s in rig['sails']),
        'deckMetadata':len(decks),
        'ropesWithMeta':sum(bool(r.get('meta')) for r in rig['ropes']),
        'ropesWithEnds':sum(bool(r.get('ends')) for r in rig['ropes'])},
      'decoder':'VoxelKit voxel_export.unpack; checksum independently recomputed scalar modulo-2^32',
      'status':'candidate; navigation integration remains with game author'}
    (ROOT/'verify_vxk_delivery.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (delivery/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()

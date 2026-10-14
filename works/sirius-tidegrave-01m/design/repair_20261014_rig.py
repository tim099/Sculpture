"""Small guarded rig repair, all actual mutations through sculpture CLI."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from build_structure import cli,get_actual,BASE
ASSEMBLY=BASE+'-assembly'
AUDIT=Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/rig_audit_20261014/capsule_and_reroutes.json')
ROUTES=[('fore-course.sheet-S',(490,162,128),132),('main-course.sheet-S',(335,170,128),136),
        ('main-topgallant.brace-S',(335,170,128),136),('jib.sheet-S',(510,160,128),156),
        ('mizzen-lateen.sheet-P',(185,86,150),182)]
def write_list(path,cells):
    path.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(cells.items())),encoding='utf-8')
def main():
    before=get_actual(BASE);post={}
    for name,(x,y,z0),z1 in ROUTES:
        if (x,y,z0) not in before:raise RuntimeError('Fairlead has no existing root: '+name)
        for yy in {y,240-y}:
            if (x,yy,z0) not in before:raise RuntimeError('Mirror fairlead has no root')
            for z in range(z0+1,z1+1):post[(x,yy,z)]=109
    changed=[]
    missing={q:c for q,c in post.items() if q not in before}
    out=ROOT/'rig_fairlead_posts.vox.txt';write_list(out,missing)
    if missing:
        result=cli(op='stampvox',work=BASE,voxels=out,at='0,0,0',expect_pixels=len(missing))
        if int(result.get('placed',-1))!=len(missing):raise RuntimeError('Post count mismatch')
    ropes=json.loads((ROOT.parent.parent/ASSEMBLY/'ropes.json').read_text(encoding='utf-8'))['ropes']
    by={r['name']:r for r in ropes}
    for name,(x,y,z0),z1 in ROUTES:
        anchor='fairlead-'+name.replace('.','-')
        cli(op='work',sub='anchor',work=ASSEMBLY,name=anchor,at=f'{x},{y},{z1}',overwrite=1,
            note='Rooted mirrored timber fairlead; interior capsule collision repair 20261014')
        cli(op='work',sub='rope',work=ASSEMBLY,name=name,**{'from':by[name]['from'],'to':anchor},slack=1,overwrite=1)
    after=get_actual(BASE)
    if any(after.get(q)!=c for q,c in before.items()):raise RuntimeError('Unrelated hull cells changed')
    if any(after.get(q)!=c for q,c in post.items()):raise RuntimeError('Fairlead cell mismatch')
    (ROOT/'verify_rig_repair_20261014.json').write_text(json.dumps({'sourceAudit':str(AUDIT),
      'sourceAuditSha256':hashlib.sha256(AUDIT.read_bytes()).hexdigest(),'newHullCells':len(missing),
      'unchangedExistingHullCells':len(before),'cuts':changed,'routes':ROUTES,
      'limits':'Curve and sail re-export audit still required; steering holes mirrored to preserve deck symmetry'},indent=2)+'\n',encoding='utf-8')
    print('rig repair: added',len(missing),'cut',sum(x['cut'] for x in changed))
if __name__=='__main__':main()

"""Reroute steering around stairs, drill guarded fairlead holes, lift the stern flag."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from build_structure import cli,get_actual,BASE
ASSEMBLY=BASE+'-assembly'
AUDIT=Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/rig_audit_20261014')
def write_list(path,cells):
    path.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(cells.items())),encoding='utf-8')
def main():
    audit=json.loads((AUDIT/'capsule_and_reroutes.json').read_text(encoding='utf-8'))
    route=json.loads((AUDIT/'wheel_flag_candidates.json').read_text(encoding='utf-8'))['wheel_routes'][0]
    cuts={}
    hits=[h for r in audit['steering'] if r['name'] in ('steer-lead-P','steer-lead-S','steer-wheel-S') for h in r['cells'] if h['kind']=='interior_crossing']+route['collisions']
    for hit in hits:
        x,y,z=hit['cell']
        for work in hit['source_work']:
            if work not in (BASE+'-deck-quarter',BASE+'-deck-upper',BASE+'-deck-weather'):raise RuntimeError('Do not carve stairs: '+work)
            cuts.setdefault(work,set()).update({(x,y,z),(x,240-y,z)})
    decks={work:get_actual(work) for work in set(cuts)|{BASE+'-deck-quarter'}}
    ornament=get_actual(BASE+'-ornament')
    if (105,120,208) not in ornament:raise RuntimeError('Flag staff has no root')
    quarter=decks[BASE+'-deck-quarter']
    for y in (106,134):
        if (225,y,138) not in quarter:raise RuntimeError('Steering fairlead has no root')
    changes=[]
    for work,cells in sorted(cuts.items()):
        before=decks[work];selected={q:before[q] for q in cells if q in before}
        path=ROOT/(work+'_fairlead_holes.vox.txt');write_list(path,selected)
        if selected:
            result=cli(op='carvevox',work=work,voxels=path,at='0,0,0',expect_pixels=len(selected))
            if int(result.get('placed',-1))!=len(selected):raise RuntimeError('Cut count mismatch')
        changes.append({'work':work,'cutCells':len(selected),'coordinates':sorted(selected)})
    for work,before,planned,label in [
      (BASE+'-deck-quarter',quarter,{(225,y,z):109 for y in (106,134) for z in range(139,152)},'steering_fairlead_posts'),
      (BASE+'-ornament',ornament,{(105,120,z):109 for z in range(209,232)},'raised_flag_staff')]:
        missing={q:c for q,c in planned.items() if q not in before};path=ROOT/(label+'.vox.txt');write_list(path,missing)
        if missing:
            result=cli(op='stampvox',work=work,voxels=path,at='0,0,0',expect_pixels=len(missing))
            if int(result.get('placed',-1))!=len(missing):raise RuntimeError('Post count mismatch')
        changes.append({'work':work,'newCells':len(missing)})
    cli(op='work',sub='anchor',work=ASSEMBLY,name='steering-route-P',at='225,106,151',overwrite=1)
    ropes=json.loads((ROOT.parent.parent/ASSEMBLY/'ropes.json').read_text(encoding='utf-8'))['ropes']
    wheel=next(r for r in ropes if r['name']=='steer-wheel-P')
    cli(op='work',sub='rope',work=ASSEMBLY,name='steer-wheel-P',**{'from':wheel['from'],'to':'steering-route-P'},slack=1,overwrite=1)
    cli(op='work',sub='rope',work=ASSEMBLY,name='steer-wheel-P-lead',**{'from':'steering-route-P','to':'lead-P'},group='steering',thickness=.5,slack=1,overwrite=1)
    cli(op='work',sub='sail',work=ASSEMBLY,name='ensign',corners='105.5,120.5,231.5|75.5,120.5,231.5|75.5,120.5,215.5|105.5,120.5,215.5',overwrite=1,
      note='Lifted 26 cells on rooted timber staff to clear coral ornament; final simulated mesh must be audited')
    (ROOT/'verify_steering_flag_repair_20261014.json').write_text(json.dumps({'changes':changes,'waypoint':[225.5,106.5,151.5],
      'flagZShift':26,'limits':'Re-exported capsule/sail geometry, navigation, structure and model support require final verification'},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(changes))
if __name__=='__main__':main()

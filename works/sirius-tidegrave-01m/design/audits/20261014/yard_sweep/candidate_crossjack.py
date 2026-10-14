import json,argparse,ast,math,itertools
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;p=argparse.ArgumentParser();p.add_argument('--z',type=float,action='append');args=p.parse_args();levels=args.z or [227.5,226.5,224.5,223.5,220.5,209.5];I=json.loads((OUT/'input.json').read_text('utf8'));ys=I['yards'];h=I['header'];cj=next(y for y in ys if y['name'].endswith('crossjack'));gaff=next(m for m in h['rig']['models'] if m['name'].endswith('mizzen-gaff'));boom=next(m for m in h['rig']['models'] if m['name'].endswith('mizzen-boom'));oldz=cj['world_pivot'][2];cells=np.array(cj['cells']);srcp=np.array(cj['source_pivot']);rel=np.array(cj['relative_centers']);vox=np.load(OUT/'body.npy');body=np.zeros(vox[:,:3].max(0)+3,bool);body[tuple(vox[:,:3].T)]=1;OFF=np.array(list(itertools.product((-1,0,1),(-1,0,1),(0,))));tree=ast.parse((OUT/'sweep.py').read_text('utf8'));exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('query','rot')],type_ignores=[]),'own_obb','exec'))
report={'source_sha256':I['source_sha256'],'gaff_z':gaff['bbox'][2::3],'boom_z':boom['bbox'][2::3],'candidates':[],'scope':'No mutation. Complete continuous wooden Z separation proof against gaff/boom. Body OBB angle samples at quarter-degree only; static cloth and lower sheet corners not re-simulated. Actual CLI re-export needed after move.'}
for z in levels:
    low=float(cells[:,2].min()-srcp[2]+z);high=float(cells[:,2].max()+1-srcp[2]+z);pivot=np.array([*cj['world_pivot'][:2],z]);far=set();allhit=set()
    for a in np.linspace(-.7,.7,323):
        hits=np.unique(query(rot(rel,a)+pivot,a,body),axis=0);allhit.update(map(tuple,hits))
        far.update(tuple(q) for q in hits if np.linalg.norm((q+.5-pivot)[:2])>8)
    sheets=[]
    for r in h['rig']['ropes']:
        if not r['name'].startswith('mizzen-topsail.sheet'):continue
        pts=np.array(r['pts']).reshape(-1,3);end=pts[-1].copy();end[2]+=z-oldz;sheets.append({'name':r['name'],'old_wood_endpoint':pts[-1].tolist(),'new_wood_endpoint':end.tolist(),'original_cloth_endpoint':pts[0].tolist(),'old_direct_distance':float(np.linalg.norm(pts[-1]-pts[0])),'new_direct_distance_if_cloth_frozen':float(np.linalg.norm(end-pts[0]))})
    report['candidates'].append({'center_z':z,'delta_z':z-oldz,'wood_z':[low,high],'gap_above_boom':low-boom['bbox'][5],'gap_below_gaff':gaff['bbox'][2]-high,'zero_wood_interior_overlap_continuous_all_angles':low>=boom['bbox'][5] and high<=gaff['bbox'][2],'positive_wood_clearance':low>boom['bbox'][5] and high<gaff['bbox'][2],'body_far_from_pivot_collision_cells':sorted(far),'body_contact_unique_cells':len(allhit),'sheets':sheets})
(OUT/'crossjack_candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:int(x)),'utf8');print([(c['center_z'],c['wood_z'],c['gap_above_boom'],c['gap_below_gaff'],len(c['body_far_from_pivot_collision_cells'])) for c in report['candidates']])

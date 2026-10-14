import pathlib,sys,json,hashlib,shutil,os
OUT=pathlib.Path(__file__).parent
os.environ.pop('VERIFY_FROZEN',None);os.environ.pop('VERIFY_VXK',None)
sys.argv=[str(OUT/'check.py'),'final_heads.vxk']
exec((OUT/'check.py').read_text(encoding='utf8').split('sel=[r')[0])
out=[]
for y in yards:
    mast,name=y['name'].split('/')
    mp=ROOT/f'sirius-tidegrave-01m-mast-{mast}'/'models.json'; md=json.loads(mp.read_text(encoding='utf8'));m=next(q for q in md['models'] if q['name']==name)
    events=[{'path':str(ep),'sha256':hashlib.sha256(ep.read_bytes()).hexdigest()} for ep in sorted((ROOT/m['work']/'events').rglob('*.json'))]
    out.append({**{k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in y.items()},'source_work':m['work'],'source_events':events,'placement_models_file':str(mp),'placement_models_sha256':hashlib.sha256(mp.read_bytes()).hexdigest()})
(OUT/'frozen_yards.json').write_text(json.dumps({'snapshot_vxk_sha256':hashlib.sha256(blob).hexdigest(),'replay_fields':['placed_colored','carved_voxels'],'yards':out},ensure_ascii=False),encoding='utf8')
game=pathlib.Path('D:/Unity/Valhalla/Blockside/src/js');frozen=OUT/'frozen_game';frozen.mkdir(exist_ok=True);prov=[]
for name in ['10_ship.js','21_gunnery.js','30_rig_physics.js']:
    src=game/name;dst=frozen/name;shutil.copyfile(src,dst);prov.append({'source_path':str(src),'frozen_path':'frozen_game/'+name,'bytes':dst.stat().st_size,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
(OUT/'frozen_game/provenance.json').write_text(json.dumps({'files':prov,'actual_functions':{'meshOcc':'21_gunnery.js','yardNear':'10_ship.js','ropeYards':'10_ship.js','yardRopes':'30_rig_physics.js','braceYards':'30_rig_physics.js'},'constants':{'BRACE_MAX':.70,'BOOM_MIN':.14,'BOOM_MAX':1.40,'BRACE_RATE':.14,'BRACE_HYST':2.7}},ensure_ascii=False,indent=2),encoding='utf8')
snap=OUT/'snapshots';snap.mkdir(exist_ok=True);shutil.copyfile(SRC,snap/'final_heads.vxk')
print('froze',len(out),'yards,',len(prov),'game files and final_heads.vxk')

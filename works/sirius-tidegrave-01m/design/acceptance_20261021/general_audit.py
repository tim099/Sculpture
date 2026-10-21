"""Stage-zero audit. Runs only a copied drawing generator; never invokes builders."""
from pathlib import Path
import contextlib, hashlib, importlib.util, io, json, math, shutil
from PIL import Image, ImageDraw, ImageFont

BASE = Path('D:/Unity/Valhalla/Sculpture/works')
DESIGN = BASE/'sirius-tidegrave-01m/design'
OUT = Path(__file__).resolve().parent/'general'
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
plan = read(DESIGN/'plan.json')
models = read(BASE/'sirius-tidegrave-01m-assembly/models.json')['models']
anchors = {m['name']: m for m in models if m['name'] in ('anchor-P','anchor-S')}
changes = []
for side in ('P','S'):
    old = plan['equipment']['anchors'][side]['at']
    new = anchors['anchor-'+side]['at']
    changes.append({'field':'equipment.anchors.'+side+'.at','before':old,'after':new})
    plan['equipment']['anchors'][side]['at'] = new
plan['revision'] = 10
plan['equipment']['anchors']['note'] = 'Original placement x580.5; historical import moved aft20 cells to560.5; final48-portlid fit moved forward3 cells to563.5. Both current poses are recorded above; hawse stays at560.5. Supported by local bow timber; no claimed new anchor mechanics.'
plan['acceptance_20261021'] = {
    'base_plan_sha256':sha(DESIGN/'plan.json'),
    'scope':'Stage-zero arrangement; not full dynamic or clean ship reconstruction acceptance.',
    'changes':changes,
    'supplements':['../portlids_complete_20261019/README.md','../fittings_20261018/README.md'],
    'source_boundary':'Original hull and rig dimensions; final anchor positions from CLI-confirmed assembly models; detailed equipment and portlids in their separate drawings.'}

hashes = []
for n in (1,2):
    d = OUT/('gen'+str(n)); d.mkdir(exist_ok=True)
    shutil.copyfile(DESIGN/'draft_general.py',d/'draft_general.py')
    (d/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('general_'+str(n),d/'draft_general.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    with contextlib.redirect_stdout(io.StringIO()):mod.main()
    # Existing renderer has a historical Rev08 footer. Label this added edition explicitly.
    im=Image.open(d/'general_arrangement.png').convert('RGB');draw=ImageDraw.Draw(im)
    draw.rectangle((65,2238,1725,2375),fill='#102630')
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',21)
    for i,s in enumerate([
        'Rev10 / 2026-10-21：兩錨 X=563.5；0.1m/格，側視、俯視與五剖面。',
        '甲板22件陳設與48砲門蓋板另見各階段施工圖；本圖不冒充動態碰撞驗收。',
        '來源、設計決定與實物讀回分列；反向對照使用整份主桅事件資產平移3格。']):
        draw.text((70,2245+37*i),s,font=font,fill='#d9e2d0')
    im.save(d/'general_arrangement.png')
    hashes.append(sha(d/'general_arrangement.png'))
assert hashes[0]==hashes[1]
shutil.copyfile(OUT/'gen1/general_arrangement.png',OUT/'general_arrangement.png')
shutil.copyfile(OUT/'gen1/plan.json',OUT/'plan_rev10.json')

# Probe begins at a drawn mast-top pixel, then measures original event voxels.
im=Image.open(OUT/'general_arrangement.png').convert('RGB')
ink=(217,226,208);sx,sy,scale=90,1600,2.65
x0=sx+355*scale;y0=sy-510*scale
pixels=[(x,y) for y in range(round(y0)-3,round(y0)+4)
        for x in range(round(x0)-4,round(x0)+5) if im.getpixel((x,y))==ink]
pixel=min(pixels,key=lambda q:(q[0]-x0)**2+(q[1]-y0)**2)
probe=(355.5,120.5,math.floor((sy-pixel[1])/scale)+.5)
vox={};events=[]
for p in sorted((BASE/'sirius-tidegrave-01m-mast-main/events').rglob('*.json')):
    e=read(p);events.append({'file':p.name,'sha256':sha(p)})
    for c in e.get('placed_colored',[]):vox[tuple(c[:3])]=c[3]
    for c in e.get('placed_voxels',[]):vox[tuple(c[:3])]=e['color']
    for c in e.get('carved_voxels',[]):vox.pop(tuple(c[:3]),None)
assert len(vox)>0
nearest=lambda dz:min(math.dist(probe,(x+.5,y+.5,z+.5+dz)) for x,y,z in vox)
distance=[nearest(0),nearest(-3)]
assert distance==[0.,3.],distance
link=next(l for l in read(BASE/'sirius-tidegrave-01m-assembly/links.json')['links'] if l['name']=='main')
assert link['at']==[0,0,0] and link['turn']==0 and not link['mirror']

# Recompute design dimensions independently, without using generated verify_general.json.
h=plan['hull']
def radius(x,z):
    rake=max(0,1-z/h['rake_height']);lo=h['stern_x']+h['stern_rake']*rake;hi=h['bow_x']-h['bow_rake']*rake
    t=(x-lo)/(hi-lo)
    if not 0<=t<=1:return 0
    floor=h['floor_base']+h['floor_end_rise']*abs(2*t-1)**3
    if z<=floor:return 0
    for a,b in zip(h['stations'],h['stations'][1:]):
        if a[0]<=t<=b[0]:w=a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0]);break
    return w*math.sqrt((1-math.exp(-(z-floor)/h['bilge_height']))/(1-math.exp(-(h['tumblehome_start']-h['floor_base'])/h['bilge_height'])))*max(.48,1-h['tumblehome_per_z']*max(0,z-h['tumblehome_start']))
rake55=max(0,1-55/h['rake_height'])
mid55=(h['stern_x']+h['stern_rake']*rake55+h['bow_x']-h['bow_rake']*rake55)/2
beam=2*radius(mid55,55)*.1
assert abs(beam-13.4)<1e-9
report={'scope':'TASK-0541 only; drawing and dimension provenance, not whole ship acceptance',
    'base_plan_sha256':sha(DESIGN/'plan.json'),'generator_sha256':sha(DESIGN/'draft_general.py'),
    'revision':10,'generated_png_sha256':hashes,'byte_stable':True,'sections':5,
    'original_plan_changes':changes,'main_mast_events':events,'main_mast_voxels':len(vox),
    'probe_from_pixel':pixel,'quantized_probe':probe,'asset_z_shift':-3,'nearest_before_after':distance,
    'independent_design_beam_m':beam,'hull_span_m':(h['bow_x']-h['stern_x'])*.1,
    'limitations':['Mast-top pixel is quantized to the voxel centre; unquantized pixel rounding is not claimed exact.',
    'Renderer source copied only to check deterministic design regeneration; independent checks do not trust its verify JSON.',
    'Supplement plan does not change original plan.json or existing sculpture.',
    'Full clean-stage ship rebuild and all-wind cloth contact are outside TASK-0541.']}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

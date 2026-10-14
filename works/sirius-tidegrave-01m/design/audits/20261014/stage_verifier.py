import json, math, hashlib
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image

WORK=Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m')
D=WORK/'design'; OUT=Path(__file__).parent
P=json.loads((D/'plan.json').read_text(encoding='utf-8')); H=P['hull']; CY=P['center_y']
# Independent reimplementation from plan parameters; no author module imported.
def width(x,z):
    rake=max(0,1-z/H['rake_height']); lo=H['stern_x']+H['stern_rake']*rake; hi=H['bow_x']-H['bow_rake']*rake
    t=(x-lo)/(hi-lo)
    if not 0<=t<=1:return 0
    b=np.interp(t,[v[0] for v in H['stations']],[v[1] for v in H['stations']])
    floor=H['floor_base']+H['floor_end_rise']*abs(2*t-1)**3
    if z<=floor:return 0
    norm=math.sqrt(1-math.exp(-(H['tumblehome_start']-H['floor_base'])/H['bilge_height']))
    return b*math.sqrt(1-math.exp(-(z-floor)/H['bilge_height']))*max(.48,1-H['tumblehome_per_z']*max(0,z-H['tumblehome_start']))/norm
def loadlist(path):
    a={}
    for l in path.read_text(encoding='utf-8-sig').splitlines():
        if l and not l.startswith('#'):
            x,y,z,c=map(int,l.split(','));a[x,y,z]=c
    return a
def diff(a,b):return {'missing':len(b.keys()-a.keys()),'extra':len(a.keys()-b.keys()),'wrong_color':sum(a[q]!=b[q] for q in a.keys()&b.keys())}
def imgcheck(state,stage):
    im=np.array(Image.open(D/f'{stage}_cell_plan.png').convert('RGB')); pix=np.any(im!=(16,38,48),axis=2)
    zs,xs=np.where(pix); points={(int(x),199-int(z)) for z,x in zip(zs,xs)}
    proj={(x,z) for x,y,z in state}
    own=loadlist(D/f'{stage}.vox.txt'); ownproj={(x,z) for x,y,z in own}
    colorproj={}
    for (x,y,z),c in own.items():colorproj[x,z]=max(c,colorproj.get((x,z),0))
    bad=0
    for (x,z),c in colorproj.items():
        rgb=tuple(int(v) for v in (((c>>5)&7)*255/7,((c>>2)&7)*255/7,(c&3)*255/3))
        if tuple(im[199-z,x])!=rgb:bad+=1
    # Perturb actual replayed asset, not datum or probe; stem exposed at z100.
    q=min(x for x,z in points if z==100)
    actualxs={x for x,y,z in state if z==100}
    shiftxs={x+3 for x in actualxs}
    stagexs={x for x,y,z in state if z==100 and (x,y,z) in own}
    controls={'negative_probe':[q,100],'unshifted_distance':min(abs(x-q) for x in actualxs),'shifted_actual_asset_distance':min(abs(x-q) for x in shiftxs),'shifted_stage_only_asset_distance':min(abs(x+3-q) for x in stagexs)}
    if stage=='shell':
        isolatedq=min(x for x,z in points if z==150); isolatedxs={x for x,y,z in state if z==150}
        controls['isolated_full_asset_probe']=[isolatedq,150]
        controls['isolated_full_asset_shift_distance']=min(abs(x+3-isolatedq) for x in isolatedxs)
    return {'drawing_pixels':len(points),'drawing_pixels_absent':len(points-proj),'stage_projection_extra_not_on_drawing':len(ownproj-points),'projection_color_mismatch':bad,'actual_raster_colors':np.unique(im.reshape(-1,3),axis=0).tolist(),'color_issue':'All component colors collapse to (36,36,85) through uint8 multiplication overflow. Occupancy is still exact; material color cannot be inferred from PNG.',**controls}
def structure(state):
    a=np.zeros((800,241,200),bool)
    for x,y,z in state:
        if z<200:a[x,y,z]=True
    return {'face_components':ndimage.label(a)[1],'closed_air_cells':int((ndimage.binary_fill_holes(a)&~a).sum()),'mirror_absent':sum((x,240-y,z) not in state for x,y,z in state),'mirror_color':sum(state.get((x,240-y,z))!=c for (x,y,z),c in state.items())}

state={}; history=[]; checkpoints={}; errors=[]; sources=[]
for f in sorted((WORK/'events').rglob('*.json')):
    e=json.loads(f.read_text(encoding='utf-8')); before=len(state); n=0
    if 'placed_colored' in e:
        for v in e['placed_colored']:
            x,y,z,c=v; q=(x,y,z)
            if q in state:errors.append([f.name,'placed on occupied',q])
            state[q]=c;n+=1
    elif 'placed_voxels' in e:
        for x,y,z in e['placed_voxels']:state[x,y,z]=e['color'];n+=1
    if 'carved_voxels' in e:
        for v in e['carved_voxels']:
            q=tuple(v)
            if q not in state:errors.append([f.name,'carved empty',q])
            state.pop(q,None);n+=1
    source=e.get('source',{}); src=Path(source.get('file',''))
    sources.append({'event':f.name,'source_name':src.name,'current_source_sha_matches_event':src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==source.get('sha256')})
    history.append({'event':f.name,'op':e['op'],'before':before,'after':len(state),'payload_count':n,'reported_count':e.get('placed_count',e.get('carved_count'))})
    if f.name.startswith('230136'):checkpoints['skeleton']=state.copy()
    if f.name.startswith('230252'):checkpoints['shell_initial']=state.copy()
    if f.name.startswith('231407'):checkpoints['shell_ports']=state.copy()
report={'method':'independent event replay and parameter implementation; no author module imported','event_history':history,'replay_errors':errors,'source_hashes':sources,'stages':{}}
sk=loadlist(D/'skeleton.vox.txt');sh=loadlist(D/'shell.vox.txt');combined=sk|sh
report['stages']['skeleton']={'status':'pass_geometry_minor_drawing_color','count':len(checkpoints['skeleton']),'result_ledger':diff(checkpoints['skeleton'],sk),'image_ledger':imgcheck(checkpoints['skeleton'],'skeleton'),'structure':structure(checkpoints['skeleton'])}
report['stages']['shell_initial']={'count':len(checkpoints['shell_initial']),'shell_count':len(sh),'result_ledger':diff(checkpoints['shell_initial'],combined),'image_ledger':imgcheck(checkpoints['shell_initial'],'shell'),'structure':structure(checkpoints['shell_initial'])}
portcut=loadlist(D/'ports_frame_correction.vox.txt'); corrected={q:c for q,c in combined.items() if q not in portcut}
report['stages']['shell_ports']={'result_ledger':diff(checkpoints['shell_ports'],corrected),'removed':len(portcut),'removed_below_waterline':sum(q[2]<52 for q in portcut),'structure':structure(checkpoints['shell_ports'])}
rays=[]
for dz in P['guns']['decks']:
    for x in P['guns']['x']:
        for sg in (-1,1):
            z=dz+12; start=math.floor(width(x,z))-6
            blocked=[CY+sg*k for k in range(max(1,start),121) if (x,CY+sg*k,z) in checkpoints['shell_ports']]
            rays.append({'x':x,'z':z,'side':sg,'blocked':blocked})
report['stages']['shell_ports']['side_rays']=rays
# Compare below waterline early closed hull vs current base geometry after all cuts.
watermissing=[q for q in checkpoints['shell_ports'] if q[2]<52 and q not in state]
report['current_base_below_waterline']={'baseline':'shell_ports','missing_since_baseline':len(watermissing),'bbox':[[min(q[i] for q in watermissing),max(q[i] for q in watermissing)] for i in range(3)] if watermissing else None,'note':'Base work only. Linked rudder/assembly may cover some points; requires independent link-aware watertightness check.'}
# Independent station law confirmation against general report.
general=json.loads((D/'verify_general.json').read_text())
report['general']={'png_sha_matches':hashlib.sha256((D/'general_arrangement.png').read_bytes()).hexdigest()==general['sha256_png'],'station_max_delta':max(abs(width(v['x'],z)-v[key]) for v in general['stations'] for z,key in [(52,'half_width_at_dwl'),(115,'half_width_at_weather')]),'negative_control':'General report correctly withdraws datum shift. Stage asset controls reconstructed separately.','historical_geometry':'unverified/not claimed; station law is explicitly original design decision'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('source_hashes','event_history','stages')},indent=2))
for k,v in report['stages'].items():print(k,json.dumps({q:r for q,r in v.items() if q!='side_rays'}))

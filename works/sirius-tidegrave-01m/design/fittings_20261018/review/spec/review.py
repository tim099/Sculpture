import json, itertools, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path('D:/Unity/Valhalla')
OUT=ROOT/'scratchpad/sirius-tidegrave/fittings_review_spec'
D=ROOT/'Sculpture/works/sirius-tidegrave-01m/design/fittings_20261018'
p=json.loads((D/'placement.json').read_text('utf-8-sig'))
b=json.loads((D/'baseline_parts.json').read_text('utf-8-sig'))
body=np.load(D/'baseline_body.npz')['cells'][:,:3]
cells=set(map(tuple,body.tolist()))
findings=[]; results=[]
# Independent requirements: same deck floors/ladder positions from baseline export,
# without author reserved array or diagnostics.
ladders=[v for x in b['links'] if x.get('meta',{}).get('kind')=='ladders' for v in x.get('points',{}).values()]
def overlap(a,c): return all(a[i]<c[i+3] and a[i+3]>c[i] for i in range(3))
for n,x in enumerate(p['placements'],1):
    src=ROOT/'Sculpture/works'/x['source']
    w=json.loads((src/'work.json').read_text('utf-8-sig'))
    vals=np.loadtxt(ROOT/('scratchpad/sirius-tidegrave/source_'+x['source']+'.txt'),delimiter=',',comments='#',dtype=int)[:,:3]
    s=x['scale']; pivot=np.array(x['pivot']); at=np.array(x['at'])
    assert x['rotate'][:2]==[0,0]
    angle=np.deg2rad(x['rotate'][2]);c=np.cos(angle);ss=np.sin(angle)
    rot=np.array([[c,-ss,0],[ss,c,0],[0,0,1]])
    corners=np.stack([((vals+v-pivot)*s)@rot.T+at for v in itertools.product((0,1),repeat=3)])
    lo=corners.min(axis=0); hi=corners.max(axis=0)
    actual_box=np.r_[lo.min(axis=0),hi.max(axis=0)]
    meta=x['meta']; issues=[]
    if meta.get('deco') and meta.get('kind'): issues.append('FAIL functional kind marked deco')
    if not np.allclose(actual_box,x['box']): issues.append('FAIL occupied bounds differ')
    # Source point convention in exports is voxel centre.
    anchors={}
    if (src/'anchors.json').exists():
        aa=json.loads((src/'anchors.json').read_text('utf-8-sig'))
        anchors={v['name']:(((np.array(v['at'])+.5-pivot)*s)@rot.T+at).tolist() for v in aa['anchors']}
    if meta.get('kind')=='light' and not {'base','bail','wick'}<=anchors.keys(): issues.append('FAIL missing light anchors')
    for point in ladders:
        reserve=[point[0]-7,point[1]-6,point[2]-1,point[0]+7,point[1]+6,point[2]+22]
        if overlap(actual_box,reserve): issues.append('FAIL ladder clearance')
    # independent centre lane: 1.9m wide, exclude pre-existing central masts.
    if actual_box[0]>180 and actual_box[3]<610 and actual_box[1]<130 and actual_box[4]>111:
        issues.append('FAIL centre passage overlap')
    # Use transformed occupied cube centres and all eight inset corners for body intersections.
    samples=[(lo+hi)/2]+[lo+(hi-lo)*np.array(v) for v in itertools.product((.001,.999),repeat=3)]
    collisions=sum(sum(tuple(q) in cells for q in np.floor(t).astype(int)) for t in samples)
    if collisions: issues.append('FAIL body sampled intersection')
    if meta.get('kind')=='boat':
        length=(actual_box[3]-actual_box[0])*.1
        if abs(length-meta['length_m'])>.1: issues.append('FAIL physical boat length mismatch')
    results.append(dict(index=n,name=x['name'],source=x['source'],source_mpv=w.get('meters_per_voxel'),scale=s,physical_box_m=((actual_box[3:]-actual_box[:3])*.1).tolist(),anchors=anchors,issues=issues,sampled_body_intersections=collisions))
# Pixel-origin check: exact deck figure depicts the starboard boat and paired lights;
# manually read original image at native resolution. Fit used only to corroborate footprint.
im=Image.open(D/'deck_plan.png').convert('RGB')
colors=im.getcolors(im.width*im.height)
results_image={'size':im.size,'nonbackground_colors':sorted(colors,reverse=True)[:12]}
palette={'whaleboat':(144,169,180),'galley':(198,107,73),'shotrack':(197,161,110),'bitts':(147,113,78),'barrel':(189,151,99),'crate':(156,135,95),'lantern':(255,225,148)}
pixel_checks=[]
for x in p['placements']:
    q=x['box']; x1,y1,x2,y2=q[0]*2.4-164,q[1]*2.4+30,q[3]*2.4-164,q[4]*2.4+30
    target=palette[x['source'].split('-')[-1]]
    hits=[]
    for a,bb in [((x1+x2)/2,y1),((x1+x2)/2,y2),(x1,(y1+y2)/2),(x2,(y1+y2)/2)]:
        hits.append(any(im.getpixel((round(a)+dx,round(bb)+dy))==target for dx in range(-2,3) for dy in range(-2,3)))
    pixel_checks.append({'name':x['name'],'four_edges':hits})
results_image['pixel_footprint_checks']=pixel_checks
data={'requirements':'Shipbuilding 2.1/9.9; independent baseline ladders and centre lane; no author generator imported','counts':{'models':len(results),'deco':sum(x['meta'].get('deco',0)==1 for x in p['placements']),'functional':sum('kind' in x['meta'] for x in p['placements'])},'results':results,'image':results_image}
(OUT/'review_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))

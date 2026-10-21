"""Independent TASK-0545 audit. Imports only standard/scientific libraries; no author code."""
from pathlib import Path
import json, hashlib, math
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_fill_holes,generate_binary_structure
R=Path('D:/Unity/Valhalla/Sculpture/works'); B='sirius-tidegrave-01m'; D=R/B/'design'; O=Path(__file__).parent
inputs={}
def read(p):
 b=p.read_bytes();inputs[str(p)] = hashlib.sha256(b).hexdigest();return json.loads(b)
P=read(D/'plan.json');H=P['hull'];C=P['center_y']
def events(name):return [(f,read(f)) for f in sorted((R/name/'events').rglob('*.json'))]
def replay(es):
 a={}
 for f,e in es:
  for q in e.get('carved_voxels',[]):a.pop(tuple(q[:3]),None)
  for q in e.get('placed_colored',[]):a[tuple(q[:3])]=q[3]
  for q in e.get('placed_voxels',[]):a[tuple(q[:3])]=e['color']
 return a
def diff(a,b):return {'missing':len(a.keys()-b.keys()),'extra':len(b.keys()-a.keys()),'color':sum(a[q]!=b[q] for q in a.keys()&b.keys())}
def width(x,z):
 r=max(0,1-z/H['rake_height']);l=H['stern_x']+H['stern_rake']*r;h=H['bow_x']-H['bow_rake']*r;t=(x-l)/(h-l)
 if not 0<=t<=1:return 0
 stations=H['stations']; b=float(np.interp(t,[v[0] for v in stations],[v[1] for v in stations]));floor=H['floor_base']+H['floor_end_rise']*abs(2*t-1)**3
 if z<=floor:return 0
 return b*math.sqrt(1-math.exp(-(z-floor)/H['bilge_height']))*max(.48,1-H['tumblehome_per_z']*max(0,z-H['tumblehome_start']))/math.sqrt(1-math.exp(-(H['tumblehome_start']-H['floor_base'])/H['bilge_height']))
base_events=events(B);base=replay([(f,e) for f,e in base_events if str(f.parent.name)=='2026-10-13' and f.name<'230625'])
occupied=base.copy(); deckreports=[]; full_current=replay(base_events); historical=base.copy(); children={}
for spec in P['decks']:
 name=B+'-deck-'+spec['id'];es=events(name);actual_initial=replay(es[:1]);cur=replay(es);z=spec['z'];a={}
 for x in range(spec['x'][0],spec['x'][1]+1):
  for zz in [z-1,z]:
   w=width(x,zz)
   for y in range(241):
    q=(x,y,zz)
    hatch=spec['id'] in ['lower','upper','weather'] and any(h-18<=x<h+20 and 111<=y<=129 for h in [290,425])
    mast=any(m['x']-5<=x<=m['x']+5 and 115<=y<=125 for m in P['masts'])
    special=111<=y<=129 and ((spec['id']=='quarter' and 219<=x<240) or (spec['id']=='poop' and 159<=x<180) or (spec['id']=='forecastle' and 550<=x<574))
    if w>0 and abs(y-C)<=w and q not in occupied and not(hatch or mast or special):a[q]=136
 initialdiff=diff(a,actual_initial);occupied.update(actual_initial);historical.update(actual_initial);full_current.update(cur);children[name]=cur
 # Start at every PNG pixel; independently project replayed initial grid.
 im=np.array(Image.open(D/('deck_'+spec['id']+'_cell_plan.png')).convert('RGB'));inputs[str(D/('deck_'+spec['id']+'_cell_plan.png'))]=hashlib.sha256((D/('deck_'+spec['id']+'_cell_plan.png')).read_bytes()).hexdigest()
 projected={(x,y) for x,y,z in actual_initial};bg=(16,38,48); expected_rgb=(145,72,0) # RGB332(136) with integer channel flooring
 rgb=tuple([((136>>5)&7)*255//7,((136>>2)&7)*255//7,(136&3)*255//3])
 pixset={(x,240-row) for row in range(241) for x in range(800) if tuple(im[row,x])==rgb}
 other=sum(tuple(im[row,x]) not in [bg,rgb] for row in range(241) for x in range(800))
 deckreports.append({'deck':spec['id'],'design_count':len(a),'initial_count':len(actual_initial),'current_count':len(cur),'initial_result':initialdiff,'later_removed':len(actual_initial.keys()-cur.keys()),'later_added':len(cur.keys()-actual_initial.keys()),'later_color':sum(cur[q]!=actual_initial[q] for q in cur.keys()&actual_initial.keys()),'png_rgb':rgb,'png_missing':len(pixset-projected),'png_extra':len(projected-pixset),'png_other_colors':other})
le=events(B+'-ladders');lad=replay(le);children[B+'-ladders']=lad;full_current.update(lad);historical.update(lad)
specs=[('lower-upper-a',65,90,272,1),('lower-upper-b',65,90,407,1),('upper-weather-a',90,115,272,1),('upper-weather-b',90,115,407,1),('weather-quarter',115,138,219,1),('quarter-poop',138,164,159,1),('weather-forecastle',115,138,573,-1)]
expected={}
def put(x,y,z):
 if (x,y,z) not in occupied:expected[(x,y,z)]=109
for name,low,high,land,s in specs:
 for i in range(8):
  x=land+s*(32-4*i);z=low+round((high-low)*(i+1)/8)
  for xx in range(min(x,x+s*3),max(x,x+s*3)+1):
   for y in range(111,130):
    for zz in [z-1,z]:put(xx,y,zz)
   for y in [110,130]:
    for zz in range(low+1,z+2):put(xx,y,zz)
 for xx in range(min(land,land+s*4),max(land,land+s*4)+1):
  for y in range(113,128):
   for z in [high-1,high]:put(xx,y,z)
 for xx in range(min(land+s*35,land+s*38),max(land+s*35,land+s*38)+1):
  for y in range(111,130):
   for z in [low-1,low]:put(xx,y,z)
def structure(a):
 v=np.array(list(a),dtype=int);lo=v.min(0)-1;hi=v.max(0)+1;m=np.zeros(tuple(hi-lo+1),bool);m[tuple((v-lo).T)]=True
 _,n=label(m,structure=generate_binary_structure(3,1));holes=int(np.sum(binary_fill_holes(m)&~m));return {'voxels':len(a),'components6':int(n),'enclosed_empty':holes}
report={'scope':'Historical original deck and final revised ladder result ledger independently recomputed; current child sources replayed. No game/navigation/actor collision claim.','inputs_sha256':inputs,'decks':deckreports,'ladders':{'expected':len(expected),'actual':len(lad),'result':diff(expected,lad),'events':[str(f) for f,e in le]},'historical_decks_ladders_hull_structure':structure(historical),'current_decks_ladders_hull_structure':structure(full_current),'assets_modified':False}
# A real negative: remove an occupied design cell and recolor another in memory.
q=next(iter(expected));r=next(v for v in expected if v!=q);bad=lad.copy();bad.pop(q,None);bad[r]=108
report['negative_result_ledger']={'removed':q,'recolored':r,'readback':diff(expected,bad)}
probe=(100,125);deck=children[B+'-deck-poop'];proj={(x,y) for x,y,z in deck};initial=read(D/'verify_decks.json')
# Find a PNG-edge point whose +3 shifted projection has exactly distance3.
poop_image=np.array(Image.open(D/'deck_poop_cell_plan.png').convert('RGB'))
png_probes={(x,240-row) for row in range(241) for x in range(800) if tuple(poop_image[row,x])==(145,72,0)}
for x,y in sorted(png_probes):
 dist=min((x-(xx+3))**2+(y-yy)**2 for xx,yy in proj)
 if dist==9:probe=(x,y);break
report['negative_shift3']={'source':'Probe selected from deck_poop_cell_plan.png RGB136 pixels, compared to independent current events projection','probe':probe,'png_rgb':poop_image[240-probe[1],probe[0]].tolist(),'unshifted_distance':math.sqrt(min((probe[0]-x)**2+(probe[1]-y)**2 for x,y in proj)),'whole_projection_shift_x':3,'shifted_distance':math.sqrt(min((probe[0]-(x+3))**2+(probe[1]-y)**2 for x,y in proj))}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='inputs_sha256'},indent=2))

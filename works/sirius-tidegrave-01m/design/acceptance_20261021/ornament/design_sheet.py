"""New independent design-union sheet; historic PNG untouched."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent
D=Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design')
W=Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m-ornament')
files=['ornament.vox.txt','ornament_root_correction.vox.txt','raised_flag_staff.vox.txt']
design={};sources=[]
for name in files:
 p=D/name;before=len(design);v=[]
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip() and not l.startswith('#'):
   row=list(map(int,l.split(',')));design[tuple(row[:3])]=row[3];v.append(row)
 sources.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':len(v),'new_cells':len(design)-before})
rgb=np.zeros((240,241,3),np.uint8);rgb[:]=(16,38,48)
proj={}
for (x,y,z),c in design.items():proj[y,z]=max(c,proj.get((y,z),0))
for (y,z),c in proj.items():rgb[239-z,y]=[(c//32)*255//7,((c//4)%8)*255//7,(c%4)*255//3]
dest=O/'ornament_design_union_stern_cell_plan.png';Image.fromarray(rgb).save(dest)
# Separate readback measurement from output PNG against replay of actual events.
actual={}
for p in sorted((W/'events').rglob('*.json')):
 e=json.loads(p.read_text())
 for r in e.get('placed_colored',[]):actual[tuple(r[:3])]=r[3]
actualproj={}
for (x,y,z),c in actual.items():actualproj[y,z]=max(c,actualproj.get((y,z),0))
img=Image.open(dest).convert('RGB');missing=[];colors=[];seen=set()
for v in range(img.height):
 for y in range(img.width):
  pix=img.getpixel((y,v))
  if pix==(16,38,48):continue
  yz=(y,239-v);seen.add(yz)
  if yz not in actualproj:missing.append(yz);continue
  c=actualproj[yz];expected=(((c>>5)&7)*255//7,((c>>2)&7)*255//7,(c&3)*255//3)
  if pix!=expected:colors.append(yz)
report={'title':'New current design union sheet, not historic original','source_order':sources,'design_cells':len(design),'png':str(dest),'png_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'pixel_to_cell':'column=y, row=239-z; max RGB332 palette index across X; y mirror center=120; 0.1m/cell','drawing_pixels':len(seen),'drawing_pixels_absent_actual':len(missing),'actual_projection_extra_pixels':len(actualproj.keys()-seen),'color_different_pixels':len(colors),'limits':'Projection collapses X. Geometry and provenance are three frozen author masks; this sheet does not independently reconstruct all design geometry from descriptive parameters.'}
(O/'design_sheet_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
views=[]
for name,axes,size in [('side',(0,2),(800,240)),('top',(0,1),(800,241))]:
 dp={};ap={}
 for q,c in design.items():
  key=(q[axes[0]],q[axes[1]]);dp[key]=max(c,dp.get(key,0))
 for q,c in actual.items():
  key=(q[axes[0]],q[axes[1]]);ap[key]=max(c,ap.get(key,0))
 im=Image.new('RGB',size,(16,38,48))
 for (u,v),c in dp.items():im.putpixel((u,size[1]-1-v),(((c>>5)&7)*255//7,((c>>2)&7)*255//7,(c&3)*255//3))
 raw=O/f'ornament_design_union_{name}_raw.png';im.save(raw)
 read=Image.open(raw).convert('RGB');seen={};bad=0
 for v in range(size[1]):
  for u in range(size[0]):
   pix=read.getpixel((u,v))
   if pix==(16,38,48):continue
   key=(u,size[1]-1-v);seen[key]=pix;c=ap.get(key)
   if c is None or pix!=(((c>>5)&7)*255//7,((c>>2)&7)*255//7,(c&3)*255//3):bad+=1
 frame=Image.new('RGB',(size[0]*2+100,size[1]*2+100),(245,245,235));frame.paste(im.resize((size[0]*2,size[1]*2),Image.Resampling.NEAREST),(60,55));dr=ImageDraw.Draw(frame)
 dr.text((10,8),f'Tidegrave ORIGINAL DESIGN UNION - {name.upper()} | 0.1 m / voxel | X bow+, Y mirror=120, Z=0 keel bottom',(0,0,0))
 dr.text((10,26),'Masks: original 31405 + root correction 340 + raised staff 23 = 31768 voxels. Max palette index projection; not a render.',(0,0,0))
 for x in range(0,801,50):dr.text((60+x*2,60+size[1]*2),str(x),(0,0,0))
 for vv in range(0,size[1],25):dr.text((8,55+(size[1]-1-vv)*2),str(vv),(0,0,0))
 dr.text((size[0]*2+65,size[1]*2+60),'X',(0,0,0));dr.text((8,45),'Z' if name=='side' else 'Y',(0,0,0));frame.save(O/f'ornament_design_union_{name}_annotated.png')
 if name=='side':
  crop=im.crop((560,0,705,240)).resize((580,960),Image.Resampling.NEAREST)
  cf=Image.new('RGB',(700,1060),(245,245,235));cf.paste(crop,(60,60));cd=ImageDraw.Draw(cf)
  cd.text((10,8),'Original design union BOW DETAIL | 0.1 m / voxel | not render',(0,0,0))
  cd.text((10,26),'X=560..704 bow+; Z=0 keel bottom; Y mirror=120; max Y projection',(0,0,0))
  for x in range(560,705,20):cd.text((60+(x-560)*4,1030),str(x),(0,0,0))
  for z in range(0,240,25):cd.text((10,60+(239-z)*4),str(z),(0,0,0))
  cf.save(O/'ornament_design_union_bow_detail_X560_704.png')
 views.append({'view':name,'raw_png':str(raw),'drawing_pixels':len(seen),'drawing_pixel_missing_or_color_diff':bad,'actual_projection_extra':len(ap.keys()-seen.keys())})
report['additional_views']=views
(O/'design_sheet_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(report)

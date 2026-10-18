import numpy as np,json,pathlib,hashlib,itertools,collections
root=pathlib.Path('D:/Unity/Valhalla'); base=root/'Sculpture/works/sirius-tidegrave-01m/design/fittings_20261018'; out=root/'scratchpad/sirius-tidegrave/fittings_review_geometry'
raw=(base/'placement.json').read_bytes(); plan=json.loads(raw.decode('utf-8-sig')); parts=json.loads((base/'baseline_parts.json').read_text(encoding='utf-8-sig')); body=np.load(base/'baseline_body.npz')['cells']; occupied={tuple(x) for x in body[:,:3]}; models=parts['models']; src={}; transformed={}; results=[]
def intersect(a,b):
 return bool(np.all(np.minimum(a[3:],b[3:])-np.maximum(a[:3],b[:3])>1e-8))
def geometry(item):
 key=item['source']
 if key not in src:
  path=root/f'scratchpad/sirius-tidegrave/source_{key}.txt'; arr=np.loadtxt(path,delimiter=',',comments='#',dtype=int,encoding='utf-8-sig')[:,:3];src[key]=arr
 arr=src[key]; scale=item['scale']; pivot=np.array(item['pivot']); at=np.array(item['at']); angle=np.radians(item['rotate'][2]); c,s=np.cos(angle),np.sin(angle); R=np.array([[c,-s,0],[s,c,0],[0,0,1]])
 corners=np.array(list(itertools.product([0,1],repeat=3))); vertices=(arr[:,None,:]+corners[None,:,:]-pivot)*scale@R.T+at
 return np.column_stack((vertices.min(1),vertices.max(1)))
def body_intersections(boxes):
 hits=[]
 for idx,b in enumerate(boxes):
  for cell in itertools.product(*(range(int(np.floor(b[i]+1e-8)),int(np.ceil(b[i+3]-1e-8))) for i in range(3))):
   if cell in occupied: hits.append((idx,cell));break
 return hits
def support(boxes):
 z=boxes[:,2].min(); bottom=boxes[np.isclose(boxes[:,2],z)]; total=0; supported=0; contacts=[]
 for b in bottom:
  area=(b[3]-b[0])*(b[4]-b[1]); total+=area
  # Only count direct contact when voxel top is coplanar with base, not rounded by floor.
  if abs(z-round(z))>1e-8:continue
  bz=int(round(z))-1
  for x in range(int(np.floor(b[0]+1e-8)),int(np.ceil(b[3]-1e-8))):
   for y in range(int(np.floor(b[1]+1e-8)),int(np.ceil(b[4]-1e-8))):
    if (x,y,bz) in occupied:
     lo=np.maximum(b[:2],[x,y]);hi=np.minimum(b[3:5],[x+1,y+1]);a=float(np.prod(hi-lo));supported+=a
     if a>0:contacts.extend([lo.tolist(),hi.tolist()])
 return {'z':float(z),'lowest_face_count':len(bottom),'area':total,'contact_area':supported,'contact_fraction':supported/total,'contact_xy_bounds':np.r_[np.min(contacts,0),np.max(contacts,0)].tolist() if contacts else None,'geometric_centre_xy':((boxes[:,:3]+boxes[:,3:])/2).mean(0)[:2].tolist()}
for item in plan['placements']:
 boxes=geometry(item); transformed[item['name']]=boxes; whole=np.r_[boxes[:,:3].min(0),boxes[:,3:].max(0)]; bodyhits=body_intersections(boxes)
 oldhits=[]
 for old in models:
  ob=np.array(old['box']); ids=[i for i,b in enumerate(boxes) if intersect(b,ob)] if intersect(whole,ob) else []
  if ids:oldhits.append({'path':old['path'],'count':len(ids)})
 reserve=[]
 for name,rb in plan['reserved']:
  rb=np.array(rb); ids=[i for i,b in enumerate(boxes) if intersect(b,rb)] if intersect(whole,rb) else []
  if ids:reserve.append({'name':name,'count':len(ids)})
 # Exactly sample centre and eight inset corners, separately from exact cube/body test.
 points=np.concatenate([((boxes[:,:3]+boxes[:,3:])/2)[:,None,:],np.array([boxes[:,:3]+np.array(c)*(boxes[:,3:]-boxes[:,:3]) for c in itertools.product([1e-6,1-1e-6],repeat=3)]).transpose(1,0,2)],axis=1)
 samplehits=sum(tuple(np.floor(p).astype(int)) in occupied for p in points.reshape(-1,3))
 results.append({'name':item['name'],'source_voxels':len(boxes),'bounds':whole.tolist(),'declared_bounds_match':np.allclose(whole,item['box']),'body_positive_volume_voxels':len(bodyhits),'body_samples_hit':int(samplehits),'old_model_boxes':oldhits,'reserve_hits':reserve,'support':support(boxes)})
pairhits=[]
for (an,aa),(bn,bb) in itertools.combinations(transformed.items(),2):
 ab=np.r_[aa[:,:3].min(0),aa[:,3:].max(0)];bbounds=np.r_[bb[:,:3].min(0),bb[:,3:].max(0)]
 if intersect(ab,bbounds):
  pairs=sum(int(np.count_nonzero(np.all(np.minimum(a[3:],bb[:,3:])-np.maximum(a[:3],bb[:,:3])>1e-8,axis=1))) for a in aa)
  if pairs:pairhits.append([an,bn,pairs])
# Real negative: drop one barrel 1 voxel into the weather deck.
negative_item=dict(next(i for i in plan['placements'] if i['name']=='備用水桶-P1'));negative_item['at']=list(negative_item['at']);negative_item['at'][2]-=1;neg=geometry(negative_item);negative={'perturbation':'備用水桶-P1 z=116 -> 115','hit_voxel_count':len(body_intersections(neg)),'expected_detected':len(body_intersections(neg))>0}
report={'plan_sha256':hashlib.sha256(raw).hexdigest(),'baseline_file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'baseline_body.npz',base/'baseline_parts.json']},'body_voxels':len(body),'old_models':len(models),'results':results,'new_pair_hits':pairhits,'negative_control':negative,'scope':'Static supplied baseline only; exact axis-aligned cube overlap (all rotations here are multiples of 90 degrees), centre + eight inset corners checked independently. Old models use conservative supplied boxes; no dynamic rig/sail clearance certificate.'}
(out/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))


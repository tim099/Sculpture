import json,zlib,struct,pathlib,hashlib,math,sys,os
import numpy as np
OUT=pathlib.Path(__file__).parent
ROOT=pathlib.Path('D:/Unity/Valhalla/Sculpture/works')
SRC=pathlib.Path(os.environ['VERIFY_VXK']) if os.environ.get('VERIFY_VXK') else ROOT/('sirius-tidegrave-01m/design/continued_20261015/'+(sys.argv[1] if len(sys.argv)>1 else 'after_braces.vxk'))
blob=SRC.read_bytes(); raw=zlib.decompress(blob,-15); hn=struct.unpack_from('<I',raw,4)[0]; H=json.loads(raw[8:8+hn]); off=8+hn; nc=H['nchunks']
ch=np.frombuffer(raw,dtype='<u2',count=nc*3,offset=off).reshape(-1,3).astype(int); off+=nc*6
dat=np.frombuffer(raw,dtype='u1',count=nc*4096,offset=off).reshape(nc,4096); ci,li=np.nonzero(dat)
body=ch[ci]*16+np.column_stack([li%16,li//16%16,li//256]); rig=H['rig']
(OUT/'header.json').write_text(json.dumps(H),encoding='utf8')
def rot(p,piv,ang):
    p=np.asarray(p); q=p-np.asarray(piv); c=math.cos(ang); s=math.sin(ang)
    return np.column_stack([q[:,0]*c-q[:,1]*s,q[:,0]*s+q[:,1]*c,q[:,2]])+piv
yards=[]
for m in ([] if os.environ.get('VERIFY_FROZEN')=='1' else rig['models']):
    if m.get('meta',{}).get('kind')!='yard':continue
    mast,name=m['name'].split('/'); md=json.loads((ROOT/f'sirius-tidegrave-01m-mast-{mast}'/'models.json').read_text(encoding='utf8'))
    M=next(q for q in md['models'] if q['name']==name)
    cells={}
    for ep in sorted((ROOT/M['work']/'events').rglob('*.json')):
        e=json.loads(ep.read_text(encoding='utf8'))
        for c in e.get('placed_colored',[]):cells[tuple(c[:3])]=c[3]
        for c in e.get('carved_voxels',[]):cells.pop(tuple(c[:3]),None)
    if not cells:raise RuntimeError(M['work'])
    yards.append(dict(name=m['name'],cubes=np.array(list(cells),float),piv=np.array(M['pivot']),at=np.array(M['at']),r0=math.radians(M['rotate'][2]),meta=m['meta']))

if os.environ.get('VERIFY_FROZEN')=='1':
    frozen=json.loads((OUT/'frozen_yards.json').read_text(encoding='utf8'))
    yards=[{**y,'cubes':np.array(y['cubes'],float),'piv':np.array(y['piv']),'at':np.array(y['at'])} for y in frozen['yards']]

def probe(A,B,cubes,radius):
    # Exact segment-to-AABB squared distance: convex 1-D function, ternary minimization.
    # Broadphase rejects disjoint expanded AABBs, then numerical minimum to <1e-10 in t.
    lo=np.minimum(A,B)-radius; hi=np.maximum(A,B)+radius
    cc=cubes[np.all(cubes+1>=lo,axis=1)&np.all(cubes<=hi,axis=1)]
    if not len(cc):return None
    d=B-A
    l=np.zeros(len(cc)); u=np.ones(len(cc))
    def dist(t):
        p=A+t[:,None]*d; delta=np.maximum(np.maximum(cc-p,p-(cc+1)),0); return np.sum(delta*delta,axis=1)
    for _ in range(55):
        t1=(2*l+u)/3;t2=(l+2*u)/3; sel=dist(t1)<dist(t2); u=np.where(sel,t2,u);l=np.where(sel,l,t1)
    t=(l+u)/2; ds=dist(t); hit=ds<=radius*radius+1e-9
    if not hit.any():return None
    # Conservative contact arc interval from expanded box slabs, per confirmed cube.
    hitc=cc[hit]; tlo=np.zeros(len(hitc)); thi=np.ones(len(hitc))
    for k in range(3):
        if abs(d[k])<1e-14:continue
        v=(hitc[:,k]-radius-A[k])/d[k]; w=(hitc[:,k]+1+radius-A[k])/d[k]
        tlo=np.maximum(tlo,np.minimum(v,w));thi=np.minimum(thi,np.maximum(v,w))
    length=float(np.linalg.norm(d))
    return dict(n=int(hit.sum()),arc=[float(tlo.min()*length),float(thi.max()*length)],length=length,cells=hitc.astype(int).tolist(),min_distance=float(np.sqrt(ds.min())))

sel=[r for r in rig['ropes'] if ((r['name'].startswith(('main-','fore-')) and ('shroud' in r['name'] or 'backstay' in r['name'] or 'ratline' in r['name'])) or (r['name'].startswith(('main-course.','fore-course.','main-topsail.','fore-topsail.')) and '.lift-' in r['name'])) or ('.brace-' in r['name'] and 'topsail' in r['name'] or '.brace-' in r['name'] and 'topgallant' in r['name'])]
angles=np.linspace(-.7,.7,163)
result={'source':str(SRC),'sha256':hashlib.sha256(blob).hexdigest(),'body_voxels':len(body),'scope':len(sel),'angles':len(angles),'records':[]}
for r in sel:
    pts=np.array(r['pts']).reshape(-1,3); rec={'name':r['name'],'points':len(pts),'ends':r.get('ends'),'body':[],'yard':{}}
    lift='.lift-' in r['name'] or '.brace-' in r['name']; own=next((y for y in yards if y['name']==r['ends'][0].split('model:')[-1].rsplit('/',1)[0]),None) if lift else None
    if lift and (len(pts)!=2 or own is None):raise RuntimeError(r['name'])
    localbody=body[(body[:,2]+1>=pts[:,2].min()-r['radius']) & (body[:,2]<=pts[:,2].max()+r['radius'])]
    for theta in angles if lift else [None]:
        P=pts.copy()
        if lift:P[0]=rot(P[:1],own['at'],theta-own['r0'])[0]
        for i in range(len(P)-1):
            h=probe(P[i],P[i+1],localbody,r['radius'])
            if h:rec['body'].append({'angle':None if theta is None else float(theta),**h})
    for y in yards:
        # Z excludes most pairs for all angles, because all rotations are around Z.
        zlo=y['cubes'][:,2].min()-y['piv'][2]+y['at'][2]; zhi=y['cubes'][:,2].max()+1-y['piv'][2]+y['at'][2]
        if pts[:,2].max()+r['radius']<zlo or pts[:,2].min()-r['radius']>zhi:continue
        hits=[]
        for theta in angles if y['meta']['yard'] not in ('gaff','boom') else np.linspace(-1.4,1.4,323):
            P=pts.copy()
            # All square yards have same steady absolute angle. Own lift's only possible Z-contact is own yard.
            if lift:P[0]=rot(P[:1],own['at'],theta-own['r0'])[0]
            local=rot(P,y['at'],-theta)+y['piv']-y['at']
            for i in range(len(P)-1):
                h=probe(local[i],local[i+1],y['cubes'],r['radius'])
                if h:hits.append({'angle':float(theta),**h})
        if hits:rec['yard'][y['name']]=hits
    result['records'].append(rec)
    print(r['name'],'body',len(rec['body']),'yards',[(k,len(v)) for k,v in rec['yard'].items()],flush=True)
(OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
print('DONE',result['sha256'],flush=True)

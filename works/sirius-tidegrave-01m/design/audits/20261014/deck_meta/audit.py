from pathlib import Path
import json,zlib,struct,collections,hashlib,math
W=Path('D:/Unity/Valhalla/Sculpture/works');D=W/'sirius-tidegrave-01m/design/deck_meta_20261014';O=Path(__file__).parent
plan=json.loads((D.parent/'plan.json').read_text()); metas=[]
for l in (D/'measured.tsv').read_text(encoding='utf-8-sig').splitlines():
    a=l.split('\t');metas.append({'path':a[1],**json.loads(a[2])})
def load(p):
    b=zlib.decompress(p.read_bytes(),-15);n=struct.unpack_from('<I',b,4)[0];h=json.loads(b[8:8+n]);off=8+n;cnt=(len(b)-off)//4102;cs=struct.unpack_from('<'+str(cnt*3)+'H',b,off);off+=cnt*6;cols=collections.defaultdict(list)
    for i in range(cnt):
        cx,cy,cz=cs[i*3:i*3+3];block=b[off+4096*i:off+4096*(i+1)]
        for k,v in enumerate(block):
            if v:cols[cx*16+(k&15),cy*16+((k>>4)&15)].append(cz*16+(k>>8))
    return h,{q:sorted(v) for q,v in cols.items()}
def floor(m,x):
    p=m['poly']
    if x<p[0][0]-.5 or x>p[-1][0]+.5:return None
    for (x0,z0),(x1,z1) in zip(p,p[1:]):
        if x<=x1:return math.floor(z0+(z1-z0)*(x-x0)/(x1-x0)+.5)
    return p[-1][1]
decks=[]
for m in metas:
    ident=m['deck'];h,cols=load(D/(ident+'.vxk'));expected=next(v['z']+1 for v in plan['decks'] if v['id']==ident);cy=h['size'][1]//2
    m['poly']=[list(map(int,p.split(':'))) for p in m['floor'].split(',')];m['zmin']=min(v[1] for v in m['poly']);m['zmax']=max(v[1] for v in m['poly'])
    alltop=collections.Counter(v[-1]+1 for v in cols.values());sampled=[];raw={};out=[]
    for x in sorted({q[0] for q in cols}):
        c=collections.Counter(cols[x,cy+dy][-1]+1 for dy in (-28,-22,-16,-10,-4,4,10,16,22,28) if (x,cy+dy) in cols)
        if c:
            best=sorted(c,key=lambda z:(-c[z],z))[0]
            if c[best]>=2:raw[x]=best
            sampled.extend(c.elements())
            if any(z!=expected for z in c):out.append({'x':x,'tops':dict(c)})
    given=range(m['poly'][0][0],m['poly'][-1][0]+1)
    # All actual deck columns are separately checked; no wall-top data is trusted.
    thin=collections.Counter(len(v) for v in cols.values())
    decks.append({'deck':ident,'expected_first_air':expected,'measured_meta':m,'voxel_count':sum(map(len,cols.values())),'actual_x_extent':[min(q[0] for q in cols),max(q[0] for q in cols)],'actual_top_histogram':dict(alltop),'per_column_voxel_count_histogram':dict(thin),'sampled_top_outliers':out,'raw_valid_x_extent':[min(raw),max(raw)],'raw_x_missing_inside_meta':[x for x in given if x not in raw],'floor_wrong_in_meta_range':[x for x in given if floor(m,x)!=expected],'geometry_outside_meta_x_columns':sum(1 for x,y in cols if floor(m,x) is None),'sha256':hashlib.sha256((D/(ident+'.vxk')).read_bytes()).hexdigest()})
DM=sorted(metas,key=lambda m:(m['level'],m['zmin']));levels=[]
for i,m in enumerate(DM):
    lo=math.floor((DM[i-1]['zmax']+m['zmin'])/2)+1 if i else m['zmin']-10;hi=math.floor((m['zmax']+DM[i+1]['zmin'])/2) if i<len(DM)-1 else m['zmax']+20
    levels.append({'deck':m['deck'],'path':m['path'],'zr':[lo,hi],'cache_key_height_prefix':f'{lo},{hi}','own_floor_outside_zr':not(lo<=m['zmin']<=hi and lo<=m['zmax']<=hi)})
def lvOf(z):return next((i for i,L in enumerate(levels) if L['zr'][0]<=z<=L['zr'][1]),-1)
anchors=json.loads((W/'sirius-tidegrave-01m-ladders/anchors.json').read_text())['anchors'];lads=collections.defaultdict(dict)
for a in anchors:
    name,kind=a['name'].rsplit('.',1);lads[name][kind]=a['at']
ladreport=[]
for name,a in lads.items():
    ends=[]
    for kind in ('foot','head'):
        x,y,z=a[kind];candidates=[{'deck':m['deck'],'floor':floor(m,x),'distance':abs(z-floor(m,x))} for m in DM if floor(m,x) is not None and -3<=z-floor(m,x)<=20];candidates.sort(key=lambda m:m['distance']);li=lvOf(z);assigned=levels[li]['deck'] if li>=0 else None
        ends.append({'kind':kind,'at':[x,y,z],'height_only_lvOf':assigned,'spatial_floor_nearest':candidates[0] if candidates else None,'height_vs_spatial_disagree':bool(candidates and assigned!=candidates[0]['deck'])})
    ladreport.append({'name':name,'ends':ends})
report={'method':'Independent VXK decode / column support / meta and current-source algorithm reproduction; no game or author module imported. Static logic analysis does not assert runtime seven ladders pass.','decks':decks,'levels_current_42_hands':levels,'cache_height_prefixes_unique':len({tuple(L['zr']) for L in levels})==len(levels),'ladders':ladreport,'obsolete_patch':'Current navRegions stores N.reg/N.regs and retains all sufficiently large components; old patch requires N.component/N.bestComponent from old largest-only implementation. Do not apply old patch. Position-aware endpoint selection remains needed for coheight decks.'}
(O/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'deck_summary':[{k:v for k,v in d.items() if k not in ('measured_meta','sha256')} for d in decks],'levels':levels,'ladders':ladreport},ensure_ascii=False,indent=2))

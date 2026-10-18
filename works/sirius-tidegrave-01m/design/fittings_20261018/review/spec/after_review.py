import json,hashlib
from pathlib import Path
import numpy as np
D=Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/fittings_20261018')
O=Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/fittings_review_spec')
def read(p):return json.loads(p.read_text('utf-8-sig'))
b=read(D/'baseline_parts.json');a=read(D/'after_parts.json');p=read(D/'placement.json');review=read(O/'review_data.json')
old={x['path']:x for x in b['models']};after={x['path']:x for x in a['models']}
issues=[];new=[]
for k,v in old.items():
    if after.get(k)!=v:issues.append('old model changed '+k)
for k in b:
    if k!='models' and b[k]!=a[k]:issues.append('old export field changed '+k)
for spec,expected in zip(p['placements'],review['results']):
    matches=[x for x in a['models'] if x['path'] not in old and x['name']==spec['name']]
    if len(matches)!=1:issues.append('new name count '+spec['name']);continue
    actual=matches[0];errors=[]
    for k,v in [('work',spec['source']),('meta',spec['meta']),('box',spec['box'])]:
        if k=='box':same=np.allclose(actual[k],v,atol=1e-7)
        else:same=actual[k]==v
        if not same:errors.append(k)
    # Checked anchors against independently transformed source point centres.
    for k,v in expected['anchors'].items():
        if k not in actual['points'] or not np.allclose(actual['points'][k],v,atol=1e-7):errors.append('anchor '+k)
    if actual['state']!='ok':errors.append('state')
    expected_frame='甲板-'+spec['frame']
    if actual['frame']!=expected_frame or actual['path']!=expected_frame+'/'+spec['name']:errors.append('frame/path')
    raw=read(D.parents[2]/('sirius-tidegrave-01m-deck-'+spec['frame'])/'models.json')
    raw=[r for r in raw['models'] if r['name']==spec['name']]
    if len(raw)!=1:errors.append('raw model count')
    else:
        for k in ['at','pivot','rotate']:
            if not np.allclose(raw[0][k],spec[k]):errors.append('raw transform '+k)
        if not np.allclose(raw[0]['scale'],spec['scale']):errors.append('raw scale')
    if errors:issues.append(spec['name']+' '+','.join(errors))
    new.append({'path':actual['path'],'frame':actual['frame'],'name':spec['name'],'issues':errors,'points':actual['points']})
out={'baseline_models':len(old),'after_models':len(after),'new_models':len(new),'old_models_exactly_preserved':all(after.get(k)==v for k,v in old.items()),'old_links_points_meta_size_exactly_preserved':all(b[k]==a[k] for k in b if k!='models'),'placement_sha256':hashlib.sha256((D/'placement.json').read_bytes()).hexdigest(),'new':new,'issues':issues}
(O/'after_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))

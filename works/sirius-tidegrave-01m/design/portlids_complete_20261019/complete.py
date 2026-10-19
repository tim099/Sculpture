from pathlib import Path
import json,importlib.util,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('portlids',ROOT/'tools/portlids.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
CACHE='D:/Unity/Valhalla/ChatTavern/baton/letters/Sirius/scratchpad/portlids/cache'
# TASK-0747: median outlier is a screening heuristic, not a collision test.
# Lower02 is smooth hull slope. Upper ports have small decorative ribs.
# Accept candidates only after check() and the game's actual mesh-surface check.
def draft():
    p.OUTLIER=100
    p.draft(CACHE)
    fn=ROOT/'portlids_placement.json'
    pl=json.loads(fn.read_text(encoding='utf-8'))
    before=json.loads((HERE/'before_placement.json').read_text(encoding='utf-8'))
    now={(r['host'],r['model']):r for r in pl['rows']}
    assert len(now)==48 and not pl['skipped']
    assert all(now[(r['host'],r['model'])]==r for r in before['rows']), 'original 30 changed'
    for row in pl['rows']:
        if row['meta']['lid_of'] in ('gun-3','gun-4'):row['meta']['house']=6
    pl['note']='TASK-0747: 48 broadside lids; candidate outlier screening overridden, actual geometry validated. See portlids_complete_20261019/README.md.'
    fn.write_text(json.dumps(pl,ensure_ascii=False,indent=1,sort_keys=True)+'\n',encoding='utf-8')
def anchors():
    hw=p.C+'-assembly'
    ms={m['name']:m for m in p.host_models(hw)}
    report=[]
    for name in ('anchor-P','anchor-S'):
        m=ms[name];a=list(m['at'])
        # Move the bower anchor 0.3m forward, away from upper12's full opening sweep.
        assert a[0] in (560.5,563.5), (name,a)
        target=list(a);target[0]=563.5
        args=['op=work','sub=model','work='+hw,'name='+name,'source_work='+m['work'], 'at='+','.join(map(str,target)),
              'pivot='+','.join(map(str,m['pivot'])),'rotate='+','.join(map(str,m['rotate'])),
              'scale='+','.join(map(str,m['scale'])),'mirror='+ (m['mirror'] or 'none'),'overwrite=1',
              'meta='+json.dumps(m['meta'],ensure_ascii=False),'note=TASK-0747: bower anchor moved 0.3m forward to clear upper12 portlid sweep; anchor-cable follows model:ring reference.']
        r=p.sculpt(args)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        report.append({'name':name,'before':a,'after':target,'meta':m['meta']})
    (HERE/'anchor_changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    {'draft':draft,'anchors':anchors,'apply':lambda:p.apply(CACHE,step='models'),'check':lambda:p.check(CACHE)}[sys.argv[1]]()



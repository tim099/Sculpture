"""Supported contact repairs. Writes work state exclusively through Senate CLI."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

AUDIT = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit')
OUT = ROOT / 'task0603'
WORK = BASE + '-assembly'
WORKDIR = ROOT.parent.parent / WORK


def xyz(p):
    return ','.join(str(float(x)) for x in p)


def component(suffix, size, pivot, anchors, vox):
    wid = BASE + '-' + suffix
    card = ROOT.parent.parent / wid / 'work.json'
    if not card.exists():
        cli(op='work', sub='create', id=wid, title=suffix, size=','.join(str(int(x)) for x in size),
            parent_work=BASE, tags='sub')
        cli(op='work', sub='update', work=wid, meters_per_voxel=.05)
        count = len([x for x in vox.read_text('utf8').splitlines() if x and not x.startswith('#')])
        cli(op='stampvox', work=wid, voxels=vox, at='0,0,0', expect_pixels=count, share=0)
    return wid


def run():
    OUT.mkdir(exist_ok=True)
    before = json.loads((WORKDIR / 'ropes.json').read_text('utf8'))
    snap = OUT / 'ropes_before_attachments.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, ensure_ascii=False, indent=2), 'utf8')
    original = {r['name']: r for r in json.loads(snap.read_text('utf8'))['ropes']}
    routes = json.loads((AUDIT / 'route_clearance.json').read_text('utf8'))
    spec = json.loads((AUDIT / 'gun_prototype.json').read_text('utf8'))
    src = component('gun-fairleads', [48, 24, 32], spec['source_pivot'],
                    spec['anchors'], AUDIT / 'gun_fairlead.vox.txt')
    groups = {}
    for r in routes:
        groups.setdefault(r['model'], []).append(r)
    assert len(groups) == 48 and len(routes) == 96
    for number, (gun, rs) in enumerate(groups.items()):
        name = 'gun-fairlead-' + str(number + 1).zfill(2)
        p = rs[0]['route'][0]
        port = '-P' in gun
        cli(op='work', sub='model', work=WORK, name=name, source_work=src,
            pivot=xyz(spec['source_pivot']), at=xyz(p), scale=.5,
            rotate='0,0,180' if port else '0,0,0', overwrite=1,
            meta=json.dumps({'kind': 'fairlead', 'gun_mount': gun}))
        for r in rs:
            old = original[r['rope']]
            aft = r['rope'].endswith('-aft')
            label = 'aft' if aft != port else 'fwd'
            # Source anchors accept integer cells only. Use the exact measured
            # centre of each real, static guide aperture rather than rounding it.
            a, b = xyz(r['route'][1]), xyz(r['route'][2])
            cli(op='work', sub='rope', work=WORK, name=r['rope'],
                to=a, slack=1, thickness=.5, overwrite=1)
            for suffix, start, end in [('guide', a, b), ('wall', b, old['to'])]:
                cli(op='work', sub='rope', work=WORK, name=r['rope'] + '.' + suffix,
                    **{'from': start, 'to': end}, slack=1, thickness=.5,
                    color=old['color'], group=old.get('group', 'none'), overwrite=1)
                if old.get('meta'):
                    cli(op='work', sub='meta', work=WORK, part='rope',
                        name=r['rope'] + '.' + suffix, meta=json.dumps(old['meta']))
        print('gun guides', number + 1, gun, flush=True)
    for spec in json.loads((AUDIT / 'wheel_prototypes.json').read_text('utf8')):
        wid = component(spec['name'].replace('_', '-'), spec['size'],
                        spec['source_pivot'], {'eye': [x + .5 for x in spec['anchor_at']]},
                        AUDIT / (spec['name'] + '.vox.txt'))
        cli(op='work', sub='model', work=WORK, name=spec['name'].replace('_', '-'),
            source_work=wid, pivot=xyz(spec['source_pivot']), at=xyz(spec['at']),
            scale=.5, overwrite=1, meta=json.dumps({'kind': 'fairlead'}))
    old = original['steer-wheel-S']
    points = [old['from'], '199.5,155.5,154.5',
              '225.5,155.5,154.5', '225.5,134.5,151.5', old['to']]
    for i in range(4):
        name = 'steer-wheel-S' + ('' if i == 0 else '.guide' + str(i))
        cli(op='work', sub='rope', work=WORK, name=name,
            **{'from': points[i], 'to': points[i + 1]}, slack=1,
            thickness=.5, color=old['color'], overwrite=1)
        if old.get('meta'):
            cli(op='work', sub='meta', work=WORK, part='rope', name=name,
                meta=json.dumps(old['meta']))
    cli(op='export', work=WORK, format='vxk', include='rig,models,parts,meta,ends',
        out=OUT / 'attachments_candidate.vxk')


if __name__ == '__main__':
    run()

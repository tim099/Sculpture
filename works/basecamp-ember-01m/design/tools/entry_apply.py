# 餘燼號 階段十三 entry port：建 -entry-side（一舷）→ 落格 → 固定點 → 組裝件關聯（＋鏡像）→ man rope 4 條
# 用法：python -I entry_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建；關聯已在 ⇒ 不重掛；固定點／繩 overwrite=1）
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import existing_links   # noqa: E402

P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['entry_build']
A = json.load(open(os.path.join(D, 'entry_anchors.json'), encoding='utf-8'))
R = json.load(open(os.path.join(D, 'entry_ropes.json'), encoding='utf-8'))['ropes']
V = json.load(open(os.path.join(D, 'verify_entry.json'), encoding='utf-8'))
ok = bad = retried = 0


def cli(args, show=False, tries=3):
    global ok, bad, retried
    for k in range(tries):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode == 0:
            ok += 1
            if show:
                print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
            return 0
        if 'IOException' in r.stdout + r.stderr and k < tries - 1:
            retried += 1
            time.sleep(0.5)
            continue
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-300:])
        return r.returncode


def xyz(v):
    return ','.join('%g' % c for c in v)


w = P['subwork']['id']
if cli(['op=work', 'sub=show', 'work=' + w], tries=1):
    bad -= 1
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + P['subwork']['title'], 'size=' + xyz(A['size']), 'parent_work=basecamp-ember-01m', 'tags=sub'], show=True)
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + os.path.join(D, 'masks', 'entry', 'side.vox.txt').replace('\\', '/'), 'at=0,0,0',
         'expect_pixels=%d' % V['file']['cells']], show=True)
for a in A['anchors']:
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + w, 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=entry port（世界 S %s）' % xyz(a['world_S'])])
have = set(existing_links(P['assembly']))
for name, at, mir in ((P['link'], A['at'], ''), (P['mirror_link'], [A['at'][0], A['mirror_at_y'], A['at'][2]], 'y')):
    if name in have:
        print('· 關聯已在：' + name)
        continue
    args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + P['assembly'], 'name=' + name, 'source_work=' + w, 'at=' + xyz(at), 'note=階段十三 entry port 與 side steps' + ('（另一舷 mirror=y）' if mir else '')]
    if mir:
        args.append('mirror=y')
    cli(args, show=True)
for r in R:
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + P['assembly'], 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
         'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=entry man rope（階段十三）'], show=True)
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))

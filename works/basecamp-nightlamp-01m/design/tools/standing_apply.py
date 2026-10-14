# 階段十五：照 design/masks/channels、rig_points_standing.json、standing_ropes.json 下 CLI
# 用法：python -I standing_apply.py <design 資料夾> <步驟> [名字 regex]
#   步驟：create（開索具台子作品＋記 0.1 m）｜stamp（落索具台）｜link（組裝件兩條關聯：右舷 at 0,0,0、左舷 mirror=y at 0,1,0）｜
#         anchors（各件登記固定點）｜ropes（組裝件拉繩，照檔案順序：先主繩、子繩最後）｜meta（繩的 meta 一份批次檔）｜readback
#   · 重跑一樣：anchors／ropes overwrite=1；create 已存在 ⇒ 略過；stamp 擋重複（引擎禁覆蓋）
import sys, os, json, re, subprocess, tempfile
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
WORKS = os.path.dirname(os.path.dirname(D))
ASM = 'basecamp-nightlamp-01m-assembly'
HULL = 'basecamp-nightlamp-01m'
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['standing']
C = plan['channels']
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('🔢 placed') or l.startswith('✓'))[-600:])
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'create':
    if os.path.exists(os.path.join(WORKS, C['work'], 'work.json')):
        print('已有', C['work'])
    else:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + C['work'], 'title=' + C['title'], 'size=' + xyz(C['size']), 'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + C['work'], 'meters_per_voxel=0.1'])

elif step == 'stamp':
    path = os.path.join(D, 'masks', 'channels', 'channels.vox.txt').replace('\\', '/')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cli(['op=stampvox', 'persona=basecamp', 'work=' + C['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0'], show=True)

elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + C['link'], 'source_work=' + C['work'], 'at=' + xyz(C['origin']), 'overwrite=1',
         'note=索具台（右舷；階段十五）'], show=True)
    cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + C['link_mirror'], 'source_work=' + C['work'], 'at=%d,%d,%d' % (C['origin'][0], 321 - C['origin'][1] - C['size'][1], C['origin'][2]), 'mirror=y', 'overwrite=1',
         'note=索具台（左舷 ＝ 右舷 mirror=y；格 y ↔ 320 − y）'], show=True)

elif step == 'anchors':
    pts = json.load(open(os.path.join(D, 'rig_points_standing.json'), encoding='utf-8'))['points']
    for a in pts:
        if not flt.search(a['name']):
            continue
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + a['owner'], 'name=' + a['name'], 'at=' + xyz(a['local']), 'overwrite=1',
             'note=%s（階段十五 rig_points_standing.json）' % a['kind']])

elif step == 'ropes':
    R = json.load(open(os.path.join(D, 'standing_ropes.json'), encoding='utf-8'))['ropes']
    for i, r in enumerate(R):
        if not flt.search(r['name']):
            continue
        cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'],
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1',
             'note=階段十五 靜索（standing_ropes.json）'])
        if i % 50 == 0:
            print(i, r['name'], 'ok', ok, 'bad', bad, flush=True)

elif step == 'meta':
    R = json.load(open(os.path.join(D, 'standing_ropes.json'), encoding='utf-8'))['ropes']
    lines = ['rope\t%s\t%s' % (r['name'], json.dumps(r['meta'], ensure_ascii=False)) for r in R if r['meta'] and flt.search(r['name'])]
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'meta.tsv')
        open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
        cli(['op=work', 'sub=meta', 'persona=basecamp', 'work=' + ASM, 'file=' + p.replace('\\', '/')], show=True)
    print('meta lines', len(lines))

elif step == 'readback':
    pts = json.load(open(os.path.join(D, 'rig_points_standing.json'), encoding='utf-8'))['points']
    miss = diff = 0
    cache = {}
    for a in pts:
        if a['owner'] not in cache:
            p = os.path.join(WORKS, a['owner'], 'anchors.json')
            cache[a['owner']] = {x['name']: x for x in json.load(open(p, encoding='utf-8'))['anchors']} if os.path.exists(p) else {}
        g = cache[a['owner']].get(a['name'])
        if g is None:
            miss += 1
        elif [round(c) for c in g['at']] != a['local']:
            diff += 1
    print('anchors', len(pts), 'missing', miss, 'diff', diff)
    R = json.load(open(os.path.join(D, 'standing_ropes.json'), encoding='utf-8'))['ropes']
    got = {r['name']: r for r in json.load(open(os.path.join(WORKS, ASM, 'ropes.json'), encoding='utf-8'))['ropes']}
    rm = [r['name'] for r in R if r['name'] not in got]
    rd = [r['name'] for r in R if r['name'] in got and (got[r['name']]['from'] != r['from'] or got[r['name']]['to'] != r['to'] or abs(got[r['name']]['slack'] - r['slack']) > 1e-9
                                                       or got[r['name']].get('group') != r['group'] or abs(got[r['name']]['thickness'] - r['thickness']) > 1e-9)]
    mm = [r['name'] for r in R if r['meta'] and r['name'] in got and (got[r['name']].get('meta') or {}) != r['meta']]
    print('ropes', len(R), 'missing', len(rm), 'diff', len(rd), rd[:5], 'meta_diff', len(mm), mm[:5])
else:
    raise SystemExit('步驟？ create|stamp|link|anchors|ropes|meta|readback')
print(step, 'ok', ok, 'bad', bad)

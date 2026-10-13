# 餘燼號 階段八b：照 ladders_placement.json 下 CLI —— 建新梯子子作品、落格、關聯進甲板子作品、扶手固定點、扶手繩（掛在組裝件）
# 用法：python -I ladders_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建、已有格 ⇒ 不重落；關聯已在 ⇒ 不重掛；固定點與繩 overwrite=1）
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = 'basecamp-ember-01m'
PL = json.load(open(os.path.join(D, 'ladders_placement.json'), encoding='utf-8'))
ASM = PL['assembly']
ok = bad = 0


def cli(args, show=False, probe=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode and not probe:
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-400:])
    elif not r.returncode:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%d' % c for c in v)


for deck, F in PL['files'].items():
    S = PL['subworks'][deck]
    w = S['id']
    rc, _ = cli(['op=work', 'sub=show', 'work=' + w], probe=True)
    if rc:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + S['title'], 'size=1024,320,800', 'parent_work=' + P, 'tags=sub'], show=True)
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
        cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + os.path.join(D, F['file']).replace('\\', '/'), 'at=0,0,0',
             'expect_pixels=%d' % F['cells']], show=True)
    else:
        print('· 已在：' + w)
    _, have = cli(['op=work', 'sub=links', 'work=' + S['link_in']])
    if '`' + S['link'] + '` → ' in have:
        print('· 關聯已在：%s / %s' % (S['link_in'], S['link']))
    else:
        cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + S['link_in'], 'name=' + S['link'], 'source_work=' + w, 'at=0,0,0',
             'note=階段八b：艙口梯＋扶手柱（新圖紙 08）'], show=True)

for a in PL['anchors']:
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + a['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=' + a['note']])
print('anchors', len(PL['anchors']), 'ok', ok, 'bad', bad)

for r in PL['ropes']:
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
         'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=扶手繩（階段八b）'])
print('ok %d / bad %d' % (ok, bad))

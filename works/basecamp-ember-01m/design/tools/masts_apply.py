# 餘燼號 階段六：照 masks/masts 與 masts_placement.json 下 CLI —— 建桅杆子作品、落格、固定點、帆桁模型、關聯進組裝件
# 用法：python -I masts_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建、已有格 ⇒ 不重落；固定點與模型 overwrite=1）
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = 'basecamp-ember-01m'
ASM = P + '-assembly'
PL = json.load(open(os.path.join(D, 'masts_placement.json'), encoding='utf-8'))
WORK = {'fore': (P + '-mast-fore', '餘燼號 前桅', '1024,320,800', '前桅'), 'main': (P + '-mast-main', '餘燼號 主桅', '1024,320,800', '主桅'),
        'mizzen': (P + '-mast-mizzen', '餘燼號 後桅', '1024,320,800', '後桅'), 'bowsprit': (P + '-bowsprit', '餘燼號 艏斜桅', '1100,320,800', '艏斜桅')}
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-400:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + ASM, 'size=1100,320,800'])
for nm, (w, title, size, link) in WORK.items():
    rc, _ = cli(['op=work', 'sub=show', 'work=' + w])
    if rc:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + title, 'size=' + size, 'parent_work=' + P, 'tags=sub'], show=True)
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
        path = os.path.join(D, 'masks', 'masts', nm + '.vox.txt').replace('\\', '/')
        n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
        cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n], show=True)
    for a in PL['anchors'][nm]:
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + w, 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=' + (a['note'] + '；' if a['note'] else '') + '憲法號 %s 換算（階段六）' % xyz(a['con_at'])])
    for m in PL['models'][nm]:
        args = ['op=work', 'sub=model', 'persona=basecamp', 'work=' + w, 'name=' + m['name'], 'source_work=' + m['work'], 'at=' + xyz(m['at']),
                'pivot=' + xyz(m['pivot']), 'rotate=' + xyz(m['rotate']), 'scale=' + xyz(m['scale']), 'overwrite=1',
                'note=帆桁（沿用憲法號的子作品；階段六換算%s）' % ('；' + m['override']['provenance'] if m.get('override') else '')]
        if m['meta']:
            args.append('meta=' + json.dumps(m['meta'], ensure_ascii=False))
        if m.get('mirror'):
            args.append('mirror=' + m['mirror'])
        cli(args)
    cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0'], show=True)
print('masts ok', ok, 'bad', bad)

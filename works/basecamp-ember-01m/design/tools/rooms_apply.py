# 餘燼號 階段八a：照 rooms_placement.json 下 CLI —— 建房間／艙壁／梯子子作品、落格、關聯進各層甲板子作品
# 用法：python -I rooms_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建、已有格 ⇒ 不重落；關聯已在 ⇒ 不重掛）
#   side 件的框一定要跟 plan 記的一樣大（mirror=y 是在零件自己的框裡翻：框 y 不對，另一舷就落錯位置）
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = 'basecamp-ember-01m'
PL = json.load(open(os.path.join(D, 'rooms_placement.json'), encoding='utf-8'))
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-400:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%d' % c for c in v)


for nm, E in PL.items():
    w = E['work']
    if not E.get('reuse'):
        rc, out = cli(['op=work', 'sub=show', 'work=' + w])
        if rc:
            bad -= 1
            size = xyz(E['size']) if E['kind'] == 'side' else '1024,320,800'
            cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + E['title'], 'size=' + size, 'parent_work=' + P, 'tags=sub'], show=True)
            cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
            path = os.path.join(D, E['file']).replace('\\', '/')
            cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % E['cells']], show=True)
        else:
            print('· 已在：' + w)
    # 關聯
    rc, out = cli(['op=work', 'sub=links', 'work=' + E['deck_work']])
    have = out
    links = [(E['link'], E.get('at', [0, 0, 0]), '')]
    if E['kind'] == 'side':
        links.append((E['link'] + '-鏡像', E['at_mirror'], 'y'))
    for name, at, mirror in links:
        if '`' + name + '` → ' in have:
            print('· 關聯已在：%s / %s' % (E['deck_work'], name))
            continue
        note = '階段八a：憲法號照換算搬（%s）' % ('直接沿用憲法號子作品' if E.get('reuse') else '新子作品')
        if mirror:
            note += '；另一舷 mirror=y'
        args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + E['deck_work'], 'name=' + name, 'source_work=' + w, 'at=' + xyz(at), 'note=' + note]
        if mirror:
            args.append('mirror=' + mirror)
        cli(args, show=True)
print('ok %d / bad %d' % (ok, bad))

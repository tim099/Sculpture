# 餘燼號 階段十 砲：照 guns_placement.json 下 CLI —— 建 32 磅長砲子作品（落格、固定點）、每門砲一個外部模型掛在所在甲板的子作品上
# 用法：python -I guns_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建；模型 overwrite=1）
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'basecamp-ember-01m'
GB = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']
PTS = json.load(open(os.path.join(D, 'guns_points.json'), encoding='utf-8'))['long32']
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


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(c) for c in v)


# ── 32 磅長砲（一門）──
T = GB['types']['long32']
w = T['work']
rc, out = cli(['op=work', 'sub=show', 'work=' + w])
if rc:
    bad -= 1
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + T['title'], 'size=' + xyz(PTS['size']), 'parent_work=' + HULL, 'tags=sub'], show=True)
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.05'])
    path = os.path.join(D, T['cells']).replace('\\', '/')
    cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % PTS['voxels']], show=True)
else:
    print('· 已在：' + w)
for name, at in PTS['points'].items():
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + w, 'name=' + name, 'at=' + xyz(at), 'overwrite=1', 'note=32 磅長砲固定點（同憲法號 long18 的慣例）'])

# ── 模型 ──
for r in PL:
    t = GB['types'][r['type']]
    dw = GB['deck_works'][r['deck']]
    s = t['scale']
    note = '%s（階段十；%s 舷%s；place_guns.py back %s、砲口伸出 %s）' % (
        {'long32': '32 磅長砲', 'gun24': '24 磅長砲（憲法號 -gun-24）', 'long18': '18 磅追擊砲（憲法號 -gun-long18）', 'carr32': '32 磅 carronade（憲法號 -gun-carronade32）'}[r['type']],
        r['side'], ('、%s 第 %s 個砲門' % (r['deck'], r['port'])) if r['port'] != 'stern' else '、船尾', num(float(r['back'])), num(float(r['muzzle_beyond_outer'])))
    args = ['op=work', 'sub=model', 'persona=basecamp', 'work=' + dw, 'name=' + r['name'], 'source_work=' + t['work'], 'at=' + xyz(r['at']),
            'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'overwrite=1',
            'meta=' + json.dumps(t['meta'], ensure_ascii=False), 'note=' + note]
    if r['side'] == 'P':
        args.append('mirror=y')
    cli(args)
print('ok %d / bad %d' % (ok, bad))

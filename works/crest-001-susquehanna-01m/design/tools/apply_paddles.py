# 蘇士奎哈納號（crest-001，TASK-0697）階段五落格：明輪罩子作品（右舷一件、左舷鏡像關聯）＋兩具明輪子作品（外部模型 kind=propeller，平移放）
#   crest-001 自己寫的。清單 ＝ draft_paddles.py 的 masks/paddles/*；固定點 ＝ verify_paddles.json 的 anchors。
#   用法：python -I -X utf8 tools/apply_paddles.py <design>   （子作品已存在 ⇒ 不重建、不重貼）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
HULL = 'crest-001-susquehanna-01m'
ASM = HULL + '-assembly'
BOX = HULL + '-paddlebox'
WHEEL = {'S': HULL + '-wheel-s', 'P': HULL + '-wheel-p'}
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
V = json.load(open(os.path.join(design, 'verify_paddles.json'), encoding='utf-8'))
Pd = plan['paddles']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def exists(work):
    return os.path.exists(os.path.join(os.path.dirname(os.path.dirname(design)), work, 'work.json'))


def make(work, title):
    if exists(work):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=crest-001', 'id=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=1300,400,800', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=crest-001', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=crest-001', 'work=' + work, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d ✓' % (os.path.basename(path), n))


md = os.path.join(design, 'masks', 'paddles')
if make(BOX, '蘇士奎哈納號 明輪罩（右舷；扇形通風槽＋百葉、前後側台；左舷用鏡像關聯）'):
    stamp(BOX, os.path.join(md, 'box_S.vox.txt'))
    # 整船框的子作品沒辦法對中線 y 200 鏡像（at.y 要 1 ⇒ 越界）⇒ 收緊成箱子的外框（verify_paddles.box_extent）、關聯 at ＝ 框的原點
    E = V['box_extent']
    lo, hi = [E[a][0] for a in 'xyz'], [E[a][1] for a in 'xyz']
    cli('op=work', 'sub=move', 'persona=crest-001', 'work=' + BOX, 'region=%d..%d,%d..%d,%d..%d' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]), 'delta=%d,%d,%d' % (-lo[0], -lo[1], -lo[2]))
    cli('op=work', 'sub=update', 'persona=crest-001', 'work=' + BOX, 'size=%d,%d,%d' % (hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1))
for s in ('S', 'P'):
    if make(WHEEL[s], '蘇士奎哈納號 明輪（%s；直徑 9.5 m、26 片徑向槳板；外部模型的來源，0.1 m，整船的框）' % ('右舷' if s == 'S' else '左舷')):
        stamp(WHEEL[s], os.path.join(md, 'wheel_%s.vox.txt' % s))
        for nm in ('hub', 'shaft-fwd'):
            x, y, z = V['anchors'][s][nm]
            cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + WHEEL[s], 'name=' + nm, 'at=%d,%d,%d' % (x, y, z),
                'note=' + ('轉軸中心（明輪軸心）' if nm == 'hub' else '軸接到船殼那一格（遊戲把明輪掛在它旁邊 8 格內的船殼上）'))
E = V['box_extent']
ax, ay, az = E['x'][0], E['y'][0], E['z'][0]
ny = E['y'][1] - E['y'][0] + 1
cli('op=work', 'sub=link', 'persona=crest-001', 'work=' + ASM, 'name=明輪罩', 'source_work=' + BOX, 'at=%d,%d,%d' % (ax, ay, az), 'note=階段五：右舷', ok=(0, 2))
cli('op=work', 'sub=link', 'persona=crest-001', 'work=' + ASM, 'name=明輪罩-鏡像', 'source_work=' + BOX, 'at=%d,%d,%d' % (ax, 401 - ay - ny, az), 'mirror=y',
    'note=階段五：左舷（mirror=y，at.y ＝ 401 − %d − %d）' % (ay, ny), ok=(0, 2))
for s in ('S', 'P'):
    hx, hy, hz = V['anchors'][s]['hub']
    piv = '%g,%g,%g' % (hx + 0.5, hy + 0.5, hz + 0.5)
    meta = {'kind': 'propeller', 'axis_x': 0, 'axis_y': 1, 'axis_z': 0, 'blades': Pd['n'], 'diameter_m': round(2 * Pd['R'] * 0.1, 2), 'rpm_max': 12, 'wheel': 'paddle'}
    cli('op=work', 'sub=model', 'persona=crest-001', 'work=' + ASM, 'name=明輪-' + s, 'source_work=' + WHEEL[s], 'pivot=' + piv, 'at=' + piv, 'scale=1',
        'meta=' + json.dumps(meta), ok=(0, 2))
    cli('op=work', 'sub=meta', 'persona=crest-001', 'work=' + ASM, 'part=model', 'name=明輪-' + s, 'meta=' + json.dumps(meta))
print('✓ 明輪罩×2（關聯）、明輪×2（模型 kind=propeller、axis 0,1,0、rpm_max 12）')

# 拿破崙號 主機的大齒輪與小齒輪拆成外部模型、跟著螺旋槳轉（Tim 2026-10-16：截圖「另外這個能旋轉嗎」「可以參考螺旋槳做法」）
#   做法照 split_screw.py（螺旋槳）：每個齒輪一件子作品、整船的框、世界座標；組裝件的外部模型 at ＝ pivot ＝ 轉軸那一格的格心、scale 1 ⇒ 原樣放回。
#   轉：造船規格 §9.8 的 spin（Blockside 26_spin.js）—— spin=rpm（模型自己不是動力的輸出 ⇒ 這艘第一個螺旋槳的轉速）、spin_mode=rate（每秒 spin_k × rpm 度）。
#     小齒輪在螺旋槳軸上 ⇒ 跟螺旋槳同轉速同方向：spin_k ＝ 6（rpm × 6 ＝ 每秒幾度）、軸 +x（螺旋槳 axis 1,0,0）。
#     大齒輪在曲軸上、外咬合 ⇒ 反方向、轉速 ÷（18 ／ 4 ＝ 4.5）：spin_k ＝ −6 × 4 ／ 18。
#   轉軸：子作品裡的固定點 spin-a（轉軸上、齒輪中間那一片的中心格）→ spin-b（往船頭 1 格）。
#   哪幾格：主機子作品（-engine）裡 x 在齒輪那 3 片（gear.x − 1 … gear.x − 2 + th）、離曲軸心（y 200, z 64）≤ r ＋ 0.5 的 ⇒ 大齒輪（含那 3 片裡的曲軸段）；
#     離軸心（y 200, z 42）≤ pinion.r ＋ 0.5 的 ⇒ 小齒輪（兩個圓在咬合處重疊 ⇒ 歸小齒輪，同 draft_engine 後畫的蓋前面的）。
#   用法：python -I -X utf8 tools/split_gears.py <design> [plan|apply|check]
import json, math, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
step = sys.argv[2] if len(sys.argv) > 2 else 'plan'
sys.path.insert(0, D)
import mio  # noqa: E402

HULL = 'kotoko-napoleon-01m'
ENG = HULL + '-engine'
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
G = plan['engine']['engine']
gr, pr, ck, sz = G['gear'], G['pinion'], G['crank'], plan['engine']['shaft']['z']
PL = json.load(open(os.path.join(D, 'engine_placement.json'), encoding='utf-8'))['engine']
ORG = PL['at']                                                        # 主機子作品原點（組裝件座標）
XS = list(range(gr['x'] - 1, gr['x'] - 1 + gr['th']))
XM = XS[len(XS) // 2]
RATIO = gr['r'] / float(pr['r'])
SPEC = {
    '大齒輪': {'work': HULL + '-engine-gear', 'title': '拿破崙號 主機大齒輪（曲軸上；外部模型的來源，0.1 m，整船的框）', 'axis': [XM, 200, ck['z']],
              'meta': {'kind': 'gear', 'gear': 'crank', 'spin': 'rpm', 'spin_mode': 'rate', 'spin_k': round(-6 / RATIO, 4)}},
    '小齒輪': {'work': HULL + '-engine-pinion', 'title': '拿破崙號 主機小齒輪（螺旋槳軸上；外部模型的來源，0.1 m，整船的框）', 'axis': [XM, 200, sz],
              'meta': {'kind': 'gear', 'gear': 'pinion', 'spin': 'rpm', 'spin_mode': 'rate', 'spin_k': 6}},
}


def cli(*a, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode not in ok:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))
    return r.stdout


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        cli('op=export', 'format=parts', 'work=' + mio.ASM, 'out=' + out)
        return json.load(open(out, encoding='utf-8'))


def pick(E):
    """主機子作品的格（世界座標 {(x,y,z): c}）⇒ (大齒輪, 小齒輪)。"""
    big, small = {}, {}
    for (x, y, z), c in E.items():
        if x not in XS:
            continue
        if math.hypot(y - 200, z - sz) <= pr['r'] + 0.5:
            small[(x, y, z)] = c
        elif math.hypot(y - 200, z - ck['z']) <= gr['r'] + 0.5:
            big[(x, y, z)] = c
    return big, small


def world(work, org):
    A = mio.export_list(work, None)
    return {(x + org[0], y + org[1], z + org[2]): c for x, y, z, c in A.tolist()}


def write(path, cells, head, org=(0, 0, 0)):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head)
        for (x, y, z) in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (x - org[0], y - org[1], z - org[2], cells[(x, y, z)]))


cache = os.path.join(D, 'masks', 'engine', 'gears_from_engine.json')
if os.path.exists(cache):                                             # 拆過了 ⇒ 用拆的那一刻記下的格（主機子作品裡已經沒有了）
    S = json.load(open(cache, encoding='utf-8'))
    big = {tuple(map(int, k.split(','))): v for k, v in S['大齒輪'].items()}
    small = {tuple(map(int, k.split(','))): v for k, v in S['小齒輪'].items()}
else:
    E = world(ENG, ORG)
    big, small = pick(E)
    with open(cache, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'大齒輪': {'%d,%d,%d' % k: v for k, v in sorted(big.items())}, '小齒輪': {'%d,%d,%d' % k: v for k, v in sorted(small.items())}}, f, sort_keys=True)
cells = {'大齒輪': big, '小齒輪': small}
asym = {k: sum(1 for (x, y, z), c in v.items() if v.get((x, 400 - y, z)) != c) for k, v in cells.items()}
print('大齒輪 %d 格、小齒輪 %d 格；鏡像差 %s；轉軸 %s；spin_k %s' % (len(big), len(small), asym, {k: v['axis'] for k, v in SPEC.items()},
                                                          {k: v['meta']['spin_k'] for k, v in SPEC.items()}))
if step == 'plan':
    raise SystemExit(0)

if step == 'extend':
    # 🩸 拆完量到主機件浮空 29 格：曲軸在齒輪後面那一段（x ck.x0 … 齒輪第一片 − 1）只靠齒輪那三片接著 ⇒ 一起搬進大齒輪（本來就跟著曲軸轉）
    E = world(ENG, ORG)
    extra = {(x, y, z): c for (x, y, z), c in E.items() if ck['x'][0] <= x < XS[0] and math.hypot(y - 200, z - ck['z']) <= ck['r'] + 0.5}
    print('曲軸後段 %d 格 ⇒ 大齒輪' % len(extra))
    if extra:
        od = os.path.join(D, 'masks', 'engine')
        cp = os.path.join(od, 'gears_extend_carve_local.vox.txt')
        write(cp, extra, '# 主機子作品要刻掉的曲軸後段（子作品座標；x,y,z,原色 ＝ 守門）\n', ORG)
        lp = os.path.join(od, 'gear_crank_extend.vox.txt')
        write(lp, extra, '# 大齒輪補上的曲軸後段（世界座標）\n')
        cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + ENG, 'name=曲軸後段併進大齒輪', 'phase=begin', 'note=齒輪拆件後浮空的那一段')
        cli('op=carvevox', 'persona=kotoko', 'work=' + ENG, 'voxels=' + cp.replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=%d' % len(extra))
        cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + ENG, 'name=曲軸後段併進大齒輪', 'phase=end', 'note=刻 %d 格（顏色守門）' % len(extra))
        out = cli('op=stampvox', 'persona=kotoko', 'work=' + SPEC['大齒輪']['work'], 'voxels=' + lp.replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=%d' % len(extra), 'share=0')
        assert int(re.search(r'🔢 placed = (\d+)', out).group(1)) == len(extra)
        big.update(extra)
        with open(cache, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'大齒輪': {'%d,%d,%d' % k: v for k, v in sorted(big.items())}, '小齒輪': {'%d,%d,%d' % k: v for k, v in sorted(small.items())}}, f, sort_keys=True)

if step == 'apply':
    before = mio.export_list(mio.ASM, 'all')
    od = os.path.join(D, 'masks', 'engine')
    carve = dict(big)
    carve.update(small)
    cp = os.path.join(od, 'gears_carve_local.vox.txt')
    write(cp, carve, '# 主機子作品要刻掉的齒輪格（子作品座標；x,y,z,原色 ＝ 守門）\n', ORG)
    for nm, sp in SPEC.items():
        W = sp['work']
        lp = os.path.join(od, 'gear_%s.vox.txt' % ('crank' if nm == '大齒輪' else 'pinion'))
        write(lp, cells[nm], '# %s（世界座標，整船的框）\n' % nm)
        if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + W], capture_output=True).returncode != 0:
            cli('op=work', 'sub=create', 'persona=kotoko', 'id=' + W, 'title=' + sp['title'], 'size=1200,400,800', 'parent_work=' + HULL, 'tags=sub')
            cli('op=work', 'sub=update', 'persona=kotoko', 'work=' + W, 'meters_per_voxel=0.1')
        have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + W)).group(1))
        if have == 0:
            out = cli('op=stampvox', 'persona=kotoko', 'work=' + W, 'voxels=' + lp.replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells[nm]), 'share=0')
            assert int(re.search(r'🔢 placed = (\d+)', out).group(1)) == len(cells[nm])
        a = sp['axis']
        cli('op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=spin-a', 'at=%d,%d,%d' % tuple(a), 'overwrite=1', 'note=轉軸（中間那一片的中心格）')
        cli('op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=spin-b', 'at=%d,%d,%d' % (a[0] + 1, a[1], a[2]), 'overwrite=1', 'note=轉軸往船頭 1 格（spin-a → spin-b ＝ +x）')
    marks = cli('op=work', 'sub=marks', 'work=' + ENG)
    if '齒輪拆件:end' not in marks:
        cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + ENG, 'name=齒輪拆件', 'phase=begin', 'note=大齒輪、小齒輪拆成外部模型（跟著螺旋槳轉）')
        cli('op=carvevox', 'persona=kotoko', 'work=' + ENG, 'voxels=' + cp.replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=%d' % len(carve))
        cli('op=work', 'sub=mark', 'persona=kotoko', 'work=' + ENG, 'name=齒輪拆件', 'phase=end', 'note=刻 %d 格（顏色守門）' % len(carve))
    for nm, sp in SPEC.items():
        a = sp['axis']
        piv = '%g,%g,%g' % (a[0] + 0.5, a[1] + 0.5, a[2] + 0.5)
        cli('op=work', 'sub=model', 'persona=kotoko', 'work=' + mio.ASM, 'name=' + nm, 'source_work=' + sp['work'], 'at=' + piv, 'pivot=' + piv,
            'rotate=0,0,0', 'scale=1', 'overwrite=1', 'meta=' + json.dumps(sp['meta'], sort_keys=True, ensure_ascii=False),
            'note=%s（外部模型：照螺旋槳轉速轉，§9.8 spin；at ＝ pivot ＝ 轉軸格心 ⇒ 子作品的世界座標原樣）' % nm)
    after = mio.export_list(mio.ASM, 'all')
    kb = set(map(tuple, before[:, :4].tolist())); ka = set(map(tuple, after[:, :4].tolist()))
    ks = {k + (v,) for k, v in carve.items()}
    print('組裝件 %d → %d：少掉的 ＝ 齒輪的格 %s（少 %d、多 %d）' % (len(before), len(after), (kb - ka) == ks, len(kb - ka), len(ka - kb)))

# check：parts 的模型（state、meta、spin-a／b）、子作品格 ＝ 拆的那一刻記下的格
P = parts()
by = {m['path']: m for m in P['models']}
R = {}
for nm, sp in SPEC.items():
    m = by.get(nm)
    got = world(sp['work'], (0, 0, 0))
    R[nm] = {'model': bool(m), 'state': m and m.get('state'), 'meta_same': bool(m) and all(str((m.get('meta') or {}).get(k)) == str(v) for k, v in sp['meta'].items()),
             'points': m and {k: m.get('points', {}).get(k) for k in ('spin-a', 'spin-b')}, 'cells': len(got), 'cells_same': got == cells[nm]}
E = world(ENG, ORG)
R['engine_left_in_gear_slices'] = sum(1 for k in pick(E)[0]) + sum(1 for k in pick(E)[1])
print(json.dumps(R, ensure_ascii=False))

# 哨兵號的速射砲加鐵砲房（TASK-0661；Tim 2026-10-16：「哨兵號的炮 可以嘗試用裝甲子模組做炮盾(目前太脆弱了)」）：
#   五座速射砲各改成一座小砲塔（砲塔層 kind=turret，造船規格 §4.8）：殼 ＝ 平台＋前盾＋兩片側翼（鐵、2 格厚），砲固定在上面，砲塔照砲原本的射界轉。
#   原本速射砲台（-mounts）裡的砲模型搬進各自的砲房作品；圍欄照舊留在 -mounts（不轉）、外推讓砲房轉得開。
#   砲房的框只包砲房（z 35 起）⇒ 框裡不會收到甲板、圍欄的格（照哨兵號整艘的格子清單檢查，有 ⇒ 停）。
# 砲房（砲塔座標：u ＝ 沿砲軸往前、v ＝ 橫的，原點 ＝ 耳軸＝轉軸）—— 開放的：
#   平台 z 35、−13 ≤ u < 10、8.5 ≤ |v| < 13.5（中間挖空給砲架，砲架照舊在砲井裡）：砲班前四個站在上面（u −5／−11、v ±10.75），跟著轉（會轉的甲板）；
#   前盾 8 ≤ u < 10、|v| < 13.5、z 35–47，中間砲門 |v| < 5.5、z 40–42（三根砲管 v −3.5／0／3.5、z 41.25）；側翼 12 ≤ |v| < 13.5、−13 ≤ u < 8、z 36–47；頂緣一圈鉛灰。
#   高到 z 47（站在平台上的人腳下 z 36、胸口 z 45 ⇒ 1.1 m 高才擋得到；⛔ 第一版做到 z 43／45 ⇒ 側面那條線從翼板上面過去）。
#   砲班後兩個（u −18）站在平台後面的甲板上（背面不擋）。
#   圍欄外推到半徑 22–23（原本 18–19；照舊朝船內留出入口、只放在底下有甲板的地方）⇒ 砲房轉一整圈不碰。
# 用法：python -I -X utf8 apply_shields.py [--dry]
import sys, os, json, math, subprocess, shutil, tempfile
S = shutil.which('senate'); PER = 'meadow'; W = 'meadow-sentinel-01m'; MOUNTS = W + '-mounts'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DRY = '--dry' in sys.argv
IRON_BLACK, LEAD = 36, 146
GW = 'gura-tridente-01m-gun-trident'
#        key   砲的名字        x    y  rotate  射界         開火
GUNS = [('bow', '速射砲-艏', 503, 65, -90, '-150,150', '-140,140', 'C'),
        ('ms', '速射砲-中S', 228, 31, 180, '-110,110', '-100,100', 'S'),
        ('mp', '速射砲-中P', 228, 99, 0, '-110,110', '-100,100', 'P'),
        ('as', '速射砲-艉S', 150, 33, 180, '-110,110', '-100,100', 'S'),
        ('ap', '速射砲-艉P', 150, 97, 0, '-110,110', '-100,100', 'P')]
PIV, SC = (16.5, 34, 0), 0.5                                             # 砲模型的 pivot、scale（照 gen_sentinel.py）
TRUN = (16.5, 30.5, 16.5)                                                # 三叉戟砲的耳軸（gura 的固定點 trunnion 那一格的格心）
RW0, RW1, RH, GAP, ZFL = 22, 23, 2, 5, 35                                # 圍欄（照 gen_sentinel.py 的畫法，半徑外推）


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1500:]); sys.exit(1)
    return p.stdout


def rz(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def names(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    return [x['name'] for x in json.load(open(f, encoding='utf-8'))[key]] if os.path.exists(f) else []


tmp = tempfile.mkdtemp(prefix='shield_')


def load_list(fn):
    d = {}
    if os.path.exists(fn):
        for l in open(fn, encoding='utf-8'):
            if l[:1].isdigit(): a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


def export_own(wid):
    fn = os.path.join(tmp, wid + '_cur.txt').replace(os.sep, '/')
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', fn), ('links', 'none'))
    return load_list(fn)


def sync(wid, new, size):
    """作品 wid 自己的格換成 new（作品座標）：先刻掉不要的、再調框、再補新的（⛔ 先縮框會切到現有的格）。"""
    old = export_own(wid)
    rm = [k for k, c in old.items() if new.get(k) != c]; add = [k for k, c in new.items() if old.get(k) != c]
    for nm, lst, op, src in (('rm', rm, 'carvevox', old), ('add', add, 'stampvox', new)):
        if op == 'stampvox' and size: run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', '0.1'), ('size', size), ('tags', 'sub'))
        if not lst: continue
        fn = os.path.join(tmp, '%s_%s.txt' % (wid, nm)).replace(os.sep, '/')
        open(fn, 'w').write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], src[k]) for k in lst) + '\n')
        run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(lst))), ('share', '0'))
    print('  %s：刻 %d、補 %d（現在 %d 格）' % (wid, len(rm), len(add), len(new)))


# 哨兵號整艘現在的格；扣掉這支自己管的（圍欄、砲房）＝ 不能碰的
cur = os.path.join(tmp, 'all.txt').replace(os.sep, '/')
run(('op', 'export'), ('format', 'list'), ('work', W), ('out', cur))
have = set(load_list(cur))
own = set(export_own(MOUNTS))                                            # 速射砲台（-mounts）的格 ＝ 圍欄（關聯 at 0,0,0）
LK = {l['name']: l for l in json.load(open(os.path.join(WORKS, W, 'links.json'), encoding='utf-8'))['links']}
for key, gname, *_ in GUNS:
    wid = '%s-shield-%s' % (W, key); ln = '砲盾-' + gname.split('-')[1]
    if ln in LK and os.path.exists(os.path.join(WORKS, wid, 'work.json')):
        o = LK[ln]['at']; own |= {(k[0] + o[0], k[1] + o[1], k[2] + o[2]) for k in export_own(wid)}
base = have - own
print('哨兵號現在 %d 格；圍欄＋砲房 %d 格 ⇒ 不能碰的 %d 格' % (len(have), len(have & own), len(base)))

# 圍欄：半徑 RW0..RW1、高 RH 格，朝船內留 GAP 格寬的出入口，只放在底下有甲板（z 34）的地方
fence = {}
for key, gname, gx, gy, rot, arc, fire, side in GUNS:
    face = {'C': 'fwd', 'S': 'S', 'P': 'P'}[side]
    for x in range(gx - RW1 - 1, gx + RW1 + 2):
        for y in range(gy - RW1 - 1, gy + RW1 + 2):
            r = math.hypot(x - gx, y - gy)
            if not (RW0 <= r < RW1 + 1): continue
            if face == 'fwd' and x < gx and abs(y - gy) <= GAP // 2: continue
            if face != 'fwd' and abs(x - gx) <= GAP // 2 and ((y > gy) if face == 'S' else (y < gy)): continue
            if (x, y, ZFL - 1) not in base: continue                    # 底下沒有甲板 ⇒ 不放（船頭收窄、舷邊）
            for z in range(ZFL, ZFL + RH):
                fence[(x, y, z)] = LEAD if (z == ZFL + RH - 1 and r >= RW1) else IRON_BLACK
hit = [k for k in fence if k in base]                                    # 碰到甲板上原本的東西（艉砲座旁的進氣管）⇒ 圍欄在那裡讓開
for k in hit: del fence[k]
print('圍欄 %d 格（半徑 %d–%d；讓開原本就有的 %d 格 %s）' % (len(fence), RW0, RW1, len(hit), sorted(hit)[:4]))

plan = []
for key, gname, gx, gy, rot, arc, fire, side in GUNS:
    at = (gx + 0.5, gy + 0.5, 33)
    t = rz(((TRUN[0] - PIV[0]) * SC, (TRUN[1] - PIV[1]) * SC), rot); c = (at[0] + t[0], at[1] + t[1])   # 轉軸 ＝ 耳軸
    ax = rz((0, 1), rot); pv = rz((1, 0), rot)
    cells = {}
    for x in range(int(c[0]) - 16, int(c[0]) + 17):
        for y in range(int(c[1]) - 16, int(c[1]) + 17):
            dx, dy = x + 0.5 - c[0], y + 0.5 - c[1]
            u, v = dx * ax[0] + dy * ax[1], dx * pv[0] + dy * pv[1]
            for z in range(35, 48):
                plate = 8 <= u < 10 and abs(v) < 13.5 and not (abs(v) < 5.5 and 40 <= z <= 42)
                wing = 12 <= abs(v) < 13.5 and -13 <= u < 8 and 36 <= z <= 47
                deck = z == 35 and -13 <= u < 10 and 8.5 <= abs(v) < 13.5
                if plate or wing or deck:
                    top = z == 47
                    cells[(x, y, z)] = LEAD if top else IRON_BLACK
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    inbox = [p for p in list(base) + list(fence) if lo[0] <= p[0] <= hi[0] and lo[1] <= p[1] <= hi[1] and lo[2] <= p[2] <= hi[2]]
    if inbox: sys.exit('%s：砲房的框 %s–%s 裡已經有 %d 格（例 %s）⇒ 停' % (gname, lo, hi, len(inbox), inbox[:3]))
    piv = (int(math.floor(c[0])) - lo[0], int(math.floor(c[1])) - lo[1], 0)
    fr = (int(math.floor(c[0] + 8 * ax[0])) - lo[0], int(math.floor(c[1] + 8 * ax[1])) - lo[1], 0)
    rmax = max(math.hypot(k[0] + 0.5 - c[0], k[1] + 0.5 - c[1]) for k in cells)
    print('%s：轉軸 %.2f,%.2f、砲房 %d 格、框 %s–%s（%d×%d×%d）、離轉軸最遠 %.1f 格' % (gname, c[0], c[1], len(cells), lo, hi, hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1, rmax))
    plan.append((key, gname, at, rot, arc, fire, side, cells, lo, hi, piv, fr))
if DRY: sys.exit(0)

sync(MOUNTS, fence, None)
for key, gname, at, rot, arc, fire, side, cells, lo, hi, piv, fr in plan:
    wid = '%s-shield-%s' % (W, key); size = '%d,%d,%d' % (hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1)
    title = '哨兵號 %s 的鐵砲房（小砲塔：平台＋前盾＋兩片側翼）' % gname
    if not os.path.exists(os.path.join(WORKS, wid, 'work.json')):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', W), ('size', size), ('tags', 'sub'))
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('title', title))
    sync(wid, {(k[0] - lo[0], k[1] - lo[1], k[2] - lo[2]): c for k, c in cells.items()}, size)
    for nm, p_, note in (('pivot', piv, '轉軸 ＝ 砲的耳軸'), ('front', fr, '前方 ＝ 砲口那一邊')):
        if nm in [x['name'] for x in json.load(open(os.path.join(WORKS, wid, 'anchors.json'), encoding='utf-8'))['anchors']] if os.path.exists(os.path.join(WORKS, wid, 'anchors.json')) else []:
            run(('op', 'work'), ('sub', 'unanchor'), ('persona', PER), ('work', wid), ('name', nm))
        run(('op', 'work'), ('sub', 'anchor'), ('persona', PER), ('work', wid), ('name', nm), ('at', '%d,%d,%d' % p_), ('note', note))
    a = [('op', 'work'), ('sub', 'model'), ('persona', PER), ('work', wid), ('name', gname), ('source_work', GW),
         ('at', '%s,%s,%s' % (at[0] - lo[0], at[1] - lo[1], at[2] - lo[2])), ('pivot', '%s,%s,%s' % PIV), ('rotate', '0,0,%d' % rot), ('scale', '0.5,0.5,0.5'),
         ('meta', json.dumps({'kind': 'gun', 'gun': 'trident', 'barrels': 3, 'deck': 'main', 'side': side}, ensure_ascii=False))]
    if gname in names(wid, 'models.json', 'models'): a.append(('overwrite', '1'))
    run(*a)
    ln = '砲盾-' + gname.split('-')[1]
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', W), ('name', ln), ('source_work', wid), ('at', '%d,%d,%d' % lo),
         ('meta', json.dumps({'kind': 'turret', 'arc': arc, 'fire': fire, 'rate': 40, 'material': 'iron'}, ensure_ascii=False))]
    if ln in names(W, 'links.json', 'links'): a.append(('overwrite', '1'))
    run(*a)
    if gname in names(MOUNTS, 'models.json', 'models'): run(('op', 'work'), ('sub', 'unmodel'), ('persona', PER), ('work', MOUNTS), ('name', gname))
    print('  %s ✓（%s、關聯 %s at %s）' % (gname, wid, ln, lo))
print('done')

# 錨（Tim 2026-10-16：「你的船好像都沒有設定錨 先加上吧」「會導致無法拋錨」）—— 夜隼號、風暴角號共用這一支（照 design 資料夾認船）
#   遊戲（Blockside 76_anchor.js anchorsOf）：每舷找一個 meta kind=anchor 的模型（外框中心在那一舷）、鍊子綁 ring；船殼固定點 hawse-P／S ＝ 錨鏈孔。
#   做法照夜燈號（basecamp 階段十九-b）：共用元件 basecamp-frigate-constitution-01m-anchor、pivot ＝ ring、錨從吊錨架（cathead）端下垂直掛著。
#   吊錨架：子作品 -cathead（一舷，右舷 S），左舷 mirror=y 關聯；橫樑垂直船身往外伸，根貼在舷牆外面那一格（⛔ 不跟現有格重疊）。
#   長度：從 k+1 格起搜，取第一個讓「錨的每一格 3×3×3 鄰域裡沒有任何現有格（吊錨架只放過 ring 那兩層）、離每條繩的直線 ≥ ROPE_CLR」的長度；兩舷各驗一次。
#   錨的格 ＝ 來源每一格的格心照 (v + 0.5 − pivot) × scale + at 落到哪一格（模型的近似；scale < 1 會好幾格落同一格）。
# 用法：python -I -X utf8 -B draft_anchors.py <design> <組裝件 list 匯出> <組裝件 list 匯出的 stdout（繩）> <錨來源 list 匯出> <船殼 list 匯出>
#   ⇒ <design>/verify_anchors.json、<design>/masks/anchors/cathead.vox.txt（子作品座標）
import sys, os, json, re, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); F_ASM, F_ROPES, F_SRC, F_HULL = sys.argv[2:6]
SHIP = os.path.basename(os.path.dirname(D))
# scale：錨的線性尺寸照排水量的立方根，對憲法號（scale 1、約 2,200 t）縮 —— ⚠ 估算：憲法號那隻錨的比例與排水量都沒查證（basecamp notes 階段四十一寫「未查證」）
CFG = {
    # xc：艏樓前端、船殼作品自己還有舷牆的那幾站（風暴角號 x 520 以前、夜隼號 x 269 以前；再往前是船頭子作品的 beakhead／head）
    # hawse：船殼作品在那一站、那一高度最外那一格（船頭收窄處、水線與艏樓甲板之間）
    'summit-night-falcon-01m': dict(W=161, wl=15, xc=264, k=2, scale=0.3, disp_t=69, hawse_x=269, hawse_z=39, title='夜隼號 吊錨架（右舷一支）'),
    'summit-stormkaap-01m':    dict(W=261, wl=50, xc=505, k=3, scale=0.85, disp_t=1286, hawse_x=530, hawse_z=92, title='風暴角號 吊錨架（右舷一支）'),
}[SHIP]
W, WL, XC, K, SC = CFG['W'], CFG['wl'], CFG['xc'], CFG['k'], CFG['scale']
CY = (W - 1) / 2.0                    # 中線（格座標）；格心鏡像 c ↔ W − c
PIVOT = [23.5, 16.5, 56.5]            # 來源的 ring 格心（basecamp 登記 ring @23,16,56）
ROPE_CLR = 2.0
SRC_PTS = {'ring': [23, 16, 56], 'crown': [23, 16, 2], 'fluke-a': [23, 2, 12], 'fluke-b': [23, 30, 12]}


def load(f):
    return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


A = load(F_ASM); occ = set(map(tuple, A[:, :3].tolist()))
col = {tuple(r[:3]): int(r[3]) for r in A.tolist()}
HULL = set(map(tuple, load(F_HULL)[:, :3].tolist()))
SRC = load(F_SRC)[:, :3]
ropes = []
for line in open(F_ROPES, encoding='utf-8'):
    if '→' not in line or not line.startswith('- '): continue
    ps = re.findall(r'\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\)', line)
    if len(ps) >= 2:
        ropes.append((re.search(r'`([^`]+)`', line).group(1), np.array(ps[0], float), np.array(ps[1], float)))


RA = np.array([a for _, a, _ in ropes]); RB = np.array([b for _, _, b in ropes])


def rope_min(cells):
    """這些格的格心離每條繩（兩端直線）最近多遠；先篩掉外框離這一團 > 10 格的繩。"""
    P = np.array(sorted(cells), float) + 0.5
    lo, hi = P.min(0) - 10, P.max(0) + 10
    keep = ~((np.minimum(RA, RB) > hi).any(1) | (np.maximum(RA, RB) < lo).any(1))
    if not keep.any(): return 99.0
    a, b = RA[keep], RB[keep]; ab = b - a
    t = np.clip(((P[:, None, :] - a[None]) * ab[None]).sum(2) / np.maximum((ab * ab).sum(1), 1e-9)[None], 0, 1)
    return float(np.linalg.norm(P[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2).min())


def anchor_cells(at):
    c = (SRC + 0.5 - PIVOT) * SC                                    # 兩舷都是同一個擺法（模型不鏡像 —— ⛔ v1 左舷照鏡像算，跟實際放的差 1 格、fluke-a／b 對調）
    return set(map(tuple, np.floor(c + at).astype(int).tolist()))


def side(sgn):
    """sgn +1 ＝ 右舷 S（y 大）、−1 ＝ 左舷 P。回傳 (吊錨架的格, 錨 at, 錨的格, 長度, 讀數)。"""
    xs = range(XC, XC + K)
    # 舷牆頂 ＝ 船殼作品在這一段、這一舷最高的格（⛔ v1 取「最外那幾欄最高的格」⇒ 風暴角號抓到 z 93 的外板最寬處、錨冠落到水線下）
    zt = max(p[2] for p in HULL if p[0] in xs and (p[1] - CY) * sgn > 0)
    zs = range(zt - K + 1, zt + 1)
    blk = [p for p in occ if p[0] in xs and p[2] in zs and (p[1] - CY) * sgn > 0]
    y0 = int(max(abs(p[1] - CY) for p in blk) + 1)             # 吊錨架根：這一塊最外那一格再往外一格（離中線）
    for L in range(K + 1, 61):
        cat = {(x, int(round(CY + sgn * (y0 + i))), z) for x in xs for i in range(L) for z in zs}
        if cat & occ: return None, None, None, L, '吊錨架撞到現有格'
        yc = CY + 0.5 + sgn * (y0 + L - K / 2.0)                # 尖端那 K 格的中心（連續座標）
        at = [XC + K / 2.0, yc, zs[0] - 0.5]                   # ring 格心在吊錨架底下那一格
        cells = anchor_cells(np.array(at))
        near = 0
        for (x, y, z) in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        q = (x + dx, y + dy, z + dz)
                        if q in occ: near += 1
                        elif q in cat and z < zs[0] - 2: near += 1
        if near:
            if os.environ.get('ANC_DEBUG'):
                hit = sorted({q for (x, y, z) in cells for q in [(x + dx, y + dy, z + dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)] if q in occ})
                print('L', L, 'near', near, 'zt', zt, 'y0', y0, '碰到的格 y', min(q[1] for q in hit), '..', max(q[1] for q in hit), 'z', min(q[2] for q in hit), '..', max(q[2] for q in hit))
            continue
        assert min(p[2] for p in cells) > WL + 2, ('錨冠在水線附近或水線下', min(p[2] for p in cells), WL)
        rmin = rope_min(cells | cat)
        if rmin < ROPE_CLR:
            if os.environ.get('ANC_DEBUG'): print('L', L, 'rope', rmin)
            continue
        return cat, at, cells, L, dict(y0=y0, zt=zt, rope_min=round(rmin, 2), z_min=min(p[2] for p in cells))
    return None, None, None, None, '60 格內找不到'


out = {}
for nm, sgn in (('S', 1), ('P', -1)):
    cat, at, cells, L, rd = side(sgn)
    assert cat, (nm, L, rd)
    out[nm] = dict(cat=cat, at=at, cells=cells, L=L, rd=rd)
assert out['S']['L'] == out['P']['L'], ('兩舷長度不同', out['S']['L'], out['P']['L'])   # 左舷是鏡像關聯 ⇒ 要同一支
S = out['S']
assert {(x, W - 1 - y, z) for (x, y, z) in S['cat']} == out['P']['cat'], '左舷不是右舷的鏡像'
assert abs(out['P']['at'][1] - (W - S['at'][1])) < 1e-9

# 吊錨架子作品：框收緊在右舷那一支
cx = sorted({p[0] for p in S['cat']}); cyv = sorted({p[1] for p in S['cat']}); cz = sorted({p[2] for p in S['cat']})
fa = [cx[0], cyv[0], cz[0]]; fs = [cx[-1] - cx[0] + 1, cyv[-1] - cyv[0] + 1, cz[-1] - cz[0] + 1]
rail = [col[p] for p in occ if p[0] in range(XC, XC + K) and p[2] in range(S['rd']['zt'] - 2, S['rd']['zt'] + 1) and p[1] > CY and p in col]
color = max(set(rail), key=rail.count)
os.makedirs(os.path.join(D, 'masks', 'anchors'), exist_ok=True)
mask = 'masks/anchors/cathead.vox.txt'
lines = ['%d,%d,%d,%d' % (x - fa[0], y - fa[1], z - fa[2], color) for (x, y, z) in sorted(S['cat'])]
open(os.path.join(D, mask), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')

# 錨鏈孔：船頭 hawse_x 那一站、hawse_z 那一高度，最外那一格船殼（船殼作品自己的格）
hz = CFG['hawse_z']
hawse = {}
for nm, sgn in (('S', 1), ('P', -1)):
    row = [p for p in HULL if p[0] == CFG['hawse_x'] and p[2] == hz and (p[1] - CY) * sgn > 0]
    assert row, ('那一站那一高度沒有船殼格', nm, CFG['hawse_x'], hz)
    hawse[nm] = list(max(row, key=lambda p: (p[1] - CY) * sgn))
assert hawse['P'][1] == W - 1 - hawse['S'][1], ('錨鏈孔不對稱', hawse)
assert hz > WL, ('錨鏈孔在水線下', hz)

pts = {}
for nm in ('S', 'P'):
    at = np.array(out[nm]['at'])
    pts[nm] = {k: [round(float(v), 3) for v in at + (np.array(p) + 0.5 - PIVOT) * SC] for k, p in SRC_PTS.items()}

V = dict(
    ship=SHIP, scale=SC, scale_why='線性尺寸 ∝ 排水量^(1/3)：(%d / 2200)^(1/3) ≈ %.3f ⇒ 取 %g（⚠ 估算：憲法號那隻錨的比例與排水量都沒查證）' % (CFG['disp_t'], (CFG['disp_t'] / 2200) ** (1 / 3), SC),
    source='basecamp-frigate-constitution-01m-anchor', pivot=PIVOT, meta={'kind': 'anchor', 'anchor': 'bower'},
    cathead=dict(work=SHIP + '-cathead', title=CFG['title'], frame_at=fa, frame_size=fs, color=color, voxels=len(lines), file=mask,
                 sha256=hashlib.sha256(open(os.path.join(D, mask), 'rb').read()).hexdigest(), length=S['L'], section=K,
                 links=[dict(name='吊錨架', at=fa, mirror=''), dict(name='吊錨架-鏡像', at=[fa[0], W - fa[1] - fs[1], fa[2]], mirror='y')]),
    models=[dict(name='錨-' + nm, at=[round(float(v), 3) for v in out[nm]['at']], points=pts[nm],
                 cells=len(out[nm]['cells']), z_min=out[nm]['rd']['z_min'], rope_min=out[nm]['rd']['rope_min']) for nm in ('S', 'P')],
    hawse={'hawse-' + nm: hawse[nm] for nm in ('S', 'P')},
    reads=dict(waterline_z=WL, rail_top_z=S['rd']['zt'], root_off_center=S['rd']['y0'], crown_above_wl=round(pts['S']['crown'][2] - WL, 2),
               ropes_checked=len(ropes), assembly_cells=len(occ)),
)
json.dump(V, open(os.path.join(D, 'verify_anchors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps(V, ensure_ascii=False, indent=1, sort_keys=True))

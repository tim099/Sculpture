# 海鷗號 甲板-main（TASK-0024 步驟 5）：艙底板＋7 張坐板＋船頭平台＋船尾平台 ⇒ 清單 masks/decks/deck_main.vox.txt、
#   甲板 meta decks_meta.tsv、讀數 verify_decks.json、圖 sheet03_decks_v1.png
#   用法：python -I -X utf8 draft_decks.py [--probe=benches.seat_z=1] [--probe=bow_platform.board_z=1]
#   出處：結構照杉心號 basecamp-piragua-01m/design/draft_deck.py（露天小船只有一層、坐板從左舷內面鋪到右舷內面、走路格照遊戲 navBuild），
#         數字全部讀本船 plan.json 的 layout；圖紙字用英文＋Pillow 內建字型。
#   · 只有一層甲板：腰部站在艙底板上（z 7）、兩頭的平台站 z 10、坐板面 z 10 ⇒ 全部一步 3 格、連成一塊，不用梯子（杉心號同）。
#   · 每一排板都只鋪在「船殼線形裡面、船殼格以外」的空氣上 ⇒ 兩頭貼著船殼內面、跟船殼重疊 0。
#   · 桅孔：主桅穿過艙底板與 x 84 那張坐板、前桅（往前傾 8°）穿過船頭平台 ⇒ 桅的格子（rig.py，步驟 7 的 draft_masts.py 用同一支）在哪，板就不鋪哪。
#   · 走路格（遊戲 navBuild：腳下實心、頭上 12 格空、四鄰一步高低差 ≤ 3、只收 floor −2～+3）；艙底板、兩個平台、坐板要連成 1 群。
import sys, os, json, copy, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import rig

sys.stdout.reconfigure(encoding='utf-8')
NX, NY, NZ = 170, 161, 50
HEAD, STEP = 12, 3
COL = {'floor': 209, 'bench': 177, 'platform': 209}     # 209 ＝ (218,145,85) 淺木、177 ＝ (182,145,85)：設計決定（星辰號主甲板同 209）


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load_hull():
    a = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    H = np.zeros((NX, NY, NZ), np.uint8)
    H[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return H


def floor_profile(lay):
    fl, sp, bp = lay['floor'], lay['stern_platform'], lay['bow_platform']
    prof = {}
    for x in range(fl['x0'], fl['x1'] + 1):
        prof[x] = fl['board_z'] + 1
    for pf in (sp, bp):
        for x in range(pf['x0'], pf['x1'] + 1):
            prof[x] = pf['board_z'] + 1
    return dict(sorted(prof.items()))


def floor_meta(prof):
    """x:z 的折線：只留轉折的兩端點（內插回來要跟 prof 一樣）。"""
    xs = list(prof)
    pts = []
    for i, x in enumerate(xs):
        z = prof[x]
        prev = prof.get(x - 1)
        nxt = prof.get(x + 1)
        if prev != z or nxt != z:
            pts.append((x, z))
    return ','.join('%d:%d' % p for p in pts)


def build(plan, H):
    L = HL.Lines(plan)
    YC = L.YC
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    S = L.solid(0, NX - 1, NZ - 1, 0)
    hollow = S & (H == 0)
    D = np.zeros_like(H)
    fl = lay['floor']
    for x in range(fl['x0'], fl['x1'] + 1):
        row = hollow[x, :, fl['board_z']]
        D[x, row, fl['board_z']] = COL['floor']
    b = lay['benches']
    for i in range(b['n']):
        x0 = b['x0'] + i * b['pitch']
        for x in range(x0, x0 + b['w']):
            row = hollow[x, :, b['seat_z']]
            D[x, row, b['seat_z']] = COL['bench']
    for key in ('bow_platform', 'stern_platform'):
        pf = lay[key]
        for x in range(pf['x0'], pf['x1'] + 1):
            row = hollow[x, :, pf['board_z']]
            D[x, row, pf['board_z']] = COL['platform']
    holes = []
    for name in ('main', 'fore'):
        for (x, y, z) in rig.mast_cells(plan, name, YC):
            if z < NZ and D[x, y, z]:
                D[x, y, z] = 0
                holes.append([name, x, y, z])
    return D, holes


def walk(plan, H, D, prof):
    """遊戲 navBuild 的走路格：(x,y,z) 空、(x,y,z-1) 實心、z..z+11 空；只收 floor −2～+3；四鄰高低差 ≤ 3 ⇒ 連通群。"""
    occ = (H > 0) | (D > 0)
    pts = {}
    for x, fz in prof.items():
        for z in range(max(1, fz - 2), fz + 4):
            if z + HEAD > NZ:
                top_free = ~occ[x, :, z:].any(axis=1)
            else:
                top_free = ~occ[x, :, z:z + HEAD].any(axis=1)
            stand = occ[x, :, z - 1] & top_free
            for y in np.where(stand)[0]:
                # 只收船殼裡面：同一欄兩邊都有船殼（排除舷頂上面、船殼外面）
                if occ[x, :y, :].any() and occ[x, y + 1:, :].any():
                    pts.setdefault((x, int(y)), []).append(z)
    idx = {}
    for (x, y), zs in pts.items():
        for z in zs:
            idx[(x, y, z)] = len(idx)
    parent = list(range(len(idx)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for (x, y, z), i in idx.items():
        for dx, dy in ((1, 0), (0, 1)):
            for z2 in pts.get((x + dx, y + dy), []):
                if abs(z2 - z) <= STEP:
                    a, c = find(i), find(idx[(x + dx, y + dy, z2)])
                    if a != c:
                        parent[a] = c
    groups = {}
    for k, i in idx.items():
        groups.setdefault(find(i), []).append(k)
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    return {'groups': len(groups), 'cells': len(idx), 'area_m2': [round(s * 0.01, 2) for s in sizes[:5]]}


def readings(plan, H, D, holes):
    L = HL.Lines(plan)
    YC = L.YC
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    overlap = int(((H > 0) & (D > 0)).sum())
    S = L.solid(0, NX - 1, NZ - 1, 0)
    outside = int(((D > 0) & ~S).sum())
    U = (H > 0) | (D > 0)
    lab, ncomp = ndimage.label(U)
    cav = int((ndimage.binary_fill_holes(U) & ~U).sum())
    G = np.where(D > 0, D, H)
    mdiff = int((G != G[:, ::-1, :]).sum())
    # 每一排板兩頭貼不貼船殼：板那一排最外兩格的外側一格是船殼
    loose = 0
    for x, z in {(int(x), int(z)) for x, y, z in np.argwhere(D > 0)}:
        ys = np.where(D[x, :, z] > 0)[0]
        if not (H[x, ys.min() - 1, z] and H[x, ys.max() + 1, z]):
            loose += 1
    prof = floor_profile(lay)
    W = walk(plan, H, D, prof)
    return {'cells': int((D > 0).sum()), 'colors': {str(c): int((D == c).sum()) for c in np.unique(D[D > 0])},
            'overlap_with_hull': overlap, 'outside_hull_lines': outside, 'rows_not_touching_hull_both_ends': loose,
            'hull_plus_deck': {'cells': int(U.sum()), 'components': int(ncomp), 'cavity_cells': cav, 'mirror_diff_cells': mdiff},
            'mast_hole_cells': holes, 'floor_meta': floor_meta(prof), 'walk': W}


def sheet(plan, H, D, R, path):
    L = HL.Lines(plan)
    YC = L.YC
    s = 6
    img = Image.new('RGB', (NX * s + 120, 760), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 12), 'al-Nawras - new sheet 03: deck-main (floor boards z 6, 7 thwarts z 9, bow platform x 108-141 z 9, stern platform x 18-36 z 9)   0.1 m/cell', fill=(20, 20, 40), font=f)
    ox = 60
    oy = 60 + 30 * s
    d.text((40, 36), '1. centreline section y %d (hull grey, deck coloured)' % YC, fill=(20, 20, 40), font=f)
    for x in range(NX):
        for z in range(30):
            c = D[x, YC, z] or (H[x, YC, z] and 150)
            if not c and D[x, YC + 6, z]:
                c = D[x, YC + 6, z]
            if c:
                col = rgb(int(D[x, YC, z])) if D[x, YC, z] else ((rgb(int(D[x, YC + 6, z])) if D[x, YC + 6, z] else (170, 170, 170)))
                d.rectangle([ox + x * s, oy - (z + 1) * s, ox + x * s + s - 1, oy - z * s - 1], fill=col)
    oy2 = oy + 60 + 20 * s
    d.text((40, oy + 20), '2. plan view of the deck cells (top-most deck cell per column)', fill=(20, 20, 40), font=f)
    for x in range(NX):
        for y in range(YC - 20, YC + 21):
            zs = np.where(D[x, y, :] > 0)[0]
            if len(zs):
                d.rectangle([ox + x * s, oy2 - (y - YC + 1) * s, ox + x * s + s - 1, oy2 - (y - YC) * s - 1], fill=rgb(int(D[x, y, zs.max()])))
            elif H[x, y, :].any():
                d.point((ox + x * s + 2, oy2 - (y - YC) * s - 2), fill=(120, 120, 120))
    rows = ['deck cells %d, overlap with hull %d, outside hull lines %d, rows not touching hull at both ends %d' % (R['cells'], R['overlap_with_hull'], R['outside_hull_lines'], R['rows_not_touching_hull_both_ends']),
            'hull+deck: %d components, cavity %d, mirror diff %d' % (R['hull_plus_deck']['components'], R['hull_plus_deck']['cavity_cells'], R['hull_plus_deck']['mirror_diff_cells']),
            'walk grid (head 12, step 3, floor -2..+3): %d groups, areas m2 %s' % (R['walk']['groups'], R['walk']['area_m2']),
            'deck meta floor = %s, thick 1' % R['floor_meta']]
    for i, r in enumerate(rows):
        d.text((40, oy2 + 150 + i * 18), r, fill=(30, 30, 30), font=f)
    img.save(path)


def main():
    plan = HL.load_plan(HERE)
    probe = [a[len('--probe='):] for a in sys.argv[1:] if a.startswith('--probe=')]
    if probe:
        plan = copy.deepcopy(plan)
        for p in probe:
            k, v = p.split('=')
            sec, key = k.split('.')
            plan['layout'][sec]['v'][key] += int(v)
    H = load_hull()
    D, holes = build(plan, H)
    R = readings(plan, H, D, holes)
    if probe:
        print(json.dumps({'probe': probe, 'walk': R['walk'], 'hull_plus_deck': R['hull_plus_deck'], 'overlap': R['overlap_with_hull']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'decks')
    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, 'deck_main.vox.txt')
    rows = ['%d,%d,%d,%d' % (x, y, z, D[x, y, z]) for x, y, z in np.argwhere(D > 0)]
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 甲板-main（draft_decks.py）x,y,z,color —— at 0,0,0（子作品用整船的框）\n')
        f.write('\n'.join(rows) + '\n')
    R['lists'] = [{'file': 'masks/decks/deck_main.vox.txt', 'cells': len(rows), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}]
    meta = {'kind': 'deck', 'deck': 'main', 'level': 0, 'name': '甲板（艙底板、坐板、船頭船尾平台）', 'floor': R['floor_meta'], 'thick': 1}
    with open(os.path.join(HERE, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('link\t甲板-main\t%s\n' % json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    with open(os.path.join(HERE, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, H, D, R, os.path.join(HERE, 'sheet03_decks_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k != 'mast_hole_cells'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

# 蠍子號 新圖紙 03（TASK-0023 步驟 5）：甲板 ⇒ 清單 masks/decks/{deck_main,bow}.vox.txt、甲板 meta decks_meta.tsv、
#   讀數 verify_decks.json、圖 sheet03_decks_v1.png
#   用法：python -I -X utf8 draft_decks.py [--probe=corsia.h=3] [--probe=rambade.clear=4]   （probe ⇒ layout 的數字加減，只印走路格；⛔ 不寫檔）
#   出處：走路格與 floor 折線照海鷗號 claude-felucca-01m/design/draft_decks.py（遊戲 navBuild：腳下實心、頭上 12 格空、一步 ≤ 3、只收 floor −2～+3）；
#         槳帆船的 walk／walk_y 照越嶺號 kotoko-fusta-01m/design/draft_hold.py 與 Ship_Decks §9.3（皇家號）。
#   改的地方：件的格子不在這裡產 —— 甲板、中央走道、划手座、腳踏、艙口格柵照 layout.py 的 deck、船首低平台照 rambade（步驟 3 的新圖紙 02 同一支）；
#            走路格分兩種高度：walk_y 那幾欄照 walk（中央走道頂與船首低平台）、其他照 floor（甲板面）。
#   · 只有一層甲板 main（plan.json 的 decks）：船首低平台掛在甲板-main 底下；艙底不做、艙口是格柵。
import sys, os, json, copy, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import layout as LY

sys.stdout.reconfigure(encoding='utf-8')
HEAD, STEP = 12, 3          # 遊戲 42_hands.js：NAV_HEAD 12、NAV_DZ 3


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def polyline(prof):
    """{x: z} ⇒ "x:z,…"：只留轉折的兩端點（線性內插回來要跟 prof 一樣）。"""
    pts = []
    for x, z in prof.items():
        if prof.get(x - 1) != z or prof.get(x + 1) != z:
            pts.append((x, z))
    return ','.join('%d:%d' % p for p in pts)


def interp(s, x):
    pts = [tuple(map(int, p.split(':'))) for p in s.split(',')]
    if x < pts[0][0] or x > pts[-1][0]:
        return None
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return z0 if x1 == x0 else int(round(z0 + (z1 - z0) * (x - x0) / (x1 - x0)))
    return pts[-1][1]


def profiles(K, deck, bow, poop=None):
    """floor：甲板面（中線那一欄甲板最上一格 ＋1；中央走道底下照甲板拱算）、船首低平台照平台板、艉台照艉台板（步驟 6 起）；
       walk：中央走道頂 ＋1（含兩頭台階）與船首低平台板 ＋1。"""
    YC = K.YC
    co = K.P['corsia']
    rx0, rx1, zt, d_in, wf = LY.rambade_geo(K)
    floor, walk = {}, {}
    for x in range(K.SX):
        if rx0 <= x <= rx1:
            floor[x] = walk[x] = zt + 1
            continue
        if K.hw_deck(x) < 2 or not deck[x, :, :].any():
            continue
        floor[x] = K.deck_top(x, 0) + 1
        if poop is not None and poop[x, YC, :].any():
            floor[x] = int(np.where(poop[x, YC, :] == K.C['deck'])[0].max()) + 1   # 艉台板面 ＋1（燈桿那一欄照板面，不照桿頂）
        if co['x0'] - 3 <= x <= co['x1']:
            zs = np.where(deck[x, YC, :] > 0)[0]
            walk[x] = int(zs.max()) + 1
    return floor, walk


def nav(K, occ, floor, walk, walk_half):
    """遊戲 navBuild 的走路格：(x,y,z) 空、(x,y,z−1) 實心、z..z+11 空；高度只收 參考面 −2～+3（walk_y 那幾欄的參考面是 walk）；
       只收船殼裡面（同一欄兩邊都有實心）；四鄰一步 ≤ 3 ⇒ 連通群。"""
    YC = K.YC
    NZ = occ.shape[2]
    c = np.concatenate([np.zeros(occ.shape[:2] + (1,), np.int32), np.cumsum(occ, axis=2, dtype=np.int32)], axis=2)
    colany = occ.any(axis=2)                                  # (x, y) 那一欄有沒有實心
    left = np.cumsum(colany, axis=1) - colany                 # y 左邊（較小的 y）有幾欄有實心
    right = colany[:, ::-1].cumsum(axis=1)[:, ::-1] - colany
    pts = {}
    for x, fz in floor.items():
        for y in np.where((left[x] > 0) & (right[x] > 0))[0]:
            ref = walk[x] if (x in walk and abs(y - YC) <= walk_half) else fz
            for z in range(max(1, ref - 2), ref + 4):
                if z + HEAD > NZ or not occ[x, y, z - 1] or c[x, y, z + HEAD] - c[x, y, z]:
                    continue
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
    order = sorted(groups.values(), key=len, reverse=True)
    main = set(order[0]) if order else set()
    return {'groups': len(groups), 'cells': len(idx), 'main_m2': round(len(main) * 0.01, 2),
            'others_m2_top5': [round(len(g) * 0.01, 2) for g in order[1:6]],
            'others_over_1m2': sum(1 for g in order[1:] if len(g) >= 100)}, main


def build(plan):
    K = LY.Ctx(plan)
    pieces, lpts, clipped = LY.assemble(K)
    return K, pieces


def readings(plan, K, pieces):
    YC = K.YC
    deck, bow, poop = pieces['deck'], pieces['rambade'], pieces['poop']
    H = K.hull
    walk_half = int(V(plan['decks'])['walk_y_half'])
    floor, walk = profiles(K, deck, bow, poop)
    U = (H > 0) | (deck > 0) | (bow > 0) | (poop > 0)       # 篷是外部模型 deco=1：遊戲不拿它擋人（Ship_Fittings §9.9）⇒ 走路格不算它
    lab, ncomp = ndimage.label(U)
    cav = int((ndimage.binary_fill_holes(U) & ~U).sum())
    G = np.where(poop > 0, poop, np.where(bow > 0, bow, np.where(deck > 0, deck, H)))
    N, main = nav(K, U, floor, walk, walk_half)
    co = K.P['corsia']
    rx0, rx1, zt, d_in, wf = LY.rambade_geo(K)
    h = K.P['deck']['hatches'][0]
    probes = {                                               # 走得到的地方都要在最大的那一群裡
        'corsia_mid': (195, YC, walk[195]),
        'corsia_aft_step': (co['x0'] - 2, YC, walk[co['x0'] - 2]),
        'bow_platform_mid': ((rx0 + rx1) // 2, YC, zt + 1),
        'deck_beside_grating': (h['x0'] + 2, YC + h['half'] + 3, K.deck_top(h['x0'] + 2, h['half'] + 3) + 1),
        'poop_mid': (40, YC, floor[40]),
    }
    for g in K.P['guns']:
        probes['gun_' + g['id']] = (int(g['x']), YC + int(g['dy']), zt + 1)
    pr = {k: {'at': list(v), 'in_main_group': v in main} for k, v in probes.items()}
    # 格柵：孔幾個、孔底下是不是船艙的空氣（通氣）
    gx = range(h['x0'], h['x1'] + 1)
    holes = [(x, dy) for x in gx for dy in range(-h['half'], h['half'] + 1) if not deck[x, YC + dy, K.deck_top(x, abs(dy))]]
    return {
        'cells': {'deck_main': int((deck > 0).sum()), 'bow': int((bow > 0).sum()), 'poop': int((poop > 0).sum())},
        'colors': {'deck_main': {str(c): int((deck == c).sum()) for c in np.unique(deck[deck > 0])},
                   'bow': {str(c): int((bow == c).sum()) for c in np.unique(bow[bow > 0])}},
        'overlap': {'deck_hull': int(((deck > 0) & (H > 0)).sum()), 'bow_hull': int(((bow > 0) & (H > 0)).sum()), 'deck_bow': int(((deck > 0) & (bow > 0)).sum()),
                    'poop_hull': int(((poop > 0) & (H > 0)).sum()), 'poop_deck': int(((poop > 0) & (deck > 0)).sum())},
        'hull_deck_bow': {'cells': int(U.sum()), 'components': int(ncomp), 'cavity_cells': cav, 'mirror_diff_cells': int((G != G[:, ::-1, :]).sum())},
        'grating': {'x': [h['x0'], h['x1']], 'half': h['half'], 'holes': len(holes)},
        'floor': polyline(floor), 'walk': polyline(walk), 'walk_y': '%d:%d' % (YC - walk_half, YC + walk_half),
        'corsia_top_to_platform_step': (zt + 1) - walk[co['x1']],
        'nav': N, 'probes': pr,
    }


def sheet(plan, K, pieces, R, path):
    YC = K.YC
    deck, bow, H = pieces['deck'], pieces['rambade'], K.hull
    s = 3
    W = K.SX * s + 120
    img = Image.new('RGB', (W, 620), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 12), '%s - new sheet 03: deck main (deck, corsia, benches, footrests, hatch grating) + low bow platform   0.1 m/cell' % plan['title_en'], fill=(20, 20, 40), font=f)
    ox, oy = 60, 60 + 45 * s
    d.text((40, 36), '1. centreline section y %d (hull grey, deck/platform coloured); red = floor meta, blue = walk meta' % YC, fill=(20, 20, 40), font=f)
    for x in range(K.SX):
        for z in range(45):
            c = bow[x, YC, z] or deck[x, YC, z]
            col = rgb(int(c)) if c else ((170, 170, 170) if H[x, YC, z] else None)
            if col:
                d.rectangle([ox + x * s, oy - (z + 1) * s, ox + x * s + s - 1, oy - z * s - 1], fill=col)
    for key, colr in (('floor', (200, 40, 40)), ('walk', (40, 90, 200))):
        pts = [(ox + x * s, oy - z * s) for x, z in (tuple(map(int, p.split(':'))) for p in R[key].split(','))]
        d.line(pts, fill=colr, width=1)
    oy2 = oy + 40 + 2 * 32 * s
    d.text((40, oy + 14), '2. plan view (top-most deck / platform cell per column; |dy| <= 32)', fill=(20, 20, 40), font=f)
    for x in range(K.SX):
        for y in range(YC - 32, YC + 33):
            A = np.maximum(deck[x, y, :], bow[x, y, :])
            zs = np.where(A > 0)[0]
            if len(zs):
                d.rectangle([ox + x * s, oy2 - (y - YC + 32 + 1) * s, ox + x * s + s - 1, oy2 - (y - YC + 32) * s - 1], fill=rgb(int(A[zs.max()])))
    N = R['nav']
    rows = ['deck_main %d cells, bow platform %d cells; overlap deck/hull %d, bow/hull %d, deck/bow %d' % (R['cells']['deck_main'], R['cells']['bow'], R['overlap']['deck_hull'], R['overlap']['bow_hull'], R['overlap']['deck_bow']),
            'hull+deck+bow+poop: %d cells, %d components, cavity %d, mirror diff %d; hatch grating x %d-%d, %d holes' % (R['hull_deck_bow']['cells'], R['hull_deck_bow']['components'], R['hull_deck_bow']['cavity_cells'], R['hull_deck_bow']['mirror_diff_cells'], R['grating']['x'][0], R['grating']['x'][1], R['grating']['holes']),
            'walk grid (game navBuild: head 12, step 3, ref -2..+3; walk_y %s): main group %.2f m2, %d groups, other groups >= 1 m2: %d' % (R['walk_y'], N['main_m2'], N['groups'], N['others_over_1m2']),
            'in main group: ' + ', '.join('%s %s' % (k, 'yes' if v['in_main_group'] else 'NO') for k, v in R['probes'].items()),
            'deck meta: deck=main level 0 thick 2; corsia end -> platform step %d cell(s)' % R['corsia_top_to_platform_step']]
    for i, r in enumerate(rows):
        d.text((40, oy2 + 16 + i * 18), r, fill=(30, 30, 30), font=f)
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
    K, pieces = build(plan)
    R = readings(plan, K, pieces)
    if probe:
        print(json.dumps({'probe': probe, 'nav': R['nav'], 'probes': {k: v['in_main_group'] for k, v in R['probes'].items()},
                          'step': R['corsia_top_to_platform_step'], 'hull_deck_bow': R['hull_deck_bow']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'decks')
    os.makedirs(out, exist_ok=True)
    R['lists'] = []
    for name, a, title in (('deck_main', pieces['deck'], '甲板-main（甲板、中央走道、划手座、腳踏、艙口格柵）'), ('bow', pieces['rambade'], '船首低平台')):
        fn = os.path.join(out, name + '.vox.txt')
        rows = ['%d,%d,%d,%d' % (x, y, z, a[x, y, z]) for x, y, z in np.argwhere(a > 0)]
        with open(fn, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 蠍子號 %s（draft_decks.py）x,y,z,color —— at 0,0,0（子作品用船殼的框）\n' % title)
            fh.write('\n'.join(rows) + '\n')
        R['lists'].append({'file': 'masks/decks/%s.vox.txt' % name, 'cells': len(rows), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})
    dm = V(plan['decks'])['main']
    meta = {'kind': 'deck', 'deck': dm['deck'], 'level': dm['level'], 'name': dm['name'], 'floor': R['floor'], 'walk': R['walk'], 'walk_y': R['walk_y'], 'thick': dm['thick']}
    with open(os.path.join(HERE, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('link\t甲板-main\t%s\n' % json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    with open(os.path.join(HERE, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    sheet(plan, K, pieces, R, os.path.join(HERE, 'sheet03_decks_v1.png'))
    print(json.dumps(R, ensure_ascii=False)[:4000])


if __name__ == '__main__':
    main()

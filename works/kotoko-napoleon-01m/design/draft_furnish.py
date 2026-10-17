# 拿破崙號 階段十五 內部陳設第一批（TASK-0682 裝飾 meta；Tim 2026-10-17「試著繼續裝修拿破崙號吧(裝飾可以額外標meta 之後遊戲會有性能選項隱藏裝飾)」）
#   四種陳設，全部是外部模型、meta deco=1（造船規格 §9.9：載入時就拿掉、不算重量、不被打）—— 沒有功能 kind（水泵遊戲有功能 ⇒ 不在這批）。
#   每種一件子作品（0.05 m／格，掛船上 scale 0.5；pivot ＝ 底面中心），擺放照 draft_fittings.py（階段九）：
#     現況 ＝ 組裝件 links=all 的格 ＋ 所有模型外框；取樣點（每格格心＋八角）不落在現況、保留區（梯子端點）；腳下：底層每格正下方是實心。
#   爐灶（galley）：上砲甲板中線、前艙口（x 698）與前桅（x 757）之間 —— 同時期法國戰列艦的 cuisine 在前桅後面（研究 agent 2026-10-16；本艦沒有艙內圖，設計決定）。
#     煙管往上接到上甲板底下（照那一格往上第一個實心量，⇒ 煙管頂貼著）。
#   錨鏈繫纜柱（bitts）：上砲甲板中線、錨鏈孔（hawse x 878）後面，離 target 最近的。
#   桅腳繫索栓圍欄（fife rail）：上甲板主桅、前桅，框的中心 ＝ 桅軸。
#   砲彈架（shot rack）：下砲甲板、上砲甲板主艙口兩舷的圍欄外側，P 舷 mirror=y。
#   輸出：masks/furnish/<件>.vox.txt（子作品自己的座標）、furnish_placement.json、verify_furnish.json。用法：python -I -X utf8 draft_furnish.py <design>
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio as DB

NX, NY, NZ = 1200, 400, 260
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
SC = 0.5                                                                  # 子作品 0.05 m ⇒ 船上 0.1 m
WOOD, PALE, IRON, BLACK, BRICK, FIRE, COPPER = 136, 177, 73, 36, 132, 232, 172   # BLACK：鑄鐵（同鍋爐的暗鐵色；37 畫出來是藏青）
DECO = {'deco': 1}


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


# ── 四件的格（子作品座標，0.05 m）──
def galley(chim_top):
    """爐灶：磚座 44×32×2、鐵身 42×30（z 2–23）、上下一圈灰邊、朝船尾那面兩扇烤爐門＋中間火門、頂上兩只銅鍋、後面一根煙管（r 3）到 chim_top。"""
    C = {}
    for x in range(44):
        for y in range(32):
            for z in range(2):
                C[(x, y, z)] = BRICK
    for x in range(1, 43):
        for y in range(1, 31):
            for z in range(2, 24):
                edge = x in (1, 42) or y in (1, 30)
                C[(x, y, z)] = IRON if (z in (2, 23) and edge) else BLACK
    for y0, y1 in ((4, 12), (19, 27)):                                    # 烤爐門（凸出 1 格；船尾那面 x 0）
        for y in range(y0, y1 + 1):
            for z in range(10, 19):
                C[(0, y, z)] = IRON if (y in (y0, y1) or z in (10, 18)) else BLACK
    for y in range(13, 19):                                               # 火門
        for z in range(4, 9):
            C[(0, y, z)] = IRON if (y in (13, 18) or z in (4, 8)) else FIRE
    for cy in (9, 22):                                                    # 銅鍋
        for x in range(9, 20):
            for y in range(cy - 5, cy + 6):
                d = math.hypot(x - 14, y - cy)
                if d <= 5.2:
                    for z in range(24, 30):
                        C[(x, y, z)] = COPPER
                if d <= 3.2:
                    C[(x, y, 30)] = IRON
    for x in range(31, 38):                                               # 煙管
        for y in range(13, 20):
            if math.hypot(x - 34, y - 16) <= 3.2:
                for z in range(24, chim_top + 1):
                    C[(x, y, z)] = BLACK if z < chim_top - 1 else IRON
    return C


def bitts():
    """繫纜柱：兩根 9×9 柱（間距 32，高 24，頂上灰鐵帽 2 格）＋往船頭那一面的橫木 6×41×7（z 12–18）。"""
    C = {}
    for y0 in (0, 32):
        for x in range(9):
            for y in range(y0, y0 + 9):
                for z in range(24):
                    C[(x, y, z)] = IRON if z >= 22 else WOOD
    for x in range(9, 15):
        for y in range(41):
            for z in range(12, 19):
                C[(x, y, z)] = WOOD
    return C


def fiferail():
    """繫索栓圍欄：39×39 的方框（中心是桅），柱 3×3 在四角與四邊中點（z 0–13），欄杆一圈 3 寬（z 14–15），繫索栓每 4 格一根（z 16–18）。"""
    C = {}
    R0, R1 = 17, 19
    for dx in range(-R1, R1 + 1):
        for dy in range(-R1, R1 + 1):
            m = max(abs(dx), abs(dy))
            if R0 <= m <= R1:
                for z in (14, 15):
                    C[(dx + R1, dy + R1, z)] = WOOD
                if m == 18 and ((abs(dx) == 18 and dy % 4 == 0) or (abs(dy) == 18 and dx % 4 == 0)):
                    for z in (16, 17, 18):
                        C[(dx + R1, dy + R1, z)] = PALE
            post = lambda v: v <= -R0 or v >= R0 or -1 <= v <= 1
            if R0 <= m <= R1 and post(dx) and post(dy):
                for z in range(14):
                    C[(dx + R1, dy + R1, z)] = WOOD
    return C


def shotrack():
    """砲彈架：板 54×4×6（z 0–5），上面一排 32 磅彈（3×3×3 去角，z 6–8），每 4 格一顆。"""
    C = {}
    for x in range(54):
        for y in range(4):
            for z in range(6):
                C[(x, y, z)] = WOOD
    for cx in range(2, 53, 4):
        for x in (cx - 1, cx, cx + 1):
            for y in (0, 1, 2):
                for z in (6, 7, 8):
                    corner = (x != cx) + (y != 1) + (z != 7)
                    if corner <= 2:
                        C[(x, y, z)] = BLACK
    return C


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(design)
    A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    solid = occ.copy()                                                    # 腳下與煙管頂只看格子
    own = {'甲板-upper/爐灶', '甲板-upper/繫纜柱', '甲板-spar/繫索栓圍欄-main', '甲板-spar/繫索栓圍欄-fore',
           '甲板-lower/砲彈架-S', '甲板-lower/砲彈架-P', '甲板-upper/砲彈架-S', '甲板-upper/砲彈架-P'}
    PM = [m for m in parts() if m['path'] not in own]                    # 本階段自己掛的不算（套用之後重跑讀到的還是同一份）
    for m in PM:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    reserved = np.zeros((NX, NY, 4), bool)                                # 梯子端點（每一層）前後 6、兩側 4 格
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    lv = {'orlop': 0, 'lower': 1, 'upper': 2, 'spar': 3}
    for nm, L in sorted(LP.items()):
        for end, deck in (('head', L['up']), ('foot', L['lo'])):
            if deck in lv:
                x, y, _ = L['points'][end]
                reserved[x - 6:x + 7, y - 4:y + 5, lv[deck]] = True
    yc = plan['space']['yc'] + 0.5

    def samp(C):
        a = np.array(list(C.keys()), float)
        return (a[:, None, :] + OFFS[None]).reshape(-1, 3), a

    def size(C):
        a = np.array(list(C.keys()))
        return [int(v) for v in a.max(0) + 1]

    def world(Q, piv, at, mir):
        q = (Q - np.asarray(piv, float)) * SC
        if mir:
            q[:, 1] = -q[:, 1]
        return q + np.asarray(at, float)

    def test(C, piv, at, mir, deck):
        S, cells = samp(C)
        W = world(S, piv, at, mir)
        i = np.floor(W).astype(int)
        if (i < 0).any() or (i[:, 2] >= NZ).any() or occ[i[:, 0], i[:, 1], i[:, 2]].any() or reserved[i[:, 0], i[:, 1], lv[deck]].any():
            return None
        bot = cells[cells[:, 2] == 0]
        b = np.floor(world(bot + [0.5, 0.5, 0.5], piv, at, mir)).astype(int)
        sup = int(solid[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        lo, hi = W.min(0), W.max(0)
        return {'support': [sup, len(b)], 'box': [round(float(v), 3) for v in list(lo) + list(hi)]}

    def commit(C, piv, at, mir):
        S, _ = samp(C)
        i = np.floor(world(S, piv, at, mir)).astype(int)
        occ[i[:, 0], i[:, 1], i[:, 2]] = True

    def zd(deck, x):
        return float(LY.deck_z(plan, deck, x)) + 1.0

    rows, pieces, log = [], {}, {}

    def put(piece, C, name, deck, xs, target, ys=(0.0,), mirror=False, full=True, cy=None):
        sz = size(C)
        piv = [sz[0] / 2.0, sz[1] / 2.0 if cy is None else cy, 0]
        cands = []
        for x in xs:
            for dy in ys:
                at = [x, yc + dy, zd(deck, x)]
                r = test(C, piv, at, mirror, deck)
                if r and (r['support'][0] == r['support'][1] if full else r['support'][0] > 0):
                    cands.append((abs(x - target) + abs(dy) * 0.01, at, r))
        assert cands, '%s 擺不下' % name
        _, at, r = min(cands, key=lambda c: (c[0], c[1][0], c[1][1]))
        commit(C, piv, at, mirror)
        pieces[piece] = {'cells': len(C), 'size': sz, 'pivot': piv}
        rows.append({'model': name, 'piece': piece, 'deck_work': 'kotoko-napoleon-01m-deck-' + deck, 'path': '甲板-%s/%s' % (deck, name),
                     'at': [round(v, 3) for v in at], 'mirror': 'y' if mirror else 'none', 'pivot': piv, 'scale': SC, 'meta': DECO,
                     'candidates': len(cands), **r})
        log[name] = [min(c[1][0] for c in cands), max(c[1][0] for c in cands)]
        return at

    def halves(a, b):
        return [a + k * 0.5 for k in range(int((b - a) / 0.5) + 1)]

    # 爐灶：先用 1 格煙管擺，擺好之後照頭上第一個實心把煙管接上去、重擺同一點驗一次
    G0 = galley(25)
    at = put('galley', G0, '爐灶', 'upper', halves(700, 735), 715)
    rows.pop(); pieces.pop('galley')
    cx, cyy = int(math.floor(at[0] + (34 + 0.5 - 22) * SC)), int(math.floor(at[1] + (16 + 0.5 - 16) * SC))
    z = int(at[2])
    while z < NZ and not solid[cx, cyy, z]:
        z += 1
    top = int(math.floor((z - at[2]) / SC)) - 1                          # 子作品座標：頭上那一格的底面 ⇒ 煙管最後一格
    G = galley(top)
    S, _ = samp(G)
    i = np.floor(world(S, [22.0, 16.0, 0], at, False)).astype(int)
    occ[i[:, 0], i[:, 1], i[:, 2]] = False                                # 撤掉 1 格版
    r = test(G, [22.0, 16.0, 0], at, False, 'upper')
    assert r and r['support'][0] == r['support'][1], '爐灶接上煙管之後撞到 %s' % r
    commit(G, [22.0, 16.0, 0], at, False)
    pieces['galley'] = {'cells': len(G), 'size': size(G), 'pivot': [22.0, 16.0, 0], 'chimney_to_z': z}
    rows.append({'model': '爐灶', 'piece': 'galley', 'deck_work': 'kotoko-napoleon-01m-deck-upper', 'path': '甲板-upper/爐灶', 'at': [round(v, 3) for v in at],
                 'mirror': 'none', 'pivot': [22.0, 16.0, 0], 'scale': SC, 'meta': DECO, **r})
    put('bitts', bitts(), '繫纜柱', 'upper', halves(800, 860), 838)
    FR = fiferail()
    for key in ('main', 'fore'):
        mx = float(LY.mast_axis_x(plan, key, zd('spar', next(m['x'] for m in plan['masts']['rows'] if m['key'] == key))))
        put('fiferail', FR, '繫索栓圍欄-' + key, 'spar', [round(mx * 2) / 2.0], mx, full=False)
    SR = shotrack()
    hz = next(h for h in plan['decks_build']['hatches'] if h['name'] == '主艙口')
    for deck in ('lower', 'upper'):
        for side, mir in (('S', False), ('P', True)):
            sgn = -1 if mir else 1
            put('shotrack', SR, '砲彈架-' + side, deck, [(hz['x0'] + hz['x1'] + 1) / 2.0], (hz['x0'] + hz['x1'] + 1) / 2.0,
                ys=[sgn * (hz['half'] + d) for d in halves(1.5, 8)], mirror=mir, cy=0.0)

    gens = {'galley': lambda: galley(pieces['galley']['size'][2] - 1), 'bitts': bitts, 'fiferail': fiferail, 'shotrack': shotrack}
    for k, P in sorted(pieces.items()):
        C = gens[k]()
        assert len(C) == P['cells'], k
        n, sha = DB.write_local(os.path.join(design, 'masks', 'furnish', k + '.vox.txt'), C, (0, 0, 0), '# 拿破崙號 陳設 %s（0.05 m；draft_furnish.py）\n' % k)
        P['sha256'] = sha
    out = {'note': 'draft_furnish.py（階段十五）—— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框 %d' % (len(A), len(PM)), 'pieces': pieces, 'rows': rows, 'ranges': log}
    for f, d in (('furnish_placement.json', {'pieces': pieces, 'rows': rows}), ('verify_furnish.json', out)):
        with open(os.path.join(design, f), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write('\n')
    for r in rows:
        print(r['path'], 'at', r['at'], r['mirror'], 'support', r['support'], 'box', r['box'])
    print('件', {k: (v['cells'], v['size']) for k, v in pieces.items()}, '範圍', log)


if __name__ == '__main__':
    main()

# 松島號 裝飾（Tim 2026-10-23「然後加上裝飾吧(參考 拿破崙號)」；造船規格 §9.9 deco=1）
#   照拿破崙號 階段十五 draft_furnish.py（kotoko）的做法：全部是外部模型、meta deco=1（畫質「裝飾」關著載入時就拿掉；開著只畫、不算重量、不被打）。
#   擺放：現況 ＝ 組裝件 links=all 的格 ＋ 所有模型外框；取樣點（每格格心＋八角）不落在現況與保留區（梯子兩端）；腳下：底層每格正下方是實心。
#   四種：
#     菊花紋章（crest，本船的個性裝飾，新做）：艏柱頂、朝船頭 —— 照片 P1896 船首看得到；十六瓣八重表菊（前 16 瓣金、後 16 瓣暗金、中心圓）。直徑 1.2 m 是設計決定。
#       掛在組裝件上（不是甲板）；背面貼著艏柱（背後那一格要有實心）。
#     錨鏈繫纜柱（bitts）：⭐ 引用拿破崙號 kotoko-napoleon-01m-bitts（造船規格 §2.1 現有元件），recolor 木 → 黑（鋼船）；船首樓中線、錨（x 938–963）後面。
#     雙柱繫纜樁（bollard，通用部件，新做 —— 現有元件沒有鋼船時代的繫纜樁）：船首樓船頭、船首樓後端、後甲板船尾，兩舷各一（P mirror=y）。
#     12 cm 速射砲備便彈架（rack，通用部件，新做 —— 拿破崙號的砲彈架是圓彈，對不上 1894 年的速射砲）：中甲板 12 cm 砲列，兩門砲之間貼著舷側，兩舷各四。
#   輸出：<out>/furnish/<件>.vox.txt（子作品自己的座標，0.05 m）、<out>/furnish_placement.json、<out>/verify_furnish.json。
#   用法：python -I -X utf8 -B draft_furnish.py <輸出資料夾>
import sys, os, json, math, tempfile, subprocess, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['params']
NX, NY, NZ = P['frame']
YC = (NY - 1) // 2                                                        # 鏡像 y ↔ 180 − y ⇒ 鏡面在 y 90.5
YM = YC + 0.5
C = P['colors']
GOLD, BRASS = 248, C['brass']                                             # 金：拿破崙號 trailboard 的色
BLACK, IRON, WOOD, GREY, BRONZE = 36, C['iron'], C['beam'], C['grey'], C['bronze']   # BLACK：鑄鐵 36（船殼的 37 畫成小件是藏青；拿破崙號爐灶同一個坑）
WF1, WU1, WM1 = P['z_fc_deck'] + 1, P['z_upper_deck'] + 1, P['z_middle_deck'] + 1
W = 'ridge-001-matsushima-01m'; ASM = W + '-assembly'
BITTS_SRC = 'kotoko-napoleon-01m-bitts'
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
SC = 0.5                                                                  # 子作品 0.05 m ⇒ 船上 0.1 m
DECO = {'deco': 1}
MAT = {'crest': 'brass'}   # 哪幾件畫成金屬反光（模型 meta material，TASK-0859；Tim 2026-10-23「船頭標誌可以改金屬嗎」）：菊花紋章是鍍金的銅


def cli(*a):
    args = ['senate', 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode: raise SystemExit((r.stdout + r.stderr)[-900:])
    return r.stdout


def export_list(work, links):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'l.txt').replace('\\', '/')
        cli(('op', 'export'), ('format', 'list'), ('work', work), ('out', f), ('links', links))
        return np.array([[int(v) for v in l.split(',')[:4]] for l in open(f, encoding='utf-8') if l[:1].isdigit()], np.int32)


def export_models(work):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'p.json').replace('\\', '/')
        cli(('op', 'export'), ('format', 'parts'), ('work', work), ('out', f))
        return json.load(open(f, encoding='utf-8'))['models']


# ── 新做的三件（子作品座標，0.05 m）──
def crest():
    """菊花紋章：x 0–3 ＝ 背 → 前（朝船頭），y、z 0–23 ＝ 盤面（直徑 24 格 ＝ 1.2 m）。
    後 16 瓣（暗金，尖在 θ ＝ π/16 ＋ kπ/8）鋪底；前 16 瓣（金，尖在 kπ/8）凸一格、瓣中間再凸一格；瓣與瓣之間一道暗金的縫；中心圓凸到 x 3。"""
    Cc = {}
    R = 12.0
    for y in range(24):
        for z in range(24):
            dy, dz = y + 0.5 - 12, z + 0.5 - 12
            r = math.hypot(dy, dz); t = math.atan2(dz, dy)
            rf = R * (0.80 + 0.20 * abs(math.cos(8 * t)) ** 0.6)            # 前瓣外緣（圓頭）
            rb = R * (0.78 + 0.18 * abs(math.sin(8 * t)) ** 0.6)            # 後瓣外緣
            seam = abs(math.sin(8 * t)) > 0.9 and r > 0.3 * R             # 前瓣之間的縫
            if r <= 0.27 * R:
                for x in range(4): Cc[(x, y, z)] = GOLD
            elif r <= rf:
                Cc[(0, y, z)] = BRASS if seam else GOLD
                if not seam:
                    Cc[(1, y, z)] = GOLD
                    if r <= 0.82 * rf and abs(math.sin(8 * t)) < 0.55: Cc[(2, y, z)] = GOLD
            elif r <= rb:
                Cc[(0, y, z)] = BRASS
    return Cc


def bollard():
    """雙柱繫纜樁：底板 24×10×1、兩根柱（中心 x 5.5／18.5，半徑 3.6，z 1–11）＋頂上外張的帽（半徑 4.4，z 12–13，帽頂灰鐵）。柱沿 x（船長方向）排。"""
    Cc = {}
    for x in range(24):
        for y in range(10):
            Cc[(x, y, 0)] = BLACK
    for cx in (5.5, 18.5):
        for x in range(24):
            for y in range(10):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - 5.0)
                if d <= 3.6:
                    for z in range(1, 12): Cc[(x, y, z)] = BLACK
                if d <= 4.4:
                    Cc[(x, y, 12)] = BLACK
                    Cc[(x, y, 13)] = IRON
    return Cc


def rack():
    """12 cm 速射砲備便彈架：木底 36×8×2、背板（y 7，z 2–13）、兩頭側板（z 2–9）、前面一道擋條（y 0，z 6–7）；
    八發定裝彈直立（每 4 格一發，3×3）：黃銅藥筒 z 2–7、彈帶（青銅）z 8、彈身（灰）z 9–11、彈頭 z 12。"""
    Cc = {}
    for x in range(36):
        for y in range(8):
            for z in range(2): Cc[(x, y, z)] = WOOD
        for z in range(2, 14): Cc[(x, 7, z)] = WOOD
        for z in (6, 7): Cc[(x, 0, z)] = WOOD
    for x in (0, 35):
        for y in range(8):
            for z in range(2, 10): Cc[(x, y, z)] = WOOD
    for k in range(8):
        cx = 3 + 4 * k + 1                                                # 4、8 … 32
        for x in (cx - 1, cx, cx + 1):
            for y in (2, 3, 4):
                corner = (x != cx) and (y != 3)
                for z in range(2, 8): Cc[(x, y, z)] = BRASS
                Cc[(x, y, 8)] = BRONZE
                for z in (9, 10, 11):
                    if not (corner and z == 11): Cc[(x, y, z)] = GREY
        Cc[(cx, 3, 12)] = GREY
    return Cc


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    out = os.path.abspath(sys.argv[1]); os.makedirs(os.path.join(out, 'furnish'), exist_ok=True)
    A = export_list(ASM, 'all')
    A = A[(A[:, 2] < NZ) & (A[:, 0] >= 0) & (A[:, 1] >= 0)]
    solid = np.zeros((NX, NY, NZ), bool)
    solid[A[:, 0], A[:, 1], A[:, 2]] = True
    occ = solid.copy()
    mine = lambda p: p == '菊花紋章' or p.split('/')[-1].startswith(('錨鏈繫纜柱', '繫纜樁-', '備便彈架-'))
    MD = [m for m in export_models(ASM) if not mine(m['path'])]          # 這一支自己掛的不算（套用之後重跑讀到的還是同一份）
    for m in MD:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    reserved = np.zeros((NX, NY, NZ), bool)                               # 梯子兩端：前後 6、兩側 4、腳下 1 到頭上 20 格
    LA = json.load(open(os.path.join(HERE, '..', '..', W + '-ladders', 'anchors.json'), encoding='utf-8'))['anchors']
    for a in LA:
        if a['name'].endswith(('.foot', '.head')):
            x, y, z = a['at']
            reserved[max(0, x - 6):x + 7, max(0, y - 4):y + 5, max(0, z - 1):z + 20] = True
    BT = export_list(BITTS_SRC, 'none')
    BITTS = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in BT}

    def samp(Cc):
        a = np.array(list(Cc.keys()), float)
        return (a[:, None, :] + OFFS[None]).reshape(-1, 3), a

    def size(Cc):
        return [int(v) for v in np.array(list(Cc.keys())).max(0) + 1]

    def world(Q, piv, at, mir):
        q = (Q - np.asarray(piv, float)) * SC
        if mir: q[:, 1] = -q[:, 1]
        return q + np.asarray(at, float)

    def test(Cc, piv, at, mir, mount='floor'):
        S, cells = samp(Cc)
        Wp = world(S, piv, at, mir)
        i = np.floor(Wp).astype(int)
        if (i < 0).any() or (i[:, 0] >= NX).any() or (i[:, 1] >= NY).any() or (i[:, 2] >= NZ).any(): return None
        if occ[i[:, 0], i[:, 1], i[:, 2]].any() or reserved[i[:, 0], i[:, 1], i[:, 2]].any(): return None
        if mount == 'floor':                                              # 底層每格正下方
            bot = cells[cells[:, 2] == 0]
            b = np.floor(world(bot + 0.5, piv, at, mir)).astype(int)
            sup = int(solid[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        else:                                                             # 背面（x 0）每格正後方
            bk = cells[cells[:, 0] == 0]
            b = np.floor(world(bk + 0.5, piv, at, mir)).astype(int)
            sup = int(solid[b[:, 0] - 1, b[:, 1], b[:, 2]].sum())
            bot = bk
        lo, hi = Wp.min(0), Wp.max(0)
        return {'support': [sup, len(bot)], 'box': [round(float(v), 3) for v in list(lo) + list(hi)]}

    def commit(Cc, piv, at, mir):
        S, _ = samp(Cc)
        i = np.floor(world(S, piv, at, mir)).astype(int)
        occ[i[:, 0], i[:, 1], i[:, 2]] = True

    rows, pieces, log = [], {}, {}

    def put(piece, Cc, name, work, path, cands_at, target, piv, mirror=False, mount='floor', need=1.0, recolor=None, source=None):
        cands = []
        for at in cands_at:
            r = test(Cc, piv, at, mirror, mount)
            if r and r['support'][0] >= need * r['support'][1]:
                cands.append((math.dist(at, target), at, r))
        assert cands, '%s 擺不下（試了 %d 點）' % (path, len(cands_at))
        _, at, r = min(cands, key=lambda c: (c[0], c[1]))
        commit(Cc, piv, at, mirror)
        if piece not in pieces: pieces[piece] = {'cells': len(Cc), 'size': size(Cc), 'pivot': piv, 'source': source or (W + '-' + piece)}
        row = {'model': name, 'piece': piece, 'work': work, 'path': path, 'source_work': pieces[piece]['source'], 'at': [round(v, 3) for v in at],
               'mirror': 'y' if mirror else 'none', 'pivot': piv, 'scale': SC, 'meta': dict(DECO, material=MAT[piece]) if piece in MAT else DECO, 'candidates': len(cands), **r}
        if recolor: row['recolor'] = recolor
        rows.append(row)
        log[path] = len(cands)
        return at

    def halves(a, b, st=0.5):
        return [a + k * st for k in range(int(round((b - a) / st)) + 1)]

    def edge_y(x, z):
        """那一站、那一層甲板面上最外一格實心（右舷 +y）：舷牆／外板。"""
        col = solid[int(x), YC:, z]
        on = np.nonzero(col)[0]
        return YC + int(on.max()) if len(on) else None

    # 菊花紋章：盤面中心在中線、船首樓甲板底下 0.9 m；背面貼艏柱（x 往前找第一個背後貼到、前面不撞的）
    CR = crest(); zc = WF1 - 9
    cand = [[x, YM, zc] for x in halves(975, 995)]
    put('crest', CR, '菊花紋章', ASM, '菊花紋章', cand, [975, YM, zc], [0.0, 12.0, 12.0], mount='back', need=0.05)
    # 錨鏈繫纜柱（拿破崙號的元件，換黑）：船首樓中線、錨後面；橫木朝船頭
    bsz = size(BITTS)
    cand = [[x, YM, WF1] for x in halves(905, 950)]
    put('bitts', BITTS, '錨鏈繫纜柱', W + '-deck-fc', '甲板-fc/錨鏈繫纜柱', cand, [930, YM, WF1], [bsz[0] / 2.0, bsz[1] / 2.0, 0.0],
        recolor='%d:%d' % (136, BLACK), source=BITTS_SRC)
    # 雙柱繫纜樁：舷牆裡面 1–8 格；兩舷各自找（構造不完全對稱）
    BL = bollard(); piv_b = [12.0, 5.0, 0.0]
    for key, deck, z, xs, tx in (('艏', 'fc', WF1, halves(925, 960), 945), ('船首樓後端', 'fc', WF1, halves(392, 430), 405), ('艉', 'upper', WU1, halves(25, 80), 45)):
        for side, mir in (('S', False), ('P', True)):
            cand = []
            for x in xs:
                e = edge_y(x, z)
                if e is None: continue
                for d in halves(3, 12):
                    yS = e - d
                    cand.append([x, (2 * YM - yS) if mir else yS, z])
            put('bollard', BL, '繫纜樁-%s-%s' % (key, side), W + '-deck-' + deck, '甲板-%s/繫纜樁-%s-%s' % (deck, key, side), cand,
                [tx, (2 * YM - (edge_y(tx, z) - 3)) if mir else edge_y(tx, z) - 3, z], piv_b, mirror=mir)
    # 備便彈架：中甲板砲列，兩門砲中間、背板貼舷側（右舷背板朝 +y；左舷 mirror=y）
    RK = rack(); piv_r = [18.0, 8.0, 0.0]
    guns = sorted({round((m['box'][0] + m['box'][3]) / 2) for m in MD if m['path'].startswith('甲板-middle/砲-S') and not m['path'].endswith('座')})
    for k, (g0, g1) in enumerate(zip(guns, guns[1:])):
        xm = (g0 + g1) / 2.0
        for side, mir in (('S', False), ('P', True)):
            cand = []
            for x in halves(xm - 8, xm + 8):
                e = edge_y(x, WM1 + 6)
                if e is None: continue
                for d in halves(1, 10):
                    yS = e - d + 0.0
                    cand.append([x, (2 * YM - yS) if mir else yS, WM1])
            put('rack', RK, '備便彈架-%d%s' % (k + 1, side), W + '-deck-middle', '甲板-middle/備便彈架-%d%s' % (k + 1, side), cand,
                [xm, (2 * YM - (edge_y(xm, WM1 + 6) - 1)) if mir else edge_y(xm, WM1 + 6) - 1, WM1], piv_r, mirror=mir)

    gens = {'crest': crest, 'bollard': bollard, 'rack': rack}
    for k, Pc in sorted(pieces.items()):
        if k not in gens: continue
        Cc = gens[k]()
        assert len(Cc) == Pc['cells'], k
        txt = ''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(Cc.items()))
        with open(os.path.join(out, 'furnish', k + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 松島號 裝飾 %s（0.05 m；draft_furnish.py）\n' % k + txt)
        Pc['sha256'] = hashlib.sha256(txt.encode()).hexdigest()
    res = {'note': 'draft_furnish.py —— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框 %d' % (len(A), len(MD)), 'pieces': pieces, 'rows': rows, 'candidates': log}
    for f, d in (('furnish_placement.json', {'pieces': pieces, 'rows': rows}), ('verify_furnish.json', res)):
        with open(os.path.join(out, f), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True); fh.write('\n')
    for r in rows: print(r['path'], 'at', r['at'], r['mirror'], 'support', r['support'], 'box', r['box'], 'cands', r['candidates'])
    print('件', {k: (v['cells'], v['size']) for k, v in pieces.items()})


if __name__ == '__main__':
    main()

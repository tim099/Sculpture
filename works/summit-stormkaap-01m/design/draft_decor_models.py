# 階段二十一 裝飾（TASK-0690；Tim 2026-10-17「另外給風暴角號加一些裝飾吧(標記為裝飾 低畫質下可以隱藏的)」）
#   造船規格 §9.9：外部模型 meta deco=1 ⇒ 畫質「裝飾」低時載入就不載、開著只畫；不算重量、不被打 ⇒ ⛔ 不放有功能 kind 的、⛔ 別的部件不掛在它上面。
#   ⭐ 能引用的就引用（§2.1）：砲彈架、錨鏈繫纜柱 ＝ kotoko 拿破崙號（-shotrack、-bitts，0.05 m、本來就是 deco）；酒桶、貨箱 ＝ 岩堡港（summit-rocher-01m-barrel／-crate）。
#   新做的只有船的個性裝飾：骷髏船員（子作品 -skeleton，0.05 m；靠舷牆坐著、腿往船裡伸）。
# 擺放照 §2.1 取樣法（同 kotoko draft_furnish.py）：模型每格格心＋八角，⛔ 落在 現況（組裝件格子＋所有模型外框）、保留區（梯子兩端 ±6×±4、砲的外框往船裡 10 格、空艙房的框）；
#   腳下：底層每格正下方要是實心（⛔ 艙口上不放）。地板逐欄直接量（🩸 階段二十的絞盤：照舷弧內插量錯一格）。scale 0.5、pivot ＝ 底面中心、rotate 只用 0／180。
# 用法：python -I -X utf8 -B draft_decor_models.py <design> <exports 資料夾：assembly.list.txt、parts.json、各元件 <work>.list.txt>
#   ⇒ masks/decor_models/skeleton.vox.txt、verify_decor_models.json
import sys, os, json, math, hashlib
import numpy as np

D, EX = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
NX, NY, NZ = 760, 270, 200
SC = 0.5
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
BONE, DARK = 218, 36
DECO = {'deco': 1}
SKEL = 'summit-stormkaap-01m-skeleton'


def read(p):
    d = {}
    for ln in open(p, encoding='utf-8'):
        if ln[0] == '#' or not ln.strip():
            continue
        x, y, z, c = map(int, ln.split(','))
        d[(x, y, z)] = c
    return d


def line(C, a, b, c):
    n = int(max(abs(b[i] - a[i]) for i in range(3)))
    for t in range(n + 1):
        C[tuple(int(round(a[i] + (b[i] - a[i]) * t / max(n, 1))) for i in range(3))] = c


def skeleton():
    """骷髏船員（0.05 m）：x 左右 0–8、y 0 ＝ 背靠牆 → 腿往 +y 伸、z 0 ＝ 坐在甲板上。骨盆、脊椎、肋骨一圈一圈、胸骨、肩、頭骨（眼窩、鼻孔黑）、手垂在大腿上、腿屈膝伸出去。"""
    C = {}
    for x in range(2, 7):
        for y in range(1, 4):
            for z in (0, 1):
                C[(x, y, z)] = BONE                                     # 骨盆
    for z in range(2, 12):
        C[(4, 1, z)] = BONE                                             # 脊椎
    for z in (5, 7, 9):                                                 # 肋骨：x 1–7、y 1–4 的一圈
        for x in range(1, 8):
            for y in range(1, 5):
                if x in (1, 7) or y in (1, 4):
                    C[(x, y, z)] = BONE
    for z in range(5, 11):
        C[(4, 4, z)] = BONE                                             # 胸骨
    for x in range(1, 8):
        C[(x, 2, 11)] = BONE                                            # 肩
    for x in range(2, 7):                                               # 頭骨（去掉四個上角）
        for y in range(1, 5):
            for z in range(12, 17):
                if z == 16 and x in (2, 6) and y in (1, 4):
                    continue
                C[(x, y, z)] = BONE
    for x in (3, 5):
        C[(x, 4, 14)] = DARK                                            # 眼窩
    C[(4, 4, 13)] = DARK                                                # 鼻孔
    for x in range(3, 6):
        C[(x, 5, 12)] = BONE                                            # 下巴
    for sx, hx in ((1, 0), (7, 8)):                                     # 手臂：肩 → 肘 → 手放在大腿上
        line(C, (sx, 2, 11), (hx, 2, 6), BONE)
        line(C, (hx, 2, 6), (3 if sx == 1 else 5, 7, 3), BONE)
    for lx in (3, 5):                                                   # 腿：髖 → 膝（屈起）→ 腳踝 → 腳
        line(C, (lx, 3, 1), (lx, 8, 4), BONE)
        line(C, (lx, 8, 4), (lx, 13, 0), BONE)
        C[(lx, 14, 0)] = C[(lx, 14, 1)] = BONE
    return C


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A = read(os.path.join(EX, 'assembly.list.txt'))
    solid = np.zeros((NX, NY, NZ), bool)
    for (x, y, z) in A:
        if z < NZ:
            solid[x, y, z] = True
    occ = solid.copy()
    parts = json.load(open(os.path.join(EX, 'parts.json'), encoding='utf-8'))
    own_tag = '裝飾-'
    PM = [m for m in parts['models'] if own_tag not in m['path']]       # 本階段自己掛的不算（套用之後重跑讀到同一份）
    resv = np.zeros((NX, NY, NZ), bool)
    for m in PM:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        if (m.get('meta') or {}).get('kind') == 'gun':                  # 砲班：砲的外框往船裡 10 格、前後 3 格
            x0, x1 = int(math.floor(b[0])) - 3, int(math.ceil(b[3])) + 3
            yc = (b[1] + b[4]) / 2
            y0, y1 = (int(math.floor(b[1])) - 10, int(math.ceil(b[4]))) if yc > 130 else (int(math.floor(b[1])), int(math.ceil(b[4])) + 10)
            resv[x0:x1, max(0, y0):y1, max(0, int(b[2]) - 2):min(NZ, int(math.ceil(b[5])) + 4)] = True
    pts, rooms = 0, {}
    for L in parts['links']:                                            # 固定點在每條關聯的 points（世界座標、格心）
        for nm, p in (L.get('points') or {}).items():
            x, y, z = (int(math.floor(v)) for v in p)
            if nm.endswith(('.foot', '.head')) and not nm.startswith('manrope'):   # 梯子兩端 ±6×±4、往上 10 格
                resv[x - 6:x + 7, y - 4:y + 5, max(0, z - 1):z + 10] = True; pts += 1
            if (L.get('meta') or {}).get('kind') == 'rooms' and nm.endswith(('.min', '.max')):
                rooms.setdefault((L['path'], nm[:-4]), {})[nm[-3:]] = (x, y, z)
    for r in rooms.values():                                            # 空艙房的框（遊戲在這裡擺病床）
        lo = [min(r['min'][i], r['max'][i]) for i in range(3)]; hi = [max(r['min'][i], r['max'][i]) + 1 for i in range(3)]
        resv[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = True

    def cells_of(w):
        return read(os.path.join(EX, w + '.list.txt')) if w != SKEL else skeleton()

    def samp(C):
        a = np.array(list(C.keys()), float)
        return (a[:, None, :] + OFFS[None]).reshape(-1, 3), a

    def world(Q, piv, at, rot):
        q = (Q - np.asarray(piv, float)) * SC
        if rot == 180:
            q[:, 0] = -q[:, 0]; q[:, 1] = -q[:, 1]
        return q + np.asarray(at, float)

    def floor_z(x, y, zmin, zmax):                                     # 那一欄 zmin..zmax 裡由上往下第一個實心的上面一格
        for z in range(zmax, zmin - 1, -1):
            if solid[x, y, z]:
                return z + 1
        return None

    rows, log = [], {}

    def test(C, piv, at, rot):
        S, cells = samp(C)
        W = world(S, piv, at, rot)
        i = np.floor(W).astype(int)
        if (i < 0).any() or (i[:, 0] >= NX).any() or (i[:, 1] >= NY).any() or (i[:, 2] >= NZ).any():
            return None
        if occ[i[:, 0], i[:, 1], i[:, 2]].any() or resv[i[:, 0], i[:, 1], i[:, 2]].any():
            return None
        bot = cells[cells[:, 2] == cells[:, 2].min()]
        b = np.floor(world(bot + [0.5, 0.5, 0.5], piv, at, rot)).astype(int)
        sup = int(solid[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        if sup != len(b):
            return None
        return {'support': [sup, len(b)], 'box': [round(float(v), 2) for v in list(W.min(0)) + list(W.max(0))]}

    def commit(C, piv, at, rot):
        S, _ = samp(C)
        i = np.floor(world(S, piv, at, rot)).astype(int)
        occ[i[:, 0], i[:, 1], i[:, 2]] = True

    def put(name, deck_link, deck_work, src, xs, ys, zr, rot, key, prefer_wall=None):
        C = cells_of(src)
        a = np.array(list(C.keys()))
        sz = a.max(0) + 1
        piv = [sz[0] / 2.0, sz[1] / 2.0 if src != SKEL else 0.0, 0]     # 骷髏：pivot 在背（y 0）、左右中間
        cands = []
        for x in xs:
            for y in ys:
                z = floor_z(int(x), int(y), zr[0], zr[1])
                if z is None:
                    continue
                at = [x, y, z]
                r = test(C, piv, at, rot)
                if r:
                    cands.append((key(x, y), at, r))
        if not cands:
            rows.append({'model': name, 'placed': False}); print('✗', name, '擺不下'); return None
        _, at, r = min(cands, key=lambda c: (c[0], c[1][0], c[1][1]))
        commit(C, piv, at, rot)
        rows.append({'model': name, 'path': '%s/%s' % (deck_link, name), 'host_work': deck_work, 'work': src, 'at': at, 'pivot': piv, 'scale': SC,
                     'rotate': rot, 'meta': DECO, 'candidates': len(cands), 'cells': len(C), **r})
        print('✓', name, 'at', at, 'rot', rot, '候選', len(cands), 'box', r['box'])
        return at

    H = lambda a, b, s=0.5: [a + k * s for k in range(int(round((b - a) / s)) + 1)]
    # ── 砲彈架：下層、上層甲板主艙口（x 306–322、y 121–139，圍板 x 305／323、y 120／140）兩舷，沿 x、中心對艙口 ──
    for deck_link, deck_work, zr in (('甲板-下', 'summit-stormkaap-01m-deck-lower', (55, 66)), ('甲板-上', 'summit-stormkaap-01m-deck-upper', (74, 86))):
        for side, ys in (('S', H(142.5, 150)), ('P', H(110, 117.5))):
            put('裝飾-砲彈架-' + side, deck_link, deck_work, 'kotoko-napoleon-01m-shotrack', [314.5], ys, zr, 0, lambda x, y: abs(y - 130))
    # ── 錨鏈繫纜柱：上甲板船頭（艏樓底下）、錨鏈孔 x 530 後面、中線 ──
    put('裝飾-繫纜柱', '甲板-上', 'summit-stormkaap-01m-deck-upper', 'kotoko-napoleon-01m-bitts', H(470, 525), [130.5], (85, 105), 0, lambda x, y: abs(x - 515))
    # ── 酒桶、貨箱：下層甲板前段（前艙口 x 457 之前）、中線兩側堆一堆 ──
    for nm, src, tx, ty in (('裝飾-酒桶-1', 'summit-rocher-01m-barrel', 470, 123), ('裝飾-酒桶-2', 'summit-rocher-01m-barrel', 470, 137),
                            ('裝飾-酒桶-3', 'summit-rocher-01m-barrel', 477, 130), ('裝飾-貨箱-1', 'summit-rocher-01m-crate', 485, 124),
                            ('裝飾-貨箱-2', 'summit-rocher-01m-crate', 485, 136)):
        put(nm, '甲板-下', 'summit-stormkaap-01m-deck-lower', src, H(462, 520), H(112, 148), (58, 80), 0, lambda x, y, tx=tx, ty=ty: abs(x - tx) + abs(y - ty))
    # ── 骷髏船員：上甲板船腰靠舷牆（背貼牆、腿往船裡）×2、後甲板 ×1 ——「靠牆」＝ 背後那一格（往船外 1 格）是實心，候選裡挑最靠牆的 ──
    def wall_key(tx, side):
        def k(x, y):
            return abs(x - tx) + (y if side == 'P' else -y) * 0.3          # 越靠船外越好
        return k
    put('裝飾-骷髏-1', '甲板-上', 'summit-stormkaap-01m-deck-upper', SKEL, H(240, 290), H(150, 182), (74, 90), 180, wall_key(262, 'S'))
    put('裝飾-骷髏-2', '甲板-上', 'summit-stormkaap-01m-deck-upper', SKEL, H(240, 290), H(78, 110), (74, 90), 0, wall_key(250, 'P'))
    put('裝飾-骷髏-3', '甲板-後', 'summit-stormkaap-01m-deck-half', SKEL, H(170, 232), H(150, 180), (98, 112), 180, wall_key(205, 'S'))

    S = skeleton()
    out = os.path.join(D, 'masks', 'decor_models'); os.makedirs(out, exist_ok=True)
    NL = chr(10)
    txt = '# 風暴角號 骷髏船員（0.05 m；draft_decor_models.py）%d 格' % len(S) + NL + ''.join('%d,%d,%d,%d' % (k + (c,)) + NL for k, c in sorted(S.items()))
    open(os.path.join(out, 'skeleton.vox.txt'), 'w', encoding='utf-8', newline=NL).write(txt)
    v = {'note': 'draft_decor_models.py（階段二十一）—— 現況 ＝ 組裝件 %d 格＋模型外框 %d；保留區：梯子兩端 %d、砲、空艙房 %d' % (len(A), len(PM), pts, len(rooms)),
         'skeleton': {'work': SKEL, 'title': '風暴角號｜骷髏船員（0.05 m；裝飾 deco）', 'size': [int(v) for v in np.array(list(S)).max(0) + 1], 'cells': len(S),
                      'file': 'masks/decor_models/skeleton.vox.txt', 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()},
         'rows': rows, 'placed': sum(1 for r in rows if r.get('at')), 'of': len(rows)}
    with open(os.path.join(D, 'verify_decor_models.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
    print(v['note']); print('放了', v['placed'], '／', v['of'], '；骷髏', v['skeleton']['size'], v['skeleton']['cells'], '格')


if __name__ == '__main__':
    main()

# 拿破崙號 蒸汽機（主機、螺旋槳軸、前後兩組鍋爐與煙道）—— 自己寫的；plan.json engine。
#   Tim 2026-10-15：「是否可以建造 拿破崙號 的蒸汽引擎」「同時可能要標記 meta」「遊戲中如果引擎被破壞 引擎提供的額外動力要消失（且煙會停掉）因此需要標記」
#   ⇒ 每一件是一條關聯、帶 meta（kind=engine／boiler／shaft）與固定點（core、cyl-*、gear；boiler-*、uptake；fwd／aft）——
#     遊戲可以照「固定點旁邊的格子剩多少」判斷壞了沒有（同 78_funnel.js 判煙囪的做法）。
#   現況 ＝ 組裝件 links=all（藏本階段的關聯 ⇒ 落格之後重跑讀到的還是同一份），z < 120。
#   只放在船殼裡面的空氣（每個 (x, z) 從中線往兩舷走到第一格實心為止）；落在現況實心上的不放（照實數）。
#   輸出：masks/engine/{engine,shaft,boilers_aft,boilers_fore}.vox.txt（子作品座標，原點 ＝ 外框最小角）、engine_placement.json、verify_engine.json、sheet07_engine_v1.png
#   用法：python -I -X utf8 draft_engine.py <design> [--probe=nometa|shift:<件>:<dz>]
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import mio

NX, NY, NZ = 1200, 400, 120
YC = 200
HIDE = '機艙-主機,機艙-鍋爐-後,機艙-鍋爐-前,螺旋槳軸,甲板-engine,甲板-lower/梯子-機艙'   # 後兩條是階段十三、十四（在本件之後）


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    plan = HL.load_plan(D)
    E = plan['engine']
    C = E['colors']
    try:
        A = mio.export_list(mio.ASM, 'all', ('hide_links=' + HIDE,))
    except SystemExit:
        A = mio.export_list(mio.ASM, 'all')                              # 還沒落格：那幾條關聯不存在
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True

    # 船殼裡面：每個 (x, z) 從中線往兩舷走到第一格實心（中線那格是實心 ⇒ 那一排不算）
    X0, X1 = 180, 670
    inside = np.zeros((NX, NY, NZ), bool)
    for x in range(X0, X1):
        for z in range(NZ):
            if occ[x, YC, z]:
                continue
            ys = np.nonzero(occ[x, YC:, z])[0]
            yn = np.nonzero(occ[x, :YC + 1, z][::-1])[0]
            if not len(ys) or not len(yn):
                continue
            inside[x, YC - yn[0] + 1:YC + ys[0], z] = True

    parts = {k: {} for k in ('engine', 'shaft', 'boilers_aft', 'boilers_fore')}
    skipped = {k: 0 for k in parts}

    def put(k, x, y, z, c):
        if not (0 <= x < NX and 0 <= y < NY and 0 <= z < NZ) or not inside[x, y, z]:
            skipped[k] += 1
            return
        parts[k][(x, y, z)] = c

    # ── 主機 ──
    G = E['engine']
    ex0, ex1 = G['x']
    for x in range(ex0, ex1 + 1):                                        # 底座：從船底一路到 bed.top
        for y in range(YC - G['bed']['half'], YC + G['bed']['half'] + 1):
            for z in range(0, G['bed']['top'] + 1):
                if inside[x, y, z]:
                    parts['engine'][(x, y, z)] = C['steel']
    cy = G['cyl']
    for s in (-1, 1):                                                    # 兩缸（立式），頂蓋一圈黃銅
        yc = YC + s * cy['dy']
        for x in range(cy['x'] - cy['r'], cy['x'] + cy['r'] + 1):
            for y in range(yc - cy['r'], yc + cy['r'] + 1):
                d2 = (x - cy['x']) ** 2 + (y - yc) ** 2
                if d2 > cy['r'] ** 2:
                    continue
                for z in range(cy['z'][0], cy['z'][1] + 1):
                    put('engine', x, y, z, C['brass'] if z == cy['z'][1] and d2 >= (cy['r'] - 1) ** 2 else C['iron'])
    ck = G['crank']
    for x in range(ck['x'][0], ck['x'][1] + 1):                          # 曲軸（沿 x）
        for y in range(YC - ck['r'], YC + ck['r'] + 1):
            for z in range(ck['z'] - ck['r'], ck['z'] + ck['r'] + 1):
                if (y - YC) ** 2 + (z - ck['z']) ** 2 <= ck['r'] ** 2:
                    put('engine', x, y, z, C['steel'])
    for px in G['pedestals_x']:                                          # 軸承座：從底座到曲軸底下
        for x in range(px - 1, px + 2):
            for y in range(YC - 4, YC + 5):
                for z in range(G['bed']['top'] + 1, ck['z'] - ck['r']):
                    put('engine', x, y, z, C['iron'])
    for s in (-1, 1):                                                    # 連桿：缸頂中心 → 曲柄（斜線，2 格粗）
        a = np.array([cy['x'], YC + s * cy['dy'], cy['z'][1] + 1], float)
        b = np.array([cy['x'], YC + s * 2, ck['z'] - ck['r']], float)
        n = int(np.abs(b - a).max() * 2) + 1
        for t in np.linspace(0, 1, n):
            p = a + (b - a) * t
            for dx, dy, dz in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):   # 十字截面 ⇒ 斜線也面相連（只靠斜角相接 ⇒ 判成浮空）
                put('engine', int(math.floor(p[0])) + dx, int(round(p[1])) + dy, int(round(p[2])) + dz, C['steel'])
    gr = G['gear']                                                       # 大齒輪（曲軸上）：輪緣、六根輻條（y ↔ −y 對稱的角度）、輪轂
    for x in range(gr['x'] - 1, gr['x'] - 1 + gr['th']):
        for y in range(YC - gr['r'], YC + gr['r'] + 1):
            for z in range(ck['z'] - gr['r'], ck['z'] + gr['r'] + 1):
                r = math.hypot(y - YC, z - ck['z'])
                if r > gr['r'] + 0.5:
                    continue
                th = math.degrees(math.atan2(z - ck['z'], y - YC)) % 360
                spoke = min(abs((th - a + 180) % 360 - 180) for a in (30, 90, 150, 210, 270, 330)) * math.pi / 180 * r <= 1.0
                if r >= gr['r'] - 1.5 or r <= gr['hub'] + 0.5 or spoke:
                    put('engine', x, y, z, C['iron'])
    pr = G['pinion']; sz = plan['engine']['shaft']['z']
    for x in range(gr['x'] - 1, gr['x'] - 1 + gr['th']):                 # 小齒輪（螺旋槳軸上，跟大齒輪咬合）
        for y in range(YC - pr['r'], YC + pr['r'] + 1):
            for z in range(sz - pr['r'], sz + pr['r'] + 1):
                if math.hypot(y - YC, z - sz) <= pr['r'] + 0.5:
                    put('engine', x, y, z, C['steel'])

    # ── 螺旋槳軸 ──
    SH = E['shaft']
    gc = os.path.join(D, 'masks', 'engine', 'gears_from_engine.json')
    bore_xs = set(range(SH['x'][0], SH['x'][1] + 1)) if os.path.exists(gc) else set()   # 齒輪拆成模型之後（ame 2026-10-16 seq 25400）：軸線上的格一律歸軸（穿過小齒輪的軸孔、軸承座）⇒ 軸的格子從頭到尾不斷（遊戲照軸的格子判斷斷了沒有）
    for x in range(SH['x'][0], SH['x'][1] + 1):
        for y in range(YC - SH['r'], YC + SH['r'] + 1):
            for z in range(sz - SH['r'], sz + SH['r'] + 1):
                if (y - YC) ** 2 + (z - sz) ** 2 <= SH['r'] ** 2 and ((x, y, z) not in parts['engine'] or x in bore_xs):
                    parts['engine'].pop((x, y, z), None) if x in bore_xs else None
                    put('shaft', x, y, z, C['steel'])
    for px in range(SH['plummer_from'], SH['x'][1] - 10, SH['plummer_every']):   # 軸承座：從船底到軸底下（起點寫死：軸往後延到螺旋槳柱之後不挪它們）
        for x in range(px, px + 3):
            for y in range(YC - 3, YC + 4):
                for z in range(0, sz - SH['r']):
                    if inside[x, y, z]:
                        parts['shaft'][(x, y, z)] = C['iron']

    # 2026-10-16：大小齒輪拆成會轉的外部模型（tools/split_gears.py）⇒ 那些格不在主機件裡（⛔ 要在畫完軸之後拿：軸照「主機沒有的格」補，先拿 ⇒ 軸補進小齒輪那 39 格）
    if os.path.exists(gc):
        for v in json.load(open(gc, encoding='utf-8')).values():
            for k in v:
                parts['engine'].pop(tuple(map(int, k.split(','))), None)

    # ── 鍋爐與煙道 ──
    BO = E['boilers']
    anchors_b = {}
    for row in BO['rows']:
        k = 'boilers_' + row['key']
        P = parts[k]
        an = {}
        bi = 0
        (xa0, xa1), (xb0, xb1) = row['x']
        for (x0, x1), door_x in (((xa0, xa1), xa1), ((xb0, xb1), xb0)):  # 爐門朝兩排之間的燒火通道
            for s in (-1, 1):
                y0, y1 = sorted((YC + s * BO['dy'][0], YC + s * BO['dy'][1]))
                w = y1 - y0
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        u = (y - y0) / float(w)
                        ztop = BO['z'][1] - int(round(BO['crown'] * (2 * u - 1) ** 2))
                        for z in range(BO['z'][0], ztop + 1):
                            c = C['iron']
                            if x == door_x:
                                for yd in ((y0 + y1) / 2.0 - 8, (y0 + y1) / 2.0 + 8):   # 每座兩個爐門：火色、鐵框
                                    if abs(y - yd) <= 2.5 and 17 <= z <= 23:
                                        c = C['fire'] if abs(y - yd) <= 1.5 and 18 <= z <= 22 else C['steel']
                            put(k, x, y, z, c)
                for x in range(x0 + 2, x1 - 1):                          # 鍋爐座：鍋爐底下到船底（磚）
                    for y in range(y0 + 2, y1 - 1):
                        for z in range(0, BO['z'][0]):
                            if inside[x, y, z]:
                                P[(x, y, z)] = C['brick']
                bi += 1
                an['boiler-%d' % bi] = [int((x0 + x1) // 2), int((y0 + y1) // 2), int((BO['z'][0] + BO['z'][1]) // 2)]
                # 站位（階段十四，Tim 2026-10-16：「動力部件可以設定需要船員工作(鍋爐)」「參數都在遊戲端設定 模型只提供meta標記」）：
                #   爐門前往燒火通道 4 格、這座鍋爐的中線（兩舷鏡像：YC ∓ 21）、跟鍋爐底同高（機艙鐵地板上第一格空氣）—— 要幾個人、人不夠怎麼扣出力，遊戲那側定
                an['stoke-%d' % bi] = [door_x + (4 if door_x == x1 else -4), YC + s * ((BO['dy'][0] + BO['dy'][1] + 1) // 2), BO['z'][0]]
        # 煙道：從整組外框（z 51 一整片 smoke box）收成煙囪的圓（z 89），鐵殼 1 格
        gx0, gx1 = xa0, xb1
        cx0, fx = (gx0 + gx1) / 2.0, float(row['funnel_x'])
        zu0, zu1 = BO['uptake_z']
        def shape(z):
            t = (z - zu0) / float(zu1 - zu0)
            return cx0 + (fx - cx0) * t, (gx1 - gx0) / 2.0 + (BO['funnel_r'] - (gx1 - gx0) / 2.0) * t, BO['dy'][1] + (BO['funnel_r'] - BO['dy'][1]) * t, 8 + (2 - 8) * t
        SH_ = {z: shape(z) for z in range(zu0 - 1, zu1 + 2)}

        def inn(x, y, z):
            if z < zu0 or z > zu1:
                return False
            cxz, ax, ay, pw = SH_[z]
            return (abs(x + 0.5 - cxz) / ax) ** pw + (abs(y - YC) / ay) ** pw <= 1   # 中線那一格 y 200 ＝ 對稱軸（y ↔ 400 − y）
        def ring(x, y, z):
            return inn(x, y, z) and not (inn(x + 1, y, z) and inn(x - 1, y, z) and inn(x, y + 1, z) and inn(x, y - 1, z))
        for z in range(zu0, zu1 + 1):
            cxz, ax, ay, pw = SH_[z]
            for x in range(int(cxz - ax) - 1, int(cxz + ax) + 2):
                for y in range(int(YC - ay) - 1, int(YC + ay) + 2):
                    if not inn(x, y, z):
                        continue
                    edge = ring(x, y, z)
                    side = z < zu1 and (not inn(x, y, z + 1) or ring(x, y, z + 1))   # 上一層收進去了、或正上方是上一層的殼 ⇒ 這一格也是殼（殼才會一層接一層面相連）
                    if z == zu0 or edge or side:
                        put(k, x, y, z, C['iron'])
        an['uptake'] = [int(round(cx0)), YC, zu0]                           # smoke box 那一片（實心）的中心
        anchors_b[k] = an

    # ── 封小空腔（照三叉戟號 draft_magazines seal）：本階段新夾出來、≤ 20 格的封閉空腔 ⇒ 填進那一段的鍋爐件（煙道頂跟煙囪壁之間的縫）──
    U0 = occ[X0:X1].copy(); U1 = U0.copy()
    for P in parts.values():
        for (x, y, z) in P:
            U1[x - X0, y, z] = True
    newcav = (ndimage.binary_fill_holes(U1) & ~U1) & ~(ndimage.binary_fill_holes(U0) & ~U0)
    labc, nc = ndimage.label(newcav)
    sealed = []
    for i in range(1, nc + 1):
        q = np.argwhere(labc == i)
        assert len(q) <= 20, ('大空腔', len(q), (q.min(0) + [X0, 0, 0]).tolist())
        for (x, y, z) in q:
            k2 = 'boilers_aft' if x + X0 < 510 else 'boilers_fore'
            parts[k2][(int(x) + X0, int(y), int(z))] = C['iron']
        sealed.append([int(q[0][0]) + X0, int(q[0][1]), int(q[0][2]), int(len(q))])

    # ── probe ──
    if probe and probe.startswith('shift:'):
        _, k, dz = probe.split(':')
        parts[k] = {(x, y, z + int(dz)): c for (x, y, z), c in parts[k].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_outside': skipped}
    allc = {}
    over_parts = 0
    for k, P in parts.items():
        for p in P:
            if p in allc:
                over_parts += 1
            allc[p] = k
    over_base = {k: sum(1 for p in P if occ[p]) for k, P in parts.items()}
    lo = np.array([X0, 0, 0]); U = occ[X0:X1].copy(); Ub = U.copy()
    for (x, y, z) in allc:
        U[x - X0, y, z] = True
    lab, _ = ndimage.label(U)
    base_l = set(np.unique(lab[Ub]).tolist()) - {0}
    floating = {k: sum(1 for (x, y, z) in P if lab[x - X0, y, z] not in base_l) for k, P in parts.items()}
    FLT = [(x, y, z) for (x, y, z) in allc if lab[x - X0, y, z] not in base_l]
    R_flt = (np.array(FLT).min(0).tolist(), np.array(FLT).max(0).tolist()) if FLT else None
    holes = int((ndimage.binary_fill_holes(U) & ~U).sum() - (ndimage.binary_fill_holes(Ub) & ~Ub).sum())
    asym = {k: sum(1 for (x, y, z), c in P.items() if P.get((x, 2 * YC - y, z)) != c) for k, P in parts.items()}

    os.makedirs(os.path.join(D, 'masks', 'engine'), exist_ok=True)
    place = {}
    works = {'engine': (E['work_engine'], E['link_engine'], '拿破崙號 主機（Indret 齒輪傳動雙缸、960 nhp；0.1 m）', G['meta']),
             'shaft': (SH['work'], SH['link'], '拿破崙號 螺旋槳軸與軸承座（0.1 m）', SH['meta'])}
    for row in BO['rows']:
        works['boilers_' + row['key']] = (row['work'], row['link'], '拿破崙號 %s鍋爐 4 座與煙道（0.1 m）' % ('後' if row['key'] == 'aft' else '前'),
                                         dict(E['boiler_meta'], funnel=row['funnel']))
    anchors = {'engine': {'core': [int((ex0 + ex1) // 2), YC, ck['z']], 'cyl-1': [cy['x'], YC - cy['dy'], (cy['z'][0] + cy['z'][1]) // 2],
                          'cyl-2': [cy['x'], YC + cy['dy'], (cy['z'][0] + cy['z'][1]) // 2], 'gear': [gr['x'], YC, ck['z']],
                          # 站位（階段十四）：兩缸外側各一（缸外緣再往舷外 3 格、機艙鐵地板上）—— 機匠；框照固定點撐開（y 179 → 176）
                          'tend-1': [cy['x'], YC - cy['dy'] - cy['r'] - 3, plan['engine']['boilers']['z'][0]],
                          'tend-2': [cy['x'], YC + cy['dy'] + cy['r'] + 3, plan['engine']['boilers']['z'][0]]},
               'shaft': {'aft': [SH['x'][0], YC, sz], 'fwd': [SH['x'][1], YC, sz]}}   # aft ＝ 軸穿過 stern tube 碰到螺旋槳柱那一格（那一段是船殼、沒有軸的格；框照固定點撐開）
    anchors.update(anchors_b)
    for k, P in parts.items():
        org, size = mio.bbox(P)
        for v in anchors[k].values():                                    # 框一定包到自己的固定點（軸的 aft 在 deadwood 那一段、沒有格）
            for i in range(3):
                if v[i] < org[i]:
                    size[i] += org[i] - v[i]; org[i] = v[i]
                if v[i] >= org[i] + size[i]:
                    size[i] = v[i] - org[i] + 1
        n, h = mio.write_local(os.path.join(D, 'masks', 'engine', k + '.vox.txt'), P, org, '# 拿破崙號 %s（draft_engine.py；子作品座標，原點 ＝ 組裝件 %s）\n' % (k, org))
        an_local = {nm: [v[i] - org[i] for i in range(3)] for nm, v in anchors[k].items()}
        bad_an = [nm for nm, v in anchors[k].items() if not (0 <= v[0] - org[0] < size[0] and 0 <= v[1] - org[1] < size[1] and 0 <= v[2] - org[2] < size[2])]
        w, link, title, meta = works[k]
        if probe == 'nometa' and k == 'engine':
            meta = {kk: vv for kk, vv in meta.items() if kk != 'kind'}
        place[k] = {'work': w, 'link': link, 'title': title, 'at': org, 'size': size, 'cells': n, 'sha256': h, 'meta': meta, 'anchors': an_local, 'anchors_world': anchors[k]}
        near = {}
        for nm, v in anchors[k].items():                                 # 固定點旁 8 格內這一件自己的格數（遊戲照這個判斷壞了沒有）
            near[nm] = sum(1 for (x, y, z) in P if (x - v[0]) ** 2 + (y - v[1]) ** 2 + (z - v[2]) ** 2 <= 64)
        by = {}
        for c in P.values():
            by[str(c)] = by.get(str(c), 0) + 1
        R['parts'][k] = {'cells': n, 'colors': dict(sorted(by.items())), 'box': [org, size], 'overlap_base': over_base[k], 'floating': floating[k],
                         'asym': asym[k], 'anchor_out_of_box': bad_an, 'near_anchor_cells_r8': near}
    R['overlap_between_parts'] = over_parts
    R['new_cavities'] = holes
    R['sealed'] = sealed
    R['floating_box'] = R_flt
    if probe:
        print('probe', probe, json.dumps({k: {kk: v[kk] for kk in ('cells', 'overlap_base', 'floating', 'asym')} for k, v in R['parts'].items()}, ensure_ascii=False),
              'meta', place['engine']['meta'])
        return
    for nm, obj in (('engine_placement.json', place), ('verify_engine.json', R)):
        with open(os.path.join(D, nm), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
    sheet(D, occ, parts, anchors)
    print(json.dumps(R, ensure_ascii=False))


def sheet(D, occ, parts, anchors):
    """圖紙：上 ＝ 側面（x–z，中線剖面＋本階段每件的投影），下 ＝ 俯視（x–y，z 0–89 投影）。2 px／格。"""
    from PIL import Image, ImageDraw
    from draft_lines import font                                       # 中文字型（同 draft_lines.py）
    x0, x1, k = 180, 670, 2
    W = (x1 - x0) * k
    img = Image.new('RGB', (W + 40, 120 * k + 200 * k + 80), (250, 248, 240))
    d = ImageDraw.Draw(img)
    col = {'engine': (60, 60, 70), 'shaft': (120, 120, 130), 'boilers_aft': (170, 60, 40), 'boilers_fore': (170, 90, 40)}
    oy1, oy2 = 30, 30 + 120 * k + 30
    sec = occ[x0:x1, YC, :]
    for (xx, zz) in np.argwhere(sec):
        d.rectangle([20 + xx * k, oy1 + (119 - zz) * k, 20 + xx * k + k - 1, oy1 + (119 - zz) * k + k - 1], fill=(200, 195, 185))
    top = occ[x0:x1, 100:300, :90].any(2)
    for (xx, yy) in np.argwhere(top):
        d.point([20 + xx * k, oy2 + yy * k], fill=(205, 200, 190))
    for nm, P in parts.items():
        for (x, y, z) in P:
            d.rectangle([20 + (x - x0) * k, oy1 + (119 - z) * k, 20 + (x - x0) * k + k - 1, oy1 + (119 - z) * k + k - 1], fill=col[nm])
            if 100 <= y < 300:
                d.rectangle([20 + (x - x0) * k, oy2 + (y - 100) * k, 20 + (x - x0) * k + k - 1, oy2 + (y - 100) * k + k - 1], fill=col[nm])
    for nm, an in anchors.items():
        for a, v in an.items():
            px, pz = 20 + (v[0] - x0) * k, oy1 + (119 - v[2]) * k
            d.ellipse([px - 3, pz - 3, px + 3, pz + 3], outline=(0, 120, 200), width=2)
    d.text((20, 8), '拿破崙號 機艙 sheet07 v1 —— 上：中線側面（x %d–%d、z 0–119）；下：俯視（y 100–299）；藍圈 ＝ 固定點' % (x0, x1), fill=(0, 0, 0), font=font(16))
    img.save(os.path.join(D, 'sheet07_engine_v1.png'))


if __name__ == '__main__':
    main()

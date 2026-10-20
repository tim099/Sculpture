# 越嶺號 階段三（TASK-0760）：桅、拉丁帆桁、三角帆、靜索、旗 ⇒
#   masks/masts/{mast,deck_holes}.vox.txt、masks/yards/yard.vox.txt、yards.json、rig_plan.json、textures/{ensign,pennant}.png、verify_masts.json、sheet03_rig_v1.png
#   用法：python -I -X utf8 draft_masts.py [--probe=yard_z=-60]   （probe ⇒ 帆桁整根上下移，量碰撞；⛔ 不寫檔）
#   · 讀船殼（draft_lines）與階段二清單（masks/upper，作品 ＝ 清單已證）。
#   · 做法照皇家號 apex-one-reale-01m/design/draft_masts.py＋tools/build_rig.py：帆桁一根一件緊框子作品、固定點 pivot／fore／peak、
#     外部模型 rotate 0 放在桅子作品裡；帆的前緣 bind 在帆桁上、clew 自由；帆桁 meta yard=gaff＋rig=lateen（造船規格 §5）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_upper as DU

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 360, 161, 230


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_list(f):
    return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def world():
    """船殼＋階段二（清單）⇒ 實心格與屬於哪一件。"""
    occ = np.zeros((SX, SY, SZ), np.uint8)   # 0 空、1 船殼、2 甲板、3 槳架、4 船首、5 衝角、6 船尾篷
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    hc = DL.hull_cells(L, plan)
    occ[DL.X0:DL.X0 + hc.shape[0], :, :hc.shape[2]][hc > 0] = 1
    for i, p in enumerate(DU.PARTS, 2):
        a = load_list(os.path.join(HERE, 'masks', 'upper', p + '.vox.txt'))
        occ[a[:, 0], a[:, 1], a[:, 2]] = i
    return plan, L, occ


def build(probe):
    plan, L, occ = world()
    YC = L.YC
    rg = {k: V(v) for k, v in plan['rig'].items() if k != 'src'}
    m, y, sl = rg['mast'], rg['yard'], rg['sail']
    tz = np.floor(L.sheer(np.arange(SX) + 0.5)).astype(int)
    zdk = int(tz[m['x_deck']])                                   # 桅那一格的甲板面（板頂那一格）
    rk = math.tan(math.radians(m['rake_deg']))
    ztop = zdk + m['above_deck']
    cx = lambda z: m['x_deck'] + 0.5 + (z + 0.5 - (zdk + 0.5)) * rk
    # ── 桅：從船底往上（跟船殼重疊的不放），圓、往上變細；頂上 head 格的桅頭箱（3 × 5，沿 y 長，滑輪）──
    mast = {}
    holes = []
    for z in range(0, ztop + 1):
        t = max(0.0, (z - zdk) / m['above_deck'])
        r = m['r_deck'] + (m['r_top'] - m['r_deck']) * t
        c = cx(z)
        for x in range(int(c - r) - 1, int(c + r) + 2):
            for yy in range(YC - 3, YC + 4):
                if (x + 0.5 - c) ** 2 + (yy + 0.5 - (YC + 0.5)) ** 2 <= r * r or (z > ztop - m['head'] and abs(x + 0.5 - c) <= 1.6 and abs(yy - YC) <= 2):
                    if occ[x, yy, z] == 1:
                        continue
                    if occ[x, yy, z] == 2:
                        holes.append((x, yy, z))
                    elif occ[x, yy, z]:
                        raise SystemExit('✗ 桅撞到 %d（%d,%d,%d）' % (occ[x, yy, z], x, yy, z))
                    mast[(x, yy, z)] = 68 if z > ztop - m['head'] else m['color']
    # ── 帆桁：吊點在桅頂下 below_top、桅的左舷側 dy；沿 xz 平面、前端往下 angle；兩頭細、中間粗；每 band_every 格一圈紅／綠布條 ──
    zp = ztop - y['below_top'] + probe.get('yard_z', 0)
    P = np.array([cx(zp), YC + y['dy'] + 0.5, zp + 0.5])
    ang = math.radians(y['angle_deg'])
    u = np.array([math.cos(ang), 0.0, -math.sin(ang)])             # 往前端（船頭、往下）
    F = P + u * y['length'] * y['pivot_frac']
    Pk = P - u * y['length'] * (1 - y['pivot_frac'])
    yard_w = {}
    lo = np.floor(np.minimum(F, Pk) - 3).astype(int)
    hi = np.ceil(np.maximum(F, Pk) + 3).astype(int)
    cols = y['colors']
    for x in range(lo[0], hi[0] + 1):
        for z in range(lo[2], hi[2] + 1):
            for yy in range(lo[1], hi[1] + 1):
                q = np.array([x + 0.5, yy + 0.5, z + 0.5])
                s = float((q - Pk) @ u) / y['length']                # 0 ＝ peak、1 ＝ 前端（Pk → F 是 +u）
                if not (0 <= s <= 1):
                    continue
                dist = np.linalg.norm((q - Pk) - u * s * y['length'])
                r = y['r_end'] + (y['r_mid'] - y['r_end']) * math.sin(math.pi * min(max(s, 0), 1)) ** 0.6
                if dist <= r:
                    k = int(s * y['length'])
                    c = cols[1 + (k // y['band_every']) % 2] if (k % y['band_every']) < 2 and 0.05 < s < 0.95 else cols[0]
                    yard_w[(x, yy, z)] = c
    hit_yard = sum(1 for k in yard_w if occ[k] or k in mast)
    # ── 帆：tack ＝ 帆桁前端、head ＝ peak、clew：離前端 foot、離 peak leech，在帆桁下方（xz 平面上解兩圓交點，取下面那個）──
    Lf, Ll = y['length'] * sl['foot_ratio'], y['length'] * sl['leech_ratio']
    Fx, Fz, Px, Pz = F[0], F[2], Pk[0], Pk[2]
    D = math.hypot(Px - Fx, Pz - Fz)
    a = (Lf * Lf - Ll * Ll + D * D) / (2 * D)
    h = math.sqrt(max(0.0, Lf * Lf - a * a))
    mx, mz = Fx + a * (Px - Fx) / D, Fz + a * (Pz - Fz) / D
    cands = [(mx + h * (Pz - Fz) / D, mz - h * (Px - Fx) / D), (mx - h * (Pz - Fz) / D, mz + h * (Px - Fx) / D)]
    C = min(cands, key=lambda c: c[1])
    clew = np.array([C[0], F[1], C[1]])
    hit_sail = 0
    for i in range(0, 41):
        for j in range(0, 41 - i):
            q = F + (Pk - F) * (i / 40) + (clew - F) * (j / 40)
            k = tuple(np.floor(q).astype(int))
            if 0 <= k[2] < SZ and (occ[k] or k in mast):
                hit_sail += 1
    return plan, L, occ, rg, zdk, ztop, cx, mast, holes, yard_w, F, Pk, P, clew, hit_yard, hit_sail


def textures():
    os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
    W, H = 72, 48
    img = Image.new('RGBA', (W, H), (182, 0, 0, 255))
    d = ImageDraw.Draw(img)
    cx, cy, R = 30, 24, 15
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(245, 245, 240, 255))
    d.ellipse([cx - R + 6, cy - R + 1, cx + R + 4, cy + R - 1], fill=(182, 0, 0, 255))   # 一彎新月（兩圓相減）、⛔ 沒有星
    img.save(os.path.join(HERE, 'textures', 'ensign.png'))
    p = Image.new('RGBA', (64, 8), (182, 0, 0, 255))
    ImageDraw.Draw(p).rectangle([0, 4, 63, 7], fill=(255, 200, 0, 255))
    p.save(os.path.join(HERE, 'textures', 'pennant.png'))


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    plan, L, occ, rg, zdk, ztop, cx, mast, holes, yard_w, F, Pk, P, clew, hit_yard, hit_sail = build(probe)
    R = {'mast_cells': len(mast), 'deck_holes': len(holes), 'mast_top_z': ztop, 'mast_above_deck_m': round((ztop - zdk) * 0.1, 1),
         'yard_cells': len(yard_w), 'yard_fore': [round(float(v), 1) for v in F], 'yard_peak': [round(float(v), 1) for v in Pk], 'clew': [round(float(v), 1) for v in clew],
         'clew_above_deck_m': round(float(clew[2] - (zdk + 1)) * 0.1, 2), 'yard_hits': hit_yard, 'sail_plane_hits': hit_sail}
    if probe:
        print(json.dumps({'probe': probe, 'yard_hits': hit_yard, 'sail_plane_hits': hit_sail}, ensure_ascii=False))
        return
    YC = L.YC
    for sub in ('masts', 'yards'):
        os.makedirs(os.path.join(HERE, 'masks', sub), exist_ok=True)

    def dump(fn, cells, title):
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 越嶺號 %s（draft_masts.py）x,y,z,color\n' % title)
            f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in sorted(cells.items())))
        return hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    R['sha256'] = {}
    R['sha256']['mast'] = dump(os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt'), mast, '桅（整船的座標，at 0,0,0）')
    hc = {k: 0 for k in holes}
    deck = {tuple(r[:3]): r[3] for r in load_list(os.path.join(HERE, 'masks', 'upper', 'deck.vox.txt')).tolist()}
    R['sha256']['deck_holes'] = dump(os.path.join(HERE, 'masks', 'masts', 'deck_holes.vox.txt'), {k: deck[k] for k in holes}, '桅孔（從甲板-main 刻掉；帶原本的顏色守門）')
    # 帆桁：緊框
    ks = np.array(list(yard_w.keys()))
    off = ks.min(0)
    size = (ks.max(0) - off + 1).tolist()
    local = {tuple((np.array(k) - off).tolist()): c for k, c in yard_w.items()}
    R['sha256']['yard'] = dump(os.path.join(HERE, 'masks', 'yards', 'yard.vox.txt'), local, '拉丁帆桁（緊框，子作品自己的座標）')

    def cell(p):
        return [int(v) for v in np.floor(np.array(p) - off)]
    piv = cell(P)
    yj = {'size': size, 'offset': off.tolist(),
          'anchors': {'pivot': piv, 'fore': cell(F - (F - P) / np.linalg.norm(F - P) * 1.0), 'peak': cell(Pk + (F - Pk) / np.linalg.norm(F - Pk) * 1.0)},
          'pivot': [piv[0] + 0.5, piv[1] + 0.5, piv[2] + 0.5], 'mast_link': '主桅',
          'meta': {'kind': 'yard', 'mast': 'main', 'yard': 'gaff', 'rig': 'lateen', 'sail': 'lateen', 'length_m': round(rg['yard']['length'] * 0.1, 1),
                   'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}}
    for nm, a in yj['anchors'].items():
        assert tuple(a) in local, ('帆桁固定點不在格上', nm, a)
    yj['at'] = [round(off[i] + yj['pivot'][i], 3) for i in range(3)]
    with open(os.path.join(HERE, 'yards.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'main': yj}, f, ensure_ascii=False, indent=1)
    # 索具：hound（桅頭下、兩舷各一格）、靜索綁在槳架縱樑（dy 28、z 18）、sheet 綁在縱樑、tack 綁在船首平台前胸牆頂
    hz = ztop - rg['shrouds']['hound_below_top']
    hx = int(cx(hz))
    mr = int(math.ceil(1.0 + (1.55 - 1.0) * 0.0))
    anchors = [{'work': 'mast', 'name': 'hound-P', 'at': [hx, YC - 1, hz]}, {'work': 'mast', 'name': 'hound-S', 'at': [hx, YC + 1, hz]}]
    for k in (('mast', 'hound-P', (hx, YC - 1, hz)), ('mast', 'hound-S', (hx, YC + 1, hz))):
        assert k[2] in mast, ('hound 不在桅的格上', k)
    ropes, sails = [], []
    for side, sg in (('P', -1), ('S', 1)):
        for i, x in enumerate(rg['shrouds']['x'], 1):
            a = [x, YC + sg * 28, 18]
            assert occ[tuple(a)] == 3, ('靜索固定點不在槳架上', a)
            anchors.append({'work': 'apostis', 'name': 'shroud-%s%d' % (side, i), 'at': a})
            ropes.append({'name': 'shroud-%s%d' % (side, i), 'from': '主桅/hound-%s' % side, 'to': '舷外槳架/shroud-%s%d' % (side, i), 'slack': 1.0,
                          'thickness': 0.6, 'color': '#2b2620', 'group': 'standing/shrouds', 'meta': {'kind': 'shroud'}})
        bx = int(round(clew[0]))
        while not occ[bx, YC + sg * 28, 18] == 3:
            bx += 1
        a = [bx, YC + sg * 28, 18]
        anchors.append({'work': 'apostis', 'name': 'belay-sheet-%s' % side, 'at': a})
        ropes.append({'name': 'lateen.sheet-%s' % side, 'from': 'sail:lateen/clew', 'to': '舷外槳架/belay-sheet-%s' % side, 'slack': 1.03,
                      'thickness': 0.45, 'color': '#a08458', 'group': 'running/sheets', 'meta': {'kind': 'sheet', 'sail': 'lateen'}})
    bp = V(plan['layout']['bow_platform'])
    tack = [bp['x1'], YC + 3, bp['top'] + bp['wall_h']]          # 中線開了砲口 ⇒ 綁在砲口右邊那一段胸牆頂
    assert occ[tuple(tack)] == 4, ('tack 固定點不在船首胸牆上', tack)
    anchors.append({'work': 'bow', 'name': 'tack', 'at': tack})
    ropes.append({'name': 'lateen.tack', 'from': 'model:主桅/yard/fore', 'to': '甲板-bow/tack', 'slack': 1.02, 'thickness': 0.5, 'color': '#a08458',
                  'group': 'running/tacks', 'meta': {'kind': 'tack', 'sail': 'lateen'}})
    sails.append({'name': 'lateen', 'corners': ['model:主桅/yard/fore', 'model:主桅/yard/peak', '%.1f,%.1f,%.1f' % tuple(clew)],
                  'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'color': rg['sail']['color'],
                  'meta': {'kind': 'sail', 'mast': 'main', 'sail': 'gaff', 'set': '1'}})
    tx, tz_ = hx + 0.5, ztop + 0.5
    sails.append({'name': 'pennant', 'corners': ['%.1f,%.1f,%.1f' % (tx, YC + 0.5, tz_ - 0.5), '%.1f,%.1f,%.1f' % (tx - 70, YC + 0.5, tz_ - 1.5), '%.1f,%.1f,%.1f' % (tx, YC + 0.5, tz_ - 7.5)],
                  'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'color': '#b60000', 'texture': 'textures/pennant.png', 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}})
    pk_l = yj['anchors']['peak']
    foot_l = [int(v) for v in np.floor(np.array(yj['pivot']) + (np.array(Pk) - np.array(P)) * 0.86)]
    while tuple(foot_l) not in local:
        foot_l[2] -= 1
    ep = np.array(Pk)
    sails.append({'name': 'ensign', 'corners': ['model:主桅/yard/peak', '%.1f,%.1f,%.1f' % (ep[0] - 36, ep[1], ep[2] + 2), '%.1f,%.1f,%.1f' % (ep[0] - 36, ep[1], ep[2] - 22),
                                                'model:主桅/yard/%d,%d,%d' % tuple(foot_l)],
                  'corner_names': ['head', 'fly-top', 'fly-foot', 'foot'], 'bind': [3], 'free': [2, 1], 'color': '#b60000', 'texture': 'textures/ensign.png', 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'ensign'}})
    rp = {'anchors': anchors, 'ropes': ropes, 'sails': sails}
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rp, f, ensure_ascii=False, indent=1)
    textures()
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, occ, mast, yard_w, F, Pk, clew, R)
    print(json.dumps(R, ensure_ascii=False, indent=1))


def sheet(plan, occ, mast, yard_w, F, Pk, clew, R):
    s = 3
    img = Image.new('RGB', (SX * s + 80, SZ * s + 140), (246, 242, 230))
    d = ImageDraw.Draw(img)
    d.text((30, 14), '越嶺號 新圖紙 03：桅、拉丁帆桁、三角帆（右舷外觀；帆畫成三角形外框）　kotoko 2026-10-20', fill=(20, 20, 40), font=DL.font(26))
    oy = 60 + SZ * s
    view = np.zeros((SX, SZ), np.int32)
    for k in zip(*np.nonzero(occ)):
        view[k[0], k[2]] = 1
    for (x, y, z) in mast:
        view[x, z] = 2
    for (x, y, z) in yard_w:
        view[x, z] = 3
    cmap = {1: (150, 110, 85), 2: (255, 182, 0), 3: (182, 109, 85)}
    for x in range(SX):
        for z in range(SZ):
            if view[x, z]:
                d.rectangle([40 + x * s, oy - (z + 1) * s, 40 + x * s + s - 1, oy - z * s - 1], fill=cmap[view[x, z]])
    pt = lambda p: (40 + p[0] * s, oy - p[2] * s)
    d.polygon([pt(F), pt(Pk), pt(clew)], outline=(60, 60, 160))
    wl = plan['waterline']['z']
    d.line([40, oy - (wl + 1) * s, 40 + SX * s, oy - (wl + 1) * s], fill=(40, 110, 200))
    d.text((40, oy + 20), '桅頂 z %d（甲板以上 %.1f m）；帆桁 %.0f m、前端 %s、peak %s；帆腳角離甲板 %.1f m；帆桁碰撞 %d、帆面碰撞 %d' % (
        R['mast_top_z'], R['mast_above_deck_m'], plan['rig']['yard']['v']['length'] * 0.1, R['yard_fore'], R['yard_peak'], R['clew_above_deck_m'], R['yard_hits'], R['sail_plane_hits']),
        fill=(60, 60, 60), font=DL.font(15))
    img.save(os.path.join(HERE, 'sheet03_rig_v1.png'))


if __name__ == '__main__':
    main()

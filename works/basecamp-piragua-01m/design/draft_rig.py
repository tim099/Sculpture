# 杉心號 步驟 7–8（TASK-1152）：桅、拉丁帆桁、三角帆、靜索、帆腳索、tack、長旗 ⇒
#   masks/masts/{mast,thwart_hole}.vox.txt、masks/yards/yard.vox.txt、yards.json、rig_plan.json、verify_rig.json、sheet03_rig_v1.png
#   出處：kotoko-fusta-01m/design/draft_masts.py（越嶺號）—— 一根桅、拉丁帆桁照抄；靜索、帆腳索改綁舷頂（沒有舷外槳架），tack 綁船頭，只掛一面長旗。
#   用法：python -I -X utf8 draft_rig.py [--probe=yard_z=-30]   （probe ⇒ 帆桁整根上下移，量碰撞；⛔ 不寫檔）
#   · 讀船殼與甲板-main 清單（作品 ＝ 清單已證，步驟 4、5）。
#   · 帆桁一根一件緊框子作品、固定點 pivot／fore／peak、外部模型 rotate 0 放在桅子作品裡；帆的前緣 bind 在帆桁上、clew 自由；
#     帆桁 meta yard=gaff＋rig=lateen（Ship_Masts §5）；只有一面帆 ⇒ 帆 meta set 1（Ship_Rigging §9.1）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 100


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def load_list(f):
    return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def world():
    """船殼（1）＋甲板-main（2）的實心格。"""
    occ = np.zeros((SX, SY, SZ), np.uint8)
    for i, f in ((1, ('hull', 'hull')), (2, ('deck', 'deck_main'))):
        a = load_list(os.path.join(HERE, 'masks', f[0], f[1] + '.vox.txt'))
        occ[a[:, 0], a[:, 1], a[:, 2]] = i
    return occ


def rim(occ, x, sg, YC):
    """x 那一站、sg 那一舷船殼最外、最高的那一格（舷頂外緣）。"""
    ys = [y for y in range(SY) if occ[x, y].any() and (y - YC) * sg > 0 and (occ[x, y] == 1).any()]
    y = max(ys, key=lambda y: (y - YC) * sg)
    z = int(np.where(occ[x, y] == 1)[0].max())
    return [x, y, z]


def build(plan, probe):
    occ = world()
    YC = plan['space']['yc']
    rg = {k: V(v) for k, v in plan['rig'].items()}
    m, y, sl = rg['mast'], rg['yard'], rg['sail']
    ztop = m['top_z']
    cx = m['x'] + 0.5
    mast, holes = {}, []
    for z in range(m['step_z'], ztop + 1):
        t = (z - m['step_z']) / (ztop - m['step_z'])
        r = m['r_base'] + (m['r_top'] - m['r_base']) * t
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for yy in range(YC - 2, YC + 3):
                head = z > ztop - m['head'] and abs(x - m['x']) <= 1 and abs(yy - YC) <= 1
                if (x + 0.5 - cx) ** 2 + (yy - YC) ** 2 <= r * r + 1e-9 or head:
                    if occ[x, yy, z] == 1:
                        raise SystemExit('✗ 桅撞到船殼（%d,%d,%d）' % (x, yy, z))
                    if occ[x, yy, z] == 2:
                        holes.append((x, yy, z))
                    mast[(x, yy, z)] = 68 if head else m['color']
    zp = ztop - y['below_top'] + probe.get('yard_z', 0)
    P = np.array([cx, YC + y['dy'] + 0.5, zp + 0.5])
    ang = math.radians(y['angle_deg'])
    u = np.array([math.cos(ang), 0.0, -math.sin(ang)])            # 往前端（船頭、往下）
    F = P + u * y['length'] * y['pivot_frac']
    Pk = P - u * y['length'] * (1 - y['pivot_frac'])
    yard_w = {}
    lo = np.floor(np.minimum(F, Pk) - 2).astype(int)
    hi = np.ceil(np.maximum(F, Pk) + 2).astype(int)
    for x in range(lo[0], hi[0] + 1):
        for z in range(lo[2], hi[2] + 1):
            for yy in range(lo[1], hi[1] + 1):
                q = np.array([x + 0.5, yy + 0.5, z + 0.5])
                s = float((q - Pk) @ u) / y['length']
                if not (0 <= s <= 1):
                    continue
                dist = np.linalg.norm((q - Pk) - u * s * y['length'])
                r = y['r_end'] + (y['r_mid'] - y['r_end']) * math.sin(math.pi * s) ** 0.6
                if dist <= r:
                    yard_w[(x, yy, z)] = y['color']
    inside = lambda k: 0 <= k[0] < SX and 0 <= k[1] < SY and 0 <= k[2] < SZ
    hit_yard = sum(1 for k in yard_w if (inside(k) and occ[k]) or k in mast)
    # 帆：tack ＝ 帆桁前端、head ＝ peak；clew 在帆桁下方（xz 平面兩圓交點取低的）
    Lf, Ll = y['length'] * sl['foot_ratio'], y['length'] * sl['leech_ratio']
    Fx, Fz, Px, Pz = F[0], F[2], Pk[0], Pk[2]
    D = math.hypot(Px - Fx, Pz - Fz)
    a = (Lf * Lf - Ll * Ll + D * D) / (2 * D)
    h = math.sqrt(max(0.0, Lf * Lf - a * a))
    mx, mz = Fx + a * (Px - Fx) / D, Fz + a * (Pz - Fz) / D
    C = min([(mx + h * (Pz - Fz) / D, mz - h * (Px - Fx) / D), (mx - h * (Pz - Fz) / D, mz + h * (Px - Fx) / D)], key=lambda c: c[1])
    clew = np.array([C[0], F[1], C[1]])
    hit_sail = 0
    for i in range(0, 41):
        for j in range(0, 41 - i):
            q = F + (Pk - F) * (i / 40) + (clew - F) * (j / 40)
            k = tuple(np.floor(q).astype(int))
            if inside(k) and (occ[k] or k in mast):
                hit_sail += 1
    area = 0.5 * np.linalg.norm(np.cross(Pk - F, clew - F)) * 0.01
    return occ, YC, rg, ztop, mast, holes, yard_w, F, Pk, P, clew, hit_yard, hit_sail, area


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    occ, YC, rg, ztop, mast, holes, yard_w, F, Pk, P, clew, hit_yard, hit_sail, area = build(plan, probe)
    gun_z = {x: int(np.where((occ[x] == 1).any(axis=0))[0].max()) for x in range(SX) if (occ[x] == 1).any()}
    R = {'mast_cells': len(mast), 'thwart_holes': len(holes), 'mast_top_z': ztop, 'mast_m_above_floor': round((ztop + 1 - 1) * 0.1, 1),
         'yard_cells': len(yard_w), 'yard_fore': [round(float(v), 1) for v in F], 'yard_peak': [round(float(v), 1) for v in Pk], 'clew': [round(float(v), 1) for v in clew],
         'clew_above_gunwale_m': round(float(clew[2] - (gun_z.get(int(clew[0]), 8) + 1)) * 0.1, 2), 'fore_above_gunwale_m': round(float(F[2] - (gun_z.get(int(F[0]), 10) + 1)) * 0.1, 2),
         'sail_area_m2': round(float(area), 2), 'yard_hits': hit_yard, 'sail_plane_hits': hit_sail,
         'lateen_max_swing_deg': round(math.degrees(math.asin(min(1.0, 25.0 / math.hypot(F[0] - P[0], F[1] - P[1])))), 1)}
    if probe:
        print(json.dumps({'probe': probe, 'yard_hits': hit_yard, 'sail_plane_hits': hit_sail}, ensure_ascii=False))
        return
    for sub in ('masts', 'yards'):
        os.makedirs(os.path.join(HERE, 'masks', sub), exist_ok=True)

    def dump(fn, cells, title):
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 杉心號 %s（draft_rig.py）x,y,z,color\n' % title)
            f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in sorted(cells.items())))
        return hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    R['sha256'] = {'mast': dump(os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt'), mast, '桅（整船的座標，at 0,0,0）')}
    deck = {tuple(r[:3]): r[3] for r in load_list(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt')).tolist()}
    R['sha256']['thwart_hole'] = dump(os.path.join(HERE, 'masks', 'masts', 'thwart_hole.vox.txt'), {k: deck[k] for k in holes}, '桅孔（從甲板-main 第七塊坐板刻掉；帶原本的顏色守門）')
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
          'pivot': [piv[0] + 0.5, piv[1] + 0.5, piv[2] + 0.5], 'mast_link': '桅',
          'meta': {'kind': 'yard', 'mast': 'main', 'yard': 'gaff', 'rig': 'lateen', 'sail': 'lateen', 'length_m': round(rg['yard']['length'] * 0.1, 1),
                   'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}}
    for nm, a in yj['anchors'].items():
        assert tuple(a) in local, ('帆桁固定點不在格上', nm, a)
    yj['at'] = [round(off[i] + yj['pivot'][i], 3) for i in range(3)]
    with open(os.path.join(HERE, 'yards.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'main': yj}, f, ensure_ascii=False, indent=1)
    # 索具：hound（桅頭兩舷各一格）、靜索與帆腳索綁舷頂、tack 綁船頭
    hz = ztop - rg['shrouds']['hound_below_top']
    hx = rg['mast']['x']
    anchors = [{'work': 'mast', 'name': 'hound-P', 'at': [hx, YC - 1, hz]}, {'work': 'mast', 'name': 'hound-S', 'at': [hx, YC + 1, hz]}]
    for a in anchors:
        assert tuple(a['at']) in mast, ('hound 不在桅的格上', a)
    ropes, sails = [], []
    for side, sg in (('P', -1), ('S', 1)):
        for i, x in enumerate(rg['shrouds']['x'], 1):
            a = rim(occ, x, sg, YC)
            anchors.append({'work': 'hull', 'name': 'shroud-%s%d' % (side, i), 'at': a})
            ropes.append({'name': 'shroud-%s%d' % (side, i), 'from': '桅/hound-%s' % side, 'to': '船殼/shroud-%s%d' % (side, i), 'slack': 1.0,
                          'thickness': 0.4, 'color': '#2b2620', 'group': 'standing/shrouds', 'meta': {'kind': 'shroud'}})
        a = rim(occ, int(round(clew[0])) - 6, sg, YC)
        anchors.append({'work': 'hull', 'name': 'belay-sheet-%s' % side, 'at': a})
        ropes.append({'name': 'lateen.sheet-%s' % side, 'from': 'sail:lateen/clew', 'to': '船殼/belay-sheet-%s' % side, 'slack': 1.03,
                      'thickness': 0.35, 'color': '#a08458', 'group': 'running/sheets', 'meta': {'kind': 'sheet', 'sail': 'lateen'}})
    tx = max(x for x in gun_z if occ[x, YC, gun_z[x]] == 1 and x <= 122)
    tack = [tx, YC, gun_z[tx]]
    anchors.append({'work': 'hull', 'name': 'tack', 'at': tack})
    ropes.append({'name': 'lateen.tack', 'from': 'model:桅/yard/fore', 'to': '船殼/tack', 'slack': 1.02, 'thickness': 0.4, 'color': '#a08458',
                  'group': 'running/tacks', 'meta': {'kind': 'tack', 'sail': 'lateen'}})
    sails.append({'name': 'lateen', 'corners': ['model:桅/yard/fore', 'model:桅/yard/peak', '%.1f,%.1f,%.1f' % tuple(clew)],
                  'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'color': rg['sail']['color'],
                  'meta': {'kind': 'sail', 'mast': 'main', 'sail': 'gaff', 'set': '1'}})
    pn = rg['pennant']
    tx_, tz_ = hx + 0.5, ztop + 0.5
    sails.append({'name': 'pennant', 'corners': ['%.1f,%.1f,%.1f' % (tx_, YC + 0.5, tz_ + 0.5), '%.1f,%.1f,%.1f' % (tx_ - pn['length'], YC + 0.5, tz_ - 0.5), '%.1f,%.1f,%.1f' % (tx_, YC + 0.5, tz_ - 3.5)],
                  'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'color': pn['color'], 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}})
    rp = {'anchors': anchors, 'ropes': ropes, 'sails': sails}
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rp, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_rig.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, occ, mast, yard_w, F, Pk, clew, R, rp)
    print(json.dumps(R, ensure_ascii=False, indent=1))


def sheet(plan, occ, mast, yard_w, F, Pk, clew, R, rp):
    s = 7
    img = Image.new('RGB', (SX * s + 80, 94 * s + 120), (246, 242, 230))
    d = ImageDraw.Draw(img)
    d.text((30, 14), '杉心號 新圖紙 03：桅、拉丁帆桁、三角帆、靜索（左舷外觀；帆畫成三角形外框）', fill=(20, 20, 40), font=font(24))
    oy = 60 + 92 * s
    view = np.zeros((SX, SZ), np.int32)
    for k in zip(*np.nonzero(occ)):
        view[k[0], k[2]] = 1
    for (x, y, z) in mast:
        view[x, z] = 2
    for (x, y, z) in yard_w:
        if 0 <= x < SX and 0 <= z < SZ:
            view[x, z] = 3
    cmap = {1: (145, 72, 0), 2: (90, 70, 50), 3: (182, 109, 85)}
    for x in range(SX):
        for z in range(92):
            if view[x, z]:
                d.rectangle([40 + x * s, oy - (z + 1) * s, 40 + x * s + s - 1, oy - z * s - 1], fill=cmap[view[x, z]])
    pt = lambda p: (40 + p[0] * s, oy - p[2] * s)
    d.polygon([pt(F), pt(Pk), pt(clew)], outline=(60, 60, 160))
    A = {a['name']: a['at'] for a in rp['anchors']}
    for r in rp['ropes']:
        if r['from'].startswith('桅/'):
            a, b = A[r['from'].split('/')[1]], A[r['to'].split('/')[1]]
            d.line([pt(np.array(a) + 0.5), pt(np.array(b) + 0.5)], fill=(40, 30, 20))
    wl = plan['waterline']['z']
    d.line([40, oy - wl * s, 40 + SX * s, oy - wl * s], fill=(40, 110, 200))
    d.text((40, oy + 20), '桅頂 z %d（艙底起 %.1f m）；帆桁 %.1f m、前端 %s、peak %s；帆 %.1f m²、帆腳角離舷頂 %.1f m、前端離舷頂 %.1f m；帆桁碰撞 %d、帆面碰撞 %d；拉丁帆最大擺角 %.1f°' % (
        R['mast_top_z'], R['mast_m_above_floor'], plan['rig']['yard']['v']['length'] * 0.1, R['yard_fore'], R['yard_peak'], R['sail_area_m2'], R['clew_above_gunwale_m'],
        R['fore_above_gunwale_m'], R['yard_hits'], R['sail_plane_hits'], R['lateen_max_swing_deg']), fill=(60, 60, 60), font=font(14))
    img.save(os.path.join(HERE, 'sheet03_rig_v1.png'))


if __name__ == '__main__':
    main()

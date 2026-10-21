# 砲塔的轉動範圍（arc）與開火範圍（fire）：照整艘的格子（gen_dingyuan 的 own.npy，鏡像部件補上）＋別的砲塔、小艇的外形當障礙，
#   每 1° 量：① 砲管（照剖面半徑取樣）碰不碰船上的實心 ⇒ 轉得過去；② 從砲口沿砲軸水平往外 60 m 的砲線碰不碰 ⇒ 開得了火。
#   arc ＝ 包含 0°（前方）的最大連續轉得過去區間；fire ＝ arc 裡包含 0° 的最大連續開得了火區間。角度：逆時針（從上往下看）為正 ＝ 往 +y 轉（造船規格 §4.5）。
#   也量砲罩掃過的圓柱裡有沒有別的格（要 0）。
# 用法：python -I -X utf8 -B check_arcs.py <gen 輸出資料夾> [--shift=dx]（反向對照：把障礙整體往 +x 挪 dx 格）
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P = PLAN['params']; PP = PLAN['parts']
out = sys.argv[1]
shift = int([a.split('=')[1] for a in sys.argv[2:] if a.startswith('--shift=')][0]) if any(a.startswith('--shift=') for a in sys.argv[2:]) else 0
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
NX, NY, NZ = own.shape; YC = (NY - 1) // 2
solid = own > 0
for nm in ('boilers-aft', 'boilers-fwd', 'engine', 'shaft'):
    solid |= (own == names.index(nm) + 1)[:, ::-1, :]
for nm in ('rudder', 'screw-s', 'screw-p'):                              # 模型（水線下，不影響），留著
    pass
# 障礙：別的砲塔（圓柱）、小艇（盒子）
TM, T15 = P['turret_main'], P['turret_15']
obst_cyl = []
for b in P['barbettes']:
    obst_cyl.append(('turret-' + b['name'], b['x'] + 0.5, YC + b['dy'] + 0.5, TM['r_hood'][1] + 0.5, TM['z_table'], TM['hood_top'] + TM['dome']))
for t in P['turrets_15']:
    obst_cyl.append(('turret15-' + t['name'], t['x'] + 0.5, YC + 0.5, T15['r'][1] + 0.5, T15['z0'], T15['z0'] + T15['h'] + T15['dome']))
tb, sb, fb = P['torpedo_boats'], P['stern_boats'], P['fwd_boats']
L = PP['torpedo_boat']['len']; H_ = PP['torpedo_boat']['half']
obst_box = [('torpedo-boat-S', tb['x'], tb['x'] + L, YC + tb['dy'] - H_, YC + tb['dy'] + H_, tb['z'], tb['z'] + 32),
            ('torpedo-boat-P', tb['x'], tb['x'] + L, YC - tb['dy'] - H_, YC - tb['dy'] + H_, tb['z'], tb['z'] + 32),
            ('stern-boats', sb['x'] + 12, sb['x'] + 112, YC - sb['dy'] - 12, YC + sb['dy'] + 12, sb['z'], sb['z'] + 18),
            ('fwd-boats', fb['x'], fb['x'] + 81, YC - fb['dy'] - 12, YC + fb['dy'] + 12, P['z_upper_deck'] + 1, P['z_upper_deck'] + 20)]


def hit(x, y, z, me):
    """(x, y, z) 是不是障礙（陣列外 ＝ 不是）。me ＝ 自己那一座（不算）。"""
    x = x - shift
    xi, yi, zi = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    if 0 <= xi < NX and 0 <= yi < NY and 0 <= zi < NZ and solid[xi, yi, zi]: return 'ship:' + (names[own[xi, yi, zi] - 1] if own[xi, yi, zi] else 'mirror')
    for nm, cx, cy, r, z0, z1 in obst_cyl:
        if nm != me and z0 <= z <= z1 and math.hypot(x - cx, y - cy) <= r: return nm
    for nm, x0, x1, y0, y1, z0, z1 in obst_box:
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1: return nm
    return None


def radius_at(spec, u_comp):
    """砲管在元件座標 y 的半徑（元件格）。"""
    t = (u_comp - spec['breech_y']) / (spec['len'] - 1)
    if t < 0 or t > 1: return 0
    pr = spec['profile']
    return float(np.interp(t, [p[0] for p in pr], [p[1] for p in pr]))


def turret(me, cx, cy, front_deg, guns, spec, scale, gz, hood):
    """guns：[(橫向偏移, 耳軸在轉軸前幾格)]；砲管照元件剖面 × scale。hood：(r, z0, z1)。"""
    ty = spec['breech_y'] + spec['trunnion_t'] * (spec['len'] - 1)
    blocked_turn, blocked_fire = {}, {}
    for th in range(-180, 180):
        a = math.radians(front_deg + th)
        fx, fy = math.cos(a), math.sin(a); lx, ly = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)
        bt = bf = None
        for lat, fwd in guns:
            for uc in np.arange(spec['breech_y'], spec['breech_y'] + spec['len'], 1.0):
                r = radius_at(spec, uc) * scale
                u = fwd + (uc - ty) * scale
                if math.hypot(u, lat) < hood[0] - 1: continue                 # 砲罩裡面（自己的殼，不算）
                px, py = cx + fx * u + lx * lat, cy + fy * u + ly * lat
                for k in range(9):
                    if k == 8: ox, oz = 0, 0
                    else: ox, oz = r * math.cos(k * math.pi / 4), r * math.sin(k * math.pi / 4)
                    h = hit(px + lx * ox, py + ly * ox, gz + oz, me)
                    if h: bt = bt or h; break
                if bt: break
            u0 = fwd + (spec['breech_y'] + spec['len'] - 1 - ty) * scale
            for s in np.arange(0, 600, 0.5):
                u = u0 + s
                h = hit(cx + fx * u + lx * lat, cy + fy * u + ly * lat, gz, me)
                if h: bf = bf or h; break
        if bt: blocked_turn[th] = bt
        if bf: blocked_fire[th] = bf
    def span(bad):
        if not bad: return (-180, 180)
        lo = 0
        while lo - 1 >= -180 and (lo - 1) not in bad: lo -= 1
        hi = 0
        while hi + 1 <= 179 and (hi + 1) not in bad: hi += 1
        return (lo, hi)
    arc = span(blocked_turn)
    fire = span({**blocked_fire, **{k: 'arc' for k in range(-180, 180) if k < arc[0] or k > arc[1]}})
    # 砲罩掃過的圓柱裡別的格
    r0, z0, z1 = hood
    n = 0
    for xi in range(int(cx - r0 - 1), int(cx + r0 + 2)):
        for yi in range(int(cy - r0 - 1), int(cy + r0 + 2)):
            if math.hypot(xi + 0.5 - cx, yi + 0.5 - cy) <= r0 + 0.5:
                n += int(solid[xi - shift, yi, z0:z1 + 1].sum()) if 0 <= xi - shift < NX else 0
    why = {}
    for d in (blocked_turn, blocked_fire):
        for v in d.values(): why[v] = why.get(v, 0) + 1
    return dict(arc=list(arc), fire=list(fire), turn_blocked=len(blocked_turn), fire_blocked=len(blocked_fire), why=why, hood_cells=n)


res = {}
for b in P['barbettes']:
    cx, cy = b['x'] + 0.5, YC + b['dy'] + 0.5
    front = 90 if b['dy'] > 0 else -90
    res['turret-' + b['name']] = turret('turret-' + b['name'], cx, cy, front, [(-TM['gun_dx'], TM['gun_fwd']), (TM['gun_dx'], TM['gun_fwd'])], PP['gun305'], 0.5,
                                        TM['z_table'] + 1 + (PP['gun305']['axis'][1] + 0.5) * 0.5, (TM['r_hood'][1], TM['z_table'], TM['hood_top'] + TM['dome']))
for t in P['turrets_15']:
    cx, cy = t['x'] + 0.5, YC + 0.5
    front = 0 if t['front'] > 0 else 180
    res['turret15-' + t['name']] = turret('turret15-' + t['name'], cx, cy, front, [(0, T15['gun_fwd'])], PP['gun150'], 0.5,
                                          T15['z0'] + (PP['gun150']['axis'][1] + 0.5) * 0.5, (T15['r'][1], T15['z0'], T15['z0'] + T15['h'] + T15['dome']))
json.dump(res, open(os.path.join(out, 'arcs%s.json' % ('' if not shift else '_shift%d' % shift)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False))

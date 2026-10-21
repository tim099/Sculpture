# 主砲（32 cm Canet，露砲台＋砲罩，砲塔層）的轉動範圍（arc）與開火範圍（fire）：照整艘的格子（gen_matsushima 的 own.npy，鏡像部件補上）
#   ＋擺好的砲（place_guns 的 guns.json，照外框當障礙），每 1° 量：① 砲管（照剖面半徑取樣）碰不碰船上的實心 ⇒ 轉得過去；
#   ② 從砲口沿砲軸水平往外 60 m 的砲線碰不碰 ⇒ 開得了火。arc ＝ 包含 0°（前方 ＝ 朝船尾）的最大連續轉得過去區間；fire ＝ arc 裡包含 0° 的最大連續開得了火區間。
#   角度：逆時針（從上往下看）為正 ＝ 往 +y 轉（造船規格 §4.5）。也量砲罩掃過的圓柱裡有沒有別的格（要 0）。
#   寫法照定遠號的 check_arcs.py（trailhead）。
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
for nm in ('boilers', 'engine', 'shaft'):
    solid |= (own == names.index(nm) + 1)[:, ::-1, :]
GUNS = json.load(open(os.path.join(out, 'guns.json'), encoding='utf-8'))
EXT = {'gun120': (0.5, PP['gun120']['frame']), 'gun57': (0.2, PP['gun57']['frame']), 'gun47': (0.2, PP['gun47']['frame']), 'h37': (0.2, [37, 92, 72]),
       'basecamp-ember-01m-boat': (0.5, [180, 52, 27]), 'basecamp-frigate-constitution-01m-whaleboat': (0.5, [171, 37, 21]), 'basecamp-frigate-constitution-01m-anchor': (0.6, [47, 33, 58])}
obst_box = []                                                              # 擺好的砲：外框（照擺法轉過的外框，保守）
for nm, g in GUNS.items():
    if not g.get('at'): continue
    sc, fr = EXT[g['src']]
    r = math.hypot(fr[0], fr[1]) * sc / 2
    obst_box.append((nm, g['at'][0] - r, g['at'][0] + r, g['at'][1] - r, g['at'][1] + r, g['at'][2], g['at'][2] + fr[2] * sc))


def hit(x, y, z):
    x = x - shift
    xi, yi, zi = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    if 0 <= xi < NX and 0 <= yi < NY and 0 <= zi < NZ and solid[xi, yi, zi]: return 'ship:' + (names[own[xi, yi, zi] - 1] if own[xi, yi, zi] else 'mirror')
    for nm, x0, x1, y0, y1, z0, z1 in obst_box:
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1: return nm
    return None


def radius_at(spec, gy):
    t = (gy - spec['breech_y']) / (spec['len'] - 1)
    if t < 0 or t > 1: return 0
    pr = spec['profile']
    return float(np.interp(t, [p[0] for p in pr], [p[1] for p in pr]))


TM = P['turret_main']; spec = PP['gun320']; sc = 0.5
cx, cy = P['barbette']['x'] + 0.5, YC + 0.5
ty = spec['breech_y'] + spec['trunnion_t'] * (spec['len'] - 1)
gz = TM['z_table'] + 1 + (spec['axis'][1] + 0.5) * sc
a_, f_, b_ = TM['hood_plan']
hood_r = max(a_ - f_, b_)                                                   # 砲罩掃過的半徑（水滴形最遠那一點）
front = 180                                                                 # 前方 ＝ 朝船尾（−x）
blocked_turn, blocked_fire = {}, {}
for th in range(-180, 180):
    a = math.radians(front + th)
    fx, fy = math.cos(a), math.sin(a); lx, ly = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)
    bt = bf = None
    for gy in np.arange(spec['breech_y'], spec['breech_y'] + spec['len'], 1.0):
        r = radius_at(spec, gy) * sc
        u = TM['gun_u'] + (gy - ty) * sc
        if -b_ + 1 < u < (a_ + f_) - 1: continue                           # 砲罩裡面（自己的殼，不算）
        px, py = cx + fx * u, cy + fy * u
        for k in range(9):
            if k == 8: ox, oz = 0, 0
            else: ox, oz = r * math.cos(k * math.pi / 4), r * math.sin(k * math.pi / 4)
            h = hit(px + lx * ox, py + ly * ox, gz + oz)
            if h: bt = bt or h; break
        if bt: break
    u0 = TM['gun_u'] + (spec['breech_y'] + spec['len'] - 1 - ty) * sc
    for s in np.arange(0, 600, 0.5):
        u = u0 + s
        h = hit(cx + fx * u, cy + fy * u, gz)
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
n = 0                                                                       # 砲罩掃過的圓柱裡別的格（轉盤頂到罩頂）
for xi in range(int(cx - hood_r - 1), int(cx + hood_r + 2)):
    for yi in range(int(cy - hood_r - 1), int(cy + hood_r + 2)):
        if math.hypot(xi + 0.5 - cx, yi + 0.5 - cy) <= hood_r + 0.5:
            n += int(solid[xi - shift, yi, TM['z_table'] + 1:TM['hood_top'] + 2].sum()) if 0 <= xi - shift < NX else 0
why = {}
for d in (blocked_turn, blocked_fire):
    for v in d.values(): why[v] = why.get(v, 0) + 1
res = {'turret-main': dict(arc=list(arc), fire=list(fire), turn_blocked=len(blocked_turn), fire_blocked=len(blocked_fire), why=why, hood_cells=n, hood_r=hood_r, gun_axis_z=gz)}
json.dump(res, open(os.path.join(out, 'arcs%s.json' % ('' if not shift else '_shift%d' % shift)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False))

# 擺砲（外部模型）：每門砲照造船規格 §4.2「退到零碰撞」—— 模型每一格的格心＋八個角都不在船的實心格（含鏡像部件、先擺好的模型），再要求砲口在船殼外。
#   12 cm 砲列（中甲板，每舷 5 門）、艏追擊砲（上甲板，照角度搜）、57 mm 突出砲台：從舷外往船裡退（0.5 格一步）。
#   甲板上的迴旋砲（57 mm 船首樓後端、47 mm 桅樓與後甲板、37 mm 艦橋兩翼）：位置固定，量開局零碰撞。
# 用法：python -I -X utf8 -B place_guns.py <gen 輸出> <parts 輸出>   ⇒ <gen 輸出>/guns.json
# 反向對照：--shift=dz 把每門砲往下沉 dz 格再量（要報碰撞）。
import sys, os, json, math
import numpy as np

out, pout = sys.argv[1], sys.argv[2]
SHIFT = float([a.split('=')[1] for a in sys.argv[3:] if a.startswith('--shift=')][0]) if any(a.startswith('--shift=') for a in sys.argv[3:]) else 0
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P = PLAN['params']
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))
M = json.load(open(os.path.join(out, 'matsushima_meta.json'), encoding='utf-8'))
own = np.load(os.path.join(out, 'own.npy'))
names = M['names']
NX, NY, NZ = own.shape; YC = M['plan']['YC']; WALK = M['plan']['walk']
solid = own > 0
for nm in ('boilers', 'engine', 'shaft'):
    solid |= (own == names.index(nm) + 1)[:, ::-1, :]
hull = own == names.index('hull') + 1
taken = np.zeros_like(solid)                                              # 先擺好的模型（格心）
CORN = np.array([[0, 0, 0]] + [[sx, sy, sz] for sx in (-0.49, 0.49) for sy in (-0.49, 0.49) for sz in (-0.49, 0.49)], np.float32)


def cells(key):
    a = np.array([[int(v) for v in l.split(',')] for l in open(os.path.join(pout, key + '.txt'), encoding='utf-8') if l[:1].isdigit()], np.float32)
    return a[:, :3]


def xform(pts, pivot, rz, sc, at):
    p = (pts - np.asarray(pivot, np.float32)) * sc
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c, p[:, 2]], 1) + np.asarray(at, np.float32)


def hits(cl, pivot, rz, sc, at):
    """模型格心＋八角落在船的實心或已擺好的模型裡幾點。"""
    pts = (cl[:, None, :] + 0.5 + CORN[None, :, :]).reshape(-1, 3)
    q = np.floor(xform(pts, pivot, rz, sc, at)).astype(int)
    ok = (q[:, 0] >= 0) & (q[:, 0] < NX) & (q[:, 1] >= 0) & (q[:, 1] < NY) & (q[:, 2] >= 0) & (q[:, 2] < NZ)
    q = q[ok]
    return int((solid[q[:, 0], q[:, 1], q[:, 2]] | taken[q[:, 0], q[:, 1], q[:, 2]]).sum())


def outside_hull(pt):
    """這一點在船殼外面（沿 y 往外、這一欄外板以外）。"""
    x, y, z = (int(math.floor(v)) for v in pt)
    col = hull[x, :, z]
    ys = np.nonzero(col)[0]
    if not len(ys): return True
    return y > ys.max() or y < ys.min()


def out_by(pt):
    """這一點伸出外板幾格（沿 y；負 ＝ 在殼裡）。"""
    x, y, z = (int(math.floor(v)) for v in pt)
    ys = np.nonzero(hull[x, :, z])[0]
    if not len(ys): return 99.0
    return float(max(pt[1] - (ys.max() + 1), ys.min() - pt[1]))


def take(cl, pivot, rz, sc, at):
    q = np.floor(xform(cl + 0.5, pivot, rz, sc, at)).astype(int)
    q = q[(q[:, 0] >= 0) & (q[:, 0] < NX) & (q[:, 1] >= 0) & (q[:, 1] < NY) & (q[:, 2] >= 0) & (q[:, 2] < NZ)]
    taken[q[:, 0], q[:, 1], q[:, 2]] = True


res = {}
GUNS = {k: cells(k) for k in ('gun120', 'gun57', 'gun47')}
A = {k: PM[k]['anchors'] for k in ('gun120', 'gun57', 'gun47')}
SC = {'gun120': 0.5, 'gun57': 0.2, 'gun47': 0.2}


def piv(key):
    a = A[key]['pivot']; return [a[0] + 0.5, a[1] + 0.5, 0]


def muzzle(key, rz, at):
    m = np.array([A[key]['muzzle']], np.float32) + 0.5
    return xform(m, piv(key), rz, SC[key], at)[0]


def push_in(key, x, z, sg, rz, y_out=None):
    """從船裡往舷外推：y 從中線旁起每 0.5 格往外，碰到第一個碰撞就停，取前一個零碰撞的位置（砲盾、砲架留在牆裡面，砲管從砲門伸出去）。
    回傳 at、碰撞點數、砲口在不在殼外。y_out：從離中線幾格起推（突出砲台）。"""
    cl = GUNS[key]
    y = YC + sg * (y_out if y_out else 5)
    last = None
    while 0 < y < NY - 1:
        at = [x, y, z - SHIFT]
        h = hits(cl, piv(key), rz, SC[key], at)
        if h == 0: last = at
        elif last is not None: break
        y += sg * 0.5
    if last is None: return None, -1, False
    return last, 0, outside_hull(muzzle(key, rz, last))


# 12 cm 砲列：中甲板，每舷 5 門（右舷 rotate 0 砲口 +y；左舷 rotate 180）
bt = P['battery']
for i, x_ in enumerate(bt['x']):
    for s, sg, rz in (('S', 1, 0), ('P', -1, 180)):
        at, h, mo = push_in('gun120', x_ + 0.5, WALK['middle'], sg, rz)
        res['砲-%s%d' % (s, i + 1)] = dict(src='gun120', deck='甲板-middle', at=at, rz=rz, hits=h, muzzle_out=bool(mo), dy=None if at is None else round(abs(at[1] - YC), 1))
        if at: take(GUNS['gun120'], piv('gun120'), rz, 0.5, at)
# 艏追擊砲：上甲板，右舷砲口往前偏 φ（rz ＝ φ − 90）、左舷 rz ＝ −90 − φ；從砲門外沿砲軸往裡退
bc = P['bow_chasers']; pzc = (bc['port'][1] + bc['port'][2]) / 2
best = None
cl = GUNS['gun120']
for phi in range(10, 85, 5):
    ok = True; pl = {}
    for s, sg in (('S', 1), ('P', -1)):
        rz = phi - 90 if sg > 0 else -90 - phi
        d = np.array([math.cos(math.radians(phi)), sg * math.sin(math.radians(phi)), 0])
        ys = np.nonzero(hull[bc['x'], :, bc['port'][1] - 2])[0]
        port_out = None                # 砲門底下那一層的外板（砲門那幾層已經刻穿）
        port_out = np.array([bc['x'] + 0.5, (ys.max() + 1.5) if sg > 0 else (ys.min() - 0.5), WALK['upper']])
        mlen = (A['gun120']['muzzle'][1] - A['gun120']['pivot'][1]) * 0.5
        found = None                                                      # 沿砲軸從船裡往外推（砲軸穿過砲門中心）：第一次碰撞前的最後一個零碰撞位置
        for k in range(0, 200):
            at = port_out - d * (mlen + 40 - k * 0.5)
            at = [float(at[0]), float(at[1]), WALK['upper'] - SHIFT]
            if hits(cl, piv('gun120'), rz, 0.5, at) == 0: found = at
            elif found is not None: break
        if not found:
            ok = False; break
        thru = abs(muzzle('gun120', rz, found)[0] - (bc['x'] + 0.5)) <= bc['port'][0] + 12   # 砲口在砲門附近（從砲門伸出去，不是從船頭別處穿出）
        # 往外推回去：在零碰撞的範圍裡砲口儘量伸出去
        mo = out_by(muzzle('gun120', rz, found)) >= 4 and thru          # 砲口伸出外板至少 0.4 m
        pl[s] = dict(at=found, rz=rz, muzzle_out=bool(mo))
        if not mo: ok = False; break
    if ok:
        best = (phi, pl); break
if best:
    phi, pl = best
    for s in ('S', 'P'):
        res['艏砲-' + s] = dict(src='gun120', deck='甲板-upper', at=pl[s]['at'], rz=pl[s]['rz'], hits=0, muzzle_out=pl[s]['muzzle_out'], phi=phi)
        take(GUNS['gun120'], piv('gun120'), pl[s]['rz'], 0.5, pl[s]['at'])
else:
    res['艏砲'] = dict(error='找不到角度')
# 57 mm 突出砲台（上甲板）：每座砲口朝舷外
for j, (sx_, cy, sg) in enumerate(M['sponsons']):
    s = 'S' if sg > 0 else 'P'
    rz = 0 if sg > 0 else 180
    at, h, mo = push_in('gun57', sx_ + 0.5, WALK['upper'], sg, rz, y_out=abs(cy - YC) - 25)
    nm = '速射砲-%s%d' % (s, P['sponsons_57']['x'].index(sx_) + 1)
    res[nm] = dict(src='gun57', deck='甲板-upper', at=at, rz=rz, hits=h, muzzle_out=bool(mo))
    if at: take(GUNS['gun57'], piv('gun57'), rz, 0.2, at)
# 甲板上的迴旋砲（位置固定）
fixed = []
fc = P['fc_57']
for s, sg in (('S', 1), ('P', -1)):
    fixed.append(('速射砲-%s3' % s, 'gun57', '甲板-fc', [fc['x'] + 0.5, YC + sg * fc['dy'] + 0.5, WALK['fc']], 0 if sg > 0 else 180))
q = P['qd_47']
for s, sg in (('S', 1), ('P', -1)):
    fixed.append(('機關砲-艉%s' % s, 'gun47', '甲板-upper', [q['x'] + 0.5, YC + sg * q['dy'] + 0.5, WALK['upper']], 0 if sg > 0 else 180))
MS = M['mast']
for top, tz, rp in (('下', MS['top1'], 15), ('上', MS['top2'], 12.5)):
    for s, sg in (('S', 1), ('P', -1)):
        fixed.append(('機關砲-%s桅樓%s' % (top, s), 'gun47', '桅', [MS['x'] + 0.5, YC + 0.5 + sg * rp, tz + 1], 0 if sg > 0 else 180))
BR = M['bridge']
fixed37 = []
for s, sg in (('S', 1), ('P', -1)):
    fixed37.append(('機關砲-艦橋' + s, [(BR['x0'] + BR['x1']) / 2 + 0.5, YC + 0.5 + sg * (BR['half'] - 8), BR['z']], 0 if sg > 0 else 180))
for nm, key, deck, at, rz in fixed:
    at = [at[0], at[1], at[2] - SHIFT]
    h = hits(GUNS[key], piv(key), rz, SC[key], at)
    res[nm] = dict(src=key, deck=deck, at=at, rz=rz, hits=h, muzzle_out=None)
    take(GUNS[key], piv(key), rz, SC[key], at)
G37 = cells('gun37')                                                         # 共用元件 trailhead-dingyuan-01m-gun-hotchkiss37 的匯出清單（0.02 m、pivot 18,40,0）
P37 = [18.5, 40.5, 0]
for nm, at, rz in fixed37:
    at = [at[0], at[1], at[2] - SHIFT]
    res[nm] = dict(src='h37', deck='艦橋', at=at, rz=rz, hits=hits(G37, P37, rz, 0.2, at), muzzle_out=None)
    take(G37, P37, rz, 0.2, at)
# 小艇（船首樓甲板的墊木上）與錨（船頭兩舷，有橫桿、錨幹直、靠船殼那一隻爪貼著外板）—— 共用元件，量開局零碰撞
BOATS = {'cutter': ('basecamp-ember-01m-boat', [90, 26, 0], 0.5), 'whale': ('basecamp-frigate-constitution-01m-whaleboat', [85.5, 18.5, 0], 0.5),
         'anchor': ('basecamp-frigate-constitution-01m-anchor', [23.5, 16.5, 56.5], 0.6)}
BC = {k: cells(v[0]) for k, v in BOATS.items()}
for key, nm, pkey, L in (('cutter', '小艇', 'boats', 90), ('whale', '小艇-whale', 'whaleboats', 85.5)):
    bt_ = P[pkey]
    for s, sg in (('S', 1), ('P', -1)):
        at = [bt_['x'] + 37.5 + 0.5, YC + sg * bt_['dy'] + 0.5, bt_['z'] - SHIFT]
        h = hits(BC[key], BOATS[key][1], 0, BOATS[key][2], at)
        res['%s-%s' % (nm, s)] = dict(src=BOATS[key][0], deck='艇架', at=at, rz=0, hits=h, pivot=BOATS[key][1], scale=BOATS[key][2])
        take(BC[key], BOATS[key][1], 0, BOATS[key][2], at)
an = P['anchors']
for s, sg in (('S', 1), ('P', -1)):
    ys = np.nonzero(hull[an['x'], :, 100])[0]
    yo = (ys.max() + 1) if sg > 0 else ys.min()
    sc_ = BOATS['anchor'][2]
    at = [an['x'] + 0.5, yo + sg * (14 * sc_ + 1.5), 128 - SHIFT]
    h = hits(BC['anchor'], BOATS['anchor'][1], 0, sc_, at)
    res['錨-' + s] = dict(src=BOATS['anchor'][0], deck='組裝件', at=at, rz=0, hits=h, pivot=BOATS['anchor'][1], scale=sc_)
json.dump(res, open(os.path.join(out, 'guns%s.json'  % ('' if not SHIFT else '_shift')), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False))

# 松島號的零件產生程式 —— 通用部件（32 cm Canet 砲＋滑架、12 cm 速射砲＋盾、57 mm／47 mm 哈乞開斯速射砲）、主砲塔殼、旭日旗貼圖。
# 每件一個清單（x,y,z,color）＋固定點 JSON。
# 用法：python -I -X utf8 -B gen_parts.py <輸出資料夾>
# 砲照造船規格 §4.1：x 橫向（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 站的那一面；比例 0.05 m（模型 scale 0.5）、哈乞開斯 0.02 m（scale 0.2）。
# 數字的出處在 plan.json 的 parts_provenance。結構照定遠號的 gen_parts.py（trailhead）改寫。
import sys, os, json, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
C = PLAN['params']['colors']
GUN_BLACK, GUN_IRON, BRASS = 36, 73, 180


def grid(nx, ny, nz):
    return (np.arange(nx, dtype=np.float32)[:, None, None], np.arange(ny, dtype=np.float32)[None, :, None], np.arange(nz, dtype=np.float32)[None, None, :])


class Part:
    def __init__(self, shape):
        self.col = np.zeros(shape, np.uint8)

    def put(self, mask, color):
        m = mask & (self.col == 0)
        self.col[m] = color if np.isscalar(color) else np.broadcast_to(color, m.shape)[m]

    def write(self, fn, title):
        idx = np.argwhere(self.col > 0); cs = self.col[self.col > 0]
        with open(fn, 'w', newline='\n') as f:
            f.write('# %s —— x,y,z,color（框 %d×%d×%d）\n' % ((title,) + self.col.shape))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())) + '\n')
        return len(idx)


def barrel(X, Y, Z, ax, az, y_b, L, prof, bore, bore_depth):
    """沿 +y 的砲管：剖面半徑照 prof（t 0 ＝ 砲尾面、1 ＝ 砲口）內插；內膛從砲口往裡挖 bore_depth 格。"""
    t = (Y - y_b) / (L - 1)
    rad = np.interp(t, [p[0] for p in prof], [p[1] for p in prof], left=-1, right=-1)
    dr = np.hypot(X - ax, Z - az)
    body = (t >= 0) & (t <= 1) & (dr <= rad)
    hole = (dr <= bore) & (Y >= y_b + L - 1 - bore_depth)
    return body & ~hole


def canet(spec):
    """32 cm Canet 砲＋液壓滑架：砲身（多層套箍，砲尾一圈銅、斷隔螺式閂的圓蓋＋搖把）、搖架（cradle：兩片側板夾住砲身後段、耳軸）、
    斜滑座（往砲口那端低、兩條滑軌）、兩支液壓駐退筒（滑座兩側）、後面的裝填台階。"""
    nx, ny, nz = spec['frame']; ax, az = spec['axis']; y_b, L = spec['breech_y'], spec['len']
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    gun = barrel(X, Y, Z, ax, az, y_b, L, spec['profile'], spec['bore'], 16)
    ty = int(round(y_b + spec['trunnion_t'] * (L - 1)))
    ring = gun & (np.abs(Y - (y_b + 2)) <= 0.5)                                                         # 砲尾一圈黃銅
    hoop = gun & np.isin(np.round(Y).astype(int), [int(round(y_b + t * (L - 1))) for t in spec['hoops']])   # 套箍的接縫（看得出多層）
    plug = (np.hypot(X - ax, Z - az) <= spec['plug_r']) & (Y >= y_b - 2) & (Y < y_b)                      # 斷隔螺式閂塊的圓蓋
    crank = (np.abs(X - (ax + spec['plug_r'] + 1)) <= 1) & (np.abs(Y - (y_b - 1)) <= 1) & (np.abs(Z - az) <= spec['plug_r'] - 1)   # 開閂搖臂
    cw0, cw1 = spec['cradle']
    cra = (np.abs(X - ax) >= cw0) & (np.abs(X - ax) <= cw1) & (Y >= ty - spec['cradle_len']) & (Y <= ty + spec['cradle_len']) & (np.abs(Z - az) <= spec['cradle_h'])
    trun = (np.hypot(Y - ty, Z - az) <= spec['trunnion_r']) & (np.abs(X - ax) <= cw1 + 2)
    # 斜滑座：兩條滑軌，從耳軸下方往後；頂面高度 ＝ 支架（照 slide_z）
    sl0, sl1 = spec['slide']
    zs0, zs1 = spec['slide_z']                                                                           # 前端、後端的頂面高（後端高：駐退往後上坡）
    ys0, ys1 = spec['slide_y']
    t_s = np.clip((Y - ys0) / max(ys1 - ys0, 1), 0, 1)
    zsl = zs0 + (zs1 - zs0) * (1 - t_s)
    slide = (np.abs(X - ax) >= sl0) & (np.abs(X - ax) <= sl1) & (Y >= ys0) & (Y <= ys1) & (Z <= zsl)
    sup = (np.abs(X - ax) >= cw0) & (np.abs(X - ax) <= cw1) & (np.abs(Y - ty) <= spec['trunnion_r'] + 1) & (Z <= az) & (Z > 2)   # 耳軸下的支柱
    rec = np.zeros(gun.shape, bool)
    rx_, rz_, rr_ = spec['recoil']
    for sx in (-1, 1):
        rec |= (np.hypot(X - (ax + sx * rx_), Z - rz_) <= rr_) & (Y >= ty - spec['cradle_len'] - 10) & (Y <= ty + 4)
    step = (np.abs(X - ax) <= spec['step'][0]) & (Y >= y_b - spec['step'][1]) & (Y < y_b - 4) & (Z <= spec['step'][2])   # 砲尾後面的裝填台階
    p.put(ring | hoop, BRASS)
    p.put(gun | plug, GUN_BLACK)
    p.put(crank, BRASS)
    p.put(trun, GUN_BLACK)
    p.put(cra | slide | sup | rec | step, GUN_IRON)          # 沒有底板：轉盤中間的艙口（彈藥吊上來）留空
    muz = [ax, y_b + L - 1, az]
    assert p.col[tuple(muz)] == 0, '砲口那一格要空（內膛）'
    return p, {'muzzle': muz, 'breech': [ax, y_b, az], 'trunnion': [ax, ty, az], 'cascabel': [ax, y_b - 2, az]}


def qf_shield(spec):
    """速射砲（Armstrong 12 cm／40）＋中心樞軸座＋弧形砲盾：立柱、搖架、駐退筒在砲身下、側面的瞄準座與手輪、盾（前面＋兩側往後彎）。"""
    nx, ny, nz = spec['frame']; ax, az = spec['axis']; y_b, L = spec['breech_y'], spec['len']
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    gun = barrel(X, Y, Z, ax, az, y_b, L, spec['profile'], spec['bore'], 8)
    ty = int(round(y_b + spec['trunnion_t'] * (L - 1)))
    py = spec['pivot_y']
    plug = (np.hypot(X - ax, Z - az) <= spec['plug_r']) & (Y >= y_b - 1) & (Y < y_b)
    cw0, cw1 = spec['cradle']
    cra = (np.abs(X - ax) >= cw0) & (np.abs(X - ax) <= cw1) & (np.abs(Y - ty) <= spec['cradle_len']) & (np.abs(Z - az) <= 2)
    rec = (np.hypot(X - ax, Z - (az - spec['recoil'][0])) <= spec['recoil'][1]) & (Y >= ty - spec['cradle_len']) & (Y <= ty + spec['cradle_len'] + 6)
    ped = (np.hypot(X - ax, Y - py) <= spec['ped_r']) & (Z <= az - spec['recoil'][0] - spec['recoil'][1])
    base = (np.hypot(X - ax, Y - py) <= spec['ped_r'] + 3) & (Z <= 1)
    yoke = (np.abs(np.abs(X - ax) - (cw1 + 1)) <= 0.5) & (np.abs(Y - ty) <= 3) & (Z > az - 7) & (Z <= az + 1)
    sight = (np.abs(X - (ax - cw1 - 3)) <= 1) & (Y >= ty - 8) & (Y <= ty - 2) & (Z >= az - 4) & (Z <= az + 2)     # 左邊的瞄準座
    wheel = (np.abs(X - (ax + cw1 + 3)) <= 0.5) & (np.hypot(Y - (ty - 6), Z - (az - 4)) <= 3.5) & (np.hypot(Y - (ty - 6), Z - (az - 4)) > 2.2)   # 右邊的手輪
    # 盾：中心在樞軸、半徑 sr 的圓弧（前面 ± sa 度），高 z0..z1；砲口那一格開一個窄口
    sr, sa, sz0, sz1, st = spec['shield']
    rr = np.hypot(X - ax, Y - py); ang = np.degrees(np.arctan2(X - ax, Y - py))
    shield = (rr >= sr - st + 0.5) & (rr <= sr + 0.5) & (np.abs(ang) <= sa) & (Z >= sz0) & (Z <= sz1)
    roofs = (rr <= sr + 0.5) & (np.abs(ang) <= sa) & (Z > sz1 - 1) & (Z <= sz1) & (rr >= sr - 6)            # 頂上往後折一小段
    slot = (np.abs(X - ax) <= spec['slot'][0]) & (Z >= az - spec['slot'][1]) & (Z <= az + spec['slot'][1])
    p.put(gun | plug, GUN_BLACK)
    p.put((shield | roofs) & ~slot, C['grey'])
    p.put(wheel, BRASS)
    p.put(cra | rec | ped | base | yoke | sight, GUN_IRON)
    muz = [ax, y_b + L - 1, az]
    assert p.col[tuple(muz)] == 0, '砲口那一格要空（內膛）'
    return p, {'muzzle': muz, 'breech': [ax, y_b, az], 'trunnion': [ax, ty, az], 'pivot': [ax, py, 0]}


def hotchkiss_qf(spec):
    """哈乞開斯單管速射砲（57 mm 6 磅／47 mm 3 磅）＋立柱座：砲管、方形閂匣、肩托、搖架、駐退筒、立柱。"""
    nx, ny, nz = spec['frame']; ax, az = spec['axis']; y_b, L = spec['breech_y'], spec['len']
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    gun = barrel(X, Y, Z, ax, az, y_b, L, spec['profile'], spec['bore'], 10)
    bw = spec['block']
    block = (np.abs(X - ax) <= bw) & (np.abs(Z - az) <= bw) & (Y >= y_b - 2 * bw) & (Y < y_b + 2)
    py = spec['pivot_y']
    stock = (np.abs(X - (ax + bw + 2)) <= 1) & (Y >= y_b - 16) & (Y < y_b) & (np.abs(Z - (az - 4 - (y_b - Y) * 0.2)) <= 1.5)
    cra = (np.abs(X - ax) <= bw + 1) & (np.abs(Y - py) <= 10) & (Z >= az - bw - 4) & (Z < az - bw + 1)
    rec = (np.hypot(X - ax, Z - (az - bw - 2)) <= 2) & (Y >= py - 10) & (Y <= py + 20)
    yoke = (np.abs(np.abs(X - ax) - (bw + 2)) <= 1) & (np.abs(Y - py) <= 4) & (Z > az - bw - 10) & (Z <= az)
    yoke |= (np.abs(X - ax) <= bw + 3) & (np.abs(Y - py) <= 4) & (np.abs(Z - (az - bw - 10)) <= 1)
    ped = (np.hypot(X - ax, Y - py) <= 5) & (Z <= az - bw - 10)
    ped |= (np.hypot(X - ax, Y - py) <= 9) & (Z <= 2)
    sight = (np.abs(X - (ax - bw - 2)) <= 0.5) & (np.abs(Y - (y_b + 6)) <= 5) & (np.abs(Z - (az + 2)) <= 1)
    p.put(gun | block, GUN_BLACK)
    p.put(sight, BRASS)
    p.put(stock | cra | rec | yoke | ped, GUN_IRON)
    muz = [ax, y_b + L - 1, az]
    assert p.col[tuple(muz)] == 0
    return p, {'muzzle': muz, 'breech': [ax, y_b, az], 'pivot': [ax, py, 0]}


def turret_main(T):
    """主砲塔殼（0.1 m、框 N×N×NZ、轉軸在 (CX, CX)）：轉盤（中間留洞給艙口梯）＋砲盾（前面圓、後面收、頂是斜的，砲口一個豎縫、後面一扇門）。
    前方 ＝ +y。"""
    N = 2 * T['r_table'] + 1; CX = T['r_table']; NZ = T['hood_top'] - T['z_table'] + 2
    X, Y, Z = grid(N, N, NZ)
    r = np.hypot(X - CX, Y - CX)
    p = Part((N, N, NZ))
    table = (r > T['r_hole'] + 0.5) & (r <= T['r_table'] + 0.5) & (Z == 0)
    # 平面：一個「水滴」—— 前半圓（半徑 a、圓心往前 f）＋往後收到砲尾（後半照 b 收）
    a_, f_, b_ = T['hood_plan']                          # 前圓半徑、前圓心在轉軸前幾格、後面收到轉軸後幾格
    u = Y - CX; v = X - CX
    front = np.hypot(u - f_, v) <= a_ + 0.5
    back = (u <= f_) & (u >= -b_) & (np.abs(v) <= (a_ + 0.5) * np.sqrt(np.clip(1 - ((f_ - u) / (f_ + b_)) ** 2, 0, 1)))
    plan_o = front | back
    front_i = np.hypot(u - f_, v) <= a_ - T['t'] + 0.5
    back_i = (u <= f_) & (u >= -b_ + T['t']) & (np.abs(v) <= (a_ - T['t'] + 0.5) * np.sqrt(np.clip(1 - ((f_ - u) / (f_ + b_ - T['t'])) ** 2, 0, 1)))
    plan_i = front_i | back_i
    zt = T['hood_top'] - T['z_table']
    zt_back = zt - T['roof_drop']                        # 頂往後斜下
    ztop = zt_back + (zt - zt_back) * np.clip((u + b_) / (f_ + a_ + b_), 0, 1)
    ztop = np.floor(ztop)
    wall = plan_o & ~plan_i & (Z >= 1) & (Z <= ztop)
    roof = plan_o & (Z > ztop - 1) & (Z <= ztop + 1)                                                   # 頂 2 格（平滑渲染、斜頂的台階上下相連）
    gz = T['gun_axis'] - T['z_table']
    pw, ph = T['port']
    port = (u > 0) & (np.abs(v) <= pw) & (Z >= gz - ph) & (Z <= gz + ph + 2) & ~roof                  # 砲口的豎縫（仰角）；頂不切
    door = (u < -b_ + T['t'] + 2) & (np.abs(v) <= 3) & (Z >= 1) & (Z <= 20)                            # 後面的門（裝填、出入）
    hatch = (np.abs(v) <= 3) & (np.abs(u - T['hatch_u']) <= 3)                                          # 頂上的瞄準罩
    cupola = hatch & (Z > ztop + 1) & (Z <= ztop + 3)
    p.put(table, C['iron'])
    p.put(wall & ~port & ~door, C['hood'])
    p.put(roof | cupola, C['hood'])
    return p, {'pivot': [CX, CX, 0], 'front': [CX, N - 1, 0]}, dict(N=N, CX=CX, NZ=NZ)


def rising_sun_flag(fn, w=60, h=40):
    """軍艦旗（旭日旗，1889 年制定：白底、紅日偏旗桿側、十六道紅光）。像素畫，照 sail 的貼圖規則（左上 ＝ 角 0 ＝ 旗桿上端）。"""
    WHITE, RED = (250, 250, 248), (200, 24, 36)
    im = Image.new('RGBA', (w, h), WHITE + (255,)); px = im.load()
    cx, cy = w * 0.45, h * 0.5                                            # 日的中心偏旗桿（左）
    for yy in range(h):
        for xx in range(w):
            dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
            r = math.hypot(dx, dy)
            a = (math.degrees(math.atan2(dy, dx)) + 360) % 360
            ray = int((a + 360 / 32) // (360 / 16)) % 2 == 0              # 十六道：紅白相間
            if r <= h * 0.27 or ray: px[xx, yy] = RED + (255,)
    im.save(fn)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    PP = PLAN['parts']
    meta = {}
    for key, fnc in (('gun320', canet), ('gun120', qf_shield), ('gun57', hotchkiss_qf), ('gun47', hotchkiss_qf)):
        p, a = fnc(PP[key]); meta[key] = {'count': p.write(os.path.join(out, key + '.txt'), key), 'anchors': a, 'frame': list(p.col.shape)}
    p, a, d = turret_main(PLAN['params']['turret_main']); meta['turret-main-shell'] = {'count': p.write(os.path.join(out, 'turret-main-shell.txt'), 'turret-main-shell'), 'anchors': a, 'frame': list(p.col.shape), 'geom': d}
    rising_sun_flag(os.path.join(out, 'flag_rising_sun.png'))
    json.dump(meta, open(os.path.join(out, 'parts_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: (v['count'], v['frame']) for k, v in meta.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()

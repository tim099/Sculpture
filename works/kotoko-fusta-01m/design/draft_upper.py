# 越嶺號 階段二（TASK-0759）：甲板以上的構造 ⇒ masks/upper/<件>.vox.txt、verify_upper.json、sheet02_layout_v1.png
#   用法：python -I -X utf8 draft_upper.py [--probe=drop_bench=5]
#   · 只讀 plan.json（lines、layout、hull_build）與 draft_lines 的船殼（階段一證過 作品 ＝ 清單）。
#   · 每件一份清單、整船的座標（at 0,0,0）；兩舷照 |dy| 產 ⇒ 逐格對稱。
#   · 重疊：船殼 ＞ 甲板 ＞ 舷外槳架 ＞ 船首平台 ＞ 衝角 ＞ 船尾篷（後面的扣掉前面已經有的格）。
#   · 做法參考皇家號 apex-one-reale-01m/design/draft_upper.py（同一類槳帆船），尺寸與件是本船的。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 360, 161, 80
PARTS = ['deck', 'apostis', 'bow', 'spur', 'stern']
C_PLANK, C_FRAME, C_DARK, C_RED, C_GREEN, C_WHITE, C_IRON, C_SEAT, C_CLOTH = 177, 141, 68, 196, 16, 255, 73, 173, 192


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def build(probe):
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    YC = L.YC
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    hull = np.zeros((SX, SY, SZ), np.uint8)
    hc = DL.hull_cells(L, plan)
    hull[DL.X0:DL.X0 + hc.shape[0], :, :hc.shape[2]] = hc
    sol = np.zeros((SX, SY, SZ), bool)
    s0 = L.solid(DL.X0, DL.X1, DL.ZMAX, 0)
    sol[DL.X0:DL.X0 + s0.shape[0], :, :s0.shape[2]] = s0
    interior = sol & (hull == 0)
    xs = np.arange(SX)
    tz = np.floor(L.sheer(xs + 0.5)).astype(int)
    part = {p: np.zeros((SX, SY, SZ), np.uint8) for p in PARTS}
    DY = np.arange(SY) - YC

    def hw_at(x, z):
        """船殼在 (x, z) 那一層的外緣半寬（格）；沒有 ⇒ -1。"""
        ys = np.where(hull[x, :, z] > 0)[0]
        return int(np.abs(ys - YC).max()) if len(ys) else -1

    def put(p, x, y, z, c):
        if 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ:
            part[p][x, y, z] = c

    def put_sym(p, x, dy, z, c):
        put(p, x, YC + dy, z, c)
        put(p, x, YC - dy, z, c)

    # ── 甲板：一層板（頂面 ＝ 舷頂那一格）、每 6 格一根橫樑；船尾艙口 x 82–87、|dy| ≤ 3 ──
    d = part['deck']
    hatch = lambda x, dy: 82 <= x <= 87 and abs(dy) <= 3
    for x in range(SX):
        z = tz[x]
        if not (0 < z < SZ):
            continue
        ys = np.where(interior[x, :, z])[0]
        for y in ys:
            if not hatch(x, y - YC):
                d[x, y, z] = C_PLANK
        if x % lay['deck']['beam_every'] == 0:
            for y in np.where(interior[x, :, z - 1])[0]:
                if not hatch(x, y - YC):
                    d[x, y, z - 1] = C_FRAME
    # 中央走道 corsia：|dy| ≤ 3、甲板上 3 格（頂一層淺色板）；兩頭各一級台階
    co = lay['corsia']
    for x in range(co['x0'] - 2, co['x1'] + 1):
        h = co['h'] if x >= co['x0'] else 1 + (x - (co['x0'] - 2))
        for dy in range(-co['half'], co['half'] + 1):
            for k in range(1, h + 1):
                d[x, YC + dy, tz[x] + k] = C_PLANK if k == h else C_FRAME
    # 划手座：每舷 18 張（x0 ＋ 12i），座板 2 格寬、從 dy 4 到 24、高 3；腳 dy 6、14；船殼舷頂上一塊墊；座前 5 格一根腳踏
    be = lay['benches']
    drop = int(probe.get('drop_bench', -1))
    benches = []
    for i in range(be['n']):
        if i == drop:
            continue
        xb = be['x0'] + be['pitch'] * i
        benches.append(xb)
        zs = tz[xb] + be['h']
        for x in (xb, xb + 1):
            for dy in range(be['dy0'], be['dy1'] + 1):
                put_sym('deck', x, dy, zs, C_SEAT)
            for dy in be['legs'][:2]:
                for z in range(tz[x] + 1, zs):
                    put_sym('deck', x, dy, z, C_FRAME)
            hw = hw_at(x, tz[x])
            for dy in range(hw - 1, hw + 1):
                for z in range(tz[x] + 1, zs):
                    put_sym('deck', x, dy, z, C_FRAME)
        xf = xb + lay['footrest']['dx']
        hw = hw_at(xf, tz[xf]) - 2
        for dy in range(be['dy0'] + 1, hw + 1):
            put_sym('deck', xf, dy, tz[xf] + 1, C_FRAME)

    # ── 舷外槳架：縱樑（|dy| 27–28、z 17–18，頂一格紅）、兩頭橫樑 joug、每張座底下一根托樑、每張座兩根槳栓 ──
    ap = lay['apostis']
    for x in range(ap['x0'], ap['x1'] + 1):
        for dy in range(ap['rail_dy'][0], ap['rail_dy'][1] + 1):
            put_sym('apostis', x, dy, ap['rail_z'][0], C_DARK)
            put_sym('apostis', x, dy, ap['rail_z'][1], C_RED)
    beams = [ap['x0'], ap['x0'] + 1, ap['x1'] - 1, ap['x1']] + benches
    for x in beams:
        for z in ([ap['rail_z'][0]] if x in benches else ap['rail_z']):
            hw = hw_at(x, z)
            for dy in range(max(hw + 1, 1), ap['rail_dy'][0]):
                put_sym('apostis', x, dy, z, C_DARK)
    # 座的外端（dy 24）落在托樑上
    for xb in benches:
        zs = tz[xb] + be['h']
        for x in (xb, xb + 1):
            for z in range(ap['rail_z'][0] + 1, zs):
                put_sym('apostis', x, be['dy1'], z, C_DARK)
        if xb + 1 not in beams:
            hw = hw_at(xb + 1, ap['rail_z'][0])
            for dy in range(hw + 1, ap['rail_dy'][0]):
                put_sym('apostis', xb + 1, dy, ap['rail_z'][0], C_DARK)
    th = lay['tholes']
    tholes = []
    for xb in benches:
        for dx in th['dx']:
            x = xb + dx
            tholes.append(x)
            for z in range(ap['rail_z'][1] + 1, ap['rail_z'][1] + 1 + th['h']):
                put_sym('apostis', x, ap['rail_dy'][0], z, C_DARK)

    # ── 船首平台：x 294–316、頂 z 21 一層板（寬到船殼外緣）、柱、胸牆（兩側與前面，頂紅）、胸牆外的盾 ──
    bp = lay['bow_platform']
    sh = lay['shields']
    for x in range(bp['x0'], bp['x1'] + 1):
        hw = hw_at(x, tz[x])
        if hw < 0:
            continue
        for dy in range(0, hw + 1):
            put_sym('bow', x, dy, bp['top'], C_PLANK)
        if (x - bp['x0']) % 6 == 0:
            for dy in (0, max(0, hw - 1)):
                for z in range(tz[x] + 1, bp['top']):
                    put_sym('bow', x, dy, z, C_FRAME)
        for z in range(bp['top'] + 1, bp['top'] + 1 + bp['wall_h']):
            c = C_RED if z == bp['top'] + bp['wall_h'] else C_SEAT
            put_sym('bow', x, hw, z, c)
            if x == bp['x1']:
                for dy in range(0, hw + 1):
                    if dy <= 2 and z > bp['top']:          # 中線砲口（階段四：船首 bombardella 的木床從這裡伸出去 ⇒ 開到平台板面）
                        continue
                    put_sym('bow', x, dy, z, c)
    shield_cells = []

    def shield(p, xc, zc, dyface, k):
        cols = sh['colors']
        c = cols[k % len(cols)]
        r = sh['r']
        for x in range(int(xc - r) - 1, int(xc + r) + 2):
            for z in range(int(zc - r) - 1, int(zc + r) + 2):
                q = (x + 0.5 - xc) ** 2 + (z + 0.5 - zc) ** 2
                if q <= r * r:
                    cc = C_IRON if q <= 0.8 else c
                    put_sym(p, x, dyface, z, cc)
                    shield_cells.append((p, x, z))
    for k, xc in enumerate((299.5, 305.5, 311.5)):
        hw = hw_at(int(xc), tz[int(xc)])
        shield('bow', xc, bp['top'] + 3.0, hw + 1, k)

    # ── 衝角 sperone：從艏柱上段往前 3 m，往上翹、往前收；尖端鐵；一根斜撐回艏柱 ──
    sp = lay['spur']
    xs0 = int(np.floor(float(L.x_fwd(18.5)))) - 3
    for i in range(sp['len'] + 3):
        t = i / (sp['len'] + 2)
        x = xs0 + i
        zb = int(round(16 + 4 * t))
        h = 3 if t < 0.5 else 2
        w = 1 if t < 0.6 else 0
        c = C_IRON if i >= sp['len'] else C_DARK
        for dy in range(0, w + 1):
            for z in range(zb, zb + h):
                put_sym('spur', x, dy, z, c)
    for i in range(9):                              # 斜撐：每一階上下兩格都放（只放一格 ⇒ 斜角相接、斷開）
        for z in (15 - int(i * 0.6), 15 - int((i - 1) * 0.6) if i else 15):
            put_sym('spur', xs0 + 8 - i, 0, z, C_DARK)

    # ── 船尾篷：每 6 格一道木拱（落在舷頂上），拱上半部蓋紅布、最下一圈綠邊；船殼外側掛盾 ──
    aw = lay['awning']
    ribs = list(range(aw['x0'], aw['x1'] + 1, aw['every']))
    zb = int(tz[aw['x1']]) + 1                      # 整片篷同一個拱基準（篷頂水平）；舷頂往船尾抬 ⇒ 低於舷頂的那一截切掉
    for x in range(aw['x0'], aw['x1'] + 1):
        hw = hw_at(x, tz[x])
        if hw < 0:
            continue
        a, b = hw + 0.5, aw['ridge'] + 0.5
        inside = lambda dy, z: (dy / a) ** 2 + ((z - zb + 0.5) / b) ** 2 <= 1
        for dy in range(0, hw + 1):
            for z in range(max(zb, tz[x] + 1), zb + aw['ridge'] + 1):
                if not inside(dy + 0.5 if dy else 0, z + 0.5):
                    continue
                # 邊 ＝ 右、上、右上任一格在外（只看右、上 ⇒ 階梯只靠斜角相接、斷成好幾塊；v1 組起來 68 塊）
                edge = not inside(dy + 1.5, z + 0.5) or not inside(dy + 0.5 if dy else 0, z + 1.5) or not inside(dy + 1.5, z + 1.5)
                if not edge:
                    continue
                if x in ribs:
                    put_sym('stern', x, dy, z, C_FRAME)
                elif z >= zb + int(aw['ridge'] * 0.45):
                    put_sym('stern', x, dy, z, C_GREEN if z == zb + int(aw['ridge'] * 0.45) else C_CLOTH)
    for k, xc in enumerate((53.5, 61.5, 69.5, 77.5)):
        x = int(xc)
        hw = hw_at(x, tz[x] - 3)
        shield('stern', xc, tz[x] - 3.0, hw + 1, k + 1)

    # 重疊：照順序扣掉前面已有的格
    taken = hull > 0
    for p in PARTS:
        part[p][taken] = 0
        taken |= part[p] > 0
    return plan, L, hull, part, benches, tholes


def readings(plan, L, hull, part, benches, tholes):
    R = {'cells': {p: int((part[p] > 0).sum()) for p in PARTS}}
    R['benches_per_side'] = len(benches)
    R['bench_x'] = benches
    R['bench_pitch_mean'] = round(float(np.mean(np.diff(benches))), 3) if len(benches) > 1 else None
    R['tholes_per_side'] = len(tholes)
    ys = [np.where((part['apostis'] > 0).any(axis=(0, 2)))[0]]
    R['apostis_width_m'] = round((ys[0].max() - ys[0].min() + 1) * 0.1, 2)
    allp = np.zeros_like(hull)
    for p in PARTS:
        allp = allp + (part[p] > 0)
    R['overlap_between_parts'] = int((allp > 1).sum())
    R['overlap_with_hull'] = int(((allp > 0) & (hull > 0)).sum())
    sx = np.where((part['spur'] > 0).any(axis=(1, 2)))[0]
    R['spur_x'] = [int(sx.min()), int(sx.max())]
    R['length_overall_m'] = round((sx.max() - np.where((hull > 0).any(axis=(1, 2)))[0].min() + 1) * 0.1, 2)
    R['mirror_diff'] = int(sum(int((part[p] != part[p][:, ::-1, :]).sum()) for p in PARTS))
    return R


def sheet(plan, L, hull, part, R, path):
    s = 4
    W, H = SX * s + 80, 760
    img = Image.new('RGB', (W, H), (246, 242, 230))
    dr = ImageDraw.Draw(img)
    f1, f2, f3 = DL.font(28), DL.font(18), DL.font(14)
    dr.text((30, 14), '越嶺號 新圖紙 02：甲板以上（走道、划手座 ×18、舷外槳架、船首平台、衝角、船尾篷、盾）　kotoko 2026-10-20', fill=(20, 20, 40), font=f1)
    allc = hull.copy()
    for p in PARTS:
        allc = np.where(part[p] > 0, part[p], allc)
    solid = allc > 0
    ox, oy = 40, 70 + 60 * s
    dr.text((30, 52), '① 側面（右舷外觀）', fill=(20, 20, 40), font=f2)
    for x in range(SX):
        for z in range(60):
            ys = np.where(solid[x, :, z])[0]
            if len(ys):
                dr.rectangle([ox + x * s, oy - (z + 1) * s, ox + x * s + s - 1, oy - z * s - 1], fill=DL.palette_rgb(int(allc[x, ys.max(), z])))
    wl = plan['waterline']['z']
    dr.line([ox, oy - (wl + 1) * s, ox + SX * s, oy - (wl + 1) * s], fill=(40, 110, 200))
    oy2 = oy + 40 + 60 * s // 1
    dr.text((30, oy + 10), '② 俯視（從上往下看最高那一格）', fill=(20, 20, 40), font=f2)
    for x in range(SX):
        for y in range(20, 141):
            zs = np.where(solid[x, y, :])[0]
            if len(zs):
                c = DL.palette_rgb(int(allc[x, y, zs.max()]))
                yy = oy2 - 30 * s + (y - 20) * s // 2 * 1
                dr.rectangle([ox + x * s, yy, ox + x * s + s - 1, yy + s // 2], fill=c)
    txt = '划手座每舷 %d 張、平均間距 %.2f 格；槳栓每舷 %d 根；舷外槳架全寬 %.1f m；全長（含衝角）%.1f m；件與件重疊 %d、跟船殼重疊 %d' % (
        R['benches_per_side'], R['bench_pitch_mean'], R['tholes_per_side'], R['apostis_width_m'], R['length_overall_m'], R['overlap_between_parts'], R['overlap_with_hull'])
    dr.text((30, H - 36), txt, fill=(60, 60, 60), font=f3)
    img.save(path)


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    plan, L, hull, part, benches, tholes = build(probe)
    R = readings(plan, L, hull, part, benches, tholes)
    if probe:
        print(json.dumps({'probe': probe, 'benches_per_side': R['benches_per_side'], 'cells': R['cells']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'upper')
    os.makedirs(out, exist_ok=True)
    R['lists'] = {}
    for p in PARTS:
        idx = np.argwhere(part[p] > 0)
        fn = os.path.join(out, p + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 越嶺號 %s（draft_upper.py）x,y,z,color —— at 0,0,0\n' % p)
            f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, part[p][x, y, z]) for x, y, z in idx) + '\n')
        R['lists'][p] = {'cells': len(idx), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}
    with open(os.path.join(HERE, 'verify_upper.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, L, hull, part, R, os.path.join(HERE, 'sheet02_layout_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('lists', 'bench_x')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

# 莫尼特號 砲塔元件（0.05 m／格）—— 拆三件（造船規格 §4.6）：
#   -turret-gun   一門 XI 吋 Dahlgren＋Ericsson 滑架（用砲塔的框；第二門 ＝ 關聯 mirror=x）
#   -turret-shell 裝甲圓筒（兩個砲門）＋鐵軌格柵頂（兩個滑動艙口）
#   -turret       一格都不雕：關聯 shell、gun、gun(mirror=x)；上船掛這一件當模型（kind=gun、mount=turret）
# 用法：python -I -X utf8 -B gen_turret.py <輸出資料夾>
# 座標（照造船規格 §4.1）：x 橫向、y ＝ 靜止時的砲口方向、z 0 ＝ 甲板面上第一格；圓心在格 (CX, CY) ⇒ 模型 pivot ＝ (CX+0.5, CY+0.5, 0)。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['turret']

N, NZ = T['frame']                     # 正方形框 N×N×NZ（N 奇數 ⇒ 圓心落在格心）
CX = CY = (N - 1) // 2
R_IN, R_OUT, H = T['r_in'], T['r_out'], T['height']
C = T['colors']
GX, GZ, L = T['gun_dx'], T['gun_z'], T['gun_len']


def mirror_x(p): return [N - 1 - p[0], p[1], p[2]]


def build():
    X, Y, Z = np.meshgrid(np.arange(N), np.arange(N), np.arange(NZ), indexing='ij')
    Xf, Yf, Zf = X.astype(float), Y.astype(float), Z.astype(float)
    r = np.hypot(Xf - CX, Yf - CY)
    own = np.zeros(X.shape, np.uint8); col = np.zeros(X.shape, np.uint8)
    names = [None]

    def put(name, m, c):
        m = m & (own == 0)
        if name not in names: names.append(name)
        own[m] = names.index(name); col[m] = c
        return int(m.sum())

    # ── 砲 a（x ＝ CX − GX；砲 b 是它的 x 鏡像）──
    gx = CX - GX
    muz_y = CY + T['muzzle_y']          # 砲口那一格（內膛挖空 ⇒ 空格）
    br_y = muz_y - L + 1                # 砲尾面那一格
    prof = T['gun_profile']
    tt = np.array([p[0] for p in prof]); rr = np.array([p[1] for p in prof])
    t = (Yf - br_y) / max(L - 1, 1)
    rad = np.interp(t, tt, rr, left=-1, right=-1)
    dr = np.hypot(Xf - gx, Zf - GZ)
    body = (t >= 0) & (t <= 1) & (dr <= rad)
    hole = (dr <= T['bore_r']) & (Yf >= muz_y - T['bore_depth'])
    casc = (np.abs(Yf - (br_y - 2)) <= 1.5) & (dr <= T['cascabel_r'])                         # 砲尾的鈕
    put('gun', (body & ~hole) | casc, C['gun'])
    ty = br_y + int(round(L * T['trunnion_t']))
    put('gun', (np.abs(Yf - ty) <= 2) & (np.abs(Zf - GZ) <= 2) & (np.abs(Xf - gx) <= rr.max() + 2), C['gun'])   # 砲耳
    cw = T['carriage_halfw']
    cheek = (np.abs(np.abs(Xf - gx) - cw) <= 1) & (Zf <= GZ + 1) & (Zf >= 0) & (Yf >= ty - 14) & (Yf <= ty + 8) & ((Zf <= GZ - 4) | (np.abs(Yf - ty) <= 4))
    slide = (np.abs(np.abs(Xf - gx) - (cw - 3)) <= 1) & (Zf <= 2) & (Yf >= br_y - 6) & (Yf <= muz_y - 8)
    brake = (np.abs(Xf - (gx - cw - 2)) <= 0) & (np.hypot(Yf - (ty - 6), Zf - (GZ - 8)) <= 5) & (np.hypot(Yf - (ty - 6), Zf - (GZ - 8)) >= 3.5)   # 外側的煞車輪（黃銅）
    put('carriage', cheek | slide, C['carriage'])
    put('carriage', brake & (own == 0), 180)
    gun_mask = own > 0
    # ── 圓筒（兩個砲門正對兩門砲）＋頂 ──
    gxb = N - 1 - gx
    wall = (r >= R_IN) & (r <= R_OUT) & (Zf <= H - 1)
    pw, ph = T['port_halfw'], T['port_halfh']
    ports = np.zeros(X.shape, bool)
    for g in (gx, gxb):
        ports |= (Yf > CY) & (np.abs(Xf - g) <= pw) & (np.abs(Zf - GZ) <= ph) & ((np.abs(Xf - g) <= pw - 1) | (np.abs(Zf - GZ) <= ph - 1))
    shell_raw = wall & ~ports                                           # 不讓砲先佔（量重疊用）
    put('shell', shell_raw, C['turret'])
    hatch = np.zeros(X.shape, bool)
    for hx, hy, hw, hh in T['roof_hatches']:
        hatch |= (np.abs(Xf - (CX + hx)) <= hw) & (np.abs(Yf - (CY + hy)) <= hh)
    rail = (r <= R_IN) & (Zf >= H) & (Zf <= H + 1) & (((Y - CY) % T['rail_pitch']) == 0) & ~hatch           # 鐵軌（沿 x）
    rim = (r <= R_OUT) & (r > R_IN) & (Zf >= H) & (Zf <= H)                                                  # 圓筒頂緣
    beam = (np.abs(np.abs(Xf - CX) - T['roof_beam_dx']) <= 1) & (Zf == H - 1) & (r <= R_IN)                  # 撐鐵軌的兩根橫樑
    hcover = np.zeros(X.shape, bool)                                                                       # 滑動艙口蓋（推開在艙口旁）
    for hx, hy, hw, hh in T['roof_hatches']:
        hcover |= (np.abs(Xf - (CX + hx + 2 * hw + 2)) <= hw) & (np.abs(Yf - (CY + hy)) <= hh) & (Zf == H + 2) & (r <= R_IN - 2)
    put('shell', rim | beam, C['turret'])
    put('shell', rail, C['rail'])
    put('shell', hcover, C['roof'])
    anc_gun = {'pivot': [CX, CY, 0], 'muzzle': [gx, muz_y, GZ], 'breech': [gx, br_y, GZ], 'cascabel': [gx, br_y - 2, GZ]}
    anc_b = {k: mirror_x(v) for k, v in anc_gun.items()}
    anc_turret = {'pivot': [CX, CY, 0], 'muzzle': anc_gun['muzzle'], 'breech': anc_gun['breech'],
                  'muzzle-a': anc_gun['muzzle'], 'muzzle-b': anc_b['muzzle'], 'breech-a': anc_gun['breech'], 'breech-b': anc_b['breech']}
    return own, col, names, dict(gun=anc_gun, shell={'pivot': [CX, CY, 0]}, turret=anc_turret), dict(gx=gx, gxb=gxb, ty=ty, shell_raw=shell_raw, gun_mask=gun_mask)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    own, col, names, anc, info = build()
    counts = {}
    for i, nm in enumerate(names):
        if not nm: continue
        part = 'gun' if nm in ('gun', 'carriage') else nm
        counts[part] = counts.get(part, 0)
    for part, sel in (('gun', ('gun', 'carriage')), ('shell', ('shell',))):
        m = np.isin(own, [names.index(s) for s in sel])
        idx = np.argwhere(m); cs = col[m]
        o = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0])); idx, cs = idx[o], cs[o]
        with open(os.path.join(out, 'turret_%s.txt' % part), 'w', newline='\n') as f:
            f.write('# 莫尼特號 砲塔 %s —— x,y,z,color（框 %d×%d×%d、0.05 m／格）\n' % (part, N, N, NZ))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())) + '\n')
        counts[part] = len(idx)
    # 讀數：兩門砲（gun ＋ 鏡像）跟圓筒不重疊、砲口那一格是空的、砲口在圓筒內緣與外緣之間（砲門裡）
    g = np.isin(own, [names.index('gun'), names.index('carriage')])
    gb = g[::-1, :, :]
    sh = own == names.index('shell')
    shr = info['shell_raw']
    full = g | gb | sh
    mz = anc['turret']['muzzle-a']; mzb = anc['turret']['muzzle-b']
    rm = math.hypot(mz[0] - CX, mz[1] - CY)
    meta = dict(counts=counts, frame=[N, N, NZ], overlap_gun_shell=int((g & shr).sum()), overlap_gun_gunb=int((g & gb).sum()), overlap_gunb_shell=int((gb & shr).sum()),
                muzzle_empty=[int(not full[tuple(mz)]), int(not full[tuple(mzb)])], muzzle_r=round(rm, 2), r_in=R_IN, r_out=R_OUT,
                gun_x=[info['gx'], info['gxb']], anchors=anc)
    from scipy import ndimage
    meta['components_full'] = int(ndimage.label(full)[1])
    json.dump(meta, open(os.path.join(out, 'turret_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in meta if k != 'anchors'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

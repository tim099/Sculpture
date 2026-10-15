# 莫尼特號 砲塔裝甲子模組（TASK-0631）—— 圓筒（兩個砲門）與鐵軌頂改成船的比例（0.1 m）的格子，掛成「跟著砲轉的裝甲」：
#   -turret-armor  圓筒（material iron、render smooth）
#   -turret-roof   鐵軌格柵頂＋推開的艙口蓋（material iron、方塊；1 格粗的鐵軌平滑渲染會被抹平）
# 兩件的框都收緊到自己的外框、關聯 at ＝ 框的原點（組裝件座標）⇒ 匯出的部件外框 ＝ 這幾格，遊戲照外框把格子從船殼收進砲的裝甲（造船規格 §4.7）。
# 靜止方向跟砲塔模型一樣：砲口朝船尾（−x）、兩個砲門在 y ＝ 中線 ± 7。
# 用法：python -I -X utf8 -B gen_armor.py <輸出資料夾>
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PL = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P, T = PL['params'], PL['turret']
YC = (P['frame'][1] - 1) // 2
ZFL = P['z_deck_top'] + 1
TX = P['turret_x']
K = 0.5                                    # 元件 0.05 m ⇒ 船 0.1 m
R_IN, R_OUT = T['r_in'] * K, T['r_out'] * K          # 30.5、32.5
H = int(round(T['height'] * K))                      # 27.5 ⇒ 28 格牆（z ZFL..ZFL+27）
GDY = T['gun_dx'] * K                                # 砲門中心離中線 7
GZ = ZFL + T['gun_z'] * K                            # 砲軸高 46
PW, PH = T['port_halfw'] * K, T['port_halfh'] * K    # 砲門半寬 3、半高 4
R = int(math.ceil(R_OUT)) + 1
X0, Y0, Z0 = TX - R, YC - R, ZFL
NX = NY = 2 * R + 1; NZ = H + 3


def build():
    X, Y, Z = np.meshgrid(np.arange(NX) + X0, np.arange(NY) + Y0, np.arange(NZ) + Z0, indexing='ij')
    dx, dy = X + 0.5 - (TX + 0.5), Y + 0.5 - (YC + 0.5)                # 格心離轉軸（跟砲塔模型的 pivot 同一點）
    r = np.hypot(dx, dy)
    wall = (r >= R_IN) & (r <= R_OUT) & (Z < ZFL + H)
    port = np.zeros(X.shape, bool)
    for s in (-1, 1):                                                  # 砲門朝 −x：在船尾那一側、y ＝ 中線 ± 7，圓角
        ey, ez = np.abs(dy - s * GDY), np.abs(Z + 0.5 - GZ)
        port |= (dx < 0) & (ey <= PW + 0.5) & (ez <= PH + 0.5) & ((ey <= PW - 0.5) | (ez <= PH - 0.5))
    armor = wall & ~port
    zt = ZFL + H                                                       # 頂：鐵軌（沿 y，每 2 格一條）＋外圈＋兩個艙口
    hatch = np.zeros(X.shape, bool)
    for hx, hy, hw, hh in T['roof_hatches']:                           # 元件座標 (dx, dy) → 船：繞 z 轉 90°（+y → −x）⇒ 船 dx ＝ −元件 dy、船 dy ＝ 元件 dx
        hatch |= (np.abs(dx - (-hy * K)) <= hh * K) & (np.abs(dy - hx * K) <= hw * K)
    rail = (r < R_IN) & (Z == zt) & ((np.floor(dx) % 2) == 0) & ~hatch
    rim = (r >= R_IN) & (r <= R_OUT) & (Z == zt)
    cover = np.zeros(X.shape, bool)
    for hx, hy, hw, hh in T['roof_hatches']:                           # 推開的艙口蓋：疊在艙口旁的鐵軌上
        cover |= (np.abs(dx - (-hy * K)) <= hh * K) & (np.abs(dy - (hx * K + 2 * hw * K + 1)) <= hw * K) & (Z == zt + 1) & (r < R_IN - 1)
    roof = rail | rim | cover
    return X, Y, Z, armor, roof


def write(path, X, Y, Z, m, color, at):
    idx = np.argwhere(m)
    with open(path, 'w', newline='\n') as f:
        f.write('# 莫尼特號 %s —— x,y,z,color（子作品座標；關聯 at %d,%d,%d）\n' % (os.path.basename(path), *at))
        f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, color) for a, b, c in idx.tolist()) + '\n')
    return len(idx)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    X, Y, Z, armor, roof = build()
    C = T['colors']
    # 各自收緊框：圓筒 ＝ 牆的外框；頂 ＝ 頂那幾格的外框
    res = {}
    for nm, m, col in (('armor', armor, C['turret']), ('roof', roof, C['rail'])):
        ii = np.argwhere(m); lo, hi = ii.min(0), ii.max(0)
        sub = m[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
        at = [int(X0 + lo[0]), int(Y0 + lo[1]), int(Z0 + lo[2])]
        n = write(os.path.join(out, 'turret_%s.txt' % nm), None, None, None, sub, col, at)
        res[nm] = {'at': at, 'size': [int(v) for v in (hi - lo + 1)], 'count': n}
    # 讀數：兩件不重疊；框裡沒有船上別的部件的格（遊戲照框收）；砲口（模型）在砲門裡
    sys.path.insert(0, HERE)
    import gen_monitor as G
    own, col, names, anc, info = G.build()
    full = own > 0
    for nm in ('funnel', 'boilers'): full |= (own == names.index(nm))[:, ::-1, :]
    for nm, d in res.items():
        a, s = d['at'], d['size']
        d['other_voxels_in_box'] = int(full[a[0]:a[0] + s[0], a[1]:a[1] + s[1], a[2]:a[2] + s[2]].sum())
    res['overlap_armor_roof'] = int((armor & roof).sum())
    res['gun_axis_z'] = GZ; res['port_center_dy'] = GDY; res['r'] = [R_IN, R_OUT]
    json.dump(res, open(os.path.join(out, 'armor_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()

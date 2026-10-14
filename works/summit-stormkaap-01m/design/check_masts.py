# 階段六 b 讀數（作品落格之後）：桅、船首斜桅、channels 的結果帳 ＋ 從 plan 取的探針 ＋ 反向對照。
# 用法：python -I -X utf8 -B check_masts.py <design 資料夾> <export 資料夾：s6-mast-*.txt、s6-bowsprit.txt、s6-channels.txt、s6-assembly.txt>
#   · 結果帳：每件作品的 export list vs masks/masts/ 清單（含顏色）；組裝件 vs（重播到 stage6a 的船 ∪ 五件 ∪ channels 鏡像）。
#   · 探針的基準一律從 plan.json 算，量的是作品匯出 —— ⛔ 不從 verify_masts.json 的 info／anchors 取（那是 draft 自己算的，同一條路）。
#     桅腳的基準 ＝ 組裝件扣掉這根桅之後、腳印裡最高那一格的上面（引擎匯出，不經 sk_state）⇒ 平台、cap、桅頂的基準都從它往上加 plan 的長度。
#   · 探針：桅軸 x、y（下桅每一層的重心）／桅腳 vs 下面的支撐／平台那一層／下桅頂的 cap／整根最高那一格／平台半徑；
#     船首斜桅：軸的仰角（每一欄 x 的重心擬合）、x＝heel＋100 那一欄軸心的 z。
#   · 反向對照：桅與斜桅整份偏 3（x 與 z 各一次），支撐不動 ⇒ 每根位置探針都要剛好多報 3（仰角那根要報 0 —— 平移不改角度）。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_state import state_after, occupancy

NZ = 576
MASTS = ('mizzen', 'main', 'fore')
SUF = {'mizzen': '-mast-mizzen', 'main': '-mast-main', 'fore': '-mast-fore', 'bowsprit': '-bowsprit', 'channels': '-channels'}


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def mast_probes(m, pts, support, YC):
    """pts：這根桅的格（N×3）；support：組裝件扣掉這根桅的實心（bool 陣列）。回傳各探針與 plan 的差（設計 0）。"""
    xm, yc = m['x'], YC + 0.5
    r = m['d_low'] / 2
    # 支撐：腳印（下桅圓截面）裡、z < 60 最高那一格的上面 —— 量的是組裝件，不是 sk_state
    fp = [(x, y) for x in range(int(xm - r) - 1, int(xm + r) + 2) for y in range(YC - 6, YC + 7)
          if (x + 0.5 - xm) ** 2 + (y + 0.5 - yc) ** 2 <= r * r]
    heel_d = 1 + max(int(np.nonzero(support[x, y, :60])[0].max()) if support[x, y, :60].any() else -1 for x, y in fp)
    top_low_d = heel_d + m['L_low']; hounds_d = top_low_d - m['head']
    if m.get('L_tg'):
        top_d = hounds_d + m['L_top'] - m['head_top'] + m['L_tg'] - 1
    else:
        top_d = hounds_d + m['L_top'] - 1
    z = pts[:, 2]
    heel_w = int(z.min())
    # 下桅身：桅腳往上 5 格 ～ 平台下 5 格，每一層的重心
    cx, cy = [], []
    for zz in range(heel_d + 5, hounds_d - 6):
        s = pts[z == zz]
        if len(s): cx.append(s[:, 0].mean() + 0.5); cy.append(s[:, 1].mean() + 0.5)
    cx, cy = np.array(cx), np.array(cy)
    # 平台：hounds 下面那一層 ⇒ 下桅頭附近格數最多的那一層
    zz_range = np.arange(hounds_d - 15, hounds_d + 15)
    cnt = np.array([(z == zz).sum() for zz in zz_range])
    plat_w = int(zz_range[cnt.argmax()])
    sp = pts[z == plat_w]
    plat_r_w = float(max(np.abs(sp[:, 1] + 0.5 - yc).max(), np.abs(sp[:, 0] + 0.5 - xm).max()))
    # 下桅頂＋cap：桅軸後半（x 格心 < xm − 1；上桅在前面，碰不到）最高那一格 ＝ cap 第二層 ＝ heel＋L_low＋1
    aft = pts[pts[:, 0] + 0.5 < xm - 1]
    lower_top_w = int(aft[:, 2].max())
    return {'lower_top_gap': lower_top_w - (top_low_d + 1), 'heel_gap': heel_w - heel_d, 'axis_x_gap_max': round(float(np.abs(cx - xm).max()), 4), 'axis_x_gap_mean': round(float((cx - xm).mean()), 4),
            'axis_y_gap_max': round(float(np.abs(cy - yc).max()), 4), 'axis_layers': int(len(cx)),
            'platform_z_gap': plat_w - (hounds_d - 1), 'platform_r_gap': round(plat_r_w - m['top_r'], 3),
            'top_z_gap': int(z.max()) - top_d, 'design': {'heel': heel_d, 'platform_z': hounds_d - 1, 'top_z': top_d}}


def bowsprit_probes(B, pts):
    x0, z0 = B['heel']; th = math.radians(B['steeve'])
    tipx = x0 + math.cos(th) * B['L']
    xs, zs = [], []
    for x in range(int(x0) + 20, int(tipx) - 20):
        s = pts[pts[:, 0] == x]
        if len(s): xs.append(x + 0.5); zs.append(s[:, 2].mean() + 0.5)
    xs, zs = np.array(xs), np.array(zs)
    k, b = np.polyfit(xs, zs, 1)
    xr = x0 + 100
    z_design = z0 + math.tan(th) * (xr - x0)
    return {'steeve_deg_gap': round(math.degrees(math.atan(k)) - B['steeve'], 3), 'axis_z_at_heel_plus_100_gap': round(k * xr + b - z_design, 3),
            'max_x_gap': int(pts[:, 0].max()) - int(tipx + B['d_sprit_top'] / 2), 'columns': int(len(xs))}


def main():
    d, ed = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    M = plan['masts']; YC = plan['frame']['YC']; NY = plan['frame']['NY']
    V = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))
    pts, ledger = {}, {}
    for k, suf in SUF.items():
        a = load(os.path.join(ed, 's6' + suf + '.txt')); pts[k] = a
        e = load(os.path.join(d, V['stamp_order'][k][0]['file']))
        ge = {tuple(r[:3]): r[3] for r in e}; gw = {tuple(r[:3]): r[3] for r in a}
        ledger[k] = {'expected': len(ge), 'work': len(gw), 'missing': sum(1 for p in ge if p not in gw), 'extra': sum(1 for p in gw if p not in ge),
                     'color_diff': sum(1 for p, c in ge.items() if p in gw and gw[p] != c)}
    asm = load(os.path.join(ed, 's6-assembly.txt'))
    NX = plan['frame']['NX']
    occ = np.zeros((NX, NY, NZ), bool); occ[tuple(asm[:, :3].T)] = True
    union = np.zeros_like(occ); union[:, :, :200] = occupancy(state_after(d, 'stage6a', nz=200))
    for k, a in pts.items(): union[tuple(a[:, :3].T)] = True
    chp = pts['channels'][:, :3].copy(); chp[:, 1] = NY - 1 - chp[:, 1]; union[tuple(chp.T)] = True
    asm_vs_union = {'assembly': int(occ.sum()), 'union': int(union.sum()), 'diff': int((occ != union).sum())}

    def run(shift):
        out = {}
        for m in M['list']:
            n = m['name']; p = pts[n][:, :3]
            sup = occ.copy(); sup[tuple(p.T)] = False
            out[n] = mast_probes(m, p + np.array(shift), sup, YC)
        out['bowsprit'] = bowsprit_probes(M['bowsprit'], pts['bowsprit'][:, :3] + np.array(shift))
        return out

    base = run((0, 0, 0)); sx = run((3, 0, 0)); sz = run((0, 0, 3))
    rev = {}
    for n in MASTS:
        rev[n + '.axis_x(+x3)'] = round(sx[n]['axis_x_gap_mean'] - base[n]['axis_x_gap_mean'], 4)
        for key in ('heel_gap', 'platform_z_gap', 'lower_top_gap', 'top_z_gap'):
            rev[n + '.' + key + '(+z3)'] = sz[n][key] - base[n][key]
    rev['bowsprit.axis_z(+z3)'] = round(sz['bowsprit']['axis_z_at_heel_plus_100_gap'] - base['bowsprit']['axis_z_at_heel_plus_100_gap'], 3)
    rev['bowsprit.max_x(+x3)'] = sx['bowsprit']['max_x_gap'] - base['bowsprit']['max_x_gap']
    rev_angle = {'bowsprit.steeve(+x3)': round(sx['bowsprit']['steeve_deg_gap'] - base['bowsprit']['steeve_deg_gap'], 6),
                 'bowsprit.steeve(+z3)': round(sz['bowsprit']['steeve_deg_gap'] - base['bowsprit']['steeve_deg_gap'], 6)}
    R = {'ledger': ledger, 'assembly_vs_union': asm_vs_union, 'probes': base,
         'reverse_offset3': rev, 'reverse_all_report_3': all(abs(v - 3) < 1e-9 for v in rev.values()), 'reverse_n': len(rev),
         'reverse_angle_should_be_0': rev_angle}
    with open(os.path.join(d, 'verify_masts_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

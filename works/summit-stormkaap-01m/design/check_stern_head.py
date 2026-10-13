# 階段五讀數（作品落格之後）：七件的結果帳 ＋ 從圖紙取的探針（艉板的窗與砲門、beakhead 艙壁、艙壁前不留船殼、船首像尖端）＋ 反向對照。
# 用法：python -I -X utf8 -B check_stern_head.py <design 資料夾> <export 資料夾：s5*.txt、s5-assembly.txt>
#   · 探針的基準一律從 plan.json 算（窗、砲門的 z、艙壁的 x、船首像的位置），量的是作品匯出 —— ⛔ 不從遮罩取。
#   · 開口量法：每一層照艉板外面那一格的 x（作品自己的格）往裡 1 格那一欄，沿 z 找包住設計中段的那一段空（階段四學過：⛔ 固定一欄）。
#   · 反向對照：組裝件整份偏 3（窗與砲門偏 z、艙壁與船首像偏 x）⇒ 每根都要剛好多報 3。
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull
from sk_state import state_after, WORK_OF

NZ5 = 200


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def opening_z(occ, y, zmid, x_lo=60, x_hi=140):
    """艉板上 (y, zmid) 那個開口在作品裡的上下緣：在 (y) 這一欄，每一層找艉板外面那一格（x_lo..x_hi 的最小 x），往裡 1 格看空不空。"""
    sub = occ[x_lo:x_hi, y, :]
    has = sub.any(axis=0)
    xf = np.where(has, np.argmax(sub, axis=0), -1)
    def empty_at(z):
        # 開口那幾層艉板外面那一格本身就被刻了 ⇒ 用上下最近有格那一層的 x
        zz = z
        while zz >= 0 and xf[zz] < 0: zz -= 1
        return xf[zz] < 0 or not occ[x_lo + xf[zz] + 1, y, z] if zz >= 0 else True
    if not empty_at(zmid): return None, None
    lo = zmid
    while lo > 0 and empty_at(lo - 1): lo -= 1
    hi = zmid
    while hi < occ.shape[2] - 1 and empty_at(hi + 1): hi += 1
    return lo, hi


def probes(H, plan, occ_hull, works_pts):
    S = plan['stern']; Hd = plan['head']; YC = H.YC
    out = {'windows': [], 'stern_ports': []}
    for key, spec, half in (('windows', S['windows'], S['windows']['w'] // 2), ('stern_ports', S['ports'], 3)):
        z0, z1 = spec['z']
        for yc in spec['y']:
            # 🩸 第一版量組裝件：窗玻璃內縮 2 格、陽台欄杆在 x 90 ⇒「艉板外面那一格」先找到它們，窗報 None／−3 —— 窗與砲門是刻在船殼上的 ⇒ 只看船殼
            lo, hi = opening_z(occ_hull, yc, (z0 + z1) // 2)
            out[key].append({'y': yc, 'sill_gap': None if lo is None else lo - z0, 'lintel_gap': None if hi is None else hi - z1})
    # beakhead 艙壁：艏樓作品在中線往右 6 格、上甲板上 5 格那一列的最大 x ＋ 1 ＝ 艙壁前緣；設計 ＝ bulkhead_x ＋ 2
    xb = Hd['bulkhead_x']; Lup = int(np.floor(H.sheer(xb + 0.5))) - 1
    bp = works_pts['bak']
    row = bp[(bp[:, 1] == YC + 6) & (bp[:, 2] == Lup + 5)]          # 🩸 第一版 y ＋10 ＝ 落在追擊砲門（139–145）的開口裡 ⇒ 改到門與砲門之間
    out['bulkhead_front_gap'] = None if len(row) == 0 else int(row[:, 0].max() + 1 - (xb + 2))
    # 艙壁前、上甲板以上不留船殼（艏柱頭除外）：船殼作品 x ≥ xb+2 且 z > 那一欄上甲板 ＋ stem_head 的格數（設計 0）
    hp = works_pts['hull']
    Lx = np.floor(H.sheer(hp[:, 0] + 0.5)).astype(int) - 1
    out['hull_left_forward_of_bulkhead'] = int(((hp[:, 0] >= xb + 2) & (hp[:, 2] > Lx + Hd['stem_head'])).sum())
    # 船首像：船頭作品最前面那一格的 x ＋ 1 vs 設計（鼻子 fx ＋ 7·sc ＋ 1 那一格的外緣）
    F = Hd['figure']; sc = F.get('scale', 1.0); fx = Hd['x_tip'] + F['dx']
    hd = works_pts['head']
    out['figure_tip_gap'] = round(float(hd[:, 0].max() + 1 - np.floor(fx + 7 * sc + 0.5) - 1), 3)
    return out


def main():
    d, ed = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    W = state_after(d, 'stage5b', nz=NZ5)
    ledger, pts = {}, {}
    for k, suf in WORK_OF.items():
        a = load(os.path.join(ed, 's5' + suf + '.txt')); pts[k] = a[:, :3]
        got = np.zeros_like(W[k]); got[tuple(a[:, :3].T)] = a[:, 3]
        exp = W[k]
        ledger[k] = {'expected': int((exp > 0).sum()), 'work': int(len(a)), 'missing': int(((exp > 0) & (got == 0)).sum()),
                     'extra': int(((got > 0) & (exp == 0)).sum()), 'color_diff': int(((exp > 0) & (got > 0) & (exp != got)).sum())}
    asm = load(os.path.join(ed, 's5-assembly.txt'))
    occ = np.zeros(W['hull'].shape, bool); occ[tuple(asm[:, :3].T)] = True
    occ_h = np.zeros_like(occ); occ_h[tuple(pts['hull'].T)] = True
    union = np.zeros_like(occ)
    for v in W.values(): union |= v > 0
    base = probes(H, plan, occ_h, pts)
    occ_z = np.roll(occ_h, 3, axis=2)
    pts_x = {k: v + np.array([3, 0, 0]) for k, v in pts.items()}
    shz = probes(H, plan, occ_z, pts); shx = probes(H, plan, occ_h, pts_x)
    rev = []
    for key in ('windows', 'stern_ports'):
        for a_, b_ in zip(base[key], shz[key]):
            rev += [b_['sill_gap'] - a_['sill_gap'], b_['lintel_gap'] - a_['lintel_gap']]
    rev += [shx['bulkhead_front_gap'] - base['bulkhead_front_gap'], shx['figure_tip_gap'] - base['figure_tip_gap']]
    R = {'ledger': ledger, 'assembly_vs_union': {'assembly': int(occ.sum()), 'union': int(union.sum()), 'diff': int((occ != union).sum())},
         'probes': base, 'reverse_offset3': rev, 'reverse_all_report_3': all(abs(r - 3) < 1e-9 for r in rev), 'reverse_n': len(rev)}
    with open(os.path.join(d, 'verify_stern_head_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

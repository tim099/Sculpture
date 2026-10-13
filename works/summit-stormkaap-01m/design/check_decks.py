# 階段四讀數（作品落格之後）：六件的結果帳 ＋ 甲板高度與砲門的探針（從圖紙取）＋ 反向對照。
# 用法：python -I -X utf8 -B check_decks.py <design 資料夾> <export 資料夾：s4.txt、s4-deck-*.txt、s4-assembly.txt>
#   · 結果帳：sk_state 重播到 stage4 vs 每件作品的 export list（含顏色）。
#   · 甲板探針：x 站 × 每一層，右舷 y ＝ 中線 ＋ 20 那一欄，作品最高那一格板的頂（格 k 的頂 ＝ k＋1）離 sheer(x)＋偏移 多少（照設計 0..1，floor 的量化）。
#   · 砲門探針：每個砲門中心那一欄（x 中心、右舷最外那一層附近），開口的下緣／上緣（組裝件裡連續空的那一段）離 plan 算的下沿 L＋1＋sill／上沿 多少（照設計 0）。
#   · 反向對照：組裝件清單整份 z 偏 3 ⇒ 每根探針都要剛好多報 3（基準是圖紙）。
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull
from sk_state import state_after, WORK_OF

NZ4 = 180
STATIONS = [110, 150, 200, 300, 400, 500, 530]


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def deck_probes(H, Dk, works, dz=0):
    out = []
    for k, o in Dk['levels'].items():
        pts = works[k].copy(); pts[:, 2] += dz
        for x in STATIONS:
            xc = x + 0.5
            if 'x_max' in o and xc > o['x_max']: continue
            if 'x_min' in o and xc < o['x_min']: continue
            col = pts[(pts[:, 0] == x) & (pts[:, 1] == H.YC + 20)]
            if len(col) == 0: out.append({'deck': k, 'x': x, 'gap': None}); continue
            top = col[:, 2].max() + 1
            out.append({'deck': k, 'x': x, 'gap': round(float(H.sheer(xc) + o['offset']) - top, 3)})
    return out


def port_probes(H, Dk, occ, dz=0):
    """每一層 z 照那一層的船殼半寬找牆（帶狀 y ∈ [外緣 − 6, 外緣 + 2]）—— 🩸 第一版固定看開口中段那一層的外緣那一欄：
    上舷內收（x 277、359 上面的牆往裡退一格）、船尾往裡收（x 136 下面的牆在 y 150）⇒ 看到空、報 90／−2，開口本身其實逐格對。"""
    o3 = np.roll(occ, dz, axis=2) if dz else occ
    out = []
    for row in Dk['ports']:
        o = Dk['levels'][row['deck']]
        for xcen in row['x']:
            L = int(np.floor(H.sheer(xcen + 0.5) + o['offset'])) - 1
            za, zb = L + 1 + row['sill'], L + row['sill'] + row['height']
            wall = np.zeros(occ.shape[2], bool); last = None
            for z in range(occ.shape[2]):
                hb = float(H.hb(xcen + 0.5, z + 0.5))
                if np.isnan(hb):
                    if last is None: continue
                    hb = last
                last = hb
                yo = int(np.floor(H.YC + 0.5 + hb))
                wall[z] = o3[xcen, max(H.YC + 4, yo - 6):yo + 3, z].any()
            zm = (za + zb) // 2 + dz
            if wall[zm]: out.append({'x': xcen, 'row': row['name'], 'sill_gap': None, 'lintel_gap': None}); continue
            lo = zm
            while lo > 0 and not wall[lo - 1]: lo -= 1
            hi = zm
            while hi < len(wall) - 1 and not wall[hi + 1]: hi += 1
            out.append({'x': xcen, 'row': row['name'], 'sill_gap': lo - za, 'lintel_gap': hi - zb})
    return out


def main():
    d, ed = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan); Dk = plan['decks']
    W = state_after(d, 'stage4', nz=NZ4)
    ledger, works = {}, {}
    for k, suf in WORK_OF.items():
        a = load(os.path.join(ed, 's4' + suf + '.txt')); works[k] = a[:, :3]
        got = np.zeros_like(W[k]); got[tuple(a[:, :3].T)] = a[:, 3]
        exp = W[k]
        ledger[k] = {'expected': int((exp > 0).sum()), 'work': int(len(a)), 'missing': int(((exp > 0) & (got == 0)).sum()),
                     'extra': int(((got > 0) & (exp == 0)).sum()), 'color_diff': int(((exp > 0) & (got > 0) & (exp != got)).sum())}
    asm = load(os.path.join(ed, 's4-assembly.txt'))
    occ = np.zeros(W['hull'].shape, bool); occ[tuple(asm[:, :3].T)] = True
    union = np.zeros_like(occ)
    for k in WORK_OF: union |= W[k] > 0
    asm_vs_union = {'assembly': int(occ.sum()), 'union_of_designs': int(union.sum()), 'diff': int((occ != union).sum())}
    dp = deck_probes(H, Dk, works); dp3 = deck_probes(H, Dk, works, dz=3)
    pp = port_probes(H, Dk, occ); pp3 = port_probes(H, Dk, occ, dz=3)
    rev_d = [round(a['gap'] - b['gap'], 3) for a, b in zip(dp, dp3) if a['gap'] is not None]
    rev_p = [(b['sill_gap'] - a['sill_gap'], b['lintel_gap'] - a['lintel_gap']) for a, b in zip(pp, pp3) if a['sill_gap'] is not None and b['sill_gap'] is not None]
    R = {'ledger': ledger, 'assembly_vs_union': asm_vs_union,
         'deck_probes': dp, 'deck_gap_range': [min(r['gap'] for r in dp if r['gap'] is not None), max(r['gap'] for r in dp if r['gap'] is not None)],
         'port_probes': pp,
         'reverse_deck_all_3': all(abs(r - 3) < 1e-9 for r in rev_d), 'reverse_deck_n': len(rev_d),
         'reverse_port_all_3': all(a == 3 and b == 3 for a, b in rev_p), 'reverse_port_n': len(rev_p),
         'note': 'deck gap ＝ sheer＋偏移 − 作品板頂（照設計 0..1）；port sill／lintel gap ＝ 作品開口的下緣／上緣 − 設計（照設計 0）'}
    with open(os.path.join(d, 'verify_decks_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('ledger', 'assembly_vs_union', 'deck_gap_range', 'reverse_deck_all_3', 'reverse_deck_n', 'reverse_port_all_3', 'reverse_port_n')}, ensure_ascii=False))
    print('ports', [(p['row'][0], p['x'], p['sill_gap'], p['lintel_gap']) for p in pp])


if __name__ == '__main__':
    main()

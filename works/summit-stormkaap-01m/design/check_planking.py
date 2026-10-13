# 階段三讀數（作品落格之後）：結果帳 ＋ 漏水（從作品讀，先餵已知答案）＋ 外板外緣探針 ＋ 反向對照。
# 用法：python -I -X utf8 -B check_planking.py <design 資料夾> <作品 export format=list 的檔>
#   · 結果帳：sk_state 照階段二、三的清單重播 vs 作品清單（含顏色）。
#   · 漏水：船艙範圍從圖紙曲面算（Hull.hb），z < 下甲板；作品的格當牆，船外 6 連通走得到幾格船艙。
#     已知答案（夜隼號 🩸：拿掉一格只報 1 —— 那 1 格是洞本身）：在 x 300、z 30 把右舷那一排整層（y ≥ 170）拿掉 ⇒ 要報整個船艙。
#   · 探針（從圖紙取）：站 × 高度，右舷最外那格的外緣離船殼外面多少（wale 那幾層照設計多 1）；反向對照：作品清單 y 偏 3 ⇒ 每根多報 3。
import sys, os, json
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull
from sk_state import state_after

PROBE_X = [160, 230, 300, 370, 440, 503]
PROBE_Z = [10, 30, 50, 66, 85]


def leak_count(H, occ, zl):
    NX, NY = occ.shape[:2]
    x = np.arange(NX) + 0.5; z = np.arange(zl) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = np.nan_to_num(H.hb(X, Z), nan=-1)
    dy = np.abs(np.arange(NY) - H.YC).astype(float)
    hold = (hb[:, None, :] >= 0) & (dy[None, :, None] <= hb[:, None, :]) & ~occ[:, :, :zl]
    empty = ~occ[:, :, :zl]
    lab, _ = ndimage.label(empty)
    return int((hold & (lab == lab[0, 0, 0])).sum()), int(hold.sum())


def probes(H, pts, dy=0):
    P = pts.copy(); P[:, 1] += dy
    out = []
    for x in PROBE_X:
        col = P[(P[:, 0] == x) & (P[:, 1] >= H.YC)]
        for z in PROBE_Z:
            row = col[col[:, 2] == z]
            hb = float(H.hb(x + 0.5, z + 0.5))
            if len(row) == 0 or np.isnan(hb): out.append({'x': x, 'z': z, 'gap': None}); continue
            outer = row[:, 1].max() + 1 - (H.YC + 0.5)             # 最外那格的外緣離圖紙中線
            out.append({'x': x, 'z': z, 'gap': round(hb - outer, 3)})
    return out


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    work = np.loadtxt(lst, delimiter=',', dtype=int, comments='#', ndmin=2)
    Wd = state_after(d, 'stage3')['hull']
    got = np.zeros_like(Wd); got[tuple(work[:, :3].T)] = work[:, 3]
    ledger = {'expected': int((Wd > 0).sum()), 'work': int(len(work)), 'missing': int(((Wd > 0) & (got == 0)).sum()),
              'extra': int(((got > 0) & (Wd == 0)).sum()), 'color_diff': int(((Wd > 0) & (got > 0) & (Wd != got)).sum())}
    occ = got > 0
    zl = plan['planking']['leak_below_z']
    leak, hold = leak_count(H, occ, zl)
    occ2 = occ.copy(); occ2[300, 170:, 30] = False
    leak_known, _ = leak_count(H, occ2, zl)
    base = probes(H, work[:, :3]); off = probes(H, work[:, :3], dy=3)
    rev = [round(a['gap'] - b['gap'], 3) for a, b in zip(base, off) if a['gap'] is not None]
    R = {'ledger': ledger,
         'leak': {'z_below': zl, 'hold_cells': hold, 'reached_from_outside': leak,
                  'known_answer_remove_row_x300_z30_y170plus': leak_known},
         'probes': base, 'reverse_offset3_y': rev, 'reverse_all_report_3': all(abs(r - 3) < 1e-9 for r in rev),
         'note': 'gap ＝ 圖紙船殼外面 − 作品右舷最外那格的外緣；外板 ≈ 0（±0.5 量化），wale 那幾層 ≈ −1（設計：wale 在船殼外一格）'}
    with open(os.path.join(d, 'verify_planking_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

# 步驟 4 結果帳＋結構＋鏡像＋反向對照驗證（TASK-1312）
import json
import os
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import wio
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')


def main():
    plan = HL.load_plan(HERE)
    hull = HL.TekpaiHull(plan)
    SX, SY, SZ = hull.SX, hull.SY, hull.SZ

    exp_arr = wio.load_lists(os.path.join(HERE, 'masks'))
    act_arr = wio.export_list('pinnacle-tekpai-01m', mark=None, links='none')

    G_exp = np.zeros((SX, SY, SZ), dtype=np.uint8)
    G_act = np.zeros((SX, SY, SZ), dtype=np.uint8)
    if len(exp_arr):
        G_exp[exp_arr[:, 0], exp_arr[:, 1], exp_arr[:, 2]] = exp_arr[:, 3].astype(np.uint8)
    if len(act_arr):
        G_act[act_arr[:, 0], act_arr[:, 1], act_arr[:, 2]] = act_arr[:, 3].astype(np.uint8)

    occ_exp = G_exp > 0
    occ_act = G_act > 0
    missing = int((occ_exp & ~occ_act).sum())
    extra = int((occ_act & ~occ_exp).sum())
    color_mismatch = int((occ_exp & occ_act & (G_exp != G_act)).sum())

    # 結構檢查（以作品實際匯出陣列計算）
    _, comp_count = ndimage.label(occ_act)
    cavities = int((ndimage.binary_fill_holes(occ_act) & ~occ_act).sum())
    mirror_diff = int((G_act != G_act[:, ::-1, :]).sum())

    # 反向對照：作品實際艏尖頂高度 vs probe(rocker_fwd_z=+3)
    act_bow_z = int(np.where(occ_act[int(hull.xf), hull.YC, :])[0].max())
    G_probe = HL.TekpaiHull(plan, probe={'rocker_fwd_z': 3}).build_voxels()
    probe_bow_z = int(np.where(G_probe[int(hull.xf), hull.YC, :] > 0)[0].max())
    neg_delta = probe_bow_z - act_bow_z

    report = {
        'work': 'pinnacle-tekpai-01m',
        'expected_count': int(occ_exp.sum()),
        'actual_count': int(occ_act.sum()),
        'ledger': {
            'missing': missing,
            'extra': extra,
            'color_mismatch': color_mismatch,
        },
        'structure': {
            'components_6conn': int(comp_count),
            'closed_cavities': cavities,
            'mirror_diff': mirror_diff,
        },
        'reverse_control': {
            'actual_bow_tip_top_z': act_bow_z,
            'probe_rocker_fwd_z_plus3': probe_bow_z,
            'delta': neg_delta,
        },
        'ok': (
            missing == 0 and extra == 0 and color_mismatch == 0
            and comp_count == 1 and cavities == 0 and mirror_diff == 0
            and neg_delta == 3
        ),
    }
    out_path = os.path.join(HERE, 'verify_step04.json')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert report['ok'], f"步驟 4 驗收未過：{report}"


if __name__ == '__main__':
    main()

# 星辰號 步驟 4 結果帳（TASK-0019）：events 重播 vs 設計（draft_ports.build）逐格比 —— 作品＝設計
#   用法：python -X utf8 verify_step4.py <作品資料夾> [--probe=port_dx=+3]
#   · 重播只讀 events/ 的 stampvox（placed_colored）／box（placed_voxels＋color）／carve／carvevox（carved_voxels），⛔ 不讀引擎的視圖
#   · --probe：拿砲門整排挪 dx 格的設計來比（反向對照：帳要報得出差）
#   · 結構讀數（元件、空腔、鏡像差）也在重播出來的格子上算，不在設計上算
import sys, os, json, glob
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
from draft_ports import build


def replay(work_dir):
    cells = {}
    evs = sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json')))
    log = []
    for p in evs:
        e = json.load(open(p, encoding='utf-8'))
        op = e.get('op')
        n0 = len(cells)
        if op == 'stampvox' or 'placed_colored' in e:
            for x, y, z, c in e['placed_colored']:
                cells[(x, y, z)] = c
        elif op == 'box':
            for x, y, z in e.get('placed_voxels', []):
                cells[(x, y, z)] = e['color']
        if 'carved_voxels' in e:
            for v in e['carved_voxels']:
                cells.pop(tuple(v[:3]), None)
        log.append({'event': os.path.relpath(p, work_dir), 'op': op, 'delta': len(cells) - n0})
    return cells, log


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    work_dir = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    dx = int(probe[0].split('=')[1]) if probe else 0
    design = os.path.join(work_dir, 'design')
    plan = HL.load_plan(design)
    B = build(plan, port_dx=dx)
    x0, ylo, keep, final = B['x0'], B['ylo'], B['keep'], B['final']
    want = {(int(i + x0), int(j + ylo), int(k)): int(final[i, j, k]) for i, j, k in np.argwhere(keep)}
    have, log = replay(work_dir)
    missing = [k for k in want if k not in have]
    extra = [k for k in have if k not in want]
    recol = [k for k in want if k in have and have[k] != want[k]]
    # 正向對照：拿一格確定存在的格（設計清單第一格）用同一把查詢查一次
    k0 = next(iter(sorted(want)))
    R = {'probe': probe[0] if probe else None, 'events': log, 'want': len(want), 'have': len(have),
         'missing': len(missing), 'extra': len(extra), 'color_diff': len(recol),
         'positive_control': {'cell': list(k0), 'want': want[k0], 'have': have.get(k0)},
         'missing_sample': missing[:5], 'extra_sample': extra[:5], 'color_diff_sample': recol[:5]}
    if not probe:
        sx, sy, sz = 420, 160, 120
        A = np.zeros((sx, sy, sz), np.uint8)
        for (x, y, z), c in have.items():
            A[x, y, z] = c
        occ = A > 0
        lab, n = ndimage.label(occ)
        cav = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
        yc = plan['space']['yc']
        ys = np.arange(sy)
        yy = 2 * yc - ys
        ok = (yy >= 0) & (yy < sy)
        mir = int((A[:, ys[ok], :] != A[:, yy[ok], :]).sum())
        R.update({'components_6': int(n), 'cavity_cells': cav, 'mirror_diff_cells': mir,
                  'colors': {int(c): int(v) for c, v in zip(*np.unique(A[occ], return_counts=True))}})
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

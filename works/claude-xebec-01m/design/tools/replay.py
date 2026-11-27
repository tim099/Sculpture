# 出處：claude-galiot-01m/design/tools/replay.py（蠍子號，照抄；利劍號每個步驟共用）。以下是它原本的出處說明。
# 利劍號／蠍子號 結果帳（每個步驟共用）：自己重播作品的 events，跟設計清單逐格比 —— 作品＝設計（Sculpture_Blueprint_Build §6.1：⛔ 不讀引擎的視圖當真相）
#   出處：claude-felucca-01m/design/tools/replay.py（海鷗號）；重播的寫法照星辰號 claude-baghlah-01m/design/verify_step4.py 的 replay()
#        （stampvox 的 placed_colored、box 的 placed_voxels、carve／carvevox 的 carved_voxels）。
#   改的地方：寫死的寬 161（海鷗號）改成 plan.json 的 2·yc＋1；鏡像照 yc。
#   用法：python -I -X utf8 tools/replay.py <作品 id> <清單.vox.txt>[+<換色清單.vox.txt>…] [--shift=dz] [--json=<輸出檔>]
#     · 清單照順序疊：第一份是落格，後面「+」接的是 overwrite 換色（同一格後面的蓋前面的）；「+~清單」是刻掉的格（步驟 7 桅孔）。路徑相對 design/。
#     · --shift=dz：設計整片往上搬 dz 格再比（反向對照：帳要報得出缺／多）。
#   印：events 幾刀、重播幾格、缺／多／色差、正向對照（設計第一格在重播裡的顏色）；重播出來的格子上的元件數、封閉空腔、鏡像差（y ↔ 2·yc − y）。
import sys, os, json, glob
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKS = os.path.dirname(os.path.dirname(HERE))
sys.stdout.reconfigure(encoding='utf-8')
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
WY = 2 * int(PLAN['space']['yc']) + 1


def replay(work):
    d = os.path.join(WORKS, work)
    cells = {}
    evs = sorted(glob.glob(os.path.join(d, 'events', '*', '*.json')))
    ops = {}
    for p in evs:
        e = json.load(open(p, encoding='utf-8'))
        op = e.get('op')
        ops[op] = ops.get(op, 0) + 1
        if 'placed_colored' in e:
            for x, y, z, c in e['placed_colored']:
                cells[(x, y, z)] = c
        elif op == 'box':
            for x, y, z in e.get('placed_voxels', []):
                cells[(x, y, z)] = e['color']
        if 'carved_voxels' in e:
            for v in e['carved_voxels']:
                cells.pop(tuple(v[:3]), None)
    return cells, len(evs), ops


def load(spec, shift=0):
    want = {}
    for i, f in enumerate(spec.split('+')):
        cut = f.startswith('~')                             # 「+~清單」＝ 從設計拿掉這些格（步驟 7 甲板-main 的桅孔）
        a = np.loadtxt(os.path.join(HERE, f.lstrip('~')), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
        for x, y, z, c in a.tolist():
            if cut:
                want.pop((x, y, z + shift), None)
            else:
                want[(x, y, z + shift)] = c
    return want


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    work, spec = args[0], args[1]
    shift = int(opt.get('shift', 0))
    have, nev, ops = replay(work)
    want = load(spec, shift)
    missing = [k for k in want if k not in have]
    extra = [k for k in have if k not in want]
    recol = [k for k in want if k in have and have[k] != want[k]]
    k0 = sorted(want)[0]
    R = {'work': work, 'design': spec, 'shift': shift, 'events': nev, 'ops': ops, 'have': len(have), 'want': len(want),
         'missing': len(missing), 'extra': len(extra), 'color_diff': len(recol),
         'positive_control': {'cell': list(k0), 'want': want[k0], 'have': have.get(k0)}}
    if have:
        ks = np.array(sorted(have))
        mx = ks.max(axis=0) + 2
        A = np.zeros((int(mx[0]), max(int(mx[1]), WY), int(mx[2])), np.uint8)
        for k, c in have.items():
            A[k] = c
        S = A > 0
        lab, n = ndimage.label(S)
        cav = int((ndimage.binary_fill_holes(S) & ~S).sum())
        M = A[:, :WY, :]
        R['structure'] = {'components': int(n), 'cavity_cells': cav, 'mirror_diff_cells': int((M != M[:, ::-1, :]).sum())}
    print(json.dumps(R, ensure_ascii=False))
    if 'json' in opt:
        with open(os.path.join(HERE, opt['json']), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(R, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()

"""威尼斯 galeazza（TASK-1302）步驟 7：三根下桅＋三根三角帆桁（Ship_Masts §5；lateen ⇒ yard=gaff＋rig=lateen＋固定點 fore）。

出處：meadow-venice-galea-01m/design/apply_rig.py 的 geometry()（桅錐度、帆桁沿 peak→fore 一條線、pivot 在桅軸上偏左舷）。
尺寸：桅高、帆桁長查不到（plan.json rig_table 的 src）⇒ 照 meadow galea 的主帆（桅 x 248、corsia 頂 z 21）相對座標
    放大：maestra ×1.19、trinchetto 照 galea 前帆 ×1.15、mezzana 照 galea 主帆 ×0.66（帆桁比前桅短，Coronelli／Grevenbroeck 後桅最小）；基準改成本船 corsia 頂（z 38）。
    主帆 clew 往前挪到 x 185（讓開後桅，帆面不穿過 mezzana）。
輸出 masks/rig/<桅>-mast.vox.txt、<桅>-yard.vox.txt（帆桁在自己的小框裡、沒轉）、rig.json（每根的點與模型擺法）。
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent
YC, BASE, WOOD = 160, 38, 104

# galea 的原始相對量（meadow rig_dimensions.json）：(相對桅的 x, 相對走道頂的 z)
GALEA_MAIN = dict(top=163, peak=(-160, 223), fore=(81, 63), clew=(-139, 77))
GALEA_FORE = dict(top=136, peak=(-54, 169), fore=(84, 52), clew=(-38, 48))
RIG = {
    'main':   dict(x=318, src=GALEA_MAIN, s=1.19, r=(3.0, 1.8), clew_x=185, it='maestra'),
    'fore':   dict(x=452, src=GALEA_FORE, s=1.15, r=(2.7, 1.6), clew_x=None, it='trinchetto'),
    'mizzen': dict(x=168, src=GALEA_MAIN, s=0.66, r=(2.2, 1.3), clew_x=None, it='mezzana'),
}


def main():
    out = D / 'masks/rig'
    out.mkdir(parents=True, exist_ok=True)
    info = {}
    for name, R in RIG.items():
        s, x = R['s'], R['x']
        top = BASE + round(R['src']['top'] * s)
        pk = (x + round(R['src']['peak'][0] * s), BASE + round(R['src']['peak'][1] * s))
        fo = (x + round(R['src']['fore'][0] * s), BASE + round(R['src']['fore'][1] * s))
        cl = (R['clew_x'] if R['clew_x'] else x + round(R['src']['clew'][0] * s), BASE + round(R['src']['clew'][1] * s))
        mast = {}
        r0, r1 = R['r']
        for z in range(BASE, top + 1):
            rad = r0 - (r0 - r1) * (z - BASE) / (top - BASE)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx * dx + dy * dy <= rad * rad:
                        mast[(x + dx, YC + dy, z)] = WOOD
        # 帆桁：小框原點 origin，沿 peak → fore 兩格寬（y 2..3），中段 3 格（y 1..3）；pivot 在桅軸那一 x
        ax, az = pk
        bx, bz = fo
        L = int(math.ceil(math.hypot(ax - bx, az - bz)))
        origin = [ax - 2, YC - 5, bz - 2]
        peak = [2, 2, az - origin[2]]
        fore = [bx - origin[0], 2, 2]
        yard = {}
        for t in np.linspace(0.0, 1.0, L * 4):
            px = peak[0] + (fore[0] - peak[0]) * t
            pz = peak[2] + (fore[2] - peak[2]) * t
            thick = 3 if 0.3 < t < 0.7 else 2
            for dy in range(thick):
                yard[(int(round(px)), 3 - dy, int(round(pz)))] = WOOD
        lx = x - origin[0]
        lz = round(az + (bz - az) * (x - ax) / (bx - ax)) - origin[2]
        pivot = [lx, 3, lz]
        assert (lx, 3, lz) in yard or any((lx + d, 3, lz + e) in yard for d in (-1, 0, 1) for e in (-1, 0, 1)), name
        hound_z = top - 8
        info[name] = dict(italian=R['it'], x=x, top_z=top, hound=[x, YC, hound_z],
                          peak_w=list(pk), fore_w=list(fo), clew_w=[cl[0], YC - 2, cl[1]],
                          yard_origin=origin, yard_size=[fore[0] + 3, 7, peak[2] + 3], yard_length_m=round(L / 10, 1),
                          pivot=pivot, peak=peak, fore=fore, model_at=[pivot[i] + origin[i] + 0.5 for i in range(3)],
                          pivot_world_z=lz + origin[2], mast_cells=len(mast), yard_cells=len(yard))
        for part, cells in (('mast', mast), ('yard', yard)):
            body = ''.join(f'{a},{b},{c},{v}\n' for (a, b, c), v in sorted(cells.items())).encode('ascii')
            (out / f'{name}-{part}.vox.txt').write_bytes(body)
            info[name][part + '_sha16'] = hashlib.sha256(body).hexdigest()[:16]
        assert 10 <= info[name]['pivot_world_z'] - BASE, name      # 桅身在帆桁轉軸下 10–40 格有格（shipcheck）
    (D / 'rig.json').write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: {kk: v[kk] for kk in ('top_z', 'yard_length_m', 'pivot_world_z', 'peak_w', 'fore_w', 'clew_w')} for k, v in info.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()

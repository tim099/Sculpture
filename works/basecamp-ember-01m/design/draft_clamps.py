# 餘燼號 階段八b：上甲板 clamps（plan.json clamps_build）
#   憲法號 spar deck clamp（hull 裡、色 136、高 2、頂 ＝ 橫樑底；內板 177 往船艙裡多一格）照 x 拉長、z ＋23 搬到上甲板底下。
#   ⚠ 不是複製憲法號的 clamp 格：插入段的牆是 z 108 那一層複製上去的，跟憲法號 z 99–100 的牆位置不一樣 ⇒
#     照餘燼號自己的內板重生：clamp 那幾層裡、內板格同一層 4 鄰居裡的船艙空氣（組裝件現況是空的）⇒ 一格 clamp。
#   ⇒ masks/clamps/spar_clamp.vox.txt（世界座標，落進船殼 basecamp-ember-01m）、verify_clamps.json
# 用法：python -I draft_clamps.py <design 資料夾>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402

YC = 160


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    C = plan['clamps_build']
    hull = {(int(x), int(y), int(z)): int(c) for x, y, z, c in DP.export_list(C['hull'])}
    asm = {(int(x), int(y), int(z)): int(c) for x, y, z, c in DP.export_list(C['assembly'], 'all')}
    assert len(asm) == C['assembly_voxels'], ('組裝件現況對不上', len(asm))

    def layers(x):
        for a, b, zs in C['runs']:
            if a <= x <= b:
                return zs
        return ()
    cells, dropped = {}, 0
    for (x, y, z), c in hull.items():
        if c != C['lining'] or abs(y - YC) < C['min_dy'] or z not in layers(x):
            continue
        for k in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z)):
            if k in hull or k in cells:
                continue
            # 只往船艙裡：鄰格比內板更靠中線（|dy| 不變的 ±x 鄰格：船頭船尾彎的那段）
            if abs(k[1] - YC) > abs(y - YC):
                continue
            if k in asm:
                dropped += 1
                continue
            cells[k] = C['color']
    # 斜接：同一層裡兩個正交方向都貼著 clamp、又斜貼內板的空氣格補一格（船頭船尾彎處不碎成磚）
    add = {}
    for (x, y, z) in list(cells):
        for dx in (-1, 1):
            for dy in (-1, 1):
                k = (x + dx, y + dy, z)
                if k in cells or k in hull or k in asm or abs(k[1] - YC) < C['min_dy']:
                    continue
                # 只補貼著內板那一側的缺口（第一版沒這條：6 格補在內角、變成往船艙裡凸的小疙瘩）
                if not any(hull.get((k[0] + a, k[1] + b, z)) == C['lining'] for a in (-1, 0, 1) for b in (-1, 0, 1)):
                    continue
                if (x + dx, y, z) in cells and (x, y + dy, z) in cells:
                    add[k] = C['color']
    cells.update(add)
    v = {'cells': len(cells), 'miter_added': len(add), 'dropped_hit_assembly': dropped}
    v['by_z'] = {str(z): n for z, n in sorted(__import__('collections').Counter(k[2] for k in cells).items())}
    xs = [k[0] for k in cells]
    v['x'] = [min(xs), max(xs)]
    v['mirror_mismatch'] = sum(1 for (x, y, z) in cells if (x, 320 - y, z) not in cells)
    v['overlap_assembly'] = sum(1 for k in cells if k in asm)
    # 每一格都要貼著內板（6 鄰居或同層斜鄰）
    v['not_touching_lining'] = sum(1 for (x, y, z) in cells if not any(hull.get((x + a, y + b, z)) == C['lining'] for a in (-1, 0, 1) for b in (-1, 0, 1)))
    R = dict(asm)
    R.update(cells)
    v['assembly_expect'] = len(R)
    out = os.path.join(design, 'masks', 'clamps')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'spar_clamp.vox.txt')
    rows = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
    open(p, 'w', encoding='utf-8', newline='\n').write('# 上甲板 clamp（世界座標，落進船殼 at 0,0,0）（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    v['file'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    json.dump(v, open(os.path.join(design, 'verify_clamps.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

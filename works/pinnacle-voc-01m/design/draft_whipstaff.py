# 金冠號 步驟 11：操舵桿 kolderstok（whipstaff）—— TASK-1317
#   1660 年代的荷蘭大船沒有舵輪：舵柄（roerpen）從舵頭伸進砲手長艙，舵手站在 halfdek 底下的 stierplecht、握著穿過 verdeck 的 kolderstok
#   （研究筆記 references/research_voc_2026-11-18.md §8：W p.88 kolderstok 穿過舵手艙上方的拱孔、W p.92「De kolder-stock lang 9 voet, dik 4 duim」）。
#   做成一件 0.1 m 的子作品 -whipstaff、掛成 verdeck 子作品的外部模型 kind=tiller（Ship_Helm 操舵鏈「舵柄（獨立模型）」那一列）＋ spin 跟著舵角左右擺。
#   輸入：plan.json whipstaff；輸出：masks/whipstaff/whipstaff.vox.txt（子作品座標）、masks/whipstaff/deck_hole.vox.txt（verdeck 讓桿穿過的格）、whipstaff_placement.json
#   用法：python -I -X utf8 draft_whipstaff.py <design>
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    W = plan['whipstaff']
    x, y, deck = W['x'], plan['space']['yc'], W['deck_z']
    z0, z1 = W['z_bottom'], W['z_top']
    C = W['colors']
    world = {}
    for z in range(z0, z1 + 1):                                   # 桿：1 × 1（4 duim ≈ 1 格）
        world[(x, y, z)] = C['staff']
    for dz in (1, 2):                                             # rolle：甲板面上一圈 3 × 3（桿在中間）
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    world[(x + dx, y + dy, deck + dz)] = C['rolle']
    for z in (z1 - 1, z1):                                        # 把手：頂上 3 × 3
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                world[(x + dx, y + dy, z)] = C['grip']
    for dx in (-1, 1):                                            # 底下接舵柄的鐵眼（舵柄 roerpen 沒做 ⚠）
        world[(x + dx, y, z0)] = C['iron']
    o = (x - 2, y - 2, z0 - 1)                                    # 子作品的原點（世界座標）
    local = {(k[0] - o[0], k[1] - o[1], k[2] - o[2]): c for k, c in world.items()}
    od = os.path.join(design, 'masks', 'whipstaff')
    os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, 'whipstaff.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 金冠號 操舵桿 kolderstok（子作品座標，0.1 m；draft_whipstaff.py）\n')
        for k in sorted(local):
            f.write('%d,%d,%d,%d\n' % (k + (local[k],)))
    D = {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(os.path.join(design, 'masks', 'decks', 'puente.vox.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')}
    hole = sorted(k for k in world if k in D)
    with open(os.path.join(od, 'deck_hole.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# verdeck 讓 kolderstok 穿過的格（從甲板-puente 刻掉；帶現在的顏色）\n')
        for k in hole:
            f.write('%d,%d,%d,%d\n' % (k + (D[k],)))
    A = export_list('pinnacle-voc-01m-assembly', None, links=None)
    occ = set(map(tuple, A[:, :3].tolist()))
    hits = sorted(k for k in world if k in occ and k not in set(hole))
    pv_local = [W['x'] - o[0] + 0.5, y - o[1] + 0.5, deck + 1 - o[2]]          # 轉軸在 rolle（甲板面上），沿船長方向
    pv_world = [W['x'] + 0.5, y + 0.5, deck + 1.0]
    size = [5, 5, z1 - o[2] + 1]
    meta = dict(W['meta'], spin_pivot_x=pv_world[0], spin_pivot_y=pv_world[1], spin_pivot_z=pv_world[2], spin_axis_x=1, spin_axis_y=0, spin_axis_z=0)
    P = {'work': W['work'], 'host': W['host'], 'name': W['name'], 'origin': list(o), 'size': size, 'pivot': pv_local, 'at': pv_world, 'scale': 1, 'meta': meta}
    with open(os.path.join(design, 'whipstaff_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(P, f, ensure_ascii=False, indent=1)
    R = {'cells': len(local), 'deck_hole': len(hole), 'hits_solid': len(hits), 'hits_sample': hits[:6],
         'below_deck': deck - z0, 'above_deck': z1 - deck, 'mirror_diff': sum(1 for (a, b, c) in world if (a, 2 * y - b, c) not in world),
         'list_sha256': hashlib.sha256(open(os.path.join(od, 'whipstaff.vox.txt'), 'rb').read()).hexdigest()}
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

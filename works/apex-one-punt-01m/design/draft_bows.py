# 蓬特號 新圖紙 07（TASK-0754）：弓手（「弓」換皮大砲 ×4，艏艉平台各兩把）＋箭庫（貨艙梯腳旁，弩箭箱 ×4）＋弓弦
#   Tim 2026-10-20：「做「弓」換皮砲（照弩砲的做法）加箭箱當彈藥庫」。史實：蓬特浮雕的士兵帶矛、盾、斧；複合弓是同時代標準（Medinet Habu 的船上弓箭手）。
#   ⇒ masks/bow/magazine.vox.txt、bows_placement.json、verify_bows.json
#   用法：python -I -X utf8 draft_bows.py [--nudge=bow-fwd-S:0,-3]   （反向對照：把一把往某方向挪幾格 ⇒ 碰撞要報出來）
#   · 每把弓：迴旋 mount=pivot、ports 0／±45；三個角度的格心＋八角都不落在船的實心、也不碰到別的模型（別把弓、石錨、舵槳）。
#   · 箭庫：貨艙地板上一塊板（z 3）、弩箭箱（erina-dromon-01m-store-boltbox，store=bolt）四個；彈藥庫 meta hoist 三座梯子（貨艙、艉台、艏台）。
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
from draft_lines import V
from draft_oars import occupancy

sys.stdout.reconfigure(encoding='utf-8')
CORN = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)])


def rotz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def place(cells, piv, at, scale, rz):
    pts = np.concatenate([cells + 0.5] + [cells + 0.5 + c for c in CORN])
    return (pts - piv) * scale @ rotz(rz).T + at


def main():
    nudge = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--nudge=')), None)
    plan = HL.load_plan()
    K = {k: V(v) for k, v in plan['bows'].items()}
    YC = plan['space']['yc']
    occ = occupancy(plan)
    BP = json.load(open(os.path.join(HERE, 'bow_part.json'), encoding='utf-8'))
    bow = np.loadtxt(os.path.join(HERE, 'masks', 'bow', 'bow.vox.txt'), delimiter=',', comments='#', dtype=float, ndmin=2)[:, :3]
    bpiv = np.array(BP['pivot_model'])
    S = 0.5
    # 別的模型（量弓跟它們有沒有撞到）：石錨、舵槳（照它們的格心）
    others = {}
    an = json.load(open(os.path.join(HERE, 'anchor_placement.json'), encoding='utf-8'))
    stone = np.loadtxt(os.path.join(HERE, 'masks', 'anchor', 'stone.vox.txt'), delimiter=',', comments='#', dtype=float, ndmin=2)[:, :3]
    for m in an['models']:
        others[m['name']] = np.floor((stone + 0.5 - m['pivot']) * m['scale'] + m['at']).astype(int)
    rud = np.loadtxt(os.path.join(HERE, 'masks', 'steer', 'rudder.vox.txt'), delimiter=',', comments='#', dtype=int, ndmin=2)[:, :3]
    others['rudder-S'] = rud
    rp = rud.copy()
    rp[:, 1] = 2 * YC - rp[:, 1]
    others['rudder-P'] = rp
    out, R = {'bows': [], 'magazine': {}, 'ropes': []}, {'bows': []}
    placed = {}
    for b in K['bows']:
        name = b['name']
        at = np.array([b['x'] + 0.5, YC + 0.5 + b['dy'], b['z']], float)
        if nudge and nudge.split(':')[0] == name:
            dx, dy = map(float, nudge.split(':')[1].split(','))
            at += [dx, dy, 0]
        rz = 0 if b['dy'] > 0 else 180
        res = {'name': name}
        cellsets = []
        ports = [int(p) for p in b.get('ports', '0,45,-45').split(',')]
        for port in ports:
            W = place(bow, bpiv, at, S, rz + port)
            ci = np.floor(W).astype(int)
            res['collide_%+d' % port] = int(occ[ci[:, 0], ci[:, 1], ci[:, 2]].sum())
            cellsets.append(set(map(tuple, np.floor(place(bow, bpiv, at, S, rz + port)[:len(bow)]).astype(int).tolist())))
        placed[name] = set().union(*cellsets)
        # 弓手站的地方：扣弦點後面 2 格（遊戲照砲班站位找；這裡只量那一格站不站得住）
        nk = (np.array(BP['anchors']['nock']) + 0.5 - bpiv) * S @ rotz(rz).T + at
        back = nk + (rotz(rz) @ np.array([0, -2.0, 0]))
        c = np.floor(back).astype(int)
        c[2] = int(math.floor(at[2]))              # 站在平台上（扣弦點的高度是手，不是腳）
        res['archer_cell'] = c.tolist()
        res['archer_ok'] = bool(not occ[c[0], c[1], c[2]] and occ[c[0], c[1], c[2] - 1] and not occ[c[0], c[1], c[2]:c[2] + 14].any())
        out['bows'].append({'name': name, 'work': b['work'], 'at': at.round(3).tolist(), 'pivot': bpiv.tolist(), 'scale': S, 'rotate': [0, 0, rz], 'meta': dict(BP['meta'], ports=b.get('ports', BP['meta']['ports']))})
        for a, bb in (('string-a', 'nock'), ('nock', 'string-b')):
            out['ropes'].append({'work': b['work'], 'name': '%s-弦-%s' % (name, a[-1] if a != 'nock' else 'b'), 'from': 'model:%s/%s' % (name, a), 'to': 'model:%s/%s' % (name, bb),
                                 'slack': 1, 'thickness': 0.15, 'color': '#d8c8a0', 'meta': {'kind': 'bowstring', 'anim': 'gun', 'rest': 'nock', 'fire': 'nock-fire'}})
        R['bows'].append(res)
    # 弓跟弓、弓跟別的模型
    names = list(placed)
    R['bow_vs_bow'] = {'%s×%s' % (a, b): len(placed[a] & placed[b]) for i, a in enumerate(names) for b in names[i + 1:]}
    R['bow_vs_model'] = {'%s×%s' % (a, o): len(placed[a] & set(map(tuple, others[o].tolist()))) for a in names for o in others}
    R['bow_vs_model'] = {k: v for k, v in R['bow_vs_model'].items() if v}
    # ───── 箭庫 ─────
    M = K['magazine']
    shelf = {}
    for x in range(M['x'][0], M['x'][1] + 1):
        for y in range(YC - M['half'], YC + M['half'] + 1):
            if not occ[x, y, M['z']]:
                shelf[(x, y, M['z'])] = M['color']
    for p in shelf:
        occ[p] = True
    box = wio.export_list('erina-dromon-01m-store-boltbox', None)[:, :3].astype(float)
    boxes, hits = [], 0
    for i, (bx, by) in enumerate(M['boxes'], 1):
        at = [bx + 0.5, YC + 0.5 + by, M['z'] + 1.3]
        W = place(box, np.array([5.5, 3.5, 0]), np.array(at), 0.5, 0)
        ci = np.floor(W).astype(int)
        h = int(occ[ci[:, 0], ci[:, 1], ci[:, 2]].sum())
        hits += h
        boxes.append({'name': '箭箱-%d' % i, 'at': at, 'pivot': [5.5, 3.5, 0], 'scale': 0.5, 'meta': {'kind': 'powder', 'powder_lb': 100, 'store': 'bolt'}, 'collide': h})
    cx = (M['x'][0] + M['x'][1]) // 2
    out['magazine'] = {'cells': [[x, y, z, c] for (x, y, z), c in sorted(shelf.items())], 'boxes': boxes,
                       'anchors': {'blast': [cx, YC, M['z'] + 2], 'door': [M['x'][1] + 1, YC, M['z']]},
                       'meta': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(boxes), 'hoist': M['hoist']}}
    R['magazine'] = {'shelf': len(shelf), 'boxes': len(boxes), 'box_collide': hits,
                     'door_air': not occupancy(plan)[M['x'][1] + 1, YC, M['z']] and True}
    if nudge:
        print(json.dumps({'nudge': nudge, 'bows': R['bows'], 'bow_vs_bow': {k: v for k, v in R['bow_vs_bow'].items() if v}, 'bow_vs_model': R['bow_vs_model']}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'masks', 'bow', 'magazine.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蓬特號 箭庫的板（draft_bows.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % tuple(r) for r in out['magazine']['cells']) + '\n')
    with open(os.path.join(HERE, 'bows_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_bows.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

# 藍鯊號 艙壁門（kind=door）—— TASK-0967 補做（Tim 2026-10-26「繼續 go」）
#   三道 break 艙壁（後甲板前緣 x 300、船尾樓前緣 x 207、船艏樓後緣 x 436；draft_decks.py 開的門洞 寬 5 高 15、兩舷各一）各掛一扇門 ⇒ 6 扇。
#   · 一件門板子作品（0.05 m：厚 2、寬 14、高 32 ⇒ 船上 1 × 7 × 16 格 ＝ 門洞每邊大一格，底邊貼地板面）；掛在門洞所在那一層「上面那層」甲板的子作品裡
#     （艙壁是 draft_decks 畫在上面那層甲板的子作品裡的）；平貼在艙壁朝外（露天那一側）的面上。
#   · 鉸鏈直立（左右開）：固定點 hinge-a 在門板 y 0 那一邊的頂、hinge-b 在底 ⇒ 軸朝下 ⇒ 照右手定則門往模型 +x（朝外）開。
#     艙壁朝外是 +x（x 300、207）⇒ rotate 0；朝外是 −x（x 436）⇒ rotate 180（模型 +x 轉成船的 −x，照樣往外開）。
#   輸出：masks/doors/door.vox.txt（模型座標）、doors_placement.json、verify_doors.json
#   用法：python -I -X utf8 draft_doors.py <design>
import sys, os, json, math, hashlib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list

PLANK, PLANK2, SEAM, IRON = 136, 140, 96, 73
SIZE = (2, 14, 32)
PIVOT = (1, 7, 0)
SCALE = 0.5
DECK_WORK = {'alcazar': 'gura-pinas-01m-deck-alcazar', 'toldilla': 'gura-pinas-01m-deck-toldilla', 'castillo': 'gura-pinas-01m-deck-castillo'}


def build():
    v = {}
    for x in range(2):
        for y in range(14):
            for z in range(32):
                c = SEAM if y in (3, 7, 10) and x == 1 else (PLANK2 if (y // 3.5) % 2 else PLANK)
                v[(x, y, z)] = c
    for zz in (4, 5, 26, 27):                                   # 兩道鐵鉸鏈帶（外面那一層，從鉸鏈邊伸到 y 10）
        for y in range(0, 11):
            v[(1, y, zz)] = IRON
    for y in (0, 1):                                            # 鉸鏈邊的鐵條
        for z in range(3, 29):
            if z in (3, 6, 25, 28):
                v[(1, y, z)] = IRON
    for z in (15, 16):                                          # 拉環
        v[(1, 12, z)] = IRON
    return v


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    v = build()
    os.makedirs(os.path.join(design, 'masks', 'doors'), exist_ok=True)
    p = os.path.join(design, 'masks', 'doors', 'door.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 藍鯊號 艙壁門板（模型座標 0.05 m；draft_doors.py）\n')
        for k in sorted(v):
            f.write('%d,%d,%d,%d\n' % (k + (v[k],)))
    A = export_list('gura-pinas-01m-assembly', None, links=None)
    occ = set(map(tuple, A[:, :3].tolist()))
    rows, problems = [], []
    for br in plan['decks_build']['breaks']:
        bx = br['x']
        out = 1 if br.get('rail_side') == 'aft' else -1            # 船樓甲板的胸牆在船尾側（後甲板、船尾樓）⇒ 艙壁朝外是 +x；船艏樓 ⇒ −x
        for d in br['doors_dy']:
            for side, sgn in (('S', 1), ('P', -1)):
                y0 = 160 + sgn * d
                zs = [z for z in range(40, 120) if (bx, y0, z) not in occ and (bx, y0 - 3, z) in occ and (bx, y0 + 3, z) in occ]
                zb, zt = min(zs), max(zs)
                hole = [(bx, y, z) for y in range(y0 - 2, y0 + 3) for z in range(zb, zt + 1)]
                if any(h in occ for h in hole) or len(zs) != zt - zb + 1:
                    problems.append('%s %s 門洞不是一塊 5 × 15' % (br['name'], side))
                fx = bx + out
                cells = [(fx, y, z) for y in range(y0 - 3, y0 + 4) for z in range(zb, zb + 16)]
                hit = [c for c in cells if c in occ]
                back = sum(1 for (x, y, z) in cells if (bx, y, z) in occ)
                foot = all((fx, y, zb - 1) in occ for y in range(y0 - 3, y0 + 4))
                nm = '門-%s-%s' % (br['up'], side)
                rows.append({'name': nm, 'host': DECK_WORK[br['up']], 'break': br['name'], 'side': side,
                             'at': [fx + 0.5, y0 + 0.5, zb], 'rotate': 0 if out > 0 else 180, 'opening': [len(hole), zt - zb + 1],
                             'hits_solid': len(hit), 'backed_by_bulkhead': back, 'foot_ok': foot,
                             'meta': {'kind': 'door', 'open': 'side'}})
                if hit:
                    problems.append('%s 撞實心 %d' % (nm, len(hit)))
                if not foot:
                    problems.append('%s 門底下沒有地板' % nm)
    verify = {'doors': len(rows), 'model_cells': len(v), 'problems': problems, 'rows': rows,
              'list_sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    json.dump({'work': 'gura-pinas-01m-door', 'size': list(SIZE), 'pivot': list(PIVOT), 'scale': SCALE,
               'anchors': {'hinge-a': [1, 0, 31], 'hinge-b': [1, 0, 0]}, 'rows': rows},
              open(os.path.join(design, 'doors_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_doors.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: verify[k] for k in ('doors', 'model_cells', 'problems')}, ensure_ascii=False))
    for r in rows:
        print(' ', r['name'], r['at'], 'rot', r['rotate'], '洞', r['opening'], '撞', r['hits_solid'], '背後艙壁', r['backed_by_bulkhead'], '腳', r['foot_ok'])


if __name__ == '__main__':
    main()

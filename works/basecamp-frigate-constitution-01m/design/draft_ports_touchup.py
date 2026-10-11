# 階段八雕完細修（v1.1，2026-10-11；雕完派的 verifier 量到的三格）：
#   ① 白帶補漆：每個砲門上緣再往上一列、下緣再往下一列，開口 x 範圍裡最外面那一格外板是黑（36）⇒ 換白（255）
#      —— 第 4 個砲門讀數上緣 98.50 剛好落在 z98 的格中心，開口吃掉了白帶最上面那一格（上面整排變黑）；13／14／船頭那個有 1–3 欄碰到黑
#   ② 船頭砲門後壁的縫：(644, 160±32, 101..103) 兩舷各 3 格看得進船艙（cant 那一帶的肋骨面不是 m(z) 深）⇒ 補 141
#   ③ 砲門框封死的兩個單格空腔 (560, 160±56, 98) ⇒ 補 141（看不到；照「不新增封閉空腔」補上）
# v1.2（2026-10-11，船頭砲門改垂直）：
#   · 作品照「階段八之前＋設計」組出來（world_upto 重播 − carve_boxes ＋ lining），不再重播到 touchup_upto ——
#     v1 兩者逐格相同（結果帳 0 差）；v1.2 的設計沒有在作品裡單獨存在過，只能組
#   · ① 的範圍多算左右兩個角（xa−1、xb+1）：v1 第 4 個砲門上緣左上角留了一格黑缺口（todo）
#   · ② 拿掉：draft_ports.py 的砲門框改量「牆不能有洞」，那 6 格（＋上下緣 4 格）由它補
# 用法：python -I draft_ports_touchup.py <design 資料夾>  ⇒ masks/ports/touchup_paint.vox.txt（overwrite=1）、touchup_fill.vox.txt
import sys, os, json, glob, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from replay import replay      # noqa: E402

YC = 160


def load_list(f):
    out = {}
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            x, y, z, c = (int(v) for v in line.split(','))
            out[(x, y, z)] = c
    return out


def compose(design):
    """階段八之前的作品 − carve_boxes 盒子裡的格 ＋ lining（＝ 細修之前那一刻）。"""
    W = os.path.dirname(os.path.abspath(design))
    upto = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gunports']['world_upto']
    world = {k: v[0] for k, v in replay(W, upto=upto).items()}
    for b in json.load(open(os.path.join(design, 'masks', 'ports', 'carve_boxes.json'), encoding='utf-8'))['boxes']:
        for x in range(b['x1'], b['x2'] + 1):
            for y in range(b['y1'], b['y2'] + 1):
                for z in range(b['z1'], b['z2'] + 1):
                    world.pop((x, y, z), None)
    lining = load_list(os.path.join(design, 'masks', 'ports', 'lining.vox.txt'))
    assert all(c not in world for c in lining), '砲門框落在實心的格上'
    world.update(lining)
    return world


def main():
    design = sys.argv[1]
    vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
    world = compose(design)
    plank = set()
    for f in glob.glob(os.path.join(design, 'masks', 'planking', 'plank_*.vox.txt')) + [os.path.join(design, 'masks', 'planking', 'dub.vox.txt')]:
        for line in open(f, encoding='utf-8'):
            if line.strip() and not line.startswith('#'):
                plank.add(tuple(int(v) for v in line.split(',')[:3]))
    paint = {}
    for p in vp['ports']:
        rows = {int(z): v for z, v in p['x_rows'].items()}
        zs = sorted(rows)
        for z, zr in ((zs[-1] + 1, zs[-1]), (zs[0] - 1, zs[0])):
            xa, xb = rows[zr]
            for x in range(xa - 1, xb + 2):
                for side in (1, -1):
                    # 最外面那一格外板（這一欄 dy 最大的外板格）
                    outer = None
                    for d in range(80, -1, -1):
                        c = (x, YC + side * d, z)
                        if c in plank and c in world:
                            outer = c
                            break
                    if outer and world[outer] == 36:
                        paint[outer] = 255
    fill = {}
    for y in (YC + 56, YC - 56):
        fill[(560, y, 98)] = 141
    assert all(c not in world for c in fill), [c for c in fill if c in world]
    out = os.path.join(design, 'masks', 'ports')
    res = {}
    for name, cells, note in (('touchup_paint', paint, '白帶補漆：砲門上緣上一列／下緣下一列（含左右兩角）的黑外板換白（overwrite=1）'),
                              ('touchup_fill', fill, '砲門框封死的 2 個單格空腔，補 141')):
        p = os.path.join(out, name + '.vox.txt')
        body = '\n'.join('%d,%d,%d,%d' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格，at=0,0,0）\n' % (name, note, len(cells)) + body + '\n')
        res[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    by_port = {}
    for (x, y, z) in paint:
        if y > YC:
            n = next(pp['n'] for pp in vp['ports'] if any(int(zz) in (z - 1, z + 1) and v[0] - 1 <= x <= v[1] + 1 for zz, v in pp['x_rows'].items()))
            by_port[n] = by_port.get(n, 0) + 1
    res['paint_by_port_starboard'] = dict(sorted(by_port.items()))
    json.dump(res, open(os.path.join(out, 'touchup.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()

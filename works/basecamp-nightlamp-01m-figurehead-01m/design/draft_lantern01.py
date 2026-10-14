# 提燈（遊戲用 0.1 m／格，TASK-0538）：營地的大提燈 —— 逐格設計（0.1 m 看不到帳篷 Λ 與火焰，只留剪影：底板、四柱、玻璃、斜頂、煙囪蓋、提環）
# 用法：python -I draft_lantern01.py <design 資料夾>
#   · 子作品 basecamp-nightlamp-01m-lantern-01m（9×9×16）；燈置中在 x、y ＝ 4。
#   · 固定點：wick（燈身中間）、bail（提環頂）、base（底板中心）。
#   ⇒ masks/lantern01.vox.txt、lantern01_anchors.json
import sys, os, json


def main():
    design = sys.argv[1]
    C = {'iron': 73, 'brass': 172, 'glass': 253}
    g = {}
    c = 4
    for x in range(c - 3, c + 4):                       # 底板 7×7
        for y in range(c - 3, c + 4):
            g[(x, y, 0)] = C['iron']
    for z in range(1, 9):                                # 燈身 5×5×8：四柱、上下帶、玻璃
        for x in range(c - 2, c + 3):
            for y in range(c - 2, c + 3):
                edge = abs(x - c) == 2 or abs(y - c) == 2
                if not edge:
                    continue
                corner = abs(x - c) == 2 and abs(y - c) == 2
                g[(x, y, z)] = C['brass'] if corner or z in (1, 8) else C['glass']
    for x in range(c - 2, c + 3):                        # 斜頂兩層＋煙囪蓋
        for y in range(c - 2, c + 3):
            g[(x, y, 9)] = C['iron']
    for x in range(c - 1, c + 2):
        for y in range(c - 1, c + 2):
            g[(x, y, 10)] = C['iron']
    g[(c, c, 11)] = C['iron']
    for (y, z) in ((c - 1, 12), (c - 1, 13), (c - 1, 14), (c, 14), (c + 1, 14), (c + 1, 13), (c + 1, 12)):   # 提環（y–z 平面的框）
        g[(c, y, z)] = C['brass']
    cells = sorted(g.items())
    os.makedirs(os.path.join(design, 'masks'), exist_ok=True)
    with open(os.path.join(design, 'masks', 'lantern01.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜燈號 船首像的提燈 0.1 m（draft_lantern01.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
        for (x, y, z), col in cells:
            f.write('%d,%d,%d,%d\n' % (x, y, z, col))
    anchors = {'wick': [c, c, 4], 'bail': [c, c, 14], 'base': [c, c, 0]}
    json.dump(anchors, open(os.path.join(design, 'lantern01_anchors.json'), 'w', encoding='utf-8'), indent=1)
    mir = sum(1 for (x, y, z) in g if (2 * c - x, y, z) not in g or (x, 2 * c - y, z) not in g)
    print({'cells': len(cells), 'anchors': anchors, 'mirror_missing': mir})


if __name__ == '__main__':
    main()

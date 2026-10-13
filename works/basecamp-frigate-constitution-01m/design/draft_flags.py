# 憲法號 旗（Tim 2026-10-13：「是否可以給憲法號也加上旗幟」）—— 做法照餘燼號階段十九（basecamp-ember-01m/design/draft_flags.py）：
#   旗是帆（貼像素圖，TASK-0530），靠桅杆那條邊釘住、飛出去的角給風吹；桅冠上加旗桿（桅子作品），旗掛旗桿船頭那一側。
#   餘燼號的索具跟憲法號逐條比只差平移（桅在 z 109 插 23 格）⇒ 旗桿、旗角 ＝ 餘燼號的 z − 23；x 不變（後桅 187、主桅 341 都在拉長段 439 之後的船尾側）。
#   先量過（組裝件 list 匯出）：後桅 x 187 中線最高實心 z 513、主桅 x 341 z 649（＝ 餘燼號 536／672 − 23），上方 ±2 格都是空氣。
# 圖（史實，1812 年戰爭期間）：
#   · 船尾旗：十五星十五條紋旗（1795–1818 的 Flag Act 版本）—— 15 條紅白條紋（每條 2 px ⇒ 高 30）、左上藍角蓋住上面 8 條（16 px 高、22 px 寬），
#     15 顆星 5 排 × 3 交錯（十字形 5 px）。52×30 ≈ 旗角 40 × 23 格的比例。
#   · 長旗（commission pennant）：靠桅 12 欄藍底 3 顆白星、其餘上紅下白兩條，三角收尖。⚠ 1812 年長旗的星數與條紋細節沒查證 —— 照一般樣式畫。
# 用法：python -I draft_flags.py <design 資料夾> <組裝件 list 匯出檔>
#   ⇒ masks/flags/{ensign,pennant}.png、masks/flags/pole_{mizzen,main}.vox.txt（桅子作品座標 ＝ 世界座標，at 0,0,0）、verify_flags.json
import sys, os, json, hashlib
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
OUT = os.path.join(D, 'masks', 'flags')
os.makedirs(OUT, exist_ok=True)

RED, WHITE, BLUE = (178, 34, 52, 255), (245, 242, 234, 255), (40, 52, 110, 255)
ASSEMBLY = 'basecamp-frigate-constitution-01m-assembly'
ASSEMBLY_VOXELS = 1394450
PLAN = {
    'ensign': dict(name='ensign', px=[52, 30], corners=['188,160,538', '228,160,538', '228,160,515', '188,160,515'], bind='3', free='1,2', color='#b22234',
                   label='船尾旗（十五星十五條紋旗，1795–1818）'),
    'pennant': dict(name='pennant', px=[64, 6], corners=['343,160,668', '383,160,667', '343,160,664'], bind='2', free='1', color='#b22234',
                    label='長旗（commission pennant：藍底白星＋紅白兩條；細節未查證）'),
    'poles': [
        dict(work='basecamp-frigate-constitution-01m-mast-mizzen', label='後桅', x=187, y=160, z=[514, 538], color=177, cap_color=255),
        dict(work='basecamp-frigate-constitution-01m-mast-main', label='主桅', x=341, y=160, z=[650, 669], color=177, cap_color=255),
    ],
}


def plus(px, x, y, col, W, H):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x + dx < W and 0 <= y + dy < H:
            px[x + dx, y + dy] = col


def ensign():
    W, H = PLAN['ensign']['px']
    im = Image.new('RGBA', (W, H), WHITE)
    px = im.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = RED if (y // 2) % 2 == 0 else WHITE        # 15 條：最上、最下都是紅
    CW, CH = 22, 16                                                # 藍角蓋住上面 8 條
    for y in range(CH):
        for x in range(CW):
            px[x, y] = BLUE
    for r in range(5):                                             # 5 排 × 3 顆，奇數排錯開
        yy = 1 + r * 3                                             # y 1..13：下臂到 14、留 1 格藍邊不碰紅條（v2 從 2 起 ⇒ 最下一排的臂貼著紅條）
        for c in range(3):
            xx = (2 if r % 2 == 0 else 5) + c * 7                     # 偶數排 2／9／16、奇數排 5／12／19 ⇒ 左右各留 1 格藍邊（v1 從 7 起 ⇒ x 21 右臂被裁、自檢數到 13；v2 6 起 ⇒ 貼邊）
            plus(px, xx, yy, WHITE, CW, CH)
    return im


def pennant():
    W, H = PLAN['pennant']['px']
    im = Image.new('RGBA', (W, H), RED)
    px = im.load()
    for x in range(W):
        for y in range(H):
            if x < 12:
                px[x, y] = BLUE
            else:
                px[x, y] = RED if y < H // 2 else WHITE
    for x in (2, 5, 8):
        px[x, 2] = WHITE
        px[x, 3] = WHITE
    return im


files = {}
stars = 0
for name, im in (('ensign', ensign()), ('pennant', pennant())):
    p = os.path.join(OUT, name + '.png')
    im.save(p, optimize=False)
    files[name] = {'file': 'masks/flags/%s.png' % name, 'px': list(im.size), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(),
                   'colors': len({im.getpixel((x, y)) for x in range(im.size[0]) for y in range(im.size[1])})}
# 自己數一次：條紋 15、藍角裡的星 15（十字的中心格）
e = Image.open(os.path.join(OUT, 'ensign.png')).convert('RGBA')
col0 = [e.getpixel((51, y)) for y in range(30)]
files['ensign']['stripes'] = 1 + sum(1 for y in range(1, 30) if col0[y] != col0[y - 1])
files['ensign']['stars'] = sum(1 for y in range(1, 15) for x in range(1, 21)
                               if all(e.getpixel((x + dx, y + dy)) == WHITE for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))))
assert files['ensign']['stripes'] == 15 and files['ensign']['stars'] == 15, files['ensign']


def pole_cells(pole):
    cells = [(pole['x'], pole['y'], z, pole['color']) for z in range(pole['z'][0], pole['z'][1] + 1)]
    cap_z = pole['z'][1] + 1
    return cells + [(pole['x'] + dx, pole['y'] + dy, cap_z, pole['cap_color']) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]


a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
S = {(int(x), int(y), int(z)) for x, y, z, c in a}
S -= {c[:3] for pole in PLAN['poles'] for c in pole_cells(pole)}          # 重跑：扣掉本階段已落的旗桿再對格數
assert len(S) == ASSEMBLY_VOXELS, ('組裝件（這一階段之前）對不上', len(S), len(a))
for pole in PLAN['poles']:
    cells = pole_cells(pole)
    hit = [c[:3] for c in cells if c[:3] in S]
    assert not hit, ('旗桿撞到東西', pole['label'], hit[:5])
    below = (pole['x'], pole['y'], pole['z'][0] - 1)
    assert below in S, ('旗桿底下不是桅冠', pole['label'], below)
    name = 'pole_' + pole['work'].rsplit('-', 1)[1]
    txt = ''.join('%d,%d,%d,%d\n' % c for c in cells)
    open(os.path.join(OUT, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    files[name] = {'work': pole['work'], 'file': 'masks/flags/%s.vox.txt' % name, 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode()).hexdigest()}
files['plan'] = PLAN
files['assembly'] = ASSEMBLY
json.dump(files, open(os.path.join(D, 'verify_flags.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in files.items() if k != 'plan'}, ensure_ascii=False))

# 餘燼號 階段十九 旗（plan.json flags_build；外觀，自由設計）—— 旗是帆（貼像素圖，TASK-0530），靠桅杆那條邊釘住、飛出去那兩角給風吹
#   · 船尾旗（ensign）：後桅 royal 帆張到 z 525 ⇒ 桅冠（z 534–536）底下掛不下 ⇒ 桅冠上加一根旗桿（後桅子作品，x 187、y 160、
#     z 537..pole_top，頂上一塊 3×3 白冠），旗掛在旗桿船頭那一側，整面在所有帆的上方。
#   · 長旗（pennant）：主桅桅冠上也加旗桿（z 673..692），長旗掛在旗桿船頭那一側、高 0.4 m、長 4 m 的三角，燕尾。
#     v1 8 m、直接掛桅冠 ⇒ 風吹不起來、整條垂下蓋在 main-royal 帆前面（布沒有碰撞）⇒ 掛高、縮短。
#   · 圖：船尾旗 48×28 暗紅底、金邊、正中一團手畫的火（16×19：金邊→橘→黃，芯暗紅在底部；同船尾紋章色系）；長旗 64×6，靠桅杆 8 欄金、其餘暗紅、尾端燕尾（alpha 0）。
#   ⇒ masks/flags/{ensign,pennant}.png、masks/flags/pole_{mizzen,main}.vox.txt（桅杆子作品，世界座標 at 0,0,0）、verify_flags.json
# 用法：python -I draft_flags.py <design 資料夾>
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['flags_build']
OUT = os.path.join(D, 'masks', 'flags')
os.makedirs(OUT, exist_ok=True)


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


K = {k: hexrgb(v) for k, v in P['palette'].items()}


FLAME = [                                               # 手畫 16×19（G 金、O 橘、Y 黃、C 芯）；v1 用公式畫 ⇒ 芯太高、頂不夠尖，像拱門
    '.......G........',
    '......GG........',
    '......GOG.......',
    '.....GOOG....G..',
    '.....GOOG...GG..',
    '....GOOOG..GOG..',
    '....GOYOOG.GOG..',
    '...GOOYOOGGOOG..',
    '...GOYYYOOOOOG..',
    '..GOOYYYYOOOOG..',
    '..GOYYYYYYOOOG..',
    '.GOOYYYYYYYOOG..',
    '.GOYYYYCYYYYOG..',
    '.GOYYYCCCYYYOG..',
    '.GOYYCCCCCYYOG..',
    '.GOOYCCCCCYOOG..',
    '..GOOYCCCYOOG...',
    '...GGOOOOOOGG...',
    '.....GGGGGG.....',
]


def ensign():
    W, H = P['ensign']['px']
    im = Image.new('RGBA', (W, H), K['field'])
    px = im.load()
    for x in range(W):
        for y in range(H):
            if x in (0, W - 1) or y in (0, H - 1):
                px[x, y] = K['gold']
    ox, oy = (W - len(FLAME[0])) // 2, (H - len(FLAME)) // 2
    pal = {'G': K['gold'], 'O': K['orange'], 'Y': K['yellow'], 'C': K['core']}
    for r, row in enumerate(FLAME):
        for c, ch in enumerate(row):
            if ch in pal:
                px[ox + c, oy + r] = pal[ch]
    return im


def pennant():
    W, H = P['pennant']['px']
    im = Image.new('RGBA', (W, H), K['field'])
    px = im.load()
    for x in range(W):
        for y in range(H):
            if x < P['pennant']['gold_cols']:
                px[x, y] = K['gold']
            if x >= W - P['pennant']['tail_cols'] and (H - 1) / 2.0 - (x - (W - P['pennant']['tail_cols'])) * 0.5 < y + 0.5 < (H + 1) / 2.0 + (x - (W - P['pennant']['tail_cols'])) * 0.5:
                px[x, y] = (0, 0, 0, 0)                 # 燕尾：從中線往兩邊開
    return im


files = {}
for name, im in (('ensign', ensign()), ('pennant', pennant())):
    p = os.path.join(OUT, name + '.png')
    im.save(p, optimize=False)
    files[name] = {'file': 'masks/flags/%s.png' % name, 'px': list(im.size), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(),
                   'colors': len({im.getpixel((x, y)) for x in range(im.size[0]) for y in range(im.size[1]) if im.getpixel((x, y))[3] >= 128})}

# 旗桿：桅杆子作品的格（子作品 at 0,0,0 ⇒ 世界座標），每一格要是組裝件現況的空氣、最底下那格正下方要是桅冠
def pole_cells(pole):
    cells = [(pole['x'], pole['y'], z, pole['color']) for z in range(pole['z'][0], pole['z'][1] + 1)]
    cap_z = pole['z'][1] + 1
    return cells + [(pole['x'] + dx, pole['y'] + dy, cap_z, pole['cap_color']) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]


# 重跑要讀「這一階段之前」：現況扣掉本階段旗桿自己的格（已經落的那幾根），再對格數
a = export_hidden(P['assembly'], [])
S = {(int(x), int(y), int(z)) for x, y, z, c in a}
S -= {c[:3] for pole in P['poles'] for c in pole_cells(pole)}
assert len(S) == P['assembly_voxels'], ('組裝件（這一階段之前）對不上', len(S), len(a))
for pole in P['poles']:
    cells = pole_cells(pole)
    hit = [c[:3] for c in cells if c[:3] in S]
    assert not hit, ('旗桿撞到東西', pole['label'], hit[:5])
    below = (pole['x'], pole['y'], pole['z'][0] - 1)
    assert below in S, ('旗桿底下不是桅冠', pole['label'], below)
    name = 'pole_' + pole['work'].rsplit('-', 1)[1]
    txt = ''.join('%d,%d,%d,%d\n' % c for c in cells)
    open(os.path.join(OUT, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    files[name] = {'work': pole['work'], 'file': 'masks/flags/%s.vox.txt' % name, 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode()).hexdigest()}
json.dump(files, open(os.path.join(D, 'verify_flags.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps(files, ensure_ascii=False))

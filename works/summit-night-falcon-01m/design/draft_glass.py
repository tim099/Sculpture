# 窗的玻璃（Tim 2026-10-26「幫夜隼號 加上玻璃窗吧(目前是挖洞 但現在支援透明玻璃了)」；造船規格 Ship_Materials「窗的玻璃」）
#   階段六開窗時把階段五落的玻璃全刻掉（Tim 2026-10-13「窗戶部分可以直接開孔 這樣可以看到內構」）⇒ 現在遊戲有 material=glass（半透明＋反光），
#   照階段五那一份玻璃的位置原樣放回，各做成一件子作品、關聯 meta material=glass（⛔ 不寫 render）：
#   · 船尾窗：masks/stern_head/hull/stern_windows_glass.vox.txt（船殼座標，220 格、160 欄；斜艉板上下兩排補的那一格照留）
#       ⇒ 子作品 summit-night-falcon-01m-stern-glass，組裝件關聯 at = 那份清單的最小角
#   · 窗廊拱窗：masks/stern_head/quarter_gallery/quarter_gallery.vox.txt 裡玻璃色（37）那 90 格（窗廊座標）
#       ⇒ 子作品 summit-night-falcon-01m-gallery-glass，掛在窗廊（summit-night-falcon-01m-quarter-gallery）底下 ⇒ 兩舷跟著窗廊的鏡像關聯一起有
# 寫：masks/glass/stern_glass.vox.txt、gallery_glass.vox.txt（子作品自己的座標，stampvox at=0,0,0）、verify_glass.json（關聯的 at、尺寸、格數）
import os, json, hashlib
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
GLASS = 37


def read(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def part(a, name, note):
    lo = a[:, :3].min(0); hi = a[:, :3].max(0); loc = a[:, :3] - lo
    order = np.lexsort((loc[:, 2], loc[:, 1], loc[:, 0])); loc = loc[order]
    out = os.path.join(D, 'masks', 'glass', name + '.vox.txt')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    body = '# ' + note + '\n' + ''.join('%d,%d,%d,%d\n' % (x, y, z, GLASS) for x, y, z in loc)
    with open(out, 'w', encoding='utf-8', newline='\n') as f: f.write(body)
    return {'file': os.path.relpath(out, D).replace('\\', '/'), 'at': lo.tolist(), 'size': (hi - lo + 1).tolist(), 'n': int(len(loc)), 'sha1': hashlib.sha1(body.encode('utf-8')).hexdigest()[:12]}


st = read(os.path.join(D, 'masks', 'stern_head', 'hull', 'stern_windows_glass.vox.txt'))
qg = read(os.path.join(D, 'masks', 'stern_head', 'quarter_gallery', 'quarter_gallery.vox.txt'))
qg = qg[qg[:, 3] == GLASS]
v = {'stern_glass': part(st, 'stern_glass', '船尾窗玻璃（船殼座標減 at；關聯掛在組裝件）'),
     'gallery_glass': part(qg, 'gallery_glass', '窗廊拱窗玻璃（窗廊座標減 at；關聯掛在窗廊底下）')}
with open(os.path.join(D, 'verify_glass.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1); f.write('\n')
print(json.dumps(v, ensure_ascii=False))

# 蠍子號 引擎組出來的組裝件 vs 設計（步驟 10 起每一步共用）：export format=list links=all ⇒ 缺／多／色差、元件數、封閉空腔 ⇒ --json=<輸出檔>
#   出處：tools/check_masts.py（本船步驟 7）的「組裝件」那一段，拆成共用：設計 ＝ 船殼 hull_01＋步驟 6 換色＋甲板-main（扣桅孔）＋步驟 5–9 各件＋這一步加的清單（參數）。
#   用法：python -I -X utf8 tools/check_asm.py [--json=verify_stepN_assembly.json] [清單.vox.txt …]（路徑相對 design/；只收關聯進組裝件的格子件，外部模型不算）
import json, os, sys
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
T = 'claude-galiot-01m'


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
extra = [a for a in sys.argv[1:] if not a.startswith('--')]
want = load('masks/hull/hull_01.vox.txt')
want.update(load('masks/step6/hull_paint.vox.txt'))
hole = load('masks/masts/deck_hole.vox.txt')
want.update({k: c for k, c in load('masks/decks/deck_main.vox.txt').items() if k not in hole})
base = ['masks/decks/bow.vox.txt', 'masks/deco/spur.vox.txt', 'masks/deco/poop.vox.txt', 'masks/masts/main.vox.txt', 'masks/guns/posts.vox.txt']
for fn in base + extra:
    want.update(load(fn))
a = wio.export_list(T + '-assembly', None, links='all')
have = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
R = {'design_lists': ['hull_01', 'hull_paint', 'deck_main − deck_hole'] + base + extra,
     'have': len(have), 'want': len(want), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
     'color_diff': sum(1 for k in want if k in have and have[k] != want[k])}
S = np.zeros(tuple(int(v) + 2 for v in a[:, :3].max(axis=0)), bool)
S[a[:, 0], a[:, 1], a[:, 2]] = True
_, n = ndimage.label(S)
R['components_6'] = int(n)
R['cavities'] = int((ndimage.binary_fill_holes(S) & ~S).sum())
print(json.dumps(R, ensure_ascii=False))
if 'json' in opt:
    with open(os.path.join(HERE, opt['json']), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)

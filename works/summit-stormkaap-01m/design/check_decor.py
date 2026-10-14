# 階段十六讀數（落格之後）：只讀引擎的匯出，跟設計那一側（verify_decor.json、masks/decor、階段十五的匯出）比。
# 用法：python -I -X utf8 -B check_decor.py <design> <stage15 匯出資料夾> <stage16 匯出資料夾> [偏移 dx,dy,dz]
#   stage16 匯出資料夾裡：assembly.list.txt、hull.list.txt、decor.list.txt、assembly.obj
#   偏移 ＝ 反向對照：浮雕清單整批平移再比，該報的要報出來。
# 量的東西：
#   ① 子作品 -decor：引擎匯出 vs 浮雕清單（缺／多／色差）
#   ② 船殼：stage16 vs stage15，只有眼窩那幾格換了色、換成清單上的色；其他每一格逐格相同、格數不變
#   ③ 組裝件：stage16 ＝ stage15 換眼窩色 ∪ 浮雕（缺／多／色差）
#   ④ obj：砲（模型）的頂點、繩的管子頂點，落在浮雕格裡的個數
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); E15 = os.path.abspath(sys.argv[2]); E16 = os.path.abspath(sys.argv[3])
off = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else (0, 0, 0)
V = json.load(open(os.path.join(D, 'verify_decor.json'), encoding='utf-8'))


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


relief = {(k[0] + off[0], k[1] + off[1], k[2] + off[2]): c for k, c in rd(os.path.join(D, V['relief']['file'])).items()}
eyes = rd(os.path.join(D, V['eyes']['file']))
dec = rd(os.path.join(E16, 'decor.list.txt'))
print('① -decor：清單 %d vs 引擎 %d｜缺 %d、多 %d、色差 %d' % (len(relief), len(dec), len(set(relief) - set(dec)), len(set(dec) - set(relief)),
      sum(1 for k in relief if k in dec and relief[k] != dec[k])))
h15, h16 = rd(os.path.join(E15, 'hull.list.txt')), rd(os.path.join(E16, 'hull.list.txt'))
changed = {k for k in h16 if h15.get(k) != h16[k]} | (set(h15) - set(h16))
print('② 船殼：%d → %d 格｜換了色的 %d 格、都在眼窩清單裡 %s、色都對 %s｜眼窩清單 %d 格' % (
    len(h15), len(h16), len(changed), changed <= set(eyes), all(h16.get(k) == c for k, c in eyes.items()), len(eyes)))
a15, a16 = rd(os.path.join(E15, 'assembly.list.txt')), rd(os.path.join(E16, 'assembly.list.txt'))
want = dict(a15); want.update(eyes); want.update(relief)
print('③ 組裝件：stage16 %d vs 預期 %d｜缺 %d、多 %d、色差 %d' % (len(a16), len(want), len(set(want) - set(a16)), len(set(a16) - set(want)),
      sum(1 for k in want if k in a16 and want[k] != a16[k])))
rs = set(relief)
kind, hit = None, {'gun': 0, 'rope': 0, 'other_model': 0}
nv = {'gun': 0, 'rope': 0}
for line in open(os.path.join(E16, 'assembly.obj'), encoding='utf-8'):
    if line.startswith('o '):
        nm = line.split('#', 1)[1].strip() if '#' in line else ''
        kind = 'rope' if line[2:].startswith('rope_') else ('gun' if '/砲-' in nm else ('other_model' if line[2:].startswith('model_') else None))
    elif line.startswith('v ') and kind:
        t = line.split(); k = (int(np.floor(float(t[1]))), int(np.floor(float(t[3]))), int(np.floor(float(t[2]))))
        if kind in nv:
            nv[kind] += 1
        if k in rs:
            hit[kind] += 1
print('④ obj 頂點落在浮雕格裡：砲 %d（共 %d 個頂點）、繩 %d（共 %d）、別的模型 %d' % (hit['gun'], nv['gun'], hit['rope'], nv['rope'], hit['other_model']))

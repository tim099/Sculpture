# 階段二十 c 絞盤＋上甲板主艙口的格柵（TASK-0685；Tim 2026-10-17「接著參考憲法號 完成風暴角號的貨倉梯&其他細節吧」）
#   對照憲法號（2026-10-17 量）：模型有 capstan 2、grating 2；風暴角號 0、0。
# 絞盤：⭐ 引用現有元件（造船規格 §2.1）basecamp-ember-01m-capstan（憲法號兩座都是它；pivot 40,40,0 ＝ 底面中心），scale 0.163（憲法號 spar deck 那座的倍率，外框直徑 11.8 格 ≈ 1.2 m）。
#   位置：VOC 東印度船的主絞盤在上甲板、主桅後面 ⇒ 上甲板船腰（後甲板前緣 x 234 ～ 主桅 295.5）中線搜：外框 ±7、甲板上 13 格內沒有格子、腳下整片同一高度的甲板、
#   不碰任何模型外框 ⇒ x 242、257–279 放得下 ⇒ 取中間 x 268（地板站 z 80）；繩 763 條（取兩端直線）穿過 ±8 外框 0 條。
#   🩸 第一版放 x 242：地板照舷弧內插（x 250 起甲板其實低一格 ⇒ 那一段被誤判成放不下，只剩 242）；而 x 233–234 是後甲板前緣的艙壁、唯一的門在中線 y 128–132 ——
#     絞盤外框從 x 236 起正好堵在門前（剩 1 格縫）⇒ 遊戲匯入檢查多出 ⚠ 火藥 ×4（上甲板 P1、S1、AP、AS 從取用點走不到砲尾）⇒ 改逐欄量地板、挪到 x 268。
# 格柵：憲法號的格柵是照它自己艙口的尺寸做的子作品（33×44、67×44），⛔ 不能直接引用 ⇒ 照它的做法（draft_gratings.py：0.05 m／格、1 格條 1 格空、
#   縱條 ash 177、橫條 oak 136、hatch bar 同圍板色）做一件這個艙口的：上甲板主艙口開口 x 306–322、y 121–139（17×19），圍板 73 在 z 80–81（甲板板頂 z 79）。
#   ⇒ 格柵頂齊圍板頂（世界 z 82.0）：本地 z 2–3 ＝ 格柵（世界 z 81），z 0–1 ＝ 中線縱橫各一根 hatch bar（世界 z 80）。
#   艏樓那個 scuttle（x 500–506、y 126–134）大半被船首斜桅的根塞住（斜桅穿進圍板到 x 504，剩 x 502–506 一彎月牙）⇒ 不鋪。
#   鬼船：格柵爛掉 3 段（自己的 LCG 挑，⛔ 不用亂數源；重跑相同）。
# 用法：python -I -X utf8 -B draft_capstan_grating.py <design> <組裝件 export list>
#   ⇒ masks/grating/main.vox.txt（格柵子作品自己的座標）、verify_capstan_grating.json
import sys, os, json, hashlib
import numpy as np

D, LIST = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
OX, OY, OZ = 306, 121, 80                                              # 格柵子作品原點在世界的位置（關聯 at、pivot 0,0,0）
NX, NY = 17 * 2, 19 * 2                                                # 開口 17×19 世界格 ⇒ 0.05 m 本地格
COL = {'long': 177, 'cross': 136, 'bar': 73}
cells = {}
for lx in range(NX):
    for ly in range(NY):
        if ly % 2 == 0: cells[(lx, ly, 2)] = COL['cross']              # 下層：橫條（沿 x… 每隔一格一條）
        if lx % 2 == 0: cells[(lx, ly, 3)] = COL['long']               # 上層：縱條 ⇒ 從上面看 x 偶 或 y 偶 是條、奇奇是洞
for lx in range(NX):
    for z in (0, 1): cells[(lx, NY // 2 - 1, z)] = cells[(lx, NY // 2, z)] = COL['bar']   # 中線縱 bar（世界 y 130）
for ly in range(NY):
    for z in (0, 1): cells[(NX // 2 - 1, ly, z)] = cells[(NX // 2, ly, z)] = COL['bar']   # 中間橫 bar（世界 x 314–315 中間）
s, rot = 4242, []
for _ in range(3):                                                     # 爛掉的 3 段：上層某一條縱條斷掉 3–5 格
    s = (s * 1103515245 + 12345) & 0x7fffffff; lx = 2 * (s % (NX // 2))
    s = (s * 1103515245 + 12345) & 0x7fffffff; ly0 = s % (NY - 6)
    s = (s * 1103515245 + 12345) & 0x7fffffff; n = 3 + s % 3
    for ly in range(ly0, ly0 + n):
        if cells.pop((lx, ly, 3), None) is not None: rot.append((lx, ly))
# 檢查：格柵落在世界的空氣裡（開口）—— 每個本地格的中心 → 世界格
S = set()
for ln in open(LIST, encoding='utf-8'):
    if ln[0] == '#': continue
    x, y, z, c = map(int, ln.split(',')); S.add((x, y, z))
hit = sorted({(OX + lx // 2, OY + ly // 2, OZ + lz // 2) for lx, ly, lz in cells} & S)
coam = [(x, y, 81) for x in (305, 323) for y in range(120, 141)] + [(x, y, 81) for y in (120, 140) for x in range(305, 324)]
v = {'grating': {'work': 'summit-stormkaap-01m-grating-main', 'title': '風暴角號｜上甲板主艙口的格柵（0.05 m；外部模型 scale 0.5）', 'size': [NX, NY, 4], 'mpv': 0.05,
                 'cells': len(cells), 'rotten': len(rot), 'hit_world': len(hit), 'coaming_top_all_solid': all(k in S for k in coam),
                 'world_box': [[OX, OY, OZ], [OX + NX / 2, OY + NY / 2, OZ + 2]]},
     'models': [{'name': '絞盤', 'host_work': 'summit-stormkaap-01m-deck-upper', 'host_link': '甲板-上', 'work': 'basecamp-ember-01m-capstan', 'at': [268, 130, 80],
                 'pivot': [40, 40, 0], 'scale': 0.163, 'meta': {'kind': 'capstan'}},
                {'name': '格柵-主艙口', 'host_work': 'summit-stormkaap-01m-deck-upper', 'host_link': '甲板-上', 'work': 'summit-stormkaap-01m-grating-main', 'at': [OX, OY, OZ],
                 'pivot': [0, 0, 0], 'scale': 0.5, 'meta': {'kind': 'grating'}}]}
assert not hit and v['grating']['coaming_top_all_solid'], v
out = os.path.join(D, 'masks', 'grating'); os.makedirs(out, exist_ok=True)
NL = chr(10)
txt = '# %s —— draft_capstan_grating.py 產；子作品自己的座標（%d 格）' % (v['grating']['title'], len(cells)) + NL + ''.join('%d,%d,%d,%d' % (k + (c,)) + NL for k, c in sorted(cells.items()))
open(os.path.join(out, 'main.vox.txt'), 'w', encoding='utf-8', newline=NL).write(txt)
v['grating']['file'] = {'path': 'masks/grating/main.vox.txt', 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}
with open(os.path.join(D, 'verify_capstan_grating.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps(v['grating'], ensure_ascii=False))

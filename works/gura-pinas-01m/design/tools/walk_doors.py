# 出處：ame-labelle-01m/design/tools/walk_doors.py（拉貝爾號 TASK-1045；源頭康塞普西翁號、收穫號）—— 藍鯊號 TASK-0967：作品 id；欄杆頂 ＝ galjoen 在平台面以上的格（regelingen、head timber、人頭）；
#   --asm=<清單>（還沒落格時拿本機清單當組裝件）、--add=<清單;清單>（再疊上去的件：新的 galjoen、獅子、門板）
# 步驟 17（TASK-0969）：門走不走得出去 —— 照第一人稱的走法（Blockside 81_fps.js：站得住 ＝ 腳下實心、頭上 FP_HEAD 7 格空；四鄰一步上 ≤ 6、下 ≤ 8，取離腳最近的高度）
#   從每扇門艙裡那一側的甲板出發，照有向圖走：門外那一塊（stern walk 的地板、beakhead 平台）走不走得到、走不走得回來
#   用法：python -I -X utf8 tools/walk_doors.py <design> [--nocarve] [--lowrail=N]（--nocarve：反向對照 —— 門洞的格當成實心 ⇒ 應該走不出去；
#         --lowrail=N：反向對照 —— stern walk 與喙平台的欄杆最上面 N 層拿掉 ⇒ 應該站得上扶手頂、翻得出去）
#   · 讀組裝件（CLI 匯出，links 照開關）＋ verify_ports.json 的 doors；框：每扇門前後各 40 格、兩旁 40 格、上下 25 格
import json, math, os, sys
from collections import deque
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
nocarve = '--nocarve' in sys.argv
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list

FP_HEAD, FP_UP, FP_DOWN = 7, 6, 8
arg = lambda k: next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--%s=' % k)), None)
load = lambda p: np.loadtxt(p, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
A = load(arg('asm')) if arg('asm') else export_list('gura-pinas-01m-assembly', None, links=None)
occ = set(map(tuple, A[:, :3].tolist()))
for p_ in (arg('add') or '').split(';'):
    if p_:
        occ |= set(map(tuple, load(p_)[:, :3].tolist()))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
# 門：bak 前隔板（plan decks_build.breaks 裡有 face 的那一道，draft_decks.py 開的門洞 寬 5）—— 門洞底 ＝ 隔板那一欄、門中線上第一個「腳下實心、自己是空」的格
DOORS = []
for br in plan['decks_build']['breaks']:
    if not br.get('face'):
        continue
    for dd in br['doors_dy']:
        for sg in (1, -1):
            yc_ = 160 + sg * dd
            z0 = next(z for z in range(56, 120) if (br['x'], yc_, z) not in occ and (br['x'], yc_, z - 1) in occ)   # 56 起 ⇒ 跳過下甲板頂（z 42）上面那一段空
            DOORS.append({'face': 'fwd', 'deck': br['lo'], 'y0': yc_ - 2, 'y1': yc_ + 2, 'z0': z0, 'z1': z0 + 14, 'door_x': br['x'] + 1})
if nocarve:
    for d in DOORS:
        xs = range(d['door_x'] - 6, d['door_x']) if d['face'] == 'fwd' else range(d['door_x'] + 1, d['door_x'] + 7)
        for x in xs:
            for y in range(d['y0'], d['y1'] + 1):
                for z in range(d['z0'], d['z1'] + 1):
                    occ.add((x, y, z))


def solid(x, y, z):
    return (x, y, z) in occ


def stand(x, y, z):
    return solid(x, y, z - 1) and all(not solid(x, y, z + h) for h in range(FP_HEAD))


def nexts(x, y, z):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        best = None
        for dz in sorted(range(-FP_DOWN, FP_UP + 1), key=abs):      # 離腳最近的高度
            if stand(nx, ny, z + dz):
                best = z + dz
                break
        if best is not None:
            yield nx, ny, best


def reach(start, box):
    seen, q = {start}, deque([start])
    while q:
        p = q.popleft()
        for n in nexts(*p):
            if n not in seen and box(n):
                seen.add(n)
                q.append(n)
    return seen


# 欄杆頂：galjoen 在平台面以上的格（regelingen、head timber、人頭）—— 從門外走得到的格裡站在上面的 ⇒ 翻得出去
sys.path.insert(0, design)
import lines as HL
xs0 = int(math.floor(float(HL.Lines(HL.load_plan(design)).x_stem(80)) + 0.5)) - 1
V2 = plan['espolon']['v2']
P2 = V2['platform']
tip = xs0 + V2['len_beyond_stem']
ztf = lambda x: P2['top_z'] + int(math.floor(P2['rise'] * max(0.0, min(1.0, (x - xs0) / float(tip - xs0))) ** P2['rise_pow'] + 0.5))   # 同 draft_deco.py galjoen_v2
G = load(os.path.join(design, 'masks', 'deco', 'galjoen.vox.txt'))
FH = load(os.path.join(design, 'masks', 'deco', 'figurehead.vox.txt'))
caps = {tuple(r[:3]) for r in G.tolist() if r[2] > ztf(r[0])} | {tuple(r[:3]) for r in FH.tolist()}
Gs = {tuple(r[:3]) for r in G.tolist()}
low = int(arg('lowrail') or 0)
if low:                                                                 # 反向對照：平台面 low 格以上的 galjoen 全拿掉（＝ 只剩 low 格高的欄杆）⇒ 應該站得上剩下的頂
    for k in [c for c in caps if c[2] > ztf(c[0]) + low]:
        occ.discard(k)
    caps = {c for c in caps if c[2] <= ztf(c[0]) + low}
res = []
for d in DOORS:
    yc = (d['y0'] + d['y1']) // 2
    out = 1 if d['face'] == 'fwd' else -1                               # 門外在 +x（beakhead）或 −x（船尾）
    x0 = d['door_x']
    box = lambda p, x0=x0, yc=yc, zb=d['z0']: abs(p[0] - x0) <= 40 and abs(p[1] - yc) <= 40 and abs(p[2] - zb) <= 25
    # 艙裡那一側：門板往裡 8 格、門洞中線附近找站得住的那一格
    inside = next((p for k in range(7, 14) for z in range(d['z0'] - 4, d['z0'] + 4) for p in [(x0 - out * k, yc, z)] if stand(*p)), None)
    # 門外那一側：門板外 2 格（stern walk 的地板／平台）
    outside = next((p for k in range(1, 4) for z in range(d['z0'] - 4, d['z0'] + 4) for p in [(x0 + out * k, yc, z)] if stand(*p)), None)
    r = {'door': '%s %s y %d' % (d['face'], d['deck'], yc), 'inside': inside, 'outside': outside}
    if inside and outside:
        a = reach(inside, box)
        b = reach(outside, box)
        r['in_to_out'] = outside in a
        r['out_to_in'] = inside in b
        r['reach_cells'] = len(a)
        r['to_galjoen'] = sum(1 for (x, y, z) in a if x >= xs0 + 10 and z > ztf(x))     # 從艙裡走得到 galjoen 平台（艏柱往前 10 格以外）的格數
        r['on_rail_top'] = sum(1 for (x, y, z) in b if (x, y, z - 1) in caps)
        if '--list' in sys.argv:
            for c in sorted((x, y, z) for (x, y, z) in b if (x, y, z - 1) in caps):
                print('  站在頂上', c, 'galjoen' if (c[0], c[1], c[2] - 1) in Gs else '獅子')
    res.append(r)
    print(json.dumps(r, ensure_ascii=False))
bad = [r for r in res if not (r.get('in_to_out') and r.get('out_to_in') and r.get('to_galjoen'))]
print('站得上欄杆頂的格（從門外走得到的）：%d' % sum(r.get('on_rail_top', 0) for r in res))
print('門 %d 扇；走不出去或走不回來 %d%s' % (len(res), len(bad), '（反向對照：門洞當實心）' if nocarve else ''))

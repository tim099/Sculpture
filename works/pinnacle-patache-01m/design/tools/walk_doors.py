# 直接出處：apex-two-galeon-01m/design/tools/walk_doors.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 聖羅曼號 步驟 17（TASK-0970）：門走不走得出去 —— 照第一人稱的走法（Blockside 81_fps.js：站得住 ＝ 腳下實心、頭上 FP_HEAD 7 格空；四鄰一步上 ≤ 6、下 ≤ 8，取離腳最近的高度）
#   從每扇門艙裡那一側的甲板出發，照有向圖走：門外那一塊（stern walk 的地板、beakhead 平台）走不走得到、走不走得回來
#   用法：python -I -X utf8 tools/walk_doors.py <design> [--nocarve] [--lowrail=N]（--nocarve：反向對照 —— 門洞的格當成實心 ⇒ 應該走不出去；
#         --lowrail=N：反向對照 —— stern walk 與喙平台的欄杆最上面 N 層拿掉 ⇒ 應該站得上扶手頂、翻得出去）
#   · 讀組裝件（CLI 匯出，links 照開關）＋ verify_ports.json 的 doors；框：每扇門前後各 40 格、兩旁 40 格、上下 25 格
import json, os, sys
from collections import deque
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
nocarve = '--nocarve' in sys.argv
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list

FP_HEAD, FP_UP, FP_DOWN = 7, 6, 8
A = export_list('pinnacle-patache-01m-assembly', None, links=None)
occ = set(map(tuple, A[:, :3].tolist()))
VP = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
if nocarve:
    for d in VP['doors']:
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


# 欄杆頂（stern walk 的扶手、喙平台邊的欄杆頂）：門外那一塊走得到的格裡，有沒有站在扶手頂上的（⇒ 翻得出去）
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
caps = set()
for nm, zs in (('stern-deco', [w['floor_z'] + w['rail_h'] for w in plan['stern_deco']['walks']]), ('espolon', [plan['espolon']['deck_top_z'] + plan['espolon']['rail_h']])):
    for l in open(os.path.join(design, 'masks', 'deco', nm + '.vox.txt'), encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            if z in zs:
                caps.add((x, y, z))
low = int(next((a.split('=')[1] for a in sys.argv[2:] if a.startswith('--lowrail=')), 0))
if low:                                                                 # 反向對照：欄杆最上面 low 層拿掉（＝ 矮 low 格的欄杆）⇒ 應該站得上新的扶手頂
    for nm, zs in (('stern-deco', [w['floor_z'] + w['rail_h'] for w in plan['stern_deco']['walks']]), ('espolon', [plan['espolon']['deck_top_z'] + plan['espolon']['rail_h']])):
        for l in open(os.path.join(design, 'masks', 'deco', nm + '.vox.txt'), encoding='utf-8'):
            if l.strip() and not l.startswith('#'):
                x, y, z, c = map(int, l.split(','))
                for zc in zs:
                    if zc - low < z <= zc:
                        occ.discard((x, y, z))
                    if z == zc - low:
                        caps.add((x, y, z))
res = []
for d in VP['doors']:
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
        r['on_rail_top'] = sum(1 for (x, y, z) in b if (x, y, z - 1) in caps)
    res.append(r)
    print(json.dumps(r, ensure_ascii=False))
bad = [r for r in res if not (r.get('in_to_out') and r.get('out_to_in'))]
print('站得上欄杆頂的格（從門外走得到的）：%d' % sum(r.get('on_rail_top', 0) for r in res))
print('門 %d 扇；走不出去或走不回來 %d%s' % (len(res), len(bad), '（反向對照：門洞當實心）' if nocarve else ''))

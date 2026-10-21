# 船尾窗改成玻璃（Tim 2026-10-21：「拿破崙號的窗戶 參考 憲法號 改成玻璃吧」；造船規格 §9.5「窗的玻璃」，同憲法號 draft_stern_glass.py）
#   階段三（draft_ports.py）開窗的做法：刻最外一格、第二格塗玻璃色 87 —— 玻璃是船殼的格、後面還有肋骨與內板 ⇒ 不透明、看不到艙裡。
#   這裡：① 那 721 格色 87 照原位拆成子作品 -stern-glass（work sub=split colors=87、雙生引用 meta material=glass；不另放新的格），顏色換成憲法號的 155（淡藍灰）；
#        ② 每一格玻璃後面（朝船裡）的船殼刻穿到艙裡的空氣 ⇒ 遊戲裡透過玻璃看得到艙裡。
#   朝船裡 ＝ 窗洞那一側（玻璃旁邊空的那幾格，就是開窗刻掉的外板）的反方向，只取水平（船尾是圓的，每扇窗朝向不同）；沿那個方向每 0.5 格走，碰到的船殼格都刻，碰到空氣停。
# 用法：python -I draft_window_glass.py <船殼 export list> <組裝件 export list（船尾那一塊、links=all）> [--probe=keep_behind=<n>]
# 寫：masks/glass/glass.vox.txt（色 155，原位）、masks/glass/behind_carve.vox.txt（x,y,z,color —— 帶色守門）、verify_window_glass.json
import json, math, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OLD, NEW = 87, 155
MAX_STEPS = 16                       # 半格一步 ⇒ 最多走 8 格（牆 4 格厚）


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        x, y, z, c = (int(t) for t in ln.split(','))
        out[(x, y, z)] = c
    return out


hull, asm = cells(sys.argv[1]), cells(sys.argv[2])
probe = dict(a.split('=', 1)[1].split(':') for a in sys.argv[3:] if a.startswith('--probe='))
glass = {p for p, c in hull.items() if c == OLD}
carve, bad, depth, blocked = {}, [], Counter(), []
for g in sorted(glass):
    out = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (g[0] + dx, g[1] + dy, g[2]) not in asm]
    if not out:
        bad.append(('no_open_side', g)); continue
    vx, vy = -sum(d[0] for d in out), -sum(d[1] for d in out)
    n = math.hypot(vx, vy)
    if n == 0:
        bad.append(('ambiguous', g)); continue
    vx, vy = vx / n, vy / n
    hit_air, k = False, 0
    for s in range(1, MAX_STEPS + 1):
        p = (int(math.floor(g[0] + 0.5 + vx * s * 0.5)), int(math.floor(g[1] + 0.5 + vy * s * 0.5)), g[2])
        if p == g or p in glass:
            continue
        if p not in asm:
            hit_air = True; break
        if p not in hull:                                  # 別的子作品（甲板、裝飾）擋在後面 ⇒ 不刻、報出來
            blocked.append((g, p, asm[p])); break
        carve[p] = hull[p]; k += 1
    if not hit_air and not (blocked and blocked[-1][0] == g):
        bad.append(('no_air', g))
    depth[k] += 1
# 窗洞轉角的玻璃（兩面朝外）：斜著走只刻到斜對角那一格，正後方兩格還是牆（第一版：721 格裡 40 格後面貼著牆）⇒ 補刻正後方的船殼格，
#   條件：那一格不碰到窗外的空氣（＝ 每一格玻璃朝外那一側的空格）—— 不然刻了就繞過玻璃、成了一個洞。碰到的照實報、不刻。
outside = {(g[0] + dx, g[1] + dy, g[2]) for g in glass for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (g[0] + dx, g[1] + dy, g[2]) not in asm}
corner_added, corner_unsafe = 0, []
for g in sorted(glass):
    out = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (g[0] + dx, g[1] + dy, g[2]) not in asm]
    if len(out) < 2:
        continue
    for dx, dy in out:
        q = (g[0] - dx, g[1] - dy, g[2])
        if q in glass or q not in hull or q in carve:
            continue
        nb = [(q[0] + a, q[1] + b, q[2] + c) for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        if any(n in outside for n in nb):
            corner_unsafe.append(q); continue
        carve[q] = hull[q]; corner_added += 1
# 同一條規矩套到全部要刻的格：斜著走刻到的格也可能碰到窗外（第二版量到 4 格）⇒ 不刻
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
leak = [p for p in carve if any((p[0] + a, p[1] + b, p[2] + c) in outside for a, b, c in N6)]
for p in leak:
    del carve[p]
# 第三版（落格之後引擎量到：元件 1 → 93、封閉空腔 0 → 10 個 24 格）：斜著走的刻法在刻掉的格之間漏下單格的殘牆（177／141），
#   窗緣的玻璃靠旁邊的窗框撐著、轉角補刻把窗框刻掉 ⇒ 30 格玻璃浮空；玻璃跟殘牆之間夾出封死的小空間。
#   ⇒ 反覆到穩定：浮空的殘牆（不含玻璃、不碰窗外）也刻；浮空的玻璃 ⇒ 貼著它、被刻掉的格放回來；封死的空氣 ⇒ 那幾格放回來（它們都是刻出來的）。
#   浮空 ／ 封死 ＝ 在匯出的那一塊裡碰不到框的邊（框切過船身與艙裡 ⇒ 碰到框邊的就是接在船上、或通到外面）。
from collections import deque
BOX = [min(p[i] for p in asm) for i in range(3)] + [max(p[i] for p in asm) for i in range(3)]


def on_edge(p):
    return any(p[i] in (BOX[i], BOX[i + 3]) for i in range(3))


def comps(cells):
    seen, out = set(), []
    for s in cells:
        if s in seen:
            continue
        seen.add(s); q = deque([s]); c = [s]
        while q:
            p = q.popleft()
            for a, b, d in N6:
                n = (p[0] + a, p[1] + b, p[2] + d)
                if n in cells and n not in seen:
                    seen.add(n); q.append(n); c.append(n)
        out.append(c)
    return out


fix = Counter()
for it in range(20):
    solid = set(asm) - set(carve)
    changed = False
    for c in comps(solid):
        if any(on_edge(p) for p in c):
            continue
        if any(p in glass for p in c):                     # 浮空的玻璃：旁邊被刻掉的格放回來
            for p in c:
                for a, b, d in N6:
                    n = (p[0] + a, p[1] + b, p[2] + d)
                    if n in carve:
                        del carve[n]; fix['restore_for_glass'] += 1; changed = True
        else:                                              # 殘牆：一起刻掉（只刻船殼的格、不碰窗外）
            for p in c:
                if p in hull and p not in glass and not any((p[0] + a, p[1] + b, p[2] + d) in outside for a, b, d in N6):
                    carve[p] = hull[p]; fix['carve_leftover'] += 1; changed = True
    # 封死的空氣（刻出來的那幾格自成一團、碰不到框邊）⇒ 放回來
    air = {p for p in carve}
    for c in comps(air):
        open_ = any(on_edge(p) or any((p[0] + a, p[1] + b, p[2] + d) not in asm for a, b, d in N6) for p in c)
        if not open_:
            for p in c:
                del carve[p]; fix['restore_cavity'] += 1; changed = True
    if not changed:
        break
fix['iterations'] = it + 1
if 'keep_behind' in probe:                                 # 反向對照：故意少刻 ⇒ 驗算要報出那幾格玻璃後面不是空的
    for p in sorted(carve)[:int(probe['keep_behind'])]:
        del carve[p]

os.makedirs(os.path.join(HERE, 'masks', 'glass'), exist_ok=True)
with open(os.path.join(HERE, 'masks', 'glass', 'glass.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 船尾窗玻璃（原位、色 %d；拆出來之後換色用）\n' % NEW)
    for p in sorted(glass):
        f.write('%d,%d,%d,%d\n' % (p + (NEW,)))
with open(os.path.join(HERE, 'masks', 'glass', 'behind_carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 玻璃後面刻穿的船殼格（x,y,z,現在的色 —— carvevox 守門）\n')
    for p in sorted(carve):
        f.write('%d,%d,%d,%d\n' % (p + (carve[p],)))

# 驗算：刻完之後每一格玻璃，朝船裡那一側的鄰格要是空的（照「組裝件 − 刻掉的」重算）
after = set(asm) - set(carve)
open_behind = 0
for g in glass:
    out = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (g[0] + dx, g[1] + dy, g[2]) not in asm]
    inward = [(-dx, -dy) for dx, dy in out]
    if any((g[0] + dx, g[1] + dy, g[2]) not in after or (g[0] + dx, g[1] + dy, g[2]) in glass for dx, dy in inward):
        open_behind += 1
v = dict(glass=len(glass), carve=len(carve), carve_colors=dict(Counter(carve.values())), depth=dict(sorted(depth.items())),
         bad=len(bad), bad_examples=bad[:5], blocked=len(blocked), blocked_examples=blocked[:5],
         glass_open_behind=open_behind, fix=dict(fix), leak_dropped=len(leak), leak_examples=leak[:5], corner_added=corner_added, corner_unsafe=len(corner_unsafe), corner_unsafe_examples=corner_unsafe[:5],
         carve_touching_outside=sum(1 for p in carve if any((p[0] + a, p[1] + b, p[2] + c) in outside
                                                                for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))),
         z=sorted({p[2] for p in glass}))
json.dump(v, open(os.path.join(HERE, 'verify_window_glass.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(v, ensure_ascii=False))

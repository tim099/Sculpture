# 階段十六：裝飾 —— 荷蘭人號的特徵表裡留到「裝飾階段」的三樣（notes 第零階段）：
#   ① 砲門的臉：嘴 ＝ 砲門；上下緣一排骨色的牙（在砲門外面那一層、⛔ 不碰砲）、眼窩漆黑（船殼換色）、眉凸出一格（深色）；四種表情輪替，兩舷錯開
#   ② 海草：從砲門下沿往下垂的綠色細條（凸出船殼一格，左右晃）
#   ③ 藤壺：水線帶附近零星的淺灰點（凸出一格，1–3 格一叢）
# 設計 plan.json decor（出處 provenance decor）；現況 ＝ 引擎匯出（<exports>/assembly.list.txt 全部格、hull.list.txt 船殼、assembly.obj 的繩、parts.json 不用）＋ verify_guns.json（砲門與砲）。
# 浮雕（牙、眉、海草、藤壺）放子作品 -decor（框 ＝ 整個組裝件、at 0,0,0）；眼窩是船殼換色（stampvox overwrite，換之前逐格對原色）。
# 每一格浮雕：那一格是空的、不在任何砲（模型取樣點）裡、不在任何繩的管子頂點所在的格、六鄰有一格是實心（接得上）。
# 輸出：masks/decor/relief.vox.txt（子作品座標 ＝ 世界）、masks/decor/eyes_hull.vox.txt（船殼座標；新色）、verify_decor.json（含眼窩每格的原色）
# 用法：python -I -X utf8 -B draft_decor.py <design 資料夾> <exports 資料夾>
import sys, os, json, math, random, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
YC = plan['frame']['YC']
P = plan['decor']; C = P['colors']
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
S = VG['scale']


def read_list(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


A = read_list(os.path.join(EX, 'assembly.list.txt'))
col = np.zeros((NX, NY, NZ), np.uint8); col[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
H = read_list(os.path.join(EX, 'hull.list.txt'))
hcol = np.zeros((NX, NY, NZ), np.uint8); hcol[H[:, 0], H[:, 1], H[:, 2]] = H[:, 3]
hullset = hcol > 0

# 砲（模型取樣點）
offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
gun = set()
for r in VG['rows']:
    tp = VG['types'][r['type']]
    c = read_list(os.path.join(D, tp['file']))[:, :3].astype(float)
    q = ((c[:, None, :] + offs[None]).reshape(-1, 3) - np.array(r['pivot'], float)) * S
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    g = math.radians(r['rotate'][2]); cc, ss = round(math.cos(g), 12), round(math.sin(g), 12)
    q = np.stack([q[:, 0] * cc - q[:, 1] * ss, q[:, 0] * ss + q[:, 1] * cc, q[:, 2]], 1) + np.array(r['at'], float)
    gun |= set(map(tuple, np.floor(q).astype(int)))
# 繩的管子頂點所在的格（obj：y 朝上 ⇒ (x, 作品 z, 作品 y)）
rope = set()
if P['avoid_rope_cells']:
    vs, isr, cur = [], [], False
    for line in open(os.path.join(EX, 'assembly.obj'), encoding='utf-8'):
        if line.startswith('o '):
            cur = line[2:].startswith('rope_')
        elif line.startswith('v ') and cur:
            t = line.split(); vs.append((float(t[1]), float(t[3]), float(t[2])))
    rope = set(map(tuple, np.floor(np.array(vs)).astype(int)))
print('assembly', len(A), 'hull', len(H), 'gun cells', len(gun), 'rope cells', len(rope))

relief = {}      # (x,y,z) → 色
eyes = {}        # (x,y,z) → (新色, 原色)
skipped = {'occupied': 0, 'gun': 0, 'rope': 0, 'float': 0, 'oob': 0}


def free(k):
    if not (0 <= k[0] < NX and 0 <= k[1] < NY and 0 <= k[2] < NZ):
        skipped['oob'] += 1; return False
    if col[k] or k in relief:
        skipped['occupied'] += 1; return False
    if k in gun:
        skipped['gun'] += 1; return False
    if k in rope:
        skipped['rope'] += 1; return False
    return True


def attached(k):
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        q = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
        if col[q] or q in relief:
            return True
    return False


def put(k, c):
    if free(k) and attached(k):
        relief[k] = c; return True
    if free(k):
        skipped['float'] += 1
    return False


def outer(x, z, side):
    """(x, z) 這一柱、這一舷船殼最外面那一格的 y（船殼作品）；沒有 ⇒ None。"""
    if side > 0:
        ys = np.nonzero(hullset[x, YC:, z])[0]
        return int(ys.max()) + YC if len(ys) else None
    ys = np.nonzero(hullset[x, :YC + 1, z])[0]
    return int(ys.min()) if len(ys) else None


rng = random.Random(P['seed'])
F = P['faces']
faces = []
side_rows = [r for r in VG['rows'] if r['meta'].get('side') in ('S', 'P') and r['rotate'][2] == 0]
side_rows.sort(key=lambda r: (r['host_link'], r['meta']['side'], r['opening_lat'][0]))
for r in side_rows:
    side = 1 if r['meta']['side'] == 'S' else -1
    x0, x1 = r['opening_lat']; z0, z1 = r['opening_z']
    n = int(r['meta'].get('port', 0))
    ex_i = (n + (F['p_offset'] if side < 0 else 0) + (0 if r['host_link'] == '甲板-下' else 1)) % len(F['expressions'])
    expr = F['expressions'][ex_i]
    rec = {'gun': r['host_link'] + '/' + r['model'], 'expr': expr, 'teeth': 0, 'eye_cells': 0, 'brow': 0, 'weed': 0}
    # ── 牙：砲門外面那一層（上緣下一排、下緣上一排），每隔一格一顆 ──
    for z, row_ref, xs in ((z1, z1 + 1, range(x0 + 1, x1, 2)), (z0, z0 - 1, range(x0 + 2, x1 - 1, 2))):
        for x in xs:
            y = outer(x, row_ref, side)
            if y is None:
                continue
            if put((x, y, z), C['tooth']):
                rec['teeth'] += 1
    # ── 眼：從砲門上緣往上找，兩眼的格都是船殼上的 eye_paint_on 色（不是 wale、不是別的砲門）⇒ 那一排 ──
    def find_eye(ex):
        eh, ew = {'angry': (2, 2), 'sorrow': (2, 2), 'scream': (3, 2), 'dead': (1, 3)}[ex]
        lx = [x0 + i for i in range(ew)] if ex != 'dead' else [x0 - 1 + i for i in range(ew)]
        rx = [x1 - i for i in range(ew)] if ex != 'dead' else [x1 + 1 - i for i in range(ew)]
        # 上排砲門在船腰那一段，上面只有 3 格船板就是舷牆頂蓋（量過：x 247–253，z 90–92 是 109、93 是 73）⇒ 找不到才退回緊貼上緣（dz 1）
        for dz in list(range(F['eye_search'][0], F['eye_search'][1] + 1)) + [F['eye_fallback']]:
            zb = z1 + dz
            cells = []
            ok = True
            for x in lx + rx:
                for z in range(zb, zb + eh):
                    y = outer(x, z, side)
                    if y is None or hcol[x, y, z] not in F['eye_paint_on'] or col[x, y, z] != hcol[x, y, z]:
                        ok = False; break
                    cells.append((x, y, z))
                if not ok:
                    break
            if ok:
                return zb, eh, cells
        return None
    # 放不下原本的表情（尖叫要 3 排；上排船腰只有 3 排船板、頂蓋又是斜的）⇒ 換表情清單裡下一個放得下的，照實記 expr_wanted
    found = None
    for ex in [expr] + [e for e in F['expressions'] if e != expr]:
        found = find_eye(ex)
        if found:
            if ex != expr:
                rec['expr_wanted'] = expr; rec['expr'] = ex; expr = ex
            break
    if found is None:
        rec['eye'] = '找不到（四種表情都放不下）'
    else:
        zb, eh, cells = found
        for k in cells:
            eyes[k] = (C['eye'], int(hcol[k]))
        # 瞳孔：每隻眼最靠鼻樑、最低那一格點淡綠（鬼火；呼應船頭大嘴發光的眼）—— 「死寂」不點。
        # 🩸 第一版只有暗色眼窩（36）：側視圖上跟陰影分不出來，臉讀不出是臉。
        if expr != 'dead':
            for eye_x in ([x for x in range(x0, x1 + 1) if any(k[0] == x for k in cells)][:2], [x for x in range(x1, x0 - 1, -1) if any(k[0] == x for k in cells)][:2]):
                inner = eye_x[-1]
                k = min((c for c in cells if c[0] == inner), key=lambda c: c[2])
                eyes[k] = (C['pupil'], int(hcol[k]))
                rec['pupils'] = rec.get('pupils', 0) + 1
        rec['eye_cells'] = len(cells); rec['eye_z'] = zb
        zt = zb + eh - 1
        # 眉：外端／內端的高度照表情；左眉 外→內 ＝ x 小→大；右眉鏡過來
        bl = {'angry': [(x0 - 1, 2), (x0, 2), (x0 + 1, 1), (x0 + 2, 1)],
              'sorrow': [(x0 - 1, 1), (x0, 1), (x0 + 1, 2), (x0 + 2, 2)],
              'scream': [(x0 - 1, 2), (x0, 2), (x0 + 1, 2), (x0 + 2, 2)],
              'dead': [(x0 - 1, 1), (x0, 1), (x0 + 1, 1)]}[expr]
        for bx, h in bl:
            for xx in (bx, x0 + x1 - bx):
                z = zt + h
                y = outer(xx, z, side)
                if y is None:
                    continue
                if put((xx, y + side, z), C['brow']):
                    rec['brow'] += 1
    # ── 海草：砲門下沿往下垂 ──
    W = P['weed']
    for s in range(W['per_port']):
        x = rng.randint(x0 + 1, x1 - 1)
        L = rng.randint(*W['len'])
        z = z0 - 1
        for i in range(L):
            y = outer(x, z, side)
            if y is None:
                break
            k = (x, y + side, z)
            if not put(k, C['weed'][(i + s) % 2]):
                break
            rec['weed'] += 1
            z -= 1
            if rng.random() < W['jitter']:
                x += rng.choice((-1, 1))
    faces.append(rec)

# ── 藤壺 ──
B = P['barnacle']
nb = 0
for side in (1, -1):
    for x in range(B['x'][0], B['x'][1] + 1):
        for z in range(B['z'][0], B['z'][1] + 1):
            if rng.random() >= B['p']:
                continue
            y = outer(x, z, side)
            if y is None or hcol[x, y, z] not in B['on']:
                continue
            c = C['barnacle'][rng.randint(0, 1)]
            if put((x, y + side, z), c):
                nb += 1
                for _ in range(rng.randint(0, B['cluster'])):
                    dx, dz = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                    y2 = outer(x + dx, z + dz, side)
                    if y2 is not None and put((x + dx, y2 + side, z + dz), c):
                        nb += 1


def write(path, cells, title):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = '# 風暴角號 ' + title + '（draft_decor.py）x,y,z,color —— at 0,0,0\n' + ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cells.items()))
    open(path, 'w', encoding='utf-8', newline='\n').write(txt)
    return hashlib.sha256(txt.encode('utf-8')).hexdigest()


hr = write(os.path.join(D, 'masks', 'decor', 'relief.vox.txt'), relief, '裝飾浮雕（牙、眉、海草、藤壺）')
he = write(os.path.join(D, 'masks', 'decor', 'eyes_hull.vox.txt'), {k: v[0] for k, v in eyes.items()}, '砲門的臉：眼窩（船殼換色）')
from collections import Counter
cnt = Counter(relief.values())
out = {'note': 'draft_decor.py（階段十六）—— 現況 ＝ 引擎匯出 %s（組裝件 %d 格、船殼 %d 格）＋ verify_guns.json＋ obj 的繩' % (os.path.relpath(EX, os.path.dirname(D)).replace('\\', '/'), len(A), len(H)),
       'work': P['work'], 'title': P['title'], 'link': P['link'],
       'relief': {'file': 'masks/decor/relief.vox.txt', 'cells': len(relief), 'sha256': hr, 'colors': {str(k): v for k, v in sorted(cnt.items())}},
       'eyes': {'file': 'masks/decor/eyes_hull.vox.txt', 'cells': len(eyes), 'sha256': he, 'palette': [C['eye'], C['pupil']], 'was': [[k[0], k[1], k[2], v[1]] for k, v in sorted(eyes.items())]},
       'faces': faces, 'barnacles': nb, 'skipped': skipped}
with open(os.path.join(D, 'verify_decor.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('relief', len(relief), dict(cnt), 'eyes', len(eyes), 'barnacles', nb, 'skipped', skipped)
print('faces', len(faces), 'expr', dict(Counter(f['expr'] for f in faces)), 'no eye', [f['gun'] for f in faces if 'eye_z' not in f])
print('teeth per face', Counter(f['teeth'] for f in faces), 'brow', Counter(f['brow'] for f in faces), 'weed', sum(f['weed'] for f in faces))

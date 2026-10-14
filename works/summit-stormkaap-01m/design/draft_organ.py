# 階段十八：管風琴 —— 荷蘭人號特徵表的最後一格（選做；Tim 2026-10-14 晚「管風琴 GO」）。
# 子作品 -organ（0.05 m）當外部模型掛在 甲板-後（船長室，艉樓底下），右舷側牆、x 150–157（兩根橫樑之間）、面朝左舷。
# 位置是量出來的（現況 ＝ 引擎匯出 <exports>/assembly.list.txt，見 notes 階段十八）：
#   艉板內面 z 118–124 是一整排會發綠光的船尾窗 ⇒ ⛔ 不靠艉板；右舷 x 150–157：地板平（第一層空氣 z 108）、天花板 z 124–125、
#   牆內面 y 155–157（z ≤ 118），z 119–123 的 clamp 凸到 y 153 ⇒ 琴身到 y 154.5、管子到 y 151.5。
# 子作品座標：x 沿船長（x 0 ＝ 世界 150）、y 由琴凳往牆（y 0 ＝ 世界 145）、z 0 ＝ 甲板面上第一層；世界 ＝ at ＋ 0.5 × 子作品（scale 0.5、pivot 0,0,0）。
# 檢查（設計那一側）：模型每一格的格心＋八角取樣都不落在實心、底面每一格正下方是實心、不碰繩的管子頂點、外框不跟別的模型外框重疊。
# 輸出：masks/organ/organ.vox.txt、verify_organ.json
# 用法：python -I -X utf8 -B draft_organ.py <design 資料夾> <exports 資料夾（assembly.list.txt、assembly.obj、parts.json）>
import sys, os, json, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
O = plan['organ']; C = O['colors']
SX, SY, SZ = O['size']
cells = {}


def put(x, y, z, c, over=False):
    assert 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ, ('框外', x, y, z)
    if over or (x, y, z) not in cells:
        cells[(x, y, z)] = c


# 琴身：前面板 case、四角與頂緣 trim
cy, cz = O['case']['y'], O['case']['z']
for x in range(SX):
    for y in range(cy[0], cy[1] + 1):
        for z in range(cz[0], cz[1] + 1):
            edge = x in (0, SX - 1) and y == cy[0] or z in (cz[0], cz[1]) and y == cy[0]
            put(x, y, z, C['trim'] if edge else C['case'])
# 鍵盤架（從琴身往琴凳那側伸出去）＋鍵：白鍵一排、黑鍵照 2-3 的分組（每 7 格一組：1 2 _ 4 5 6 _）
ky, kz = O['console']['y'], O['console']['z']
for x in range(1, SX - 1):
    for y in range(ky[0], ky[1] + 1):
        for z in range(kz[0], kz[1] + 1):
            put(x, y, z, C['trim'])
    for y in range(ky[0], ky[1] + 1):
        put(x, y, kz[1] + 1, C['white'])
    if (x - 1) % 7 in (1, 2, 4, 5, 6):
        put(x, ky[1], kz[1] + 2, C['black'])
# 琴凳：四隻腳＋座面
B = O['bench']
for x in range(B['x'][0], B['x'][1] + 1):
    for y in range(B['y'][0], B['y'][1] + 1):
        put(x, y, B['seat_z'], C['seat'])
        if x in B['x'] and y in B['y']:
            for z in range(B['seat_z']):
                put(x, y, z, C['seat'])
# 管子：前排 5 根兩格寬、每根之間空一格（🩸 第一版 8 根貼在一起 ⇒ 側看是一座實心的階梯，讀不出是管子）；
#   後排 4 根一格寬的細管塞在前排的縫後面；管口（mouth_z）在前排面向琴凳那一面點鬼火
P = O['pipes']
for rank, mouth in (('front', True), ('back', False)):
    R_ = P[rank]
    for (xa, xb), top in zip(R_['x'], R_['tops']):
        for x in range(xa, xb + 1):
            for y in range(R_['y'][0], R_['y'][1] + 1):
                for z in range(P['z0'], top + 1):
                    put(x, y, z, C['pipe'])
            if mouth:
                for z in P['mouth_z']:
                    put(x, R_['y'][0], z, C['mouth'], over=True)
# 海草：從鍵盤架前緣垂下來；藤壺：琴身側面幾顆
for i, x in enumerate(O['weed_x']):
    for z in range(kz[0] - 1, kz[0] - 6, -1):
        put(x, ky[0], z, C['weed'][(i + z) % 2])
for x, y, z in O['barnacles']:
    put(x, y, z, C['barnacle'], over=True)


def components(cs):
    S = set(cs); seen = set(); n = 0
    for c in S:
        if c in seen:
            continue
        n += 1; st = [c]; seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
    return n


# 現況
a = np.loadtxt(os.path.join(EX, 'assembly.list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True
S = O['scale']; at = np.array(O['at'], float)
offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
smp = (np.array(sorted(cells), float)[:, None, :] + offs[None]).reshape(-1, 3) * S + at
i = np.floor(smp).astype(int)
in_solid = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
bot = np.array([[x + ox, y + oy, 0.0] for (x, y, z) in cells if z == 0 for ox in (0.25, 0.75) for oy in (0.25, 0.75)]) * S + at
j = np.floor(bot).astype(int)
support = int(occ[j[:, 0], j[:, 1], j[:, 2] - 1].sum())
lo, hi = smp.min(0), smp.max(0)
vs, cur = [], False
for line in open(os.path.join(EX, 'assembly.obj'), encoding='utf-8'):
    if line.startswith('o '):
        cur = line[2:].startswith('rope_')
    elif line.startswith('v ') and cur:
        t = line.split(); vs.append((float(t[1]), float(t[3]), float(t[2])))
RV = np.array(vs)
ropes_in = int(((RV >= lo - 0.3) & (RV <= hi + 0.3)).all(1).sum())
PJ = json.load(open(os.path.join(EX, 'parts.json'), encoding='utf-8'))
box_hits = [m['path'] for m in PJ['models'] if all(m['box'][k] < hi[k] and m['box'][k + 3] > lo[k] for k in range(3))]
txt = '# 風暴角號 管風琴（draft_organ.py，0.05 m）x,y,z,color —— at 0,0,0\n' + ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cells.items()))
path = os.path.join(D, 'masks', 'organ', 'organ.vox.txt')
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path, 'w', encoding='utf-8', newline='\n').write(txt)
from collections import Counter
out = {'note': 'draft_organ.py（階段十八）—— 現況 ＝ 引擎匯出 %s（%d 格）' % (os.path.relpath(EX, os.path.dirname(D)).replace('\\', '/'), len(a)),
       'work': O['work'], 'title': O['title'], 'host_work': O['host_work'], 'host_link': O['host_link'], 'model': O['model'],
       'file': 'masks/organ/organ.vox.txt', 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest(),
       'colors': {str(k): v for k, v in sorted(Counter(cells.values()).items())}, 'components': components(cells),
       'size': O['size'], 'mpv': O['mpv'], 'scale': S, 'at': O['at'], 'pivot': [0, 0, 0],
       'box_world': [lo.round(3).tolist(), hi.round(3).tolist()],
       'check': {'samples_in_solid': in_solid, 'samples': len(smp), 'bottom_supported': support, 'bottom_samples': len(bot), 'rope_vertices_in_box': ropes_in, 'model_box_overlap': box_hits}}
with open(os.path.join(D, 'verify_organ.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('cells', len(cells), 'components', out['components'], 'colors', out['colors'])
print('box', out['box_world'], json.dumps(out['check'], ensure_ascii=False))

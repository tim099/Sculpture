# TASK-0680：管風琴就是魔法動力源（Tim 2026-10-17「直接讓管風琴等於動力源」「放在水線上(艙房中)」「目前鍋爐實際上都打不到(水線下)」「可以加光源」）。
# 子作品 -organ-engine（0.1 m、用整船的框；組裝件關聯 `管風琴` at 0,0,0、meta kind=engine、engine=organ）—— 取代階段十八那台 0.05 m 的裝飾模型（同一個位置、大一號）。
# 位置是量出來的（引擎匯出 <exports>/assembly.list.txt；tools/cabin_measure.py 的讀數記在 notes）：船長室（艉樓底下）右舷牆、x 139–160；
#   地板一階一階（x 134–140 z 110、143–149 z 109、152–160 z 108，第一層空氣），天花板 z 123–125 ⇒ 琴身底照每一欄自己的地板、頂一律 z 118；管子到天花板下一格。
#   右舷牆照每一欄、每一層實際量（中線往右舷第一格實心）⇒ 琴身貼牆（舷牆內收、clamp 凸出都照實讓開）。
# 給遊戲：固定點 core（琴身正中、實心）、tend-1（琴師站的那一格：腳下實心、頭上 12 格空）；燈 ＝ 管口那一圈發光格（色 154），game.json lamps 指過來。
# 檢查（設計那一側）：每一格都落在空氣（現況匯出）、底下那一層不是自己就是實心（不浮空）、tend-1 站得住；反向對照：整台往下 1 ⇒ 要撞地板。
# 輸出：masks/organ_engine/organ_engine.vox.txt（世界座標）、verify_organ_engine.json
# 用法：python -I -X utf8 -B draft_organ_engine.py <design 資料夾> <exports 資料夾（assembly.list.txt）>
import sys, os, json, hashlib

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
C = plan['organ']['colors']                                   # 跟階段十八那台同一組顏色（琴身 100、邊框 73、白鍵 218、黑鍵 36、管 146、管口鬼火 154、凳 136、海草、藤壺）
X0, X1 = 139, 160                                              # 沿船長（含）
TOP = 118                                                      # 琴身頂（含）
FRONT = 148                                                    # 琴身前面板（y；固定一條直線）—— 🩸 第一版照牆往船裡 7 格 ⇒ 管子站的那一排撞上 clamp（z 120–121 凸到 y 151–153，整段 x 139–160 都是）、天花板往牆那側一路掉到 z 110（舷牆內收）⇒ 前面板拉到 148，管子只站 y 149、150

solid = set()
with open(os.path.join(EX, 'assembly.list.txt'), encoding='utf-8') as f:
    for ln in f:
        if ln[0] == '#':
            continue
        x, y, z, c = map(int, ln.split(','))
        if 130 <= x <= 170 and 120 <= y <= 175 and 100 <= z <= 130:
            solid.add((x, y, z))
S = lambda x, y, z: (x, y, z) in solid


def floor_at(x, y):                                            # 第一層空氣（往上找：下面實心、自己空氣）
    for z in range(102, 128):
        if S(x, y, z - 1) and not S(x, y, z):
            return z
    raise SystemExit('找不到地板 %d,%d' % (x, y))


def wall_at(x, z):                                             # 中線往右舷第一格實心
    for y in range(131, 175):
        if S(x, y, z):
            return y
    raise SystemExit('找不到牆 %d,%d' % (x, z))


def ceil_at(x, y, z0):
    for z in range(z0, 130):
        if S(x, y, z):
            return z
    raise SystemExit('找不到天花板 %d,%d' % (x, y))


cells = {}


def put(x, y, z, c):
    cells[(x, y, z)] = c


# 每一欄的牆：琴身那段（地板到 TOP）取最靠船裡的那一格 ⇒ 琴身不鑽牆；管子那段另外量
case_wall, pipe_wall, flo, ceil = {}, {}, {}, {}
for x in range(X0, X1 + 1):
    fz = floor_at(x, 140)
    flo[x] = fz
    case_wall[x] = min(wall_at(x, z) for z in range(fz, TOP + 1))
PIPE_Y = (FRONT + 1, FRONT + 2)                                # 前排（管口）、後排
for x in range(X0, X1 + 1):
    ceil[x] = min(ceil_at(x, y, TOP + 1) for y in PIPE_Y)       # 只量管子站的那兩排正上方
    pipe_wall[x] = min(wall_at(x, z) for z in range(TOP + 1, ceil[x]))
# 琴身：前面板 FRONT、往牆填到那一欄的牆 −1；底照那一欄的地板（填平地板的台階）、頂 TOP；邊框（四角、頂緣、底緣）73
#   🩸 第一版用「這一欄琴身那段最靠船裡的牆」當背板、地板只量 y 140 那一排 ⇒ 舷牆往下越往外、牆邊的地板低一階 ⇒ 琴身背後封出 5 個空腔 226 格（stats；拿掉這條關聯 ⇒ 0）
#   ⇒ 每一層各自填到那一層的牆、每一排各自從那一排的地板起
for x in range(X0, X1 + 1):
    for z in range(min(floor_at(x, y) for y in range(FRONT, case_wall[x])), TOP + 1):
        for y in range(FRONT, wall_at(x, z)):
            if z < floor_at(x, y) or S(x, y, z):
                continue
            edge = (y == FRONT and (x in (X0, X1) or z in (flo[x], TOP))) or (z == TOP and x in (X0, X1))
            put(x, y, z, C['trim'] if edge else C['case'])
# 鍵盤：從前面板往船裡伸 2 格，z 114–115；白鍵一排、黑鍵照 2-3 分組（每 7 格：1 2 _ 4 5 6 _）
for x in range(X0 + 2, X1 - 1):
    for y in (FRONT - 2, FRONT - 1):
        put(x, y, 114, C['trim'])
        put(x, y, 115, C['white'])
    if (x - X0 - 2) % 7 in (1, 2, 4, 5, 6):
        put(x, FRONT - 1, 116, C['black'])
# 琴凳：前面板往船裡 5–6 格、座面 z 112（離 z 108 的地板 0.4 m）、四隻腳照那一欄的地板
BX0, BX1, BY0, BY1, SEAT = 145, 154, FRONT - 6, FRONT - 5, 112
for x in range(BX0, BX1 + 1):
    for y in range(BY0, BY1 + 1):
        put(x, y, SEAT, C['seat'])
        if x in (BX0, BX1):
            for z in range(floor_at(x, y), SEAT):
                put(x, y, z, C['seat'])
# 管子：琴身頂上，前排一格寬、每根之間空一格（🩸 階段十八的教訓：貼在一起 ⇒ 側看是實心的階梯）；後排在前排的縫後面；
#   高度照那一欄的天花板 −1（中間高、兩端低：再減一個拱）；前排管口（底上第 1–2 格、朝船裡那一面）點鬼火 154
mid = (X0 + X1) / 2
mouths = []
for x in range(X0 + 1, X1):
    front = (x - X0) % 2 == 1
    y = PIPE_Y[0] if front else PIPE_Y[1]
    if y >= pipe_wall[x]:
        continue
    arch = int(round(abs(x - mid) / (mid - X0) * 3))            # 兩端矮 3 格
    top = ceil[x] - 1 - arch
    for z in range(TOP + 1, top + 1):
        put(x, y, z, C['pipe'])
        if front and z in (TOP + 1, TOP + 2):
            mouths.append((x, y, z))
for p in mouths:
    put(p[0], p[1], p[2], C['mouth'])
# 海草（從鍵盤架垂下）、藤壺（琴身前面板幾顆）：同階段十八那台的意思
for x in (X0 + 3, X0 + 10, X1 - 3):
    for z in (113, 112):
        if (x, FRONT - 2, z) not in cells:
            put(x, FRONT - 2, z, C['weed'][0] if z == 113 else C['weed'][1])
for x, z in ((X0 + 1, 110), (X0 + 7, 117), (X1 - 4, 111), (X1 - 1, 116)):
    put(x, FRONT, z, C['barnacle'])

# ── 檢查 ──
hit = [k for k in cells if S(*k)]
float_ = [k for k in cells if not S(k[0], k[1], k[2] - 1) and (k[0], k[1], k[2] - 1) not in cells and cells[k] not in (C['weed'][0], C['weed'][1])]
# 海草是垂下來的：它上面那格要是自己（鍵盤架）
weed_bad = [k for k in cells if cells[k] in (C['weed'][0], C['weed'][1]) and (k[0], k[1], k[2] + 1) not in cells]
core = (int(mid), FRONT + 3, (108 + TOP) // 2)
TX, TY = int(mid), FRONT - 8
tz = floor_at(TX, TY)
tend = (TX, TY, tz)
tend_ok = S(TX, TY, tz - 1) and all(not S(TX, TY, z) and (TX, TY, z) not in cells for z in range(tz, tz + 12))
down = sum(1 for k in cells if S(k[0], k[1], k[2] - 1) and (k[0], k[1], k[2] - 1) not in cells)   # 反向對照用：往下 1 會撞到的格數（底面那一層）
shifted_hit = sum(1 for k in cells if S(k[0], k[1], k[2] - 1))
mz = sorted(set(p[2] for p in mouths)); lamp = [round(sum(p[0] for p in mouths) / len(mouths), 1), round(sum(p[1] for p in mouths) / len(mouths), 1), round(sum(mz) / len(mz), 1)]
lamp_r = int(max(abs(p[0] - lamp[0]) for p in mouths) + 2)
other154 = [k for k in solid if abs(k[0] - lamp[0]) <= lamp_r and abs(k[1] - lamp[1]) <= lamp_r and abs(k[2] - lamp[2]) <= lamp_r]   # 量不到顏色（只存了實心）⇒ 另外用顏色檔量，見下
assert core in cells, 'core 不在琴身裡'
os.makedirs(os.path.join(D, 'masks', 'organ_engine'), exist_ok=True)
fn = os.path.join(D, 'masks', 'organ_engine', 'organ_engine.vox.txt')
with open(fn, 'w', encoding='utf-8', newline='\n') as f:
    for k in sorted(cells):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
V = {'work': 'summit-stormkaap-01m-organ-engine', 'title': '風暴角號｜管風琴（魔法動力源；船長室右舷、0.1 m）', 'file': 'masks/organ_engine/organ_engine.vox.txt',
     'link': '管風琴', 'meta': {'kind': 'engine', 'engine': 'organ'}, 'anchors': {'core': core, 'tend-1': tend},
     'lamp': {'at': lamp, 'r': lamp_r, 'color': C['mouth']}, 'cells': len(cells), 'mouths': len(mouths),
     'x': [X0, X1], 'front_y': FRONT, 'case_wall': case_wall, 'pipe_wall': pipe_wall, 'floor': flo, 'ceil': ceil,
     'check': {'hit_solid': len(hit), 'floating': len(float_), 'weed_bad': len(weed_bad), 'tend_ok': tend_ok, 'reverse_down1_hits': shifted_hit},
     'sha1': hashlib.sha1(open(fn, 'rb').read()).hexdigest()}
json.dump(V, open(os.path.join(D, 'verify_organ_engine.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: V[k] for k in ('cells', 'mouths', 'front_y', 'anchors', 'lamp', 'check', 'sha1')}, ensure_ascii=False))
print('floor', flo); print('case_wall', case_wall); print('ceil', ceil); print('pipe_wall', pipe_wall)

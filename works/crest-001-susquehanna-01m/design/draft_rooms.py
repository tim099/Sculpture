# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_rooms.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段九（TASK-0614）faux-pont 艙房 —— 抄自三叉戟號 gura-tridente-01m/design/draft_rooms.py（gura）；改：mio、框 1200、
#   faux-pont 中間是機艙（x 330–650 沒有地板）⇒ plan.rooms.segments 給兩段切點，房間只在每一段裡面隔（編號接著數）。
# 原檔說明：三叉戟號 orlop 艙房（TASK-0581；造船規格 §9.2 空艙房）：兩舷各一排艙房，中線留走道（艙口、梯子、桅都在中線附近）
#   艙壁（牆 1 格：板 177、框 136 —— 牆腳、牆頂、兩端、門框、每 8 格一根立柱，同憲法號階段十一）：
#   · 橫艙壁（沿 y）落在 plan 的 x 切點上；切點取在舷弧台階（甲板面上第一層空氣換高度的那一欄）⇒ 每間地板是平的（遊戲要平地板）
#   · 內側縱艙壁（沿 x）在 y ＝ 中線 ＋ inner_dy，門洞朝走道（寬 door_w、高 door_h）
#   · 牆從甲板面上第一層空氣往上到頭上第一格實心（橫樑或甲板板）底下；往外到船殼內面為止
#   房：每間的空氣框 ＝ 牆圍起來的那一塊裡最大的長方體（x 全段、y 從內側牆往外到船殼內面最窄處、z 地板 .. 頭上最低那格 − 1），固定點 <名>.min／.max／.door
#   只做 S 舷一件子作品（框 ＝ 牆的外框），另一舷 mirror=y 關聯（固定點遊戲自己翻）。
#   現況 ＝ 組裝件 links=all 藏本階段的兩條關聯 ＋ 模型外框。輸出：masks/rooms/orlop_side.vox.txt（子作品座標）、verify_rooms.json。
#   用法：python -I -X utf8 draft_rooms.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio as DB

NX, NY, NZ = 1300, 400, 120   # 蘇士奎哈納號改：框 1300


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(D)
    R = plan['rooms']
    C = R['colors']
    YC = plan['space']['yc']
    hide = ','.join('%s/%s' % (R['host_link'], l) for l in (R['link'], R['link_mirror']))
    try:
        A = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
    except SystemExit:
        A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    nbox = 0
    for m in parts():
        b = m['box']
        if b[2] >= NZ:
            continue
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        nbox += 1
    yi = YC + R['inner_dy']                                               # 內側縱艙壁那一欄

    def floor_of(x):
        return int(LY.deck_z(plan, R['deck'], x)) + 1

    def ceil_of(x, y, f):
        for z in range(f, NZ):
            if occ[x, y, z]:
                return z
        return None

    def wall_y(x, z):
        """S 舷船殼內面：從內側牆往外第一格實心。"""
        for y in range(yi + 1, NY):
            if occ[x, y, z]:
                return y
        return None

    segs = R['segments']
    cuts = sorted({x for sg in segs for x in sg})
    for sg in segs:
        for a, b in zip(sg, sg[1:]):
            fs = {floor_of(x) for x in range(a + 1, b)}
            assert len(fs) == 1, ('這一段地板不平', a, b, sorted(fs))
    cells = {}

    def put(p, c):
        if occ[p]:
            return False
        cells[p] = c
        return True

    blocked = 0
    # 橫艙壁（沿 y），在每個切點
    for k, x in enumerate(cuts):
        f = min(floor_of(x - 1), floor_of(x + 1), floor_of(x))           # 牆腳落在兩邊低的那一階（不留縫）
        for z in range(f, NZ):
            yw = wall_y(x, z)
            if yw is None:
                break
            row_any = False
            for y in range(yi, yw):
                c0 = ceil_of(x, y, f)
                if c0 is None or z >= c0:
                    continue
                frame = (y - yi) % 8 == 0 or z == f or z == c0 - 1 or y == yw - 1 or y == yi
                if put((x, y, z), C['frame'] if frame else C['plank']):
                    row_any = True
                else:
                    blocked += 1
            if not row_any and z > f + 2:
                break
    # 內側縱艙壁（沿 x），門洞在每一間正中
    rooms = []
    pairs = [(a, b) for sg in segs for a, b in zip(sg, sg[1:])]
    for i, (a, b) in enumerate(pairs):
        f = floor_of((a + b) // 2)
        mid = (a + b) // 2
        dx0, dx1 = mid - R['door_w'] // 2, mid - R['door_w'] // 2 + R['door_w'] - 1
        for x in range(a + 1, b):
            c0 = ceil_of(x, yi, f)
            for z in range(f, c0):
                door = dx0 <= x <= dx1 and z < f + R['door_h']
                if door:
                    continue
                frame = (x - a) % 8 == 0 or z == f or z == c0 - 1 or x in (dx0 - 1, dx1 + 1) or (dx0 <= x <= dx1 and z == f + R['door_h'])
                if not put((x, yi, z), C['frame'] if frame else C['plank']):
                    blocked += 1
        rooms.append({'name': str(i + 1), 'x': [a, b], 'floor': f, 'door_x': [dx0, dx1]})
    # 每間的空氣框
    for r in rooms:
        a, b, f = r['x'][0], r['x'][1], r['floor']
        xs = range(a + 1, b)
        zt = min(ceil_of(x, y, f) for x in xs for y in range(yi + 1, yi + 4)) - 1    # 頭上最低那格底下
        ymax = min(wall_y(x, z) for x in xs for z in range(f, zt + 1)) - 1
        box = [[a + 1, yi + 1, f], [b - 1, ymax, zt]]
        sol = int(occ[a + 1:b, yi + 1:ymax + 1, f:zt + 1].sum()) + sum(1 for p in cells if a + 1 <= p[0] <= b - 1 and yi + 1 <= p[1] <= ymax and f <= p[2] <= zt)
        fl = int(occ[a + 1:b, yi + 1:ymax + 1, f - 1].sum())
        r.update({'box': box, 'size_m': [round((b - 1 - a) * 0.1, 1), round((ymax - yi) * 0.1, 1), round((zt - f + 1) * 0.1, 1)],
                  'solid_inside': sol, 'floor_solid': [fl, (b - 1 - a) * (ymax - yi)], 'door': [r['door_x'][0] + R['door_w'] // 2, yi, f]})
    xs_, ys_, zs_ = zip(*cells)
    lo = (min(xs_), min(ys_), min(zs_))
    hi = (max(xs_), max(ys_), max(zs_))
    for r in rooms:
        lo = (min(lo[0], r['box'][0][0]), min(lo[1], r['box'][0][1]), min(lo[2], r['box'][0][2]))
        hi = (max(hi[0], r['box'][1][0]), max(hi[1], r['box'][1][1]), max(hi[2], r['box'][1][2]))
    size = [hi[i] - lo[i] + 1 for i in range(3)]
    at_m = [lo[0], 2 * YC + 1 - lo[1] - size[1], lo[2]]
    os.makedirs(os.path.join(D, 'masks', 'rooms'), exist_ok=True)
    txt = '# 蘇士奎哈納號 faux-pont 艙房（S 舷一件）draft_rooms.py —— 子作品座標 x,y,z,color；世界 ＝ ＋%s\n' % (list(lo),) + \
          ''.join('%d,%d,%d,%d\n' % (p[0] - lo[0], p[1] - lo[1], p[2] - lo[2], c) for p, c in sorted(cells.items()))
    open(os.path.join(D, 'masks', 'rooms', 'orlop_side.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    anchors = []
    for r in rooms:
        anchors.append({'name': r['name'] + '.min', 'at': [r['box'][0][i] - lo[i] for i in range(3)]})
        anchors.append({'name': r['name'] + '.max', 'at': [r['box'][1][i] - lo[i] for i in range(3)]})
        anchors.append({'name': r['name'] + '.door', 'at': [r['door'][i] - lo[i] for i in range(3)]})
    # 鏡像差：牆的格鏡到另一舷，落在現況實心的
    mir = sum(1 for (x, y, z) in cells if occ[x, 2 * YC - y, z])
    out = {'note': 'draft_rooms.py —— 現況 ＝ 組裝件 links=all 藏 %s（%d 格）＋ 模型外框 %d' % (hide, len(A), nbox),
           'work': R['work'], 'title': R['title'], 'frame_at': list(lo), 'frame_size': size, 'at_mirror': at_m,
           'host_work': R['host_work'], 'link': R['link'], 'link_mirror': R['link_mirror'], 'file': 'masks/rooms/orlop_side.vox.txt', 'voxels': len(cells),
           'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest(), 'rooms': rooms, 'anchors': anchors, 'blocked_wall_cells': blocked, 'mirror_hits': mir}
    with open(os.path.join(D, 'verify_rooms.json'), 'w', encoding='utf-8', newline='\n') as f_:
        json.dump(out, f_, ensure_ascii=False, indent=1)
        f_.write('\n')
    print('牆 %d 格（擋到沒放 %d）、框 at %s size %s、鏡像那一舷 at %s、鏡像落在實心 %d' % (len(cells), blocked, list(lo), size, at_m, mir))
    for r in rooms:
        print(' ', r['name'], 'x', r['x'], 'floor', r['floor'], '框', r['box'], r['size_m'], 'm，框裡實心', r['solid_inside'], '地板', r['floor_solid'])


if __name__ == '__main__':
    main()

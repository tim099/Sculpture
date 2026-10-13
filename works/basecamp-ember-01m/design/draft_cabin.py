# 餘燼號 階段八c：船長室（great cabin，poop 底下；plan.json cabin_build）—— 自由設計（Tim 2026-10-13「房間也自由發揮吧」）
#   poop 底下（上甲板面 129 到 poop 甲板板 148、x ≤ 215）：前艙壁（門）、隔間（拱口）把它分成船尾的大艙與前面的兩間（右舷臥艙、左舷海圖室）、
#   中間走道（後桅從走道穿過）；大艙：長桌、椅子、船尾窗下的長椅；桌子上方吊「餘燼之心」（金籠＋琥珀火芯）。
#   ⚠ 兩舷不做靠牆的隔間：poop 兩舷有砲門（z 138–146 那幾列牆是開的）—— 隔間牆只到 |dy| ≤ side_wall_dy 的走道兩側。
#   每一件只放在現況是空氣的格；撞到的照實記數（不硬塞）。
#   ⇒ masks/cabin/great_cabin.vox.txt（世界座標、子作品 at 0,0,0）、verify_cabin.json、sheet09_cabin_v1.png
# 用法：python -I draft_cabin.py <design 資料夾>
import sys, os, json, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402

YC = 160


class Cabin:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.C = s.plan['cabin_build']
        # 現況 ＝ 組裝件藏起這一階段的關聯（套用之後重跑才逐位元組一樣；工作記憶 sculpt-ember）
        from draft_ladders import existing_links, export_hidden
        have = set(existing_links(s.C['assembly']))
        s.hidden = [h for h in s.C['hide_links'] if h in have]
        a = export_hidden(s.C['assembly'], s.hidden)
        assert len(a) == s.C['assembly_voxels'], ('組裝件現況對不上', len(a))
        s.A = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.cells, s.part = {}, {}
        s.hit = collections.Counter()
        s.z0 = s.C['floor_z']            # 站的那一層（上甲板面）

    def put(s, k, c, part):
        if k in s.A:
            s.hit[part] += 1
            return
        s.cells[k] = c
        s.part[k] = part

    def ceil(s, x, y):
        z = s.z0
        while (x, y, z) not in s.A and z < s.z0 + 40:
            z += 1
        return z                          # 第一個實心（poop 甲板板或橫樑）

    def half(s, x, z):
        """這一欄、這一層從中線往兩舷走到第一個實心為止的 y 範圍（中線本身實心 ⇒ 從中線兩邊各自往外）"""
        lo = hi = YC
        while (x, hi + 1, z) not in s.A and hi - YC < 70:
            hi += 1
        while (x, lo - 1, z) not in s.A and YC - lo < 70:
            lo -= 1
        return lo, hi

    def screen(s, x, part, doors, door_h, arch=False, min_dy=0):
        """橫向艙壁：這一欄每一層、從中線到兩舷內板（只放 |dy| ≥ min_dy）；門 ＝ doors 裡每一段 |dy| 範圍 [a, b]、高 door_h
        （arch ⇒ 門頂兩角各收一格）"""
        K = s.C['colors']

        def in_door(dy, z):
            for a, b in doors:
                if a <= dy <= b and z < s.z0 + door_h - (1 if arch and dy in (a, b) and a > 0 else (1 if arch and dy == b else 0)):
                    return True
            return False

        def frame(dy, z):
            for a, b in doors:
                if (dy == b + 1 or (a > 0 and dy == a - 1)) and z <= s.z0 + door_h:
                    return True                          # 門框柱
                if a - (1 if a > 0 else 0) <= dy <= b + 1 and z == s.z0 + door_h:
                    return True                          # 門楣
            return False
        for z in range(s.z0, s.z0 + 40):
            lo, hi = s.half(x, z)
            if (x, YC, z) in s.A and lo == hi == YC:
                continue
            for y in range(lo, hi + 1):
                dy = abs(y - YC)
                if dy < min_dy or in_door(dy, z):
                    continue
                top = s.ceil(x, y)
                # 頭上要有 poop 甲板（天花板在 30 格內）—— 沒有 ＝ 在船外（第一版 poop 上方露天那幾層從中線走到 70 格外，
                # 艙壁在 z 161–168 船外長出四條、各自飄著）
                if z >= top or top >= s.z0 + 30:
                    continue
                if frame(dy, z):
                    c = K['frame']
                elif dy % 8 == 0:
                    c = K['frame']                       # 每 8 格一根壁柱
                elif z == top - 1:
                    c = K['gold']                        # 頂上一條金邊
                else:
                    c = K['panel']
                s.put((x, y, z), c, part)

    def fore_aft_wall(s, dy, x0, x1, door_x, part):
        K = s.C['colors']
        for sg in (1, -1):
            y = YC + sg * dy
            for x in range(x0, x1 + 1):
                top = s.ceil(x, y)
                for z in range(s.z0, top):
                    if door_x[0] <= x <= door_x[1] and z < s.z0 + 13:
                        continue
                    c = K['frame'] if (x - x0) % 8 == 0 or x in (door_x[0] - 1, door_x[1] + 1) else (K['gold'] if z == top - 1 else K['panel'])
                    s.put((x, y, z), c, part)

    def box(s, x0, x1, y0, y1, z0, z1, c, part):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    s.put((x, y, z), c, part)

    def table(s):
        T, K = s.C['table'], s.C['colors']
        x0, x1, w, zt = T['x'][0], T['x'][1], T['half_w'], s.z0 + T['height'] - 1
        s.box(x0, x1, YC - w, YC + w, zt, zt, K['dark'], 'table')
        for x in (x0 + 1, x1 - 1):
            for y in (YC - w + 1, YC + w - 1):
                s.box(x, x, y, y, s.z0, zt - 1, K['dark'], 'table')
        # 桌巾中線一條暗紅（桌面那一層換色）
        for x in range(x0 + 2, x1 - 1):
            if (x, YC, zt) in s.cells:                     # 只換真的放下去的桌面格（撞到被跳過的不補）
                s.cells[(x, YC, zt)] = K['cloth']

    def chair(s, x, y, face, part='chairs'):
        """椅子 2×2：座面 z0+3（暗紅墊）、腿、椅背在遠離 face 的那一側（face ＝ 朝向桌子的方向 (dx, dy)）"""
        K = s.C['colors']
        xs, ys = (x, x + 1), (y, y + 1)
        for a in xs:
            for b in ys:
                s.put((a, b, s.z0), K['wood'], part)
                s.put((a, b, s.z0 + 1), K['wood'], part)
                s.put((a, b, s.z0 + 2), K['wood'], part)
                s.put((a, b, s.z0 + 3), K['cloth'], part)
        fx, fy = face
        if fy:
            yb = y + 1 if fy < 0 else y
            for a in xs:
                for z in range(s.z0 + 4, s.z0 + 9):
                    s.put((a, yb, z), K['wood'] if z < s.z0 + 8 else K['gold'], part)
        else:
            xb = x + 1 if fx < 0 else x
            for b in ys:
                for z in range(s.z0 + 4, s.z0 + 9):
                    s.put((xb, b, z), K['wood'] if z < s.z0 + 8 else K['gold'], part)

    def chairs(s):
        T = s.C['table']
        for x in T['chairs_x']:
            s.chair(x, YC + T['half_w'] + 2, (0, -1))
            s.chair(x, YC - T['half_w'] - 3, (0, 1))
        s.chair(T['x'][0] - 4, YC - 1, (1, 0))
        s.chair(T['x'][1] + 3, YC - 1, (-1, 0))

    def stern_bench(s):
        B, K = s.C['stern_bench'], s.C['colors']
        # 船尾內面：每一列從船尾往前第一格空氣（座面那一層量）；長椅後緣貼著它、前緣拉成一條直線
        # （第一版每列各自往前 depth 格 ⇒ 船尾肋骨凹凸不平，長椅前緣鋸齒狀）
        face = {}
        for y in range(YC - B['half_w'], YC + B['half_w'] + 1):
            x = next((xx for xx in range(90, 140) if (xx - 1, y, s.z0 + 2) in s.A and (xx, y, s.z0 + 2) not in s.A), None)
            if x is not None:
                face[y] = x
        xf = max(face.values()) + B['depth'] - 1
        s.bench_front = xf
        for y, x in face.items():
            for xx in range(x, xf + 1):
                for z in range(s.z0, s.z0 + B['height']):
                    c = K['cloth'] if z == s.z0 + B['height'] - 1 else K['wood']
                    s.put((xx, y, z), c, 'stern_bench')

    def heart(s):
        H, K = s.C['heart'], s.C['colors']
        cx, cz = H['x'], H['z']
        r = H['r']
        for x in range(cx - r, cx + r + 1):
            for y in range(YC - r, YC + r + 1):
                for z in range(cz - r - 1, cz + r + 2):
                    ex = abs(x - cx) == r
                    ey = abs(y - YC) == r
                    ez = z in (cz - r - 1, cz + r + 1)
                    if (ex + ey + ez) >= 2:
                        s.put((x, y, z), K['gold'], 'heart')            # 籠子的稜
                    elif abs(x - cx) <= 1 and abs(y - YC) <= 1 and abs(z - cz) <= 1:
                        c = K['flame_core'] if (x, y, z) == (cx, YC, cz) else K['flame']
                        s.put((x, y, z), c, 'heart')                    # 火芯 3×3×3
        # 籠頂一個金十字（接四條稜）＋火芯頂到十字中心一根金桿 ⇒ 火芯、籠子、吊鍊連成一塊
        # （第一版籠子只有稜：火芯浮在中間、吊鍊掛在籠頂中心那格空氣上 ⇒ 兩塊各自飄著）
        zt = cz + r + 1
        for t in range(-r, r + 1):
            s.put((cx + t, YC, zt), K['gold'], 'heart')
            s.put((cx, YC + t, zt), K['gold'], 'heart')
        for z in range(cz + 2, zt):
            s.put((cx, YC, z), K['gold'], 'heart')
        # 吊鍊：籠頂到天花板
        z = cz + r + 2
        while (cx, YC, z) not in s.A and z < cz + 20:
            s.put((cx, YC, z), K['iron'], 'heart')
            z += 1

    def bed(s):
        B, K = s.C['bed'], s.C['colors']
        x0, x1 = B['x']
        y0, y1 = B['y']
        s.box(x0, x1, y0, y1, s.z0, s.z0 + 2, K['dark'], 'bed')
        s.box(x0, x1, y0, y1, s.z0 + 3, s.z0 + 3, K['cloth'], 'bed')
        s.box(x0, x0 + 2, y0 + 1, y1 - 1, s.z0 + 4, s.z0 + 4, K['white'], 'bed')     # 枕頭
        for x in (x0, x1):                                                          # 床頭床尾板
            s.box(x, x, y0, y1, s.z0 + 3, s.z0 + 6, K['dark'], 'bed')

    def desk(s):
        D, K = s.C['desk'], s.C['colors']
        x0, x1 = D['x']
        y0, y1 = D['y']
        zt = s.z0 + 7
        s.box(x0, x1, y0, y1, zt, zt, K['dark'], 'desk')
        for x in (x0, x1):
            for y in (y0, y1):
                s.box(x, x, y, y, s.z0, zt - 1, K['dark'], 'desk')
        for x in range(x0 + 1, x1):
            for y in range(y0 + 1, y1):
                if (x, y, zt) in s.cells:
                    s.cells[(x, y, zt)] = K['chart']                               # 攤開的海圖
        s.chair(x0 + (x1 - x0) // 2, y1 + 2, (0, -1), 'desk')

    def build(s):
        S = s.C
        s.screen(S['front_x'], 'front_screen', [tuple(d) for d in S['front_doors']], S['door_h'])
        s.screen(S['partition_x'], 'partition', [(0, S['arch_dy'])], S['arch_h'], arch=True)
        # 兩間艙的前牆（只做 |dy| ≥ 走道牆那一段）—— 前面是後桅與它的 fife rail 那一塊玄關
        s.screen(S['cabin_front_x'], 'cabin_fronts', [], 0, min_dy=S['side_wall_dy'])
        s.fore_aft_wall(S['side_wall_dy'], S['partition_x'] + 1, S['cabin_front_x'] - 1, S['side_door_x'], 'side_walls')
        s.table()
        s.chairs()
        s.stern_bench()
        s.heart()
        s.bed()
        s.desk()

    def verify(s):
        v = {'cells': len(s.cells), 'by_part': dict(collections.Counter(s.part.values())), 'hit_existing': dict(s.hit)}
        v['overlap_assembly'] = sum(1 for k in s.cells if k in s.A)
        R = dict(s.A)
        R.update(s.cells)
        v['assembly_expect'] = len(R)
        # 只量這一塊附近的結構（整艘太大）：新格＋附近組裝件 → 新格都接得到？會不會封出空腔？
        xs = [k[0] for k in s.cells]
        x0, x1 = min(xs) - 6, max(xs) + 6
        sub = {k: 1 for k in R if x0 <= k[0] <= x1 and s.z0 - 8 <= k[2] <= s.z0 + 30}
        st = DP.Ember.structure(None, sub)
        v['structure_local'] = st
        v['note_structure'] = '局部量（x %d..%d、z %d..%d）：元件數會因為切邊而多 —— 看的是空腔；整艘套用後用 stats 量' % (x0, x1, s.z0 - 8, s.z0 + 30)
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'cabin')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'great_cabin.vox.txt')
        rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write('# 船長室（世界座標，子作品 at 0,0,0）（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        return {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}

    def sheet(s, path):
        # 平面（從上往下、每格取最高的）＋ 一張從船頭往船尾看的剖面（x ＝ partition_x + 1 往船尾）
        x0, x1, y0, y1, sc = 90, 222, 110, 211, 5
        im = Image.new('RGB', ((x1 - x0) * sc + 40, (y1 - y0) * sc + 60), (250, 249, 244))
        d = ImageDraw.Draw(im)
        d.text((20, 10), '餘燼號 新圖紙 09 v1：船長室（poop 底下，從上往下看；灰 ＝ 船殼與甲板、彩 ＝ 新加）', font=DP.font(16), fill=(30, 30, 30))
        px = im.load()
        top = {}
        for (x, y, z), c in s.A.items():
            if s.z0 <= z < s.z0 + 17 and x0 <= x < x1 and y0 <= y < y1:
                if (x, y) not in top or z > top[(x, y)][0]:
                    top[(x, y)] = (z, None)
        for (x, y, z), c in s.cells.items():
            if x0 <= x < x1 and y0 <= y < y1:
                if (x, y) not in top or top[(x, y)][1] is None or z > top[(x, y)][0]:
                    top[(x, y)] = (z, c)
        for (x, y), (z, c) in top.items():
            col = (205, 205, 205) if c is None else DP.rgb(c)
            for i in range(sc):
                for j in range(sc):
                    px[20 + (x - x0) * sc + i, 40 + (y1 - 1 - y) * sc + j] = col
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    C = Cabin(design)
    C.build()
    v = C.verify()
    v['file'] = C.write()
    C.sheet(os.path.join(design, 'sheet09_cabin_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_cabin.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

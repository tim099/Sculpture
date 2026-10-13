"""
餘燼號 階段十八 甲板屬具（自由設計；兩艘船原本都沒有）—— 0.02 m／格的子作品，當外部模型縮 0.2 掛在甲板-spar（同舵輪）。
座標（子作品自己的）：x ＝ 沿船長（船頭 +x）、y ＝ 橫向、z 上；z 0 ＝ 甲板面上第一層。兩件都對 y 中線左右對稱。

· 羅經櫃（binnacle）24×48×64：木櫃分三格 —— 兩邊各一個羅經、中間一盞燈；朝船尾（−x，舵手那一面）三扇玻璃窗（燈色琥珀）；
  櫃頂一條線腳、上面山形頂（屋脊沿 y）、屋脊正中一顆黃銅頂飾。⚠ 尺寸照一般比例（寬 0.9 m、深 0.4 m、櫃高 0.95 m），未查證。
· 主絞盤（capstan）80×80×66：鐵底圈（pawl ring）→ 鼓身（barrel，r 20）＋ 8 條肋（whelps，下寬上窄）→ 絞盤頭（drumhead，r 36、高 13）
  側面 12 個插桿孔、上下兩道鐵箍、頂上黃銅蓋。插桿收起來不做。⚠ 尺寸照一般比例（絞盤頭直徑約 1.5 m、總高 1.3 m），未查證。
輸出：masks/fittings/{binnacle,capstan}.vox.txt（stampvox 清單，at 0,0,0）、verify_fittings.json（格數、顏色、左右差）。
"""
import json, math, os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
WOOD, DARK, BASE, BRASS, IRON, GLASS = 141, 136, 104, 212, 36, 245

# ───────── 羅經櫃 ─────────
B_SIZE = (24, 48, 64)


def binnacle(x, y, z):
    yc = (B_SIZE[1] - 1) / 2.0           # 23.5
    dy = abs(y - yc)
    if 0 <= z <= 2:                      # 底座
        return BASE if 0 <= x <= 23 and dy <= 21.5 else 0
    if 3 <= z <= 47:                     # 櫃身
        if not (2 <= x <= 21 and dy <= 19.5):
            return 0
        if x in (2, 21) and dy >= 18.5:  # 四個角柱
            return DARK
        if x == 2 and 30 <= z <= 42:     # 船尾那面三扇窗：y 6..15 ／ 18..29（燈）／ 32..41，窗框直條 y 5、16–17、30–31、42
            return GLASS if dy <= 5.5 or 8.5 <= dy <= 17.5 else DARK
        if x == 2 and z in (29, 43):
            return DARK                   # 窗框上下橫條
        return WOOD
    if 48 <= z <= 49:                    # 櫃頂線腳
        return DARK if 1 <= x <= 22 and dy <= 20.5 else 0
    if 50 <= z <= 60:                    # 山形頂（屋脊沿 y）
        k = z - 50
        return DARK if 1 + k <= x <= 22 - k and dy <= 20.5 else 0
    if 61 <= z <= 63:                    # 黃銅頂飾
        return BRASS if 10 <= x <= 13 and dy <= (1.5 if z < 63 else 0.5) else 0
    return 0


# ───────── 主絞盤 ─────────
C_SIZE = (80, 80, 66)
CC = 39.5                                # 中心（x、y 都是）
R_RING, R_BARREL, R_HEAD = 34.0, 20.0, 36.0
N_WHELP, N_BAR = 8, 12


def capstan(x, y, z):
    px, py = x - CC, y - CC
    r = math.hypot(px, py)
    th = math.atan2(py, px)
    if 0 <= z <= 3:                      # 鐵底圈
        return IRON if r <= R_RING else 0
    if 4 <= z <= 49:                     # 鼓身＋肋
        if r <= R_BARREL:
            return WOOD
        t = (z - 4) / 45.0
        rw = R_BARREL + 9.0 - 4.0 * t    # 肋外緣：底 29、頂 25
        if r <= rw:
            for k in range(N_WHELP):
                a = 2 * math.pi * k / N_WHELP + math.pi / N_WHELP
                if abs(math.remainder(th - a, 2 * math.pi)) * r <= 2.6:
                    return DARK
        return 0
    if 50 <= z <= 62:                    # 絞盤頭
        if r > R_HEAD:
            return 0
        if z in (50, 51, 61, 62) and r >= R_HEAD - 2.5:
            return IRON                   # 上下兩道鐵箍
        if 54 <= z <= 58 and r >= R_HEAD - 12:   # 插桿孔（徑向方孔，深 12 格）
            for k in range(N_BAR):
                a = 2 * math.pi * k / N_BAR
                if abs(math.remainder(th - a, 2 * math.pi)) * r <= 3.0:
                    return 0
        return WOOD
    if 63 <= z <= 65:                    # 黃銅蓋
        return BRASS if r <= (10.0 if z < 65 else 6.0) else 0
    return 0


def build(fn, size):
    out = []
    for x in range(size[0]):
        for y in range(size[1]):
            for z in range(size[2]):
                c = fn(x, y, z)
                if c:
                    out.append((x, y, z, c))
    s = {(x, y, z): c for x, y, z, c in out}
    asym = sum(1 for (x, y, z), c in s.items() if s.get((x, size[1] - 1 - y, z)) != c)
    return out, asym


def main():
    d = os.path.join(HERE, 'masks', 'fittings')
    os.makedirs(d, exist_ok=True)
    v = {}
    for name, fn, size in (('binnacle', binnacle, B_SIZE), ('capstan', capstan, C_SIZE)):
        out, asym = build(fn, size)
        txt = ''.join(f'{x},{y},{z},{c}\n' for x, y, z, c in out)
        open(os.path.join(d, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
        cnt = {}
        for *_, c in out:
            cnt[c] = cnt.get(c, 0) + 1
        v[name] = {'size': list(size), 'voxels': len(out), 'colors': cnt, 'asym_y': asym,
                   'file': 'masks/fittings/%s.vox.txt' % name, 'sha256': hashlib.sha256(txt.encode()).hexdigest()}
        print(name, len(out), cnt, 'asym', asym)
    json.dump(v, open(os.path.join(HERE, 'verify_fittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()

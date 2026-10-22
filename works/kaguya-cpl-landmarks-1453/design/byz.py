# 君士坦丁堡地標 1453 的共用格子工具（TASK-0748）：照聖索菲亞 kaguya-hagia-sophia-1453/design/sophia.py 的做法抽出來 ——
#   量體先當實心（公尺、模型框：x ＝ 從正面看左 → 右、y ＝ 進深 y 0 ＝ 正面、z 往上）⇒ 只留離「外面的空氣」shell 公尺內的格
#   ⇒ 窗、門 ＝ 最外一格挖掉、第二格是窗玻璃（另成一件，件號 GLASS_LAY）／門板（木色）。每一座地標一支 lm_<名>.py，用這裡的形狀拼。
# 決定論：numpy、沒有亂數（要殘破的照 random.Random(種子)）；同一份參數 ⇒ 逐格相同。
import math
import numpy as np
from scipy import ndimage

# 材質（MAT）：上色在 finish() 照材質 ＋ 位置雜湊做
BRICK, STONE, BANDED, MARBLE, LEAD, TILE, DARK, DOOR, GOLD, PORPHYRY, GRANITE, GREEN, SOIL, PLASTER, TREE, WOOD, BRONZE, GLASS = range(1, 19)
GLASS_LAY = 200                       # 窗玻璃的件號：finish() 把窗的那一格放進這一件 ⇒ build.py 拆成子作品「窗玻璃」（關聯 meta part=window、material=glass；Blocksail BUILDING_SPEC §5.1）
# 色號（8 位元 RRRGGGBB；磚、灰縫、大理石、鉛、暗、門、金跟聖索菲亞同一組）
COL = {'brick': 168, 'brick_dark': 136, 'mortar': 205, 'stone': 182, 'stone_dark': 145, 'marble': 218, 'marble_2': 214,
       'lead': 146, 'lead_seam': 110, 'tile': 204, 'tile_dark': 172, 'dark': 36, 'door': 68, 'gold': 248,
       'porphyry': 133, 'porphyry_2': 101, 'granite': 206, 'green': 76, 'green_2': 108, 'soil': 100, 'plaster': 250, 'tree': 44, 'wood': 104, 'bronze': 141, 'glass': 46}


class Model:
    def __init__(self, w, d, h, mpv):
        self.w, self.d, self.h, self.mpv = w, d, h, mpv
        self.NX, self.NY, self.NZ = int(round(w / mpv)), int(round(d / mpv)), int(math.ceil(h / mpv))
        self.shape = (self.NZ, self.NY, self.NX)
        self.X = ((np.arange(self.NX) + 0.5) * mpv)[None, None, :]
        self.Y = ((np.arange(self.NY) + 0.5) * mpv)[None, :, None]
        self.Z = ((np.arange(self.NZ) + 0.5) * mpv)[:, None, None]
        self.S = np.zeros(self.shape, bool)
        self.MAT = np.zeros(self.shape, np.uint8)
        self.LAY = np.zeros(self.shape, np.uint8)
        self.WIN, self.DOORS, self.AIR = [], [], []
        self.domes = []                       # (cx, cy, z0, r, 肋數) ⇒ 鉛皮照經線畫接縫
        self.band = (1.0, 0.0)                # 帶狀磚石：(磚的高, 石的高) 公尺；石 0 ⇒ 全磚
        self.band_z0 = 0.0

    # ── 放 ──
    def full(self, m):
        return np.broadcast_to(m, self.shape)

    def add(self, m, mat, lay, over=True):
        m = self.full(m)
        if not over:
            m = m & ~self.S
        self.S[m] = True; self.MAT[m] = mat; self.LAY[m] = lay

    def air(self, m):
        self.AIR.append(m)

    def win(self, m):
        self.WIN.append(m)

    def door(self, m):
        self.DOORS.append(m)

    # ── 形狀（都回 bool 遮罩，可以廣播） ──
    def box(self, x0, x1, y0, y1, z0, z1):
        X, Y, Z = self.X, self.Y, self.Z
        return (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1) & (Z >= z0) & (Z < z1)

    def cyl(self, cx, cy, r, z0, z1):
        return ((self.X - cx) ** 2 + (self.Y - cy) ** 2 < r * r) & (self.Z >= z0) & (self.Z < z1)

    def ngon(self, cx, cy, r, n, z0, z1, rot=0.0):
        """正 n 邊形柱：r ＝ 外接圓半徑；rot ＝ 第一個頂點的方向（度，從 +x 往 +y）。"""
        dx, dy = self.X - cx, self.Y - cy
        apo = r * math.cos(math.pi / n)
        m = np.ones((1, self.NY, self.NX), bool)
        for k in range(n):
            a = math.radians(rot) + math.pi / n + 2 * math.pi * k / n          # 邊的法線
            m = m & (dx * math.cos(a) + dy * math.sin(a) <= apo)
        return m & (self.Z >= z0) & (self.Z < z1)

    def dome(self, cx, cy, z0, r, rise=None, ribs=0):
        """穹頂（橢球蓋，z0 以上）；ribs ＞ 0 ⇒ 鉛皮照經線畫接縫。"""
        rise = r if rise is None else rise
        if ribs:
            self.domes.append((cx, cy, z0, r, ribs))
        q = ((self.X - cx) ** 2 + (self.Y - cy) ** 2) / (r * r) + ((self.Z - z0) / rise) ** 2
        return (q <= 1.0) & (self.Z >= z0)

    def semidome(self, cx, cy, z0, r, toward='+y'):
        """半穹頂：圓心 (cx, cy, z0)、只留 toward 那一半。"""
        q = (self.X - cx) ** 2 + (self.Y - cy) ** 2 + (self.Z - z0) ** 2 <= r * r
        side = {'+y': self.Y >= cy, '-y': self.Y < cy, '+x': self.X >= cx, '-x': self.X < cx}[toward]
        return q & side & (self.Z >= z0)

    def apse(self, cx, y0, r, facets, z0, z1, toward='+y'):
        """後殿：外面是半個正多邊形（facets 個面）、往 toward 凸出；r ＝ 外接圓半徑。"""
        n = facets * 2
        if toward == '+y':
            m = self.ngon(cx, y0, r, n, z0, z1, rot=90 - 180.0 / n * (facets % 2 == 0)) & (self.Y >= y0)
        else:
            m = self.ngon(cx, y0, r, n, z0, z1, rot=-90 - 180.0 / n * (facets % 2 == 0)) & (self.Y < y0)
        return m

    def apse_x(self, x0, cy, r, facets, z0, z1, toward='+x'):
        """往 ±x 凸出的後殿（四葉形教堂的南北兩臂）：同 apse，圓心 (x0, cy)。"""
        n = facets * 2
        if toward == '+x':
            return self.ngon(x0, cy, r, n, z0, z1, rot=0 - 180.0 / n * (facets % 2 == 0)) & (self.X >= x0)
        return self.ngon(x0, cy, r, n, z0, z1, rot=180 - 180.0 / n * (facets % 2 == 0)) & (self.X < x0)

    def gable(self, x0, x1, y0, y1, z, rise, axis='y'):
        """雙坡屋頂：屋脊沿 axis；z ＝ 簷口高、rise ＝ 屋脊比簷口高幾公尺。"""
        if axis == 'y':
            c, hw, u = (x0 + x1) / 2, (x1 - x0) / 2, self.X
        else:
            c, hw, u = (y0 + y1) / 2, (y1 - y0) / 2, self.Y
        zt = z + rise * (1 - np.abs(u - c) / hw)
        return self.box(x0, x1, y0, y1, z, 999) & (self.Z < zt + self.mpv)

    def hip(self, x0, x1, y0, y1, z, rise, slope):
        """四坡：離邊 d 公尺 ⇒ 高 min(rise, slope·d)。"""
        d = np.minimum(np.minimum(self.X - x0, x1 - self.X), np.minimum(self.Y - y0, y1 - self.Y))
        return self.box(x0, x1, y0, y1, z, 999) & (self.Z < z + np.minimum(rise, slope * np.maximum(d, 0)) + self.mpv)

    def shed(self, x0, x1, y0, y1, z_lo, z_hi, high='+x'):
        """單坡：high 那一邊高（貼著主體）。"""
        if high in ('+x', '-x'):
            t = (self.X - x0) / (x1 - x0)
        else:
            t = (self.Y - y0) / (y1 - y0)
        if high[0] == '-':
            t = 1 - t
        zt = z_lo + (z_hi - z_lo) * np.clip(t, 0, 1)
        return self.box(x0, x1, y0, y1, z_lo, 999) & (self.Z < zt + self.mpv)

    def barrel(self, x0, x1, y0, y1, z, axis='y', rise=None):
        """筒形屋頂（半圓或扁的）：軸沿 axis、從 z 起。"""
        if axis == 'y':
            c, hw, u = (x0 + x1) / 2, (x1 - x0) / 2, self.X
        else:
            c, hw, u = (y0 + y1) / 2, (y1 - y0) / 2, self.Y
        rise = hw if rise is None else rise
        zt = z + rise * np.sqrt(np.clip(1 - ((u - c) / hw) ** 2, 0, 1))
        return self.box(x0, x1, y0, y1, z, 999) & (self.Z < zt + self.mpv)

    def arch_open(self, cx, cy, z0, z1, w, normal='y', depth=2.0):
        """拱頂開口（門、窗、拱廊）：寬 w、z0 到 z1（含半圓拱頂）；normal ＝ 開口朝哪一軸；depth ＝ 穿進去的深度（中心 ±depth/2）。"""
        r = w / 2.0
        if normal == 'y':
            u, v = self.X - cx, self.Y - cy
        else:
            u, v = self.Y - cy, self.X - cx
        top = (z1 - r) + np.sqrt(np.clip(r * r - u * u, 0, None))
        return (np.abs(u) < r) & (np.abs(v) < depth / 2.0) & (self.Z >= z0) & (self.Z < np.minimum(top, z1))

    def ring_windows(self, cx, cy, r_lo, r_hi, z0, z1, angles, half_w):
        """圍著 (cx, cy) 一圈的窗（穹頂鼓座、後殿）：角度從 +x 往 +y（度）、寬 2·half_w 公尺。"""
        dx, dy = self.X - cx, self.Y - cy
        r = np.hypot(dx, dy); a = np.arctan2(dy, dx)
        m = np.zeros((1, self.NY, self.NX), bool)
        for ang in angles:
            da = np.angle(np.exp(1j * (a - math.radians(ang))))
            m = m | (np.abs(da) * np.maximum(r, 1e-6) < half_w)
        return m & (r >= r_lo) & (r <= r_hi) & (self.Z >= z0) & (self.Z < z1)

    # ── 收尾 ──
    def finish(self, shell_m, seed=0):
        """挖空（只留離外面的空氣 shell_m 內的格；最底一層留著）、開窗開門、上色 ⇒ (G 色號, L 件號)。"""
        S, MAT = self.S, self.MAT
        for a in self.AIR:
            S[self.full(a)] = False
        # 外面的空氣：框外圍一圈當空氣（牆貼著框邊時才量得到它離外面幾格）；底下不算（地面）
        air = np.pad(~S, ((0, 1), (1, 1), (1, 1)), constant_values=True)
        lab, n = ndimage.label(air)
        edge = set(np.unique(np.concatenate([lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))) - {0}
        ext = np.isin(lab, list(edge)); del lab
        dist = ndimage.distance_transform_cdt(~ext, metric='taxicab')[:-1, 1:-1, 1:-1]
        sh = max(2, int(round(shell_m / self.mpv)))
        keep = S & ((dist <= sh) | self.full(self.Z < self.mpv))
        for lst, col in ((self.WIN, GLASS), (self.DOORS, DOOR)):
            for wm in lst:
                wm = self.full(wm)
                keep[wm & (dist == 1)] = False
                MAT[wm & (dist == 2) & keep] = col
                if col == GLASS: self.LAY[wm & (dist == 2) & keep] = GLASS_LAY
        keep &= MAT > 0
        zz, yy, xx = np.nonzero(keep)
        h = (((xx.astype(np.int64) * 73856093) ^ (yy.astype(np.int64) * 19349663) ^ (zz.astype(np.int64) * 83492791) ^ (seed * 2654435761)) & 0xffff) / 65536.0
        m = MAT[zz, yy, xx]
        Zm = (zz + 0.5) * self.mpv
        col = np.zeros(len(zz), np.uint8)
        # 帶狀磚石：從 band_z0 起，石 band[1] 公尺、磚 band[0] 公尺輪流（石 0 ⇒ 全磚）
        bh, sh_ = self.band
        per = bh + sh_
        isstone = (m == BANDED) & (sh_ > 0) & (((Zm - self.band_z0) % per) < sh_)
        brick = (m == BRICK) | ((m == BANDED) & ~isstone)
        course = max(1, int(round(0.2 / self.mpv)))                      # 灰縫：每 0.2 m 一層（0.4 m／格 ⇒ 每格）
        mort = (zz % (course * 3) == 0) if course > 1 else (zz % 3 == 0)
        col[brick] = np.where(mort[brick], np.where(h[brick] < 0.6, COL['mortar'], COL['brick']), np.where(h[brick] < 0.22, COL['brick_dark'], COL['brick']))
        st = (m == STONE) | isstone
        col[st] = np.where(h[st] < 0.25, COL['stone_dark'], COL['stone'])
        mb = m == MARBLE; col[mb] = np.where(h[mb] < 0.2, COL['marble_2'], COL['marble'])
        lb = m == LEAD
        seam = (yy % 6 == 0)
        for cx, cy, z0, r, ribs in self.domes:
            Xr, Yr = (xx + 0.5) * self.mpv, (yy + 0.5) * self.mpv
            on = (np.hypot(Xr - cx, Yr - cy) <= r + 0.6) & (Zm >= z0 - 0.2)
            a = np.arctan2(Yr - cy, Xr - cx)
            sd = np.abs(np.angle(np.exp(1j * a * ribs))) < 0.3
            seam = np.where(on, sd, seam)
        col[lb] = np.where(seam[lb], COL['lead_seam'], COL['lead'])
        tb = m == TILE; col[tb] = np.where((zz[tb] % 2 == 0) & (h[tb] < 0.5), COL['tile_dark'], COL['tile'])
        pb = m == PORPHYRY; col[pb] = np.where(h[pb] < 0.3, COL['porphyry_2'], COL['porphyry'])
        gb = m == GREEN; col[gb] = np.where(h[gb] < 0.3, COL['green_2'], COL['green'])
        for mat, name in ((DARK, 'dark'), (DOOR, 'door'), (GOLD, 'gold'), (GRANITE, 'granite'), (SOIL, 'soil'), (PLASTER, 'plaster'), (TREE, 'tree'), (WOOD, 'wood'), (BRONZE, 'bronze'), (GLASS, 'glass')):
            col[m == mat] = COL[name]
        G = np.zeros(self.shape, np.uint8)
        G[zz, yy, xx] = col
        L = np.zeros(self.shape, np.uint8)
        L[keep] = self.LAY[keep]
        return G, L

    def tree(self, x, y, h, w, lay, z0=0.0):
        """標一棵樹（Blocksail 匯入時照關聯的 meta kind=tree 換成遊戲自己生成的樹，BUILDING_SPEC §5.2）：樹幹＋橢球樹冠 —— 只拿來給位置、高（h）、寬（w）。"""
        r = w / 2.0
        self.add(self.cyl(x, y, max(0.3, self.mpv * 0.8), z0, z0 + h * 0.6), WOOD, lay)
        self.add(((self.X - x) ** 2 + (self.Y - y) ** 2) / (r * r) + ((self.Z - (z0 + h - r * 0.9)) / max(r * 0.9, h * 0.35)) ** 2 <= 1, TREE, lay)

    def cell(self, x, y, z):
        """公尺 ⇒ 格（固定點）。"""
        return [min(self.NX - 1, int(x / self.mpv)), min(self.NY - 1, int(y / self.mpv)), min(self.NZ - 1, int(z / self.mpv))]

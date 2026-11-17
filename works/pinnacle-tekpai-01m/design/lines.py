# 台灣帆竹筏 Tek-pái 幾何與竹排構造產生器（TASK-1312 步驟 3–4）
#   座標慣例：X 船長（船頭 +X）、Y 船寬（中線 yc=50，鏡像 y ↔ 2·yc − y）、Z 高度（z=0 平底竹排外底面）。
#   每格 k 佔 [k, k+1)、格心 k+0.5。
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


class TekpaiHull:
    """依 plan.json 產生 Tek-pái 雙翹主竹排、護舷竹、硬木橫擔與黃藤紮帶之決定性 3D 體素陣列。"""

    def __init__(self, plan, probe=None):
        self.plan = plan
        self.SX, self.SY, self.SZ = plan['space']['hull']
        self.YC = int(plan['space']['yc'])
        self.wl = int(plan['waterline']['z'])

        L = {k: float(V(v)) for k, v in plan['lines'].items()}
        if probe:
            for k, d in probe.items():
                L[k] = L[k] + d
        self.L = L

        self.xa = L['x_aft']
        self.xf = L['x_fwd']
        self.flat_aft = L['flat_aft']
        self.flat_fwd = L['flat_fwd']
        self.rocker_aft_z = L['rocker_aft_z']
        self.rocker_fwd_z = L['rocker_fwd_z']
        self.rocker_aft_pow = L['rocker_aft_pow']
        self.rocker_fwd_pow = L['rocker_fwd_pow']

        hb = plan['hull_build']
        self.culms = hb['culms']
        self.guard = hb['guard_rails']
        self.cross = hb['crossbeams']
        self.colors = {k: int(V(v)) for k, v in hb['colors'].items()}

    def z0_curve(self, x):
        """整數格的竹排底基準 z0(x)：中段平直 z=0，艏艉依火烤冪次上翹。"""
        x = np.asarray(x, dtype=float)
        ta = np.clip((self.flat_aft - x) / max(self.flat_aft - self.xa, 1e-6), 0.0, 1.0)
        tf = np.clip((x - self.flat_fwd) / max(self.xf - self.flat_fwd, 1e-6), 0.0, 1.0)
        zf = self.rocker_aft_z * (ta ** self.rocker_aft_pow) + self.rocker_fwd_z * (tf ** self.rocker_fwd_pow)
        return np.rint(zf).astype(np.int32)

    def build_voxels(self):
        """回傳 (G, meta_masks)：G shape=(SX, SY, SZ) uint8 色彩索引陣列（0=空）。"""
        G = np.zeros((self.SX, self.SY, self.SZ), dtype=np.uint8)
        C = self.colors
        xs = np.arange(self.SX)
        z0 = self.z0_curve(xs)

        # 1. 7 根主竹筒（dy = 0, ±4, ±8, ±12），各寬 3 格、高 3 格（z0..z0+2）
        culm_range = {}
        for c in self.culms:
            dy0 = int(c['dy'])
            x0 = int(c['x0'])
            x1 = int(c['x1'])
            h = int(c['h'])
            culm_range[dy0] = (x0, x1)
            ys = [self.YC] if dy0 == 0 else [self.YC - dy0, self.YC + dy0]
            for x in range(x0, x1 + 1):
                zb = int(z0[x])
                for yc_pos in ys:
                    for yy in range(yc_pos - 1, yc_pos + 2):
                        z_hi = min(zb + h, self.SZ)
                        G[x, yy, zb:z_hi] = C['bamboo_dry']

        # 2. 相鄰主竹筒之間的 1 格縱向綁紮槽（dy = ±2, ±6, ±10），厚 2 格（z0..z0+1）
        #    確保無空腔且左右相連成單一連通體，頂部呈現清晰竹筒弧溝
        sorted_dys = sorted(culm_range.keys())
        for idx in range(len(sorted_dys) - 1):
            d_in = sorted_dys[idx]
            d_out = sorted_dys[idx + 1]
            dy_g = (d_in + d_out) // 2
            gx0 = max(culm_range[d_in][0], culm_range[d_out][0])
            gx1 = min(culm_range[d_in][1], culm_range[d_out][1])
            for x in range(gx0, gx1 + 1):
                zb = int(z0[x])
                z_hi = min(zb + 2, self.SZ)
                G[x, self.YC - dy_g, zb:z_hi] = C['bamboo_dry']
                G[x, self.YC + dy_g, zb:z_hi] = C['bamboo_dry']

        # 3. 水下竹體與縱縫積水處著濕竹色（z < waterline_z - 1 即 z=0,1 浸水塗 bamboo_wet，上弧頂 z>=2 保留日曬竹黃）
        wet_z = max(self.wl - 1, 1)
        for x in range(self.SX):
            for y in range(self.SY):
                for z in range(min(wet_z, self.SZ)):
                    if G[x, y, z] == C['bamboo_dry']:
                        G[x, y, z] = C['bamboo_wet']

        # 4. 兩舷墊高護舷竹（dy = 14..15，x = 32..102），z = z0 + 2 .. z0 + 4
        #    並於兩端收束銜接最外排主竹筒
        gx0 = int(self.guard['x0'])
        gx1 = int(self.guard['x1'])
        glo = int(self.guard['z_lo_off'])
        ghi = int(self.guard['z_hi_off'])
        for x in range(gx0, gx1 + 1):
            zb = int(z0[x])
            zlo = zb + glo
            zhi = min(zb + ghi, self.SZ - 1)
            # 端點 3 格略低 1 格收束
            if x <= gx0 + 2 or x >= gx1 - 2:
                zhi = min(zb + glo + 1, self.SZ - 1)
            for dy in (14, 15):
                G[x, self.YC - dy, zlo:zhi + 1] = C['bamboo_dry']
                G[x, self.YC + dy, zlo:zhi + 1] = C['bamboo_dry']

        # 5. 9 道硬木橫擔（crossbeams）＋ 黃藤紮帶（lashings）
        #    先計算每個 x 上主排實際涵蓋的最大 dy，讓橫擔恰巧鎖到最外側竹排／護舷竹
        def max_dy_at(xx):
            if gx0 <= xx <= gx1:
                return 15
            m = 1
            for c in self.culms:
                if c['x0'] <= xx <= c['x1']:
                    m = max(m, int(c['dy']) + 1)
            return m

        c_lo_off = int(self.cross['z_lo_off'])
        c_hi_off = int(self.cross['z_hi_off'])
        cw = int(self.cross['x_width'])
        for st in self.cross['stations']:
            st = int(st)
            for xx in range(st, st + cw):
                if xx < 0 or xx >= self.SX:
                    continue
                zb = int(z0[xx])
                dy_lim = max_dy_at(xx)
                zlo = zb + c_lo_off
                zhi = min(zb + c_hi_off, self.SZ - 1)
                G[xx, self.YC - dy_lim : self.YC + dy_lim + 1, zlo : zhi + 1] = C['crossbar']

            # 黃藤紮帶：鎖在橫擔前側 1 格之各條縱向溝槽與兩舷護舷竹外箍（呈現一節節藤編紮感）
            lash_xs = [st]
            for lx in lash_xs:
                zb = int(z0[lx])
                dy_lim = max_dy_at(lx)
                # 外側護舷箍（若該站有護舷）
                if gx0 <= lx <= gx1:
                    for dy_f in (14, 15):
                        top_z = min(zb + ghi, self.SZ - 1)
                        G[lx, self.YC - dy_f, top_z] = C['lashing']
                        G[lx, self.YC + dy_f, top_z] = C['lashing']
                # 槽位藤索交纏點（dy = 2, 6, 10, 13 在橫擔上表層）
                for dy_l in (2, 6, 10, 13):
                    if dy_l <= dy_lim:
                        top_c = min(zb + c_hi_off, self.SZ - 1)
                        G[lx, self.YC - dy_l, top_c] = C['lashing']
                        G[lx, self.YC + dy_l, top_c] = C['lashing']

        # 6. 雙端翹首收束藤紮環（艉尖 x=19、艏尖 x=121）
        for tip_x in (19, 121):
            zb = int(z0[tip_x])
            dy_lim = max_dy_at(tip_x)
            top_c = min(zb + 3, self.SZ - 1)
            G[tip_x, self.YC - dy_lim : self.YC + dy_lim + 1, zb : top_c] = C['lashing']

        return G

# 利劍號（約 1750 阿爾及爾 xebec）線形（TASK-0022 新圖紙 01）：plan.json 的 lines ＋ sections.json ⇒ 每個 (x, z) 的半寬、船的外形
#   跟蠍子號（claude-galiot-01m/design/lines.py）不同：這艘有 Chapman 1768 Pl. LVIII No.17 的 body plan，
#   所以半寬不是參數公式，是「剖面表」：每個站一條 Y(Z)（sections.json，重新對號過），站與站之間每個高度用 PCHIP 沿船長內插，
#   沒追到的那幾段（站 12、10 的上半、17 的下半、船中的下半…）照 fill 規則補（見 build_table）。
#   兩端照 plan.json 的艏柱、艉柱外緣（側視讀數）切；底照龍骨底與 rabbet；頂照 top(X)（主舷牆頂、後甲板舷牆、船首凹弧）。
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格）、Z 高度（z 0 = 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   圖上的公尺（從 AP、從基線）× K（對齊 Chapman 尺寸表的 Lpp）⇒ 格：x = XAP + 10·X·K、z = 10·Z·K。
import json, os
import numpy as np
from scipy.interpolate import PchipInterpolator

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def interp(pts, x):
    """pts：[[a, b], …]（a 遞增）⇒ 在 x 的 b（線性、兩端外延成常數）。"""
    a = np.array([p[0] for p in pts], float)
    b = np.array([p[1] for p in pts], float)
    return np.interp(x, a, b)


class Lines:
    def __init__(self, plan, probe=None):
        L = plan['lines']
        self.plan = plan
        self.K = V(L['table_k'])
        self.XAP = V(L['x_ap_cell'])
        self.YC = plan['space']['yc']
        self.keel_hw = V(L['keel_half_cells'])
        self.probe = probe or {}
        k = self.K
        m = lambda pts: [[p[0] * k, p[1] * k] for p in pts]          # 圖上公尺 ⇒ × K
        self.keel_bottom = m(V(L['keel_bottom_XZ']))
        self.rabbet = m(V(L['rabbet_XZ']))
        self.stem = sorted(m([[p[1], p[0]] for p in V(L['stem_outer_XZ'])]))      # 存成 (Z, X)
        self.stern = sorted(m([[p[1], p[0]] for p in V(L['sternpost_outer_XZ'])]))
        self.top_pts = m(V(L['top_XZ']))
        self.hmax = V(plan['lines']['fill']['max_half_m']) * self.K   # 半寬上限（欄杆帽）
        self.build_table(plan)

    # ── 剖面表：Z 格線 × 站 ──
    def build_table(self, plan):
        SJ = json.load(open(os.path.join(HERE, 'sections.json'), encoding='utf-8'))
        assert abs(SJ['K'] - self.K) < 1e-9, 'sections.json 的 K 跟 plan.json lines.table_k 不一樣：改了 K 要重跑 make_sections.py'
        S = SJ['sections']
        fill = plan['lines']['fill']
        self.Zg = np.arange(0.0, V(fill['z_max_m']) + 1e-9, 0.25)          # 公尺（已 × K 的尺度）
        Xs, cols = [], []
        for s in S:
            zs = np.array([p[0] for p in s['ZY']]); ys = np.array([p[1] for p in s['ZY']])
            col = np.full(len(self.Zg), np.nan)
            ok = (self.Zg >= zs.min()) & (self.Zg <= zs.max())
            col[ok] = np.interp(self.Zg[ok], zs, ys)
            Xs.append(s['X']); cols.append(col)
        X = np.array(Xs); T = np.array(cols)                                # T[站, Z]
        # 1) 往下：最低一點 ⇒ 收到 (rabbet 高度, keel 半寬)。把 Z 當 Y 的函數做三次 Hermite：
        #    rabbet 那頭 dZ/dY ＝ fill.floor_rise（船底幾乎平），讀數那頭 dZ/dY ＝ 剖面在那裡的斜率（切線接上）⇒ 船舭鼓起來，不是直線。
        kh = (self.keel_hw + 0.5) * 0.1
        s0 = V(fill['floor_rise'])
        for i, x in enumerate(X):
            zr = float(interp(self.rabbet, x))
            idx = np.where(~np.isnan(T[i]))[0]
            if not len(idx):
                continue
            j0 = idx[0]
            z0, y0 = self.Zg[j0], T[i, j0]
            if j0 + 2 < len(self.Zg) and not np.isnan(T[i, j0 + 2]):
                dydz = (T[i, j0 + 2] - y0) / (self.Zg[j0 + 2] - z0)
            else:
                dydz = 1.0
            s1 = 1.0 / max(1e-3, dydz)
            dy = max(1e-6, y0 - kh)
            yy = np.linspace(kh, y0, 400); t = (yy - kh) / dy
            h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
            zz = h00 * zr + h10 * dy * s0 + h01 * z0 + h11 * dy * s1
            zz = np.maximum.accumulate(zz)
            for j in range(j0):
                z = self.Zg[j]
                T[i, j] = kh if z <= zr else float(np.interp(z, zz, yy))
        # 2) 往上（只對追到接近頂的站：最高讀數 ≥ fill.extend_from_m）：照最後兩點的斜率外延（外飄），斜率上限 fill.flare_max。
        #    ⚠ 要在沿船長內插之前做：不然上半段只有 17、8 兩站有值，中間的 12、10 會從 17 內插到 8（verifier3 抓到，12 站窄 5.6 格）。
        smax = V(fill['flare_max'])
        def extend(i):
            idx = np.where(~np.isnan(T[i]))[0]
            j1 = idx[-1]
            sl = (T[i, j1] - T[i, j1 - 2]) / (self.Zg[j1] - self.Zg[j1 - 2]) if j1 >= 2 else 0.0
            sl = float(np.clip(sl, 0, smax))
            for j in range(j1 + 1, len(self.Zg)):
                T[i, j] = T[i, j1] + sl * (self.Zg[j] - self.Zg[j1])
        zfrom = V(fill['extend_from_m'])
        for i in range(len(X)):
            idx = np.where(~np.isnan(T[i]))[0]
            if self.Zg[idx[-1]] >= zfrom:
                extend(i)
        # 3) 中間缺的高度：照同一個 Z 的其他站 PCHIP 沿船長補（只用有值的站）
        for j in range(len(self.Zg)):
            have = ~np.isnan(T[:, j])
            if have.sum() >= 3:
                f = PchipInterpolator(X[have], T[have, j], extrapolate=False)
                miss = ~have & (X > X[have].min()) & (X < X[have].max())
                T[miss, j] = f(X[miss])
        # 4) 還缺的（兩端的站）照斜率外延
        for i in range(len(X)):
            if np.isnan(T[i]).any():
                extend(i)
        for k_, d in self.probe.items():
            if k_ == 'scale_y':
                T = T * d
        self.Xst, self.T = X, T
        self.F = [PchipInterpolator(X, T[:, j], extrapolate=False) for j in range(len(self.Zg))]

    # ── 公尺 ⇔ 格 ──
    def x_m(self, xc):
        return (np.asarray(xc, float) - self.XAP) * 0.1

    def x_aft(self, z):
        return interp(self.stern, np.asarray(z, float))

    def x_fwd(self, z):
        return interp(self.stem, np.asarray(z, float))

    def top(self, X):
        return interp(self.top_pts, X)

    def hb_m(self, X, Z):
        """X、Z 公尺 ⇒ 半寬公尺（< 0 ＝ 不在船裡）。"""
        X = np.asarray(X, float); Z = np.asarray(Z, float)
        X, Z = np.broadcast_arrays(X, Z)
        out = np.full(X.shape, -1.0)
        zi = np.clip(Z / 0.25, 0, len(self.Zg) - 1.0001)
        j0 = np.floor(zi).astype(int); t = zi - j0
        Xa, Xb = self.Xst[0], self.Xst[-1]
        kh = (self.keel_hw + 0.5) * 0.1
        for j in np.unique(j0):
            m = j0 == j
            xx = np.clip(X[m], Xa, Xb)
            ya = self.F[j](xx); yb = self.F[j + 1](xx)
            y = ya + (yb - ya) * t[m]
            # 兩端：最後一站到艏柱／艉柱之間線性收到龍骨半寬
            xf = self.x_fwd(Z[m]); xa = self.x_aft(Z[m])
            yfa = self.F[j](Xb) + (self.F[j + 1](Xb) - self.F[j](Xb)) * t[m]
            yaa = self.F[j](Xa) + (self.F[j + 1](Xa) - self.F[j](Xa)) * t[m]
            fwd = X[m] > Xb
            y = np.where(fwd, kh + (yfa - kh) * np.clip((xf - X[m]) / np.maximum(1e-6, xf - Xb), 0, 1), y)
            aft = X[m] < Xa
            y = np.where(aft, kh + (yaa - kh) * np.clip((X[m] - xa) / np.maximum(1e-6, Xa - xa), 0, 1), y)
            inside = (X[m] >= xa) & (X[m] <= xf)
            y = np.minimum(y, self.hmax)
            out[m] = np.where(inside, np.maximum(y, kh), -1.0)
        # 底：龍骨底以下不算；rabbet 以下只有龍骨
        kb = interp(self.keel_bottom, X)
        zr = interp(self.rabbet, X)
        out = np.where(Z < kb, -1.0, out)
        out = np.where((Z < zr) & (out >= 0), np.minimum(out, kh), out)
        return out

    def solid(self, x0, x1, zmax, extra_top=0.0):
        """外形實心（布林 [x, y, z]，x 從 x0）。extra_top（公尺）> 0 ⇒ 頂往上多算（挖牆時不讓頂變成蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(x0, x1 + 1) + 0.5
        zs = np.arange(0, zmax + 1) + 0.5
        Xm, Zm = np.meshgrid(self.x_m(xs), zs * 0.1, indexing='ij')
        H = self.hb_m(Xm, Zm)
        top = self.top(Xm)
        H = np.where(Zm <= top + extra_top, H, -1.0)
        dy = (np.abs(np.arange(W) - self.YC))[None, :, None] * 0.1
        return dy <= H[:, None, :] + 1e-9

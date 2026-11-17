# 突尼斯湖淺水轉運划艇 Sandal 線形幾何：plan.json 的 lines ⇒ 每個 (x, z) 的半寬與實心遮罩
#   出處：basecamp-piragua-01m/design/lines.py（並沿用其連續座標與格心判定慣例）
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z=0 ＝ 船底平底外表面）；格 k 佔 [k, k+1)、格心 k+0.5。
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


class Lines:
    """將 plan['lines'] 參數轉為連續半寬 hb(x, z) 與實心船型體積 solid()。"""

    def __init__(self, plan, probe=None):
        L = {k: V(v) for k, v in plan['lines'].items()}
        if probe:
            for k, d in probe.items():
                L[k] = L[k] + d
        self.P = L
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k])
        self.xa, self.xf = g('x_aft'), g('x_fwd')
        self.xm = g('x_mid')
        self.B = g('half_beam')
        self.b0 = g('bottom_half')
        self.p = g('section_pow')
        self.D = g('depth_mid')
        self.flat_aft, self.flat_fwd = g('flat_aft'), g('flat_fwd')
        self.rock_aft, self.rock_fwd = g('rocker_pow_aft'), g('rocker_pow_fwd')
        self.zt_aft, self.zt_fwd = g('end_z_aft'), g('end_z_fwd')
        self.sh_aft, self.sh_fwd = g('sheer_z_aft'), g('sheer_z_fwd')
        self.sh_pow_aft, self.sh_pow_fwd = g('sheer_pow_aft'), g('sheer_pow_fwd')
        self.plan_pow_aft, self.plan_pow_fwd = g('plan_pow_aft'), g('plan_pow_fwd')
        self.eh_aft, self.eh_fwd = g('end_half_aft'), g('end_half_fwd')

    def u(self, x):
        """長度歸一參數：船中 0、艉端 −1、艏端 +1。"""
        x = np.asarray(x, float)
        return np.where(x < self.xm, -(self.xm - x) / (self.xm - self.xa), (x - self.xm) / (self.xf - self.xm))

    def zb(self, x):
        """龍骨/船底線：中段 [flat_aft, flat_fwd] 平底 z=0，往兩端分別依冪次起翹。"""
        x = np.asarray(x, float)
        ta = np.clip((self.flat_aft - x) / max(self.flat_aft - self.xa, 1e-6), 0, 1)
        tf = np.clip((x - self.flat_fwd) / max(self.xf - self.flat_fwd, 1e-6), 0, 1)
        return self.zt_aft * (ta ** self.rock_aft) + self.zt_fwd * (tf ** self.rock_fwd)

    def zs(self, x):
        """舷頂線（sheer）：船中 D，兩端照冪次緩緩上揚。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        return self.D + (self.sh_aft - self.D) * (ua ** self.sh_pow_aft) + (self.sh_fwd - self.D) * (uf ** self.sh_pow_fwd)

    def Bs(self, x):
        """舷頂半寬：船中 B，艉收至窄方艉鏡 eh_aft，艏收尖至 eh_fwd。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        fa = self.eh_aft + (self.B - self.eh_aft) * (1 - ua ** self.plan_pow_aft)
        ff = self.eh_fwd + (self.B - self.eh_fwd) * (1 - uf ** self.plan_pow_fwd)
        return np.where(np.asarray(u) < 0, fa, ff)

    def b0x(self, x):
        """該站平底半寬（隨平面船寬等比例縮窄，且不超過舷頂半寬）。"""
        return np.minimum(self.Bs(x), self.b0 * self.Bs(x) / self.B)

    def xa_at(self, z):
        """艉端 X：船尾鏡板隨高度略往後傾（+0 aft rake），底端略收進 2 格。"""
        t = np.clip((z - self.zt_aft) / max(self.sh_aft - self.zt_aft, 1e-6), 0, 1)
        return self.xa + 2.0 * (1.0 - t)

    def xf_at(self, z):
        """艏端 X：弧形破水艏柱（隨高度往 +X 傾出 4 格）。"""
        t = np.clip((z - self.zt_fwd) / max(self.sh_fwd - self.zt_fwd, 1e-6), 0, 1)
        return self.xf - 4.0 * ((1.0 - t) ** 1.3)

    def hb(self, x, z):
        """(x, z) 處的半寬；超出船殼長度或高度範圍回傳 −1。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        zb, zs = self.zb(x), self.zs(x)
        t = (z - zb) / np.maximum(zs - zb, 1e-6)
        h = self.b0x(x) + (self.Bs(x) - self.b0x(x)) * (np.clip(t, 0, 1) ** self.p)
        xa_z, xf_z = self.xa_at(z), self.xf_at(z)
        ok = (t >= 0) & (t <= 1) & (x >= xa_z) & (x <= xf_z)
        return np.where(ok, h, -1.0)

    def solid(self, X0, X1, ZMAX, extra=0):
        """產生 [x, y, z] 實心船型布林體積（extra>0 用於向頂部延伸再做內蝕，避免舷頂變蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(X0, X1 + 1) + 0.5
        zs = np.arange(0, ZMAX + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        if extra:
            Z2 = np.minimum(Z, self.zs(X) - 0.01)
            H = np.where(Z <= self.zs(X) + extra, self.hb(X, np.maximum(Z2, self.zb(X))), -1.0)
            H = np.where(Z < self.zb(X), -1.0, H)
        else:
            H = self.hb(X, Z)
        dy = np.abs(np.arange(W) - self.YC)
        return dy[None, :, None] <= H[:, None, :]

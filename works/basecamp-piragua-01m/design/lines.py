# 杉心號（加勒比海盜的大獨木舟 piragua）線形：plan.json 的 lines ⇒ 每個 (x, z) 的半寬、船的外形
#   出處：apex-one-punt-01m/design/lines.py（蓬特號）—— 拿掉兩頭的柱，船尾改成平的一頭（transom），兩頭各自的收尖寬度。
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 = 船底外面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   「在不在船裡」：|y − YC| ≤ hb(x, z) ⇒ 兩舷逐格對稱。
#   periago 的特徵（Dampier 1697 第 3、8 章）：一整根雪松挖空、平底、一頭尖一頭平；先把樹的上面削平 ⇒ 舷頂幾乎是平的。
#   船身剖面：hb(x, z) ＝ b0(x) ＋ (Bs(x) − b0(x)) · t^p，t ＝ (z − zb(x)) ÷ (zs(x) − zb(x))（zb 船底、zs 舷頂）。
#   被 draft_lines.py 與之後的階段 import；只讀 plan.json、不碰作品。
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


class Lines:
    """plan['lines'] 的數字 ⇒ 幾何函式（吃 numpy 陣列或純量）。"""

    def __init__(self, plan, probe=None):
        L = {k: V(v) for k, v in plan['lines'].items()}
        if probe:
            for k, d in probe.items():
                L[k] = L[k] + d
        self.P = L
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k])
        self.xa, self.xf = g('x_aft'), g('x_fwd')                 # 船尾平板、船頭尖端
        self.xm = g('x_mid')                                     # 最寬那一站
        self.B = g('half_beam')                                  # 船中舷頂半寬（格）
        self.b0 = g('bottom_half')                               # 船中平底半寬
        self.p = g('section_pow')                                # 剖面外張的指數（< 1 ⇒ 圓舭、舷側直）
        self.D = g('depth_mid')                                  # 船中舷頂高（z）
        self.flat_aft, self.flat_fwd = g('flat_aft'), g('flat_fwd')   # 船底平的那一段（x）
        self.rock_fwd = g('rocker_pow_fwd')
        self.zt_fwd = g('end_z_fwd')                             # 船頭船底翹到多高
        self.sh_aft, self.sh_fwd = g('sheer_z_aft'), g('sheer_z_fwd')
        self.sh_pow_aft, self.sh_pow_fwd = g('sheer_pow_aft'), g('sheer_pow_fwd')
        self.plan_pow_aft, self.plan_pow_fwd = g('plan_pow_aft'), g('plan_pow_fwd')
        self.eh_aft, self.eh_fwd = g('end_half_aft'), g('end_half_fwd')

    # ── 長度方向的參數 u：船中 0、船尾端 −1、船頭端 +1 ──
    def u(self, x):
        x = np.asarray(x, float)
        return np.where(x < self.xm, -(self.xm - x) / (self.xm - self.xa), (x - self.xm) / (self.xf - self.xm))

    def zb(self, x):
        """船底：平底一路到船尾（transom 底就是 z 0），船頭照冪次翹到 end_z_fwd。"""
        x = np.asarray(x, float)
        tf = np.clip((x - self.flat_fwd) / (self.xf - self.flat_fwd), 0, 1)
        return self.zt_fwd * tf ** self.rock_fwd

    def zs(self, x):
        """舷頂（sheer）：船中 D，兩頭照冪次到 sheer_z。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        return self.D + (self.sh_aft - self.D) * ua ** self.sh_pow_aft + (self.sh_fwd - self.D) * uf ** self.sh_pow_fwd

    def Bs(self, x):
        """舷頂半寬（平面圖）：船中 B，船尾收到 end_half_aft（平板）、船頭收到 end_half_fwd（尖）。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        fa = self.eh_aft + (self.B - self.eh_aft) * (1 - ua ** self.plan_pow_aft)
        ff = self.eh_fwd + (self.B - self.eh_fwd) * (1 - uf ** self.plan_pow_fwd)
        return np.where(np.asarray(u) < 0, fa, ff)

    def b0x(self, x):
        return np.minimum(self.Bs(x), self.b0 * self.Bs(x) / self.B)

    def hb(self, x, z):
        """(x, z) 那一點的半寬；不在船殼高度範圍 ⇒ −1。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        zb, zs = self.zb(x), self.zs(x)
        t = (z - zb) / np.maximum(zs - zb, 1e-6)
        h = self.b0x(x) + (self.Bs(x) - self.b0x(x)) * np.clip(t, 0, 1) ** self.p
        ok = (t >= 0) & (t <= 1) & (x >= self.xa) & (x <= self.xf)
        return np.where(ok, h, -1.0)

    def solid(self, X0, X1, ZMAX, extra=0):
        """[x, y, z] 布林陣列：線形圍出來的實心（舷頂以上多算 extra 層 ⇒ 量牆厚時舷頂不變成蓋子）。"""
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

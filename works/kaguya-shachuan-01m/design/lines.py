# 沙船線形幾何：plan.json 的 lines ⇒ 每個 (x, z) 的半寬與實心船體
#   出處：kiara-tunis-sandal-01m/design/lines.py（改寫為 1666 中式沙船平底硬舭、方艏方艉虛梢、無龍骨外張舷側）
#   座標：X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z=0 ＝ 船底板底面）；格 k 佔 [k, k+1)、格心 k+0.5。
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


class Lines:
    """將 plan['lines'] 參數轉為連續半寬 hb(x, z)、舷頂曲線 top_z(x) 與實心船型體積 solid()。"""

    def __init__(self, plan, probe=None):
        L = {k: V(v) for k, v in plan['lines'].items() if k not in ('top', 'top_src')}
        if probe:
            for k, d in probe.items():
                if k in L:
                    L[k] = L[k] + d
        self.P = L
        self.plan = plan
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
        self.aft_overhang_x = g('aft_overhang_x')
        self.fwd_rake_x = g('fwd_rake_x')
        self.top = plan['lines']['top']
        self.top_max = max(pt[1] for pt in self.top)

    def u(self, x):
        """長度歸一參數：舯 xm=0、艉 xa=-1、艏 xf=+1。"""
        x = np.asarray(x, float)
        return np.where(x < self.xm, -(self.xm - x) / (self.xm - self.xa), (x - self.xm) / (self.xf - self.xm))

    def zb(self, x):
        """船底線：中段 [flat_aft, flat_fwd] 平底 z=0，往兩端分別依冪次起翹。"""
        x = np.asarray(x, float)
        ta = np.clip((self.flat_aft - x) / max(self.flat_aft - self.xa, 1e-6), 0, 1)
        tf = np.clip((x - self.flat_fwd) / max(self.xf - self.flat_fwd, 1e-6), 0, 1)
        return self.zt_aft * (ta ** self.rock_aft) + self.zt_fwd * (tf ** self.rock_fwd)

    def zs_base(self, x):
        """基礎舷弧線（不含尾樓加高，供橫向剖面外張計算基準）。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        return self.D + (self.sh_aft - self.D) * (ua ** self.sh_pow_aft) + (self.sh_fwd - self.D) * (uf ** self.sh_pow_fwd)

    def top_z(self, x):
        """實際船殼舷頂高度（含尾樓突升），沿 plan.lines.top 折線插值。"""
        xs = np.array([p[0] for p in self.top], float)
        zs = np.array([p[1] for p in self.top], float)
        return np.interp(np.asarray(x, float), xs, zs)

    def deck_z(self, key, x):
        """該層甲板在 x 處的地板方塊 z（第一層空氣為 deck_z + 1）。"""
        x = np.asarray(x, float)
        dk = self.plan['decks'][key]
        if key == 'hold':
            return np.full_like(x, float(dk['z']) - 1.0)
        if key == 'poop':
            return np.full_like(x, float(dk['z']) - 1.0)
        # main：船中 z_low-1，從 rise_x0 起線性升 rise_fwd
        z0 = float(dk['z_low']) - 1.0
        t = np.clip((x - float(dk['rise_x0'])) / max(float(dk['x_fwd']) - float(dk['rise_x0']), 1e-6), 0, 1)
        return np.round(z0 + float(dk['rise_fwd']) * t)

    def Bs(self, x):
        """基礎舷頂半寬：舯 B，艉收至方艉半寬 eh_aft，艏收至方艏半寬 eh_fwd。"""
        u = self.u(x)
        ua, uf = np.clip(-u, 0, 1), np.clip(u, 0, 1)
        fa = self.eh_aft + (self.B - self.eh_aft) * (1 - ua ** self.plan_pow_aft)
        ff = self.eh_fwd + (self.B - self.eh_fwd) * (1 - uf ** self.plan_pow_fwd)
        return np.where(np.asarray(u) < 0, fa, ff)

    def b0x(self, x):
        """該站平底半寬（隨平面船寬等比例縮窄，且不超過舷頂半寬）。"""
        return np.minimum(self.Bs(x), self.b0 * self.Bs(x) / self.B)

    def x_aft(self, z):
        """艉端 X：z <= zt_aft 在 xa，隨高度往上至頂端向後懸出 aft_overhang_x（中式虛梢）。"""
        t = np.clip((np.asarray(z, float) - self.zt_aft) / max(self.top_max - self.zt_aft, 1e-6), 0, 1)
        return self.xa - self.aft_overhang_x * t

    def x_fwd(self, z):
        """艏端 X：方艏從 zt_fwd 往上略往前傾 fwd_rake_x（翹頭）。"""
        t = np.clip((np.asarray(z, float) - self.zt_fwd) / max(self.sh_fwd - self.zt_fwd, 1e-6), 0, 1)
        return self.xf - self.fwd_rake_x * (1.0 - t) + (self.fwd_rake_x - 1.0) * t

    def hb(self, x, z):
        """(x, z) 處的半寬（梯形外張：平底 b0x → 舭與外張舷側 → 舷頂略再微張）。超出船體回傳 −1。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        zb = self.zb(x)
        zs_b = self.zs_base(x)
        ztop = self.top_z(x)
        t = (z - zb) / np.maximum(zs_b - zb, 1e-6)
        # 在基礎舷頂以上（如尾樓段）維持小角度外張或直立不內傾
        t_clamped = np.clip(t, 0, 1)
        h_base = self.b0x(x) + (self.Bs(x) - self.b0x(x)) * (t_clamped ** self.p)
        h = np.where(t <= 1.0, h_base, self.Bs(x) + 0.04 * (z - zs_b))
        xa_z, xf_z = self.x_aft(z), self.x_fwd(z)
        ok = (z >= zb) & (z <= ztop + 0.01) & (x >= xa_z) & (x <= xf_z)
        return np.where(ok, h, -1.0)

    def solid(self, X0, X1, ZMAX, extra=0):
        """產生 [x, y, z] 實心船型布林體積（extra>0 向上延伸供內蝕，避免舷頂被侵蝕成封閉蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(X0, X1 + 1) + 0.5
        zs = np.arange(0, ZMAX + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        zb = self.zb(X)
        ztop = self.top_z(X)
        if extra:
            Z_eval = np.minimum(Z, ztop - 0.01)
            zs_b = self.zs_base(X)
            t = np.clip((Z_eval - zb) / np.maximum(zs_b - zb, 1e-6), 0, 1)
            h_base = self.b0x(X) + (self.Bs(X) - self.b0x(X)) * (t ** self.p)
            H = np.where(Z_eval <= zs_b, h_base, self.Bs(X) + 0.04 * (Z_eval - zs_b))
            xa_z, xf_z = self.x_aft(np.minimum(Z, self.top_max)), self.x_fwd(np.minimum(Z, self.sh_fwd))
            ok = (Z >= zb) & (Z <= ztop + extra) & (X >= xa_z) & (X <= xf_z)
            H = np.where(ok, H, -1.0)
        else:
            H = self.hb(X, Z)
        dy = np.abs(np.arange(W) - self.YC)
        return dy[None, :, None] <= H[:, None, :]

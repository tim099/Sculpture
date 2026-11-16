# 塔爾塔納 線形（TASK-1299 新圖紙）：plan.json 的 lines 參數 ⇒ 每個 (x, z) 的半寬、船的外形
#   參考來源：ame-labelle-01m/design/lines.py，調整為 17 世紀地中海雙桅商用 tartane（平底圓舭、高孤前傾艏柱、低腰＋短尾樓）
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_plan(design=HERE):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Lines:
    """plan['lines'] 幾何計算（支援 numpy 陣列）。"""

    def __init__(self, plan):
        L = plan['lines']
        self.P = L
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k]['v'])
        self.B2 = g('half_beam')
        self.z_keel_top = g('keel_top')
        self.keel_hw = g('keel_half')
        self.z_mb = g('max_breadth_z')
        self.th = g('tumblehome')
        self.z_th_ref = g('tumblehome_ref_z')
        self.th_pow = g('tumblehome_pow')
        self.th_up = g('tumblehome_above_per_cell')
        self.p_bilge = g('bilge_pow')
        self.plan_h = g('plan_half')
        self.astilla = g('astilla')
        self.s_a, self.s_f = g('s_aft'), g('s_fwd')
        self.x_sp0, self.sp_rake = g('sternpost_x0'), math.radians(g('sternpost_rake_deg'))
        self.z_wt = g('wing_transom_z')
        self.rt = g('transom_ratio')
        self.x_ff = g('forefoot_x')
        self.stem_rake, self.stem_ref_z, self.stem_pow = g('stem_rake'), g('stem_ref_z'), g('stem_pow')
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.k_bow_lo, self.k_bow_hi = g('bow_pow_low'), g('bow_pow_high')
        self.q_aft = g('aft_pow')
        self.top = L['top']

    def x_stem(self, z):
        z = np.clip(np.asarray(z, float), 0, None)
        return self.x_ff + self.stem_rake * (z / self.stem_ref_z) ** self.stem_pow

    def x_post(self, z):
        return self.x_sp0 - np.asarray(z, float) * math.tan(self.sp_rake)

    def x_aft(self, z):
        return self.x_post(z)

    def hb_mid(self, z, zr):
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        e = np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        ph = self.keel_hw + (self.plan_h - self.keel_hw) * (1 - e)
        zf = zr + self.astilla * (1 - e)
        floor = self.keel_hw + (ph - self.keel_hw) * np.clip((z - zr) / np.maximum(0.5, zf - zr), 0, 1)
        t = np.clip((z - zf) / np.maximum(1.0, self.z_mb - zf), 0, 1)
        p = self.p_bilge - (self.p_bilge - 1.05) * e
        f = (1 - (1 - t) ** p) ** (1 / p)
        f = f ** (1 + 1.2 * e)
        bilge = ph + (self.B2 - ph) * f
        u = np.clip((z - self.z_mb) / (self.z_th_ref - self.z_mb), 0, 1)
        high = self.B2 - self.th * u ** self.th_pow - self.th_up * np.clip(z - self.z_th_ref, 0, None)
        return np.where(z < zr, self.keel_hw, np.where(z < zf, floor, np.where(z <= self.z_mb, bilge, high)))

    def s_of(self, x, z):
        xa, xs = self.x_aft(z), self.x_stem(z)
        return (np.asarray(x, float) - xa) / np.maximum(1.0, xs - xa)

    def zr(self, s):
        aft = self.z_keel_top + (self.zr_aft - self.z_keel_top) * np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2
        fwd = self.z_keel_top + (self.zr_fwd - self.z_keel_top) * np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 3
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, self.z_keel_top))

    def breadth_k(self, s, z):
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        c = self.B2 / 60.5
        wide = 40.0 * c * (1 - ua)
        rt = self.rt * smoothstep((z - (self.z_wt - 12 * c - wide)) / (12.0 * c + wide))
        aft = rt + (1 - rt) * (1 - ua ** self.q_aft)
        k = self.k_bow_lo + (self.k_bow_hi - self.k_bow_lo) * np.clip((z - 15 * c) / (60.0 * c), 0, 1)
        uf = np.clip((s - self.s_f) / (1 - self.s_f), 0, 1)
        fwd = (1 - uf ** k) ** (1 / k)
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, 1.0))

    def hb(self, x, z):
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        s = self.s_of(x, z)
        zr = self.zr(s)
        mid = self.hb_mid(z, zr)
        h = self.keel_hw + (mid - self.keel_hw) * self.breadth_k(s, z)
        h = np.where(z < zr, self.keel_hw, h)
        inside = (s >= 0) & (s <= 1)
        return np.where(inside, h, -1.0)

    def top_z(self, x):
        pts = np.array(self.top, float)
        return np.interp(np.asarray(x, float), pts[:, 0], pts[:, 1])

    def solid(self, x0, x1, zmax, extra_top=0):
        W = 2 * self.YC + 1
        xs = np.arange(x0, x1 + 1) + 0.5
        zs = np.arange(0, zmax + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        H = self.hb(X, Z)
        top = self.top_z(xs)[:, None] + extra_top
        H = np.where(Z <= top + 0.5, H, -1.0)
        dy = np.abs(np.arange(W) - self.YC)[None, :, None]
        return dy <= H[:, None, :]

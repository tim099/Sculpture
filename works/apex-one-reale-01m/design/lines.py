# 皇家號 La Réale 線形（TASK-0695 新圖紙）：plan.json 的 lines ⇒ 每個 (x, z) 的半寬、船的外形
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 = 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   「在不在船裡」：|y − YC| ≤ hb(x, z)（拿格的整數偏移比，YC 那一格是中線）⇒ 兩舷逐格對稱。
#   結構照收穫號（calli-cosecha-01m/design/lines.py：船中剖面 × 長度方向收縮），幾何換成槳帆船：
#     · 船中剖面：平底（1691 手冊：船中底肋平）＋圓舭，最寬在甲板邊（Réale 橫剖面圖：甲板就在水線上一點、側邊到頂幾乎直）；
#     · 長度方向：中段很長一段平行，兩頭細；船尾頂上留 2 goues 寬（Hobier）；
#     · 艏柱一段圓弧（跟龍骨相切）、艉柱往上往後彎到幾乎直立；
#     · 舷頂 ＝ 甲板邊，船中低、船尾翹得多、船頭翹一點。
#   被 draft_lines.py 與之後的階段 import；只讀 plan.json、不碰作品。
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
    """plan['lines'] 的數字 ⇒ 幾何函式（全部吃 numpy 陣列）。"""

    def __init__(self, plan, probe=None):
        L = {k: (v['v'] if isinstance(v, dict) and 'v' in v else v) for k, v in plan['lines'].items()}
        if probe:
            for k, d in probe.items():
                L[k] = L[k] + d
        self.P = L
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k])
        self.x_sh, self.z_sh = g('sternpost_head_x'), g('sternpost_head_z')
        self.x_st, self.z_st = g('stem_head_x'), g('stem_head_z')
        self.x_ka, self.x_kf = g('keel_aft_x'), g('keel_fwd_x')
        self.z_keel_top, self.keel_hw = g('keel_top'), g('keel_half')
        self.B2 = g('half_beam')
        self.z_side = g('deck_side_z')            # 船中舷頂（甲板邊）
        self.plan_h = g('floor_half')             # 平底半寬
        self.astilla = g('floor_rise')            # 平底外緣比龍骨頂高幾格
        self.p_bilge = g('bilge_pow')
        self.s_a, self.s_f = g('s_aft'), g('s_fwd')
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.q_aft, self.q_fwd = g('aft_pow'), g('fwd_pow')
        self.rt = g('stern_top_ratio')
        self.sheer_aft, self.sheer_fwd = g('sheer_aft'), g('sheer_fwd')
        self.sheer_sa, self.sheer_sf = g('sheer_s_aft'), g('sheer_s_fwd')
        # 艏柱：圓心 (keel_fwd_x, R) 的圓弧，z 0 跟龍骨相切、經過艏柱頂 ⇒ R 由兩點解出
        dx = self.x_st - self.x_kf
        self.R_stem = (dx * dx + self.z_st * self.z_st) / (2 * self.z_st)

    # ── 兩端（外板外緣） ──
    def x_fwd(self, z):
        z = np.clip(np.asarray(z, float), 0, self.z_st)
        R = self.R_stem
        return self.x_kf + np.sqrt(np.clip(R * R - (R - z) ** 2, 0, None))

    def x_aft(self, z):
        """艉柱後緣：從龍骨後端往上往後彎，到艉柱頂直立（x ＝ x_ka − (x_ka − x_sh)·(1 − (1 − t)²)）。"""
        t = np.clip(np.asarray(z, float) / self.z_sh, 0, 1)
        return self.x_ka - (self.x_ka - self.x_sh) * (1 - (1 - t) ** 2)

    # ── 剖面 ──
    def hb_mid(self, z, zr):
        """船中剖面在高度 z 的半寬；zr ＝ 船底從哪個高度開始（兩端的 deadwood 往上抬 ⇒ 剖面往 V 形收）。"""
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        e = np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        ph = self.keel_hw + (self.plan_h - self.keel_hw) * (1 - e)
        zf = zr + self.astilla * (1 - e)
        floor = self.keel_hw + (ph - self.keel_hw) * np.clip((z - zr) / np.maximum(0.5, zf - zr), 0, 1)
        t = np.clip((z - zf) / np.maximum(1.0, self.z_side - zf), 0, 1)
        p = self.p_bilge - (self.p_bilge - 1.05) * e
        f = (1 - (1 - t) ** p) ** (1 / p)
        f = f ** (1 + 1.0 * e)
        bilge = ph + (self.B2 - ph) * f
        return np.where(z < zr, self.keel_hw, np.where(z < zf, floor, np.where(z <= self.z_side, bilge, self.B2)))

    def s_of(self, x, z):
        xa, xs = self.x_aft(z), self.x_fwd(z)
        return (np.asarray(x, float) - xa) / np.maximum(1.0, xs - xa)

    def zr(self, s):
        aft = self.z_keel_top + (self.zr_aft - self.z_keel_top) * np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2
        fwd = self.z_keel_top + (self.zr_fwd - self.z_keel_top) * np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 2
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, self.z_keel_top))

    def breadth_k(self, s, z):
        """長度方向的收縮（0..1）。船尾頂上留 stern_top_ratio 的寬（2 goues，Hobier），往下收到艉柱；船頭 superellipse。"""
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        rt = self.rt * smoothstep((z - (self.z_side - 14)) / 14.0)
        aft = rt + (1 - rt) * (1 - ua ** self.q_aft) ** (1 / self.q_aft)
        uf = np.clip((s - self.s_f) / (1 - self.s_f), 0, 1)
        fwd = (1 - uf ** self.q_fwd) ** (1 / self.q_fwd)
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, 1.0))

    def hb(self, x, z):
        """(x, z) 的半寬（格；< 0 ＝ 不在船長範圍）。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        s = self.s_of(x, z)
        zr = self.zr(s)
        mid = self.hb_mid(z, zr)
        h = self.keel_hw + (mid - self.keel_hw) * self.breadth_k(s, z)
        h = np.where(z < zr, self.keel_hw, h)
        inside = (s >= 0) & (s <= 1)
        return np.where(inside, h, -1.0)

    def sheer(self, x):
        """舷頂（甲板邊最上一格的 z）：船中 deck_side_z，船尾、船頭照 s 抬起（二次）。用 z ＝ 舷頂那一層的 s。"""
        x = np.asarray(x, float)
        s = (x - self.x_aft(self.z_side)) / (self.x_fwd(self.z_side) - self.x_aft(self.z_side))
        a = self.sheer_aft * np.clip((self.sheer_sa - s) / self.sheer_sa, 0, 1) ** 2
        f = self.sheer_fwd * np.clip((s - self.sheer_sf) / (1 - self.sheer_sf), 0, 1) ** 2
        return self.z_side + a + f

    # ── 體積 ──
    def solid(self, x0, x1, zmax, extra_top=0):
        """外形實心（布林陣列 [x, y, z]）；extra_top > 0 ⇒ 舷頂以上多算幾層（挖牆時不讓舷頂變成一層蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(x0, x1 + 1) + 0.5
        zs = np.arange(0, zmax + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        # 舷頂以上照舷頂那一層的半寬往上延（側邊直立），兩端照柱的外緣切
        top = self.sheer(xs)[:, None]
        Zc = np.minimum(Z, top + 0.5)
        H = self.hb(X, Zc)
        H = np.where((X >= self.x_aft(Z)) & (X <= self.x_fwd(Z)), H, -1.0)
        H = np.where(Z <= top + 0.5 + extra_top, H, -1.0)
        dy = np.abs(np.arange(W) - self.YC)[None, :, None]
        return dy <= H[:, None, :]

# 出處：erina-oxford-01m/design/lines.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 線形（TASK-0972 新圖紙 01）：plan.json 的 lines 參數 ⇒ 每個 (x, z) 的半寬、船的外形
#   座標：X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 ＝ 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   「在不在船裡」：|y − YC| ≤ hb(x, z)（拿格的整數偏移比，YC 那一格是中線）⇒ 兩舷逐格對稱。
#   來源：calli-cosecha-01m/design/lines.py（船中剖面 × 長度方向收縮；原型 gura-tridente-01m/design/hull_lines.py）。
#   換成 1650 年代英國 frigate 的地方：
#     · 艏柱是 1/4 橢圓（往前倒、往上越來越直，一路倒到艏柱頭），不是圓弧接直立；
#     · 船尾是方艉（square tuck）：wing transom 以下到約水線那一段船尾板也是平的（breadth_k 的 transom 帶往下拉）；
#     · 舷弧明顯、炮甲板以上 tumblehome 強；舷頂折線照 plan.decks 的每一層甲板＋舷牆。
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

    def __init__(self, plan):
        L = plan['lines']
        self.P = L
        self.plan = plan
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
        self.x_ff, self.st_a, self.st_b = g('forefoot_x'), g('stem_a'), g('stem_b')
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.k_bow_lo, self.k_bow_hi = g('bow_pow_low'), g('bow_pow_high')
        self.q_aft = g('aft_pow')
        self.hollow = g('end_hollow')
        self.top = L['top']

    # ── 兩端 ──
    def x_stem(self, z):
        """艏柱前緣（外板外面）的 x：1/4 橢圓 —— z 0 跟龍骨相切、到 stem_b 變直立。"""
        z = np.clip(np.asarray(z, float), 0, self.st_b)
        u = 1 - z / self.st_b
        return self.x_ff + self.st_a * np.sqrt(np.clip(1 - u * u, 0, None))

    def x_post(self, z):
        """艉柱後緣的 x（往上往後倒）。"""
        return self.x_sp0 - np.asarray(z, float) * math.tan(self.sp_rake)

    def x_aft(self, z):
        return self.x_post(z)

    # ── 剖面 ──
    def hb_mid(self, z, zr, e=None):
        """船中剖面在高度 z 的半寬；zr ＝ 船底從哪個高度開始（兩端的 deadwood 往上抬，剖面往 V 形收）。
        船中：底肋平的那一段（plan_half）從龍骨往外、抬 astilla ⇒ 圓舭接到最寬處 ⇒ 往上 tumblehome 內收。"""
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        # e：這一站離船中多遠（0 船中 … 1 船頭／船尾最末）—— 兩頭各照自己的 deadwood 高度算（收穫號是兩頭共用最高那個）⇒ 船頭也收成 V
        e = np.asarray(e, float) if e is not None else np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        ph = self.keel_hw + (self.plan_h - self.keel_hw) * (1 - e)
        zf = zr + self.astilla * (1 - e)
        floor = self.keel_hw + (ph - self.keel_hw) * np.clip((z - zr) / np.maximum(0.5, zf - zr), 0, 1)
        t = np.clip((z - zf) / np.maximum(1.0, self.z_mb - zf), 0, 1)
        p = self.p_bilge - (self.p_bilge - 1.0) * e
        f = (1 - (1 - t) ** p) ** (1 / p)
        f = f ** (1 + self.hollow * e)   # 兩頭往下凹（高腳杯形的 deadwood 肩）
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
        """長度方向的收縮（0..1）。船尾：方艉 —— transom 帶（tuck 以上）留 transom_ratio 的寬、以下收到艉柱；船頭：superellipse（上面鈍、下面尖）。"""
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        base = 1 - ua ** self.q_aft
        # 方艉：tuck（z_wt − 16）以上撐到 transom_ratio 的寬 ⇒ 船尾最末那一站是 tuck 的折角；
        #   往前過渡帶越拉越寬（6 ＋ 40·(1 − ua) 格）⇒ 水線上下是平順的高腳杯形，水線以上的船尾照樣寬（17 世紀英國船寬的上部船尾）
        band = smoothstep((z - (self.z_wt - 16)) / (6.0 + 40.0 * (1 - ua)))
        aft = base + (1 - base) * self.rt * band
        k = self.k_bow_lo + (self.k_bow_hi - self.k_bow_lo) * np.clip((z - 10) / 40.0, 0, 1)
        uf = np.clip((s - self.s_f) / (1 - self.s_f), 0, 1)
        fwd = (1 - uf ** k) ** (1 / k)
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, 1.0))

    def hb(self, x, z):
        """(x, z) 的半寬（格；< 0 ＝ 不在船長範圍）。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        s = self.s_of(x, z)
        zr = self.zr(s)
        e = np.where(s < self.s_a, np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2,
                     np.where(s > self.s_f, np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 3, 0.0))
        mid = self.hb_mid(z, zr, e)
        h = self.keel_hw + (mid - self.keel_hw) * self.breadth_k(s, z)
        h = np.where(z < zr, self.keel_hw, h)
        inside = (s >= 0) & (s <= 1)
        return np.where(inside, h, -1.0)

    def top_z(self, x):
        pts = np.array(self.top, float)
        return np.interp(np.asarray(x, float), pts[:, 0], pts[:, 1])

    # ── 甲板（第一層空氣的 z）──
    def gun_z(self, x):
        d = self.plan['decks']['gun']
        x = np.asarray(x, float)
        a = d['z_low'] + d['rise_aft'] * np.clip((d['x_low'] - x) / (d['x_low'] - d['x_aft']), 0, None) ** 2
        f = d['z_low'] + d['rise_fwd'] * np.clip((x - d['x_low']) / (d['x_fwd'] - d['x_low']), 0, None) ** 2
        return np.where(x < d['x_low'], a, f)

    def deck_z(self, name, x):
        """後甲板、艉樓、艏樓 ＝ 下面那一層 ＋ over（跟著舷弧）。"""
        D = self.plan['decks']
        if name == 'gun':
            return self.gun_z(x)
        if name == 'orlop':
            return np.full(np.shape(x), float(D['orlop']['z']))
        if name == 'poop':
            return self.deck_z('qd', x) + D['poop']['over']
        return self.gun_z(x) + D[name]['over']

    # ── 體積 ──
    def solid(self, x0, x1, zmax, extra_top=0):
        """外形實心（布林陣列 [x, y, z]）；extra_top > 0 ⇒ 舷頂以上多算幾層（挖牆時不讓舷頂變成一層蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(x0, x1 + 1) + 0.5
        zs = np.arange(0, zmax + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        H = self.hb(X, Z)
        top = self.top_z(xs)[:, None] + extra_top
        H = np.where(Z <= top + 0.5, H, -1.0)
        dy = np.abs(np.arange(W) - self.YC)[None, :, None]
        return dy <= H[:, None, :]

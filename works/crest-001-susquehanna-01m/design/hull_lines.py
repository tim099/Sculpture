# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/hull_lines.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 線形（TASK-0606 新圖紙）：plan.json 的 lines 參數 ⇒ 每個 (x, z) 的半寬、船的外形、4 格牆
#   抄自三叉戟號 gura-tridente-01m/design/hull_lines.py（gura，TASK-0554）；改：船尾 deadwood 開螺旋槳 aperture（plan.aperture）。
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 = 龍骨底面）；格 k 佔 [k, k+1)。
#   「在不在船裡」：|y − YC| ≤ hb(x, z)（拿格的整數偏移比，YC 那一格是中線）⇒ 兩舷逐格對稱。
#   被 draft_lines.py（圖紙、讀數、清單）與之後的階段 import；只讀 plan.json、不碰作品。
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
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k]['v'])
        self.B2 = g('half_beam')            # 最寬處半寬（含外板）
        self.z_keel_top = g('keel_top')     # 龍骨頂 ＝ 船底板開始
        self.keel_hw = g('keel_half')       # 龍骨半寬
        self.z_mb = g('max_breadth_z')      # 最寬的高度
        self.th = g('tumblehome')           # z_th_ref 那一格往內收幾格（每舷）
        self.z_th_ref = g('tumblehome_ref_z')
        self.th_pow = g('tumblehome_pow')
        self.p_bilge = g('bilge_pow')
        self.s_a, self.s_f = g('s_aft'), g('s_fwd')
        self.x_sp0, self.sp_rake = g('sternpost_x0'), math.radians(g('sternpost_rake_deg'))
        self.z_wt = g('wing_transom_z')
        self.counter = g('counter_aft')     # wing transom 以上 counter 往後挑幾格
        self.z_cnt = g('counter_top_z')
        self.stern_rake = math.radians(g('stern_rake_deg'))
        self.rt = g('transom_ratio')        # transom 的半寬 ÷ 船中半寬
        self.x_ff, self.R_ff, self.stem_rake = g('forefoot_x'), g('forefoot_r'), math.radians(g('stem_rake_deg'))
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.k_bow_lo, self.k_bow_hi = g('bow_pow_low'), g('bow_pow_high')
        self.q_aft = g('aft_pow')
        self.top = L['top']                 # 舷頂高度：[[x, z], …] 折線（照 x 內插）
        self.ap = plan.get('aperture')      # 螺旋槳 aperture：艉柱（舵柱）往前 x_aft_off 起、len 格長、z0..z1
        self.rs = L.get('round_stern')      # 圓船尾：{r, z0, z1}

    # ── 兩端 ──
    def x_stem(self, z):
        """艏柱前緣（外板外面）的 x：forefoot 圓弧，往上照 stem_rake 微微前傾。"""
        z = np.asarray(z, float)
        R = self.R_ff
        # 蘇士奎哈納號改：圓弧只走到切線斜率 ＝ stem_rake 那一點（z_t），再接直線 ⇒ 艏柱沒有折角（三叉戟號原版圓弧走到垂直再接斜線）
        th = math.pi / 2 - self.stem_rake
        z_t = R * (1 - math.cos(th))
        x_t = self.x_ff + R * math.sin(th)
        arc = self.x_ff + np.sqrt(np.clip(R * R - (R - np.clip(z, 0, R)) ** 2, 0, None))
        up = x_t + (z - z_t) * math.tan(self.stem_rake)
        return np.where(z <= z_t, arc, up)

    def x_post(self, z):
        """艉柱後緣的 x（往上往後倒）。"""
        return self.x_sp0 - np.asarray(z, float) * math.tan(self.sp_rake)

    def x_aft(self, z):
        """船殼最後面：wing transom 以下 ＝ 艉柱；以上 counter 往後挑、再照 stern_rake 往後倒（船尾面）。"""
        z = np.asarray(z, float)
        xp = self.x_post(z)
        t = smoothstep((z - self.z_wt) / max(1.0, self.z_cnt - self.z_wt))
        x_cnt = self.x_post(self.z_wt) - self.counter * t
        above = self.x_post(self.z_wt) - self.counter - (z - self.z_cnt) * math.tan(self.stern_rake)
        return np.where(z < self.z_wt, xp, np.where(z < self.z_cnt, x_cnt, above))

    # ── 剖面 ──
    def hb_mid(self, z, zr):
        """船中剖面在高度 z 的半寬；zr ＝ 圓底從哪個高度開始（兩端的 deadwood 往上抬）。
        兩端（zr 抬得越高）剖面越尖：圓底的指數往 1 收（V 形），再加一點 hollow（酒杯形的 garboard）⇒ 跟 deadwood 平順接上、不出一層平台。"""
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        t = np.clip((z - zr) / np.maximum(1.0, self.z_mb - zr), 0, 1)
        e = np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        p = self.p_bilge - (self.p_bilge - 1.05) * e
        f = (1 - (1 - t) ** p) ** (1 / p)
        f = f ** (1 + 1.2 * e)
        low = self.keel_hw + (self.B2 - self.keel_hw) * f
        u = np.clip((z - self.z_mb) / (self.z_th_ref - self.z_mb), 0, None)
        high = self.B2 - self.th * u ** self.th_pow
        return np.where(z < zr, self.keel_hw, np.where(z <= self.z_mb, low, high))

    def s_of(self, x, z):
        xa, xs = self.x_aft(z), self.x_stem(z)
        return (np.asarray(x, float) - xa) / np.maximum(1.0, xs - xa)

    def zr(self, s):
        aft = self.z_keel_top + (self.zr_aft - self.z_keel_top) * np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2
        fwd = self.z_keel_top + (self.zr_fwd - self.z_keel_top) * np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 3
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, self.z_keel_top))

    def breadth_k(self, s, z, d_aft=None):
        """長度方向的收縮（0..1）。船尾：wing transom 以上留 transom 的寬、以下收到艉柱；船頭：橢圓（上面鈍、下面尖）。"""
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        # transom 的寬只在船尾那一站是一道 counter（16 格內轉過去）；越往前，轉的那一段越長、越低 ⇒ buttock 平順地爬上 counter
        wide = 50.0 * (1 - ua)
        rt = self.rt * smoothstep((z - (self.z_wt - 8 - wide)) / (16.0 + wide))
        aft = rt + (1 - rt) * (1 - ua ** self.q_aft)
        if self.rs and d_aft is not None:
            # 蘇士奎哈納號改：圓船尾 —— 水線以上俯視收成半徑 r 的圓弧（離船尾端 d 格），z0 → z1 之間從細的 run 平順換過去
            R = float(self.rs['r'])
            u = np.clip((R - d_aft) / R, 0, 1)
            k_round = np.sqrt(np.clip(1 - u * u, 0, 1))
            t = smoothstep((z - self.rs['z0']) / float(self.rs['z1'] - self.rs['z0']))
            aft = (1 - t) * aft + t * np.maximum(aft, k_round)
        k = self.k_bow_lo + (self.k_bow_hi - self.k_bow_lo) * np.clip((z - 20) / 80.0, 0, 1)
        uf = np.clip((s - self.s_f) / (1 - self.s_f), 0, 1)
        fwd = (1 - uf ** k) ** (1 / k)
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, 1.0))

    def hb(self, x, z):
        """(x, z) 的半寬（格；< 0 ＝ 不在船長範圍）。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        s = self.s_of(x, z)
        zr = self.zr(s)
        mid = self.hb_mid(z, zr)
        h = self.keel_hw + (mid - self.keel_hw) * self.breadth_k(s, z, x - self.x_aft(z))
        h = np.where(z < zr, self.keel_hw, h)
        inside = (s >= 0) & (s <= 1) & ~self.in_aperture(x, z)
        return np.where(inside, h, -1.0)

    def in_aperture(self, x, z):
        """螺旋槳 aperture（艉柱與螺旋槳柱之間的開口）：艉柱往前 x_aft_off 格起、len 格長、z0 ≤ z < z1。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        if not self.ap:
            return np.zeros(np.broadcast(x, z).shape, bool)
        a = self.x_post(z) + self.ap['x_aft_off']
        return (x >= a) & (x < a + self.ap['len']) & (z >= self.ap['z0']) & (z < self.ap['z1'])

    def top_z(self, x):
        pts = np.array(self.top, float)
        return np.interp(np.asarray(x, float), pts[:, 0], pts[:, 1])

    # ── 體積 ──
    def solid(self, x0, x1, zmax, extra_top=0):
        """外形實心（布林陣列 [x, y, z]，x0..x1、y 全寬、z 0..zmax）；extra_top > 0 ⇒ 舷頂以上多算幾層（挖牆時不讓舷頂變成一層蓋子）。"""
        W = 2 * self.YC + 1
        xs = np.arange(x0, x1 + 1) + 0.5
        zs = np.arange(0, zmax + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        H = self.hb(X, Z)
        top = self.top_z(xs)[:, None] + extra_top
        H = np.where(Z <= top + 0.5, H, -1.0)
        dy = np.abs(np.arange(W) - self.YC)[None, :, None]
        return dy <= H[:, None, :]          # 龍骨不另外算：z < zr（≥ 龍骨頂）那幾層 hb ＝ keel_half，從艉柱一路到 forefoot

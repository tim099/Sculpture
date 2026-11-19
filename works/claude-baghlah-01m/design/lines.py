# 出處：apex-two-galeon-01m/design/lines.py（康塞普西翁號，TASK-0969；它再往上是 gura-pinas-01m、calli-cosecha-01m）—— 照抄後改成星辰號（TASK-0019）
# 星辰號（al-Najm）線形（TASK-0019 步驟 3 新圖紙）：plan.json 的 lines 參數 ⇒ 每個 (x, z) 的半寬、船的外形
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 = 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   「在不在船裡」：|y − YC| ≤ hb(x, z)（拿格的整數偏移比，YC 那一格是中線）⇒ 兩舷逐格對稱。
#   跟康塞普西翁號不同的地方（巴格拉，照 Pâris 1843 Pl. 2 fig. 7–9）：
#     · 艏柱是一條直線、很斜（離水平約 28°），從龍骨前端一路伸到舷頂（stem_run_per_z）；
#     · 船尾：艉柱直的往後倒；艉柱頂以上是一片低而斜的 counter，直線往後伸到 taffrail（counter.shape = ramp）；
#     · 船中剖面：V 形船底（plan 窄、astilla 高）接圓舭，兩舷幾乎直到舷頂（fig. 9 沒有 tumblehome）；
#     · 舷頂：top_curve 的節點之間預設直線（舷弧），只有 smooth 列出的那幾段走 smoothstep（船尾樓前緣的落差）；
#     · breadth_k 裡寫死的過渡長度照船的大小縮（康塞普西翁號 舷頂 z 164、這艘 z 87）：船尾 wide 40 → 20、6 → 4、12 → 8；船頭 k 的高度範圍 z 15..75 → 10..60。
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
        self.YC = plan['space']['yc']
        g = lambda k: float(L[k]['v'])
        self.B2 = g('half_beam')             # 最寬處半寬（含外板）
        self.z_keel_top = g('keel_top')      # 龍骨頂
        self.keel_hw = g('keel_half')        # 龍骨半寬
        self.z_mb = g('max_breadth_z')       # 最寬的高度
        self.th = g('tumblehome')            # 到 tumblehome_ref_z 每舷內收幾格
        self.z_th_ref = g('tumblehome_ref_z')
        self.th_pow = g('tumblehome_pow')
        self.th_up = g('tumblehome_above_per_cell')   # ref 以上每往上一格再往內收幾格
        self.p_bilge = g('bilge_pow')
        self.plan_h = g('plan_half')         # V 形船底外緣的半寬
        self.astilla = g('astilla')          # V 形船底外緣比龍骨頂高幾格（rise of floor）
        self.s_a, self.s_f = g('s_aft'), g('s_fwd')
        self.x_sp0, self.sp_rake = g('sternpost_x0'), math.radians(g('sternpost_rake_deg'))
        self.z_wt = g('wing_transom_z')
        self.rt = g('transom_ratio')
        self.x_ff, self.stem_k = g('forefoot_x'), g('stem_run_per_z')
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.k_bow_lo, self.k_bow_hi = g('bow_pow_low'), g('bow_pow_high')
        self.q_aft = g('aft_pow')
        self.ctr = L.get('counter')          # 艉柱頂以上的 counter（往後外伸）
        self.tc = L['top_curve']             # 舷頂
        xs = np.arange(0, plan['space']['x']) + 0.5
        self.top_max = float(np.max(self.top_z(xs)))

    # ── 兩端 ──
    def x_stem(self, z):
        """艏柱前緣（外板外面）的 x：龍骨前端 forefoot_x 起一條直線，每往上一格往前 stem_run_per_z 格（fig. 7）。"""
        z = np.clip(np.asarray(z, float), 0, None)
        return self.x_ff + z * self.stem_k

    def x_post(self, z):
        """艉柱後緣的 x（往上往後倒）。"""
        return self.x_sp0 - np.asarray(z, float) * math.tan(self.sp_rake)

    def counter(self, z):
        """counter 往後外伸幾格：z0 以下 0；z0..z1 照 shape 走到 c（ramp ＝ 直線 ⇒ 一片斜的 counter；smoothstep ＝ 兩頭相切）；z1 以上 c。"""
        z = np.asarray(z, float)
        if not self.ctr:
            return np.zeros(z.shape)
        C = self.ctr
        t = np.clip((z - C['z0']) / float(C['z1'] - C['z0']), 0, 1)
        if C.get('shape', 'smoothstep') == 'ramp':
            return float(C['c']) * t
        return float(C['c']) * smoothstep(t)

    def x_aft(self, z):
        """船殼最後面：艉柱線再往後外伸 counter。"""
        return self.x_post(z) - self.counter(z)

    # ── 剖面 ──
    def hb_mid(self, z, zr):
        """船中剖面在高度 z 的半寬；zr ＝ 船底從哪個高度開始（兩端的 deadwood 往上抬，剖面往 V 形收）。
        船中：V 形船底（龍骨往外、astilla 抬到 plan_half）⇒ 圓舭（superellipse）接到最寬處 ⇒ 以上照 tumblehome。
        兩端（zr 抬得越高）plan 縮成 0、圓舭的指數往 1 收 ⇒ V 形，跟 deadwood 平順接上。"""
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        e = np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        ph = self.keel_hw + (self.plan_h - self.keel_hw) * (1 - e)          # V 形船底外緣的半寬
        zf = zr + self.astilla * (1 - e)                                     # V 形船底外緣的高度
        floor = self.keel_hw + (ph - self.keel_hw) * np.clip((z - zr) / np.maximum(0.5, zf - zr), 0, 1)
        t = np.clip((z - zf) / np.maximum(1.0, self.z_mb - zf), 0, 1)
        p = self.p_bilge - (self.p_bilge - 1.05) * e
        f = (1 - (1 - t) ** p) ** (1 / p)
        f = f ** (1 + 1.2 * e)
        bilge = ph + (self.B2 - ph) * f
        u = np.clip((z - self.z_mb) / max(1.0, self.z_th_ref - self.z_mb), 0, 1)
        high = self.B2 - self.th * u ** self.th_pow - self.th_up * np.clip(z - self.z_th_ref, 0, None)
        return np.where(z < zr, self.keel_hw, np.where(z < zf, floor, np.where(z <= self.z_mb, bilge, high)))

    def s_of(self, x, z):
        """長度方向的比例：0 ＝ 艉柱線（不是 counter 的最後面 ⇒ counter 不動船身其他地方的寬）、1 ＝ 艏柱。"""
        xa, xs = self.x_post(z), self.x_stem(z)
        return (np.asarray(x, float) - xa) / np.maximum(1.0, xs - xa)

    def zr(self, s):
        aft = self.z_keel_top + (self.zr_aft - self.z_keel_top) * np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2
        fwd = self.z_keel_top + (self.zr_fwd - self.z_keel_top) * np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 3
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, self.z_keel_top))

    def breadth_k(self, s, z):
        """長度方向的收縮（0..1）。船尾：wing transom 以上留船尾的寬（transom_ratio）、以下收到艉柱；船頭：superellipse（上面鈍、下面尖）。"""
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        wide = 20.0 * (1 - ua)
        rt = self.rt * smoothstep((z - (self.z_wt - 4 - wide)) / (8.0 + wide))
        aft = rt + (1 - rt) * (1 - ua ** self.q_aft)
        k = self.k_bow_lo + (self.k_bow_hi - self.k_bow_lo) * np.clip((z - 10) / 50.0, 0, 1)
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
        h = self.keel_hw + (mid - self.keel_hw) * self.breadth_k(s, z)
        h = np.where(z < zr, self.keel_hw, h)
        st = self.P.get('stern_tumble')
        if st:            # 船尾那一段（s < s_aft）z0 以上再往裡收（船尾樓上窄）
            ua = np.clip(1 - s / self.s_a, 0, 1)
            h = h - float(st['k']) * np.clip(z - float(st['z0']), 0, None) * ua ** float(st['pow'])
        inside = (s >= 0) & (s <= 1)
        if self.ctr:      # counter：艉柱線後面那一段照 s ＝ 0 的寬往後伸，俯視往兩角收 round（圓的船尾）
            xp = self.x_post(z)
            c = self.counter(z)
            u = np.clip((xp - x) / max(1.0, float(self.ctr['c'])), 0, 1)
            h = np.where(s < 0, self.keel_hw + (h - self.keel_hw) * (1 - float(self.ctr['round']) * u ** 2), h)
            inside = (x >= xp - c) & (s <= 1)
        return np.where(inside, h, -1.0)

    def top_z(self, x):
        """舷頂：節點之間直線（舷弧）；smooth 列出的段（節點 i → i+1）走 smoothstep；再加 rise（((離起點) ÷ (到終點))^pow × dz）。"""
        x = np.asarray(x, float)
        K = np.array(self.tc['knots'], float)
        i = np.clip(np.searchsorted(K[:, 0], x) - 1, 0, len(K) - 2)
        t = np.clip((x - K[i, 0]) / (K[i + 1, 0] - K[i, 0]), 0, 1)
        sm = np.isin(i, np.array(self.tc.get('smooth', []), int))
        t = np.where(sm, smoothstep(t), t)
        z = K[i, 1] + (K[i + 1, 1] - K[i, 1]) * t
        for r in self.tc.get('rise', []):
            u = np.clip((x - r['from']) / float(r['to'] - r['from']), 0, 1)
            z = z + r['dz'] * u ** r['pow']
        return z

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

# 直接出處：apex-two-galeon-01m/design/lines.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/lines.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/lines.py（收穫號，照抄後改成聖羅曼號 —— TASK-0970）
# 聖羅曼號 線形（TASK-0590 新圖紙）：plan.json 的 lines 參數 ⇒ 每個 (x, z) 的半寬、船的外形
#   座標：X 船長（船頭 +X）、Y 船寬（中線 = 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z 0 = 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
#   「在不在船裡」：|y − YC| ≤ hb(x, z)（拿格的整數偏移比，YC 那一格是中線）⇒ 兩舷逐格對稱。
#   作法參考 gura-tridente-01m/design/hull_lines.py（船中剖面 × 長度方向收縮），幾何換成西班牙大帆船：
#     · 艏柱是一整段大圓弧（roda 的 lanzamiento），艉柱直的往後倒；
#     · 船尾 wing transom 以上是一整片平的 espejo（照艉柱的斜度往後倒），以下收到艉柱；
#     · 最寬處在第一層甲板附近，往上強烈內收（recogimiento），船樓窄；
#     · 舷頂是一條折線：船尾樓高、船腰低、船首樓次高（船首喙另做子作品）。
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
        self.th_up = g('tumblehome_above_per_cell')   # puente 以上每往上一格再往內收幾格（toptimbers 稍微拉直 ⇒ 小）
        self.p_bilge = g('bilge_pow')
        self.plan_h = g('plan_half')         # plan（平底）的半寬
        self.astilla = g('astilla')          # 平底外緣比龍骨頂高幾格
        self.s_a, self.s_f = g('s_aft'), g('s_fwd')
        self.x_sp0, self.sp_rake = g('sternpost_x0'), math.radians(g('sternpost_rake_deg'))
        self.z_wt = g('wing_transom_z')
        self.rt = g('transom_ratio')
        self.x_ff, self.R_stem = g('forefoot_x'), g('stem_radius')
        self.zr_aft, self.zr_fwd = g('deadwood_aft_z'), g('deadwood_fwd_z')
        self.k_bow_lo, self.k_bow_hi = g('bow_pow_low'), g('bow_pow_high')
        self.q_aft = g('aft_pow')
        self.top = L['top']                  # 舷頂高度：[[x, z], …] 折線
        self.ctr = L.get('counter')          # 步驟 17：船尾 counter（wing transom 以上往後外伸）；沒有 ⇒ 船尾面照艉柱的斜度
        self.tc = L.get('top_curve')         # 步驟 17：舷頂曲線（船樓前後緣 smoothstep 下降、兩頭往上翹）；沒有 ⇒ top 折線
        xs = np.arange(0, plan['space']['x']) + 0.5
        self.top_max = float(np.max(self.top_z(xs)))

    # ── 兩端 ──
    def x_stem(self, z):
        """艏柱前緣（外板外面）的 x：圓心 (forefoot_x, R) 半徑 R 的圓弧 —— z 0 那裡跟龍骨相切、往上越來越直。"""
        z = np.clip(np.asarray(z, float), 0, self.R_stem)
        R = self.R_stem
        return self.x_ff + np.sqrt(np.clip(R * R - (R - z) ** 2, 0, None))

    def x_post(self, z):
        """艉柱後緣的 x（往上往後倒）。"""
        return self.x_sp0 - np.asarray(z, float) * math.tan(self.sp_rake)

    def counter(self, z):
        """船尾 counter 往後外伸幾格（步驟 17，參考 San Felipe 模型的扇形 counter）：z0（wing transom）0 ⇒ z1 外伸 c，smoothstep（兩頭相切）；z1 以上照艉柱的斜度。"""
        z = np.asarray(z, float)
        if not self.ctr:
            return np.zeros(z.shape)
        C = self.ctr
        return float(C['c']) * smoothstep((z - C['z0']) / float(C['z1'] - C['z0']))

    def x_aft(self, z):
        """船殼最後面：wing transom 以下 ＝ 艉柱；以上 ＝ espejo，順著艉柱的斜度往後倒（步驟 17：再往後外伸 counter）。"""
        return self.x_post(z) - self.counter(z)

    # ── 剖面 ──
    def hb_mid(self, z, zr):
        """船中剖面在高度 z 的半寬；zr ＝ 船底從哪個高度開始（兩端的 deadwood 往上抬，剖面往 V 形收）。
        船中：plan（平底）從龍骨往外、astilla 抬一點 ⇒ 圓舭（superellipse）接到最寬處 ⇒ 往上 recogimiento 內收。
        兩端（zr 抬得越高）plan 縮成 0、圓舭的指數往 1 收 ⇒ V 形，跟 deadwood 平順接上。"""
        z = np.asarray(z, float)
        zr = np.asarray(zr, float)
        e = np.clip((zr - self.z_keel_top) / max(1.0, max(self.zr_aft, self.zr_fwd) - self.z_keel_top), 0, 1)
        ph = self.keel_hw + (self.plan_h - self.keel_hw) * (1 - e)          # 平底那一段的半寬
        zf = zr + self.astilla * (1 - e)                                     # 平底外緣的高度
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
        """長度方向的比例：0 ＝ 艉柱線（不是 counter 的最後面 ⇒ 加 counter 不動船身其他地方的寬）、1 ＝ 艏柱。"""
        xa, xs = self.x_post(z), self.x_stem(z)
        return (np.asarray(x, float) - xa) / np.maximum(1.0, xs - xa)

    def zr(self, s):
        aft = self.z_keel_top + (self.zr_aft - self.z_keel_top) * np.clip((self.s_a - s) / self.s_a, 0, 1) ** 2
        fwd = self.z_keel_top + (self.zr_fwd - self.z_keel_top) * np.clip((s - self.s_f) / (1 - self.s_f), 0, 1) ** 3
        return np.where(s < self.s_a, aft, np.where(s > self.s_f, fwd, self.z_keel_top))

    def breadth_k(self, s, z):
        """長度方向的收縮（0..1）。船尾：wing transom 以上留 espejo 的寬、以下收到艉柱；船頭：superellipse（上面鈍、下面尖）。"""
        z = np.asarray(z, float)
        ua = np.clip(1 - s / self.s_a, 0, 1)
        wide = 40.0 * (1 - ua)
        rt = self.rt * smoothstep((z - (self.z_wt - 6 - wide)) / (12.0 + wide))
        aft = rt + (1 - rt) * (1 - ua ** self.q_aft)
        k = self.k_bow_lo + (self.k_bow_hi - self.k_bow_lo) * np.clip((z - 15) / 60.0, 0, 1)
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
        if st:            # 步驟 17：船尾那一段（s < s_aft）z0 以上再往裡收（船尾樓上窄；San Felipe 模型的船尾兩舷往裡倒）
            ua = np.clip(1 - s / self.s_a, 0, 1)
            h = h - float(st['k']) * np.clip(z - float(st['z0']), 0, None) * ua ** float(st['pow'])
        inside = (s >= 0) & (s <= 1)
        if self.ctr:      # counter：艉柱線後面那一段照 s ＝ 0 的寬（espejo 的寬）往後伸，俯視往兩角收 round（圓的船尾）
            xp = self.x_post(z)
            c = self.counter(z)
            u = np.clip((xp - x) / max(1.0, float(self.ctr['c'])), 0, 1)
            h = np.where(s < 0, self.keel_hw + (h - self.keel_hw) * (1 - float(self.ctr['round']) * u ** 2), h)
            inside = (x >= xp - c) & (s <= 1)
        bh = self.P.get('beakhead')
        if bh:            # 步驟 17：船頭的層次（San Felipe）—— z 以上、x 以前切成一道平的 beakhead 艙壁；底下的船頭頂面成了平台
            inside = inside & ~((x >= float(bh['x'])) & (z >= float(bh['z'])))
        return np.where(inside, h, -1.0)

    def top_z(self, x):
        x = np.asarray(x, float)
        if not self.tc:
            pts = np.array(self.top, float)
            return np.interp(x, pts[:, 0], pts[:, 1])
        # 步驟 17：節點之間照 smoothstep 走（平的那幾段不變、船樓前後緣的落差變成 S 形），再加兩頭往上翹的 rise（((離起點) ÷ (到終點))^pow × dz）
        K = np.array(self.tc['knots'], float)
        i = np.clip(np.searchsorted(K[:, 0], x) - 1, 0, len(K) - 2)
        t = np.clip((x - K[i, 0]) / (K[i + 1, 0] - K[i, 0]), 0, 1)
        z = K[i, 1] + (K[i + 1, 1] - K[i, 1]) * smoothstep(t)
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

# 明鄭一號大鳥船線形幾何：plan.json 的 lines ⇒ 每個 (x, z) 的半寬與實心船體
#   出處：kotoko-ganzengchuan-01m/design/lines.py（通用參數化尖底圓舭福船線形）
#   座標：X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 YC 格，鏡像 y ↔ 2·YC − y）、Z 高度（z=0 ＝ 龍骨底面）；格 k 佔 [k, k+1)、格心 k+0.5。
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
        L = {k: V(v) for k, v in plan['lines'].items() if k not in ('top', 'top_src', 'stations')}
        if probe:
            for k, d in probe.items():
                if k in L and isinstance(L[k], (int, float)):
                    L[k] = L[k] + d
        self.P = L
        self.plan = plan
        self.YC = int(plan['space']['yc'])

        self.x_keel_aft = float(L['x_keel_aft'])
        self.x_keel_fwd = float(L['x_keel_fwd'])
        self.stern_rake = np.array(L['stern_rake'], float)  # [z, x]
        self.stem_rake = np.array(L['stem_rake'], float)    # [z, x]
        self.xm = float(L['x_mid'])
        self.B = float(L['half_beam'])
        self.keel_half = float(L['keel_half'])
        self.section_tab = np.array(L['section_halfwidth'], float)
        self.plan_aft_tab = np.array(L['plan_halfwidth_aft'], float)
        self.plan_fwd_tab = np.array(L['plan_halfwidth_fwd'], float)
        self.D = float(L['depth_mid'])
        self.sh_aft = float(L['sheer_z_aft'])
        self.sh_fwd = float(L['sheer_z_fwd'])
        self.sh_pow_aft = float(L['sheer_pow_aft'])
        self.sh_pow_fwd = float(L['sheer_pow_fwd'])
        self.top = plan['lines']['top']
        self.top_max = max(pt[1] for pt in self.top)
        self.xa_min = float(self.stern_rake[:, 1].min())
        self.xf_max = float(self.stem_rake[:, 1].max())

    def x_aft(self, z):
        """給定高度 z 的艉柱／高尾樓 X。"""
        return np.interp(np.asarray(z, float), self.stern_rake[:, 0], self.stern_rake[:, 1])

    def x_fwd(self, z):
        """給定高度 z 的艏柱 X。"""
        return np.interp(np.asarray(z, float), self.stem_rake[:, 0], self.stem_rake[:, 1])

    def zb(self, x):
        """給定縱座標 x 的船底龍骨／艏艉柱下緣 Z。"""
        x = np.asarray(x, float)
        z_aft = np.interp(x, self.stern_rake[::-1, 1], self.stern_rake[::-1, 0])
        z_fwd = np.interp(x, self.stem_rake[:, 1], self.stem_rake[:, 0])
        return np.where(x < self.x_keel_aft, z_aft, np.where(x > self.x_keel_fwd, z_fwd, 0.0))

    def zs_base(self, x):
        """基礎舷弧線（供橫剖面圓舭歸一化用，不含尾樓斷層加高）。"""
        x = np.asarray(x, float)
        ua = np.clip((self.xm - x) / max(self.xm - self.xa_min, 1e-6), 0.0, 1.0)
        uf = np.clip((x - self.xm) / max(self.xf_max - self.xm, 1e-6), 0.0, 1.0)
        return np.where(
            x < self.xm,
            self.D + (self.sh_aft - self.D) * (ua ** self.sh_pow_aft),
            self.D + (self.sh_fwd - self.D) * (uf ** self.sh_pow_fwd),
        )

    def top_z(self, x):
        """實際船殼舷頂高度（含高尾樓突升），沿 plan.lines.top 插值。"""
        xs = np.array([p[0] for p in self.top], float)
        zs = np.array([p[1] for p in self.top], float)
        return np.interp(np.asarray(x, float), xs, zs)

    def Bs(self, x, z=None):
        """平面收斂半寬：依該高度從舯 xm 往兩端依 plan_halfwidth 表收斂。"""
        x = np.asarray(x, float)
        if z is None:
            xa = self.xa_min
            xf = self.xf_max
        else:
            xa = self.x_aft(z)
            xf = self.x_fwd(z)
        ua = np.clip((self.xm - x) / np.maximum(self.xm - xa, 1e-6), 0.0, 1.0)
        uf = np.clip((x - self.xm) / np.maximum(xf - self.xm, 1e-6), 0.0, 1.0)
        fa = np.interp(ua, self.plan_aft_tab[:, 0], self.plan_aft_tab[:, 1])
        ff = np.interp(uf, self.plan_fwd_tab[:, 0], self.plan_fwd_tab[:, 1])
        return self.B * np.where(x < self.xm, fa, ff)

    def hb(self, x, z, extra_top=0.0):
        """(x, z) 處半寬（尖底圓舭福船剖面）；超出船體回傳 -1.0。"""
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        zb = self.zb(x)
        zs_b = self.zs_base(x)
        ztop = self.top_z(x) + extra_top
        xa_z = self.x_aft(np.minimum(z, self.top_max))
        xf_z = self.x_fwd(np.minimum(z, self.sh_fwd))

        s = (z - zb) / np.maximum(zs_b - zb, 1.0)
        sec = np.interp(np.maximum(s, 0.0), self.section_tab[:, 0], self.section_tab[:, 1])
        bx = self.Bs(x, np.minimum(z, self.top_max))
        h = np.maximum(self.keel_half, bx * sec)
        keel_mask = z <= 2.5
        h = np.where(keel_mask, np.minimum(h, self.keel_half + 0.8 * z), h)

        ok = (z >= zb) & (z <= ztop + 0.01) & (x >= xa_z) & (x <= xf_z)
        return np.where(ok, h, -1.0)

    def solid(self, X0, X1, ZMAX, extra=0):
        """產生 [x, y, z] 實心船型布林體積（extra>0 向上延伸供內蝕，使露天舷牆頂端不被封蓋）。"""
        W = 2 * self.YC + 1
        xs = np.arange(X0, X1 + 1) + 0.5
        zs = np.arange(0, ZMAX + 1) + 0.5
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        if extra:
            ztop = self.top_z(X)
            Z_eval = np.minimum(Z, ztop - 0.01)
            H_eval = self.hb(X, Z_eval, extra_top=0.0)
            ok = (Z >= self.zb(X)) & (Z <= ztop + extra) & (X >= self.x_aft(np.minimum(Z_eval, self.top_max))) & (X <= self.x_fwd(np.minimum(Z_eval, self.sh_fwd)))
            H = np.where(ok & (H_eval >= 0), H_eval, -1.0)
        else:
            H = self.hb(X, Z)
        dy = np.abs(np.arange(W) - self.YC)
        return dy[None, :, None] <= H[:, None, :]

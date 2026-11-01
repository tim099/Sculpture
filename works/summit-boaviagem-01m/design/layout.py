# 出處：erina-tradewind-01m/design/layout.py（TASK-1097 信風號；TASK-1151 改寫成好旅號 caravela redonda）
# 好旅號 佈置（TASK-1151 新圖紙 02）：plan.json 的 decks／ports／masts ⇒ 甲板範圍、炮門、桅軸、帆桁、帆的外框
#   座標同 lines.py。只讀 plan.json、不碰作品；之後的階段（甲板、桅、帆）照這裡的數字落格。
#   跟信風號不同：四根桅 —— 前桅方帆兩面（主帆、上桅帆）；主桅、後桅、最後桅各一根三角帆桁（〔源〕Domingues 2009）；
#   三角帆桁 ＝ 吊點（sling）在桅頂下 drop、往船尾往上斜 angle_deg、吊點前面那一段佔全長 fwd；
#   短艏斜桅只撐前支索，沒有三角帆桿、沒有艏帆。
import math
import numpy as np

MASTS = ('fore', 'main', 'mizzen', 'bonav')


class Layout:
    def __init__(self, plan, L):
        self.plan, self.L = plan, L
        self.M = plan['masts']
        self.masts = {}
        for name in MASTS:
            m = self.M[name]
            t = math.tan(math.radians(m['rake_deg']))
            z_top = m['heel_z'] + m['len'] - m['head']                  # 桅頂（下桅的 cap／吊點的參考）
            st = [('lower', m['heel_z'], m['heel_z'] + m['len'], m['r'])]
            tm = self.M.get(name + '_top')
            z_tt = None
            if tm:
                st.append(('top', z_top, z_top + tm['len'], tm['r']))
                z_tt = z_top + tm['len'] - tm['head']                    # 上桅的桅肩
            self.masts[name] = {'x0': m['x'], 'z0': m['heel_z'], 'tan': t, 'z_top': z_top, 'z_tt': z_tt, 'stages': st}
        b = self.M['bowsprit']
        a = math.radians(b['steeve_deg'])
        self.bow = {'p0': (b['heel'][0], b['heel'][1]), 'd': (math.cos(a), math.sin(a)), 'len': b['len']}

    def mast_x(self, name, z):
        m = self.masts[name]
        return m['x0'] + (np.asarray(z, float) - m['z0']) * m['tan']

    def mast_top(self, name):
        return self.masts[name]['stages'][-1][2]

    def bow_point(self, frac):
        """艏斜桅上的點（frac 0 ＝ 桅腳、1 ＝ 艏斜桅尖）。"""
        (x0, z0), (dx, dz) = self.bow['p0'], self.bow['d']
        s = self.bow['len'] * frac
        return x0 + dx * s, z0 + dz * s

    # ── 帆桁：方帆桁 中心 (x, z)；三角帆桁 吊點 (x, z)、前端 fore、尾端 peak ──
    def yards(self):
        out = {}
        for k, y in self.M['yards'].items():
            if k.startswith('_'):
                continue
            on = y['on']
            mast = on.split('_')[0]
            m = self.masts[mast]
            if k.endswith('_lateen'):
                z = float(m['z_top'] - y['drop'])
                x = float(self.mast_x(mast, z))
                a = math.radians(y['angle_deg'])
                lf, la = y['len'] * y['fwd'], y['len'] * (1 - y['fwd'])
                fore = (x + math.cos(a) * lf, z - math.sin(a) * lf)
                peak = (x - math.cos(a) * la, z + math.sin(a) * la)
                out[k] = {'x': x, 'z': z, 'len': y['len'], 'on': on, 'mast': mast, 'kind': 'lateen', 'angle_deg': y['angle_deg'],
                          'fore': fore, 'peak': peak, 'end': peak}
                continue
            if on == mast:                                   # 下桅：桅頂下 drop
                z = m['z_top'] - y['drop']
            else:                                            # 上桅：上桅桅肩下 drop
                z = m['z_tt'] - y['drop']
            x = float(self.mast_x(mast, z))
            out[k] = {'x': x, 'z': float(z), 'len': y['len'], 'on': on, 'mast': mast, 'kind': 'square'}
        return out

    # ── 帆（側面帆圖的外框）──
    #   square：(x, z_head, w_head, z_foot, w_foot)；poly：三角帆（tack ＝ 帆桁前端、peak ＝ 帆桁尾端、clew ＝ 尾端正下方、舷頂上 lateen_clew_above_rail）
    def sails(self):
        Y = self.yards()
        top = self.L.top_z
        S = {}
        R = self.M['rig']

        def sq(name, up, lo_z, lo_w):
            u = Y[up]
            S[name] = {'kind': 'square', 'x': u['x'], 'z_head': u['z'], 'w_head': u['len'] * 0.92, 'z_foot': lo_z, 'w_foot': lo_w}
        fc = Y['fore_course']
        sq('fore-course', 'fore_course', float(top(fc['x'])) + R['course_foot_above_rail'], fc['len'] * 0.92)
        sq('fore-topsail', 'fore_topsail', fc['z'] + 4, fc['len'] * 0.88)
        for k in ('main', 'mizzen', 'bonav'):
            y = Y[k + '_lateen']
            fx, fz = y['fore']
            px, pz = y['peak']
            cx = px + 6
            cz = float(top(cx)) + R['lateen_clew_above_rail']
            S[k + '-lateen'] = {'kind': 'poly', 'lateen': True, 'pts': [(fx - 2, fz + 1), (px + 2, pz - 1), (cx, cz)]}
        return S

    def sail_area_m2(self):
        A = 0.0
        m2 = self.plan['meters_per_cell'] ** 2
        for s in self.sails().values():
            if s['kind'] == 'square':
                A += (s['w_head'] + s['w_foot']) / 2 * (s['z_head'] - s['z_foot'])
            else:
                p = s['pts']
                A += abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2
        return A * m2

    # ── 炮門：每舷的 (x 中心, z 下緣, 寬, 高, 甲板) ──
    def ports(self):
        out = []
        for deck, P in self.plan['ports'].items():
            for x in P['x']:
                zd = float(self.L.deck_z(deck, x))
                out.append({'deck': deck, 'x': x, 'w': P['w'], 'h': P['h'], 'sill': int(math.floor(zd + P['sill'])), 'gun': P['gun']})
        return out

# 出處：erina-oxford-01m/design/layout.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 佈置（TASK-1097 新圖紙 02）：plan.json 的 decks／ports／masts ⇒ 甲板範圍、炮門、桅軸、帆桁、帆的外框
#   座標同 lines.py。只讀 plan.json、不碰作品；之後的階段（甲板、桅、帆）照這裡的數字落格。
#   跟牛津號不同：兩根桅（前、主）；帆桁的 z 照桅的各節算（plan 的 yards 只給長度與 drop）；
#   主桅掛 gaff＋boom 縱帆（Steel 1794：brig 沒有主橫帆，主下桅上那根是 cross-jack，只撐主上桅帆的帆腳）；
#   艏斜桅前面接三角帆桿（jib-boom），艏帆 ＝ 前支索帆＋三角帆；不掛斜桅帆。
import math
import numpy as np


class Layout:
    def __init__(self, plan, L):
        self.plan, self.L = plan, L
        self.M = plan['masts']
        self.masts = {}
        for name in ('main', 'fore'):
            m = self.M[name]
            t = math.tan(math.radians(m['rake_deg']))
            z_top = m['heel_z'] + m['len'] - m['head']                  # top（桅頂橫桁）那一層
            st = [('lower', m['heel_z'], m['heel_z'] + m['len'], m['r'])]
            tm = self.M.get(name + '_top')
            z_tt = None
            if tm:
                st.append(('top', z_top, z_top + tm['len'], tm['r']))
                z_tt = z_top + tm['len'] - tm['head']                    # 上桅的桅肩（頂桅從這裡起）
                tg = self.M.get(name + '_tg')
                if tg:
                    st.append(('tg', z_tt, z_tt + tg['len'], tg['r']))
            self.masts[name] = {'x0': m['x'], 'z0': m['heel_z'], 'tan': t, 'z_top': z_top, 'z_tt': z_tt, 'stages': st}
        b = self.M['bowsprit']
        a = math.radians(b['steeve_deg'])
        self.bow = {'p0': (b['heel'][0], b['heel'][1]), 'd': (math.cos(a), math.sin(a)), 'len': b['len']}
        j = self.M['jibboom']
        self.jib = {'from': b['len'] - j['overlap'], 'len': j['len']}  # 沿艏斜桅那條線量（從艏斜桅桅腳起算）

    def mast_x(self, name, z):
        m = self.masts[name]
        return m['x0'] + (np.asarray(z, float) - m['z0']) * m['tan']

    def bow_point(self, frac):
        """艏斜桅上的點（frac 0 ＝ 桅腳、1 ＝ 艏斜桅尖）。"""
        return self.along(self.bow['len'] * frac)

    def along(self, s):
        """艏斜桅那條線上離桅腳 s 格的點（三角帆桿也在這條線上）。"""
        (x0, z0), (dx, dz) = self.bow['p0'], self.bow['d']
        return x0 + dx * s, z0 + dz * s

    def jib_point(self, frac):
        """三角帆桿上的點（frac 0 ＝ 帆桿根部、1 ＝ 帆桿尖）。"""
        return self.along(self.jib['from'] + self.jib['len'] * frac)

    def stage_top(self, mast, stage):
        for st in self.masts[mast]['stages']:
            if st[0] == stage:
                return st[2]
        raise KeyError(stage)

    # ── 帆桁：中心 (x, z)、長、哪根桅 ──
    def yards(self):
        out = {}
        Yd = self.M['yards']
        for k, y in Yd.items():
            if k.startswith('_'):
                continue
            on = y['on']
            mast = on.split('_')[0]
            m = self.masts[mast]
            kind = 'square'
            if k.endswith('boom') or k.endswith('gaff'):
                kind = k.split('_')[1]
                z = float(y['jaws_z'])
                x = float(self.mast_x(mast, z))
                a = math.radians(y['angle_deg'])
                end = (x - math.cos(a) * y['len'], z + math.sin(a) * y['len'])      # 往船尾伸出去、往上翹 angle
                out[k] = {'x': x, 'z': z, 'len': y['len'], 'on': on, 'mast': mast, 'kind': kind, 'angle_deg': y['angle_deg'], 'end': end}
                continue
            if on == mast:                                   # 下桅：桅頂橫桁下 drop
                z = m['z_top'] - y['drop']
            elif on.endswith('_top'):                        # 上桅：上桅桅肩下 drop（升起的位置）
                z = m['z_tt'] - y['drop']
            else:                                            # 頂桅：頂桅頂下 drop
                z = self.stage_top(mast, 'tg') - y['drop']
            x = float(self.mast_x(mast, z))
            out[k] = {'x': x, 'z': float(z), 'len': y['len'], 'on': on, 'mast': mast, 'kind': kind}
        return out

    # ── 帆（側面帆圖的外框）──
    #   square：上緣帆桁、下緣下一根帆桁或舷頂上 —— (x, z_head, w_head, z_foot, w_foot)
    #   poly：縱帆、艏帆的角（x, z）照順序
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
        sq('fore-topgallant', 'fore_tg', Y['fore_topsail']['z'] + 3, Y['fore_topsail']['len'] * 0.9)
        cj = Y['main_crossjack']
        sq('main-topsail', 'main_topsail', cj['z'] + 4, cj['len'] * 0.88)
        sq('main-topgallant', 'main_tg', Y['main_topsail']['z'] + 3, Y['main_topsail']['len'] * 0.9)
        # 主帆（gaff＋boom 四邊形）：tack ＝ boom 的 jaws、throat ＝ gaff 的 jaws、peak ＝ gaff 尖、clew ＝ boom 尖往前 3 格
        b, g = Y['main_boom'], Y['main_gaff']
        S['mainsail'] = {'kind': 'poly', 'pts': [(b['x'] - 3, b['z'] + 2), (g['x'] - 3, g['z'] - 1), (g['end'][0] + 2, g['end'][1] - 1), (b['end'][0] + 3, b['end'][1] + 2)]}
        # 艏帆：前支索帆（前支索：前下桅頂 → 艏斜桅近艏柱）、三角帆（前上桅支索：前上桅桅肩 → 三角帆桿）
        fx, fz = float(self.mast_x('fore', self.masts['fore']['z_top'])), self.masts['fore']['z_top']
        sx, sz = self.bow_point(R['forestay_frac'])
        head = (fx + (sx - fx) * 0.12, fz + (sz - fz) * 0.12)
        tack = (fx + (sx - fx) * 0.94, fz + (sz - fz) * 0.94)
        S['fore-staysail'] = {'kind': 'poly', 'pts': [head, tack, (fx + 8, float(top(fx)) + R['staysail_clew_above_rail'])]}
        tx, tz = float(self.mast_x('fore', self.masts['fore']['z_tt'])), self.masts['fore']['z_tt']
        jx, jz = self.jib_point(R['jibstay_frac'])
        head = (tx + (jx - tx) * 0.1, tz + (jz - tz) * 0.1)
        tack = (tx + (jx - tx) * 0.96, tz + (jz - tz) * 0.96)
        S['jib'] = {'kind': 'poly', 'pts': [head, tack, (sx - 6, sz + R['jib_clew_above_bowsprit'])]}
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

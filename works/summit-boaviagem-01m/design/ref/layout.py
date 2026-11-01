# 牛津號 佈置（TASK-0972 新圖紙 02）：plan.json 的 decks／ports／masts ⇒ 甲板範圍、炮門、桅軸、帆桁、帆的外框
#   座標同 lines.py。只讀 plan.json、不碰作品；之後的階段（甲板、桅、帆）照這裡的數字落格。
import math
import numpy as np


class Layout:
    def __init__(self, plan, L):
        self.plan, self.L = plan, L
        self.M = plan['masts']
        self.masts = {}
        for name in ('main', 'fore', 'mizzen'):
            m = self.M[name]
            t = math.tan(math.radians(m['rake_deg']))
            z_top = m['heel_z'] + m['len'] - m['head']                  # top（桅樓平台）那一層
            st = [('lower', m['heel_z'], m['heel_z'] + m['len'], m['r'])]
            tm = self.M.get(name + '_top')
            if tm:
                st.append(('top', z_top, z_top + tm['len'], tm['r']))
                tg = self.M.get(name + '_tg')
                if tg:
                    z1 = z_top + tm['len'] - tm['head']
                    st.append(('tg', z1, z1 + tg['len'], tg['r']))
            self.masts[name] = {'x0': m['x'], 'z0': m['heel_z'], 'tan': t, 'z_top': z_top, 'stages': st}
        b = self.M['bowsprit']
        a = math.radians(b['steeve_deg'])
        self.bow = {'p0': (b['heel'][0], b['heel'][1]), 'd': (math.cos(a), math.sin(a)), 'len': b['len']}

    def mast_x(self, name, z):
        m = self.masts[name]
        return m['x0'] + (np.asarray(z, float) - m['z0']) * m['tan']

    def bow_point(self, frac):
        (x0, z0), (dx, dz) = self.bow['p0'], self.bow['d']
        s = self.bow['len'] * frac
        return x0 + dx * s, z0 + dz * s

    # ── 帆桁：中心 (x, z)、長、哪根桅 ──
    def yards(self):
        out = {}
        for k, y in self.M['yards'].items():
            on = y['on']
            if on == 'bowsprit':
                x, z = self.bow_point(y['frac'])
                z -= y['drop']
            else:
                base = on.split('_')[0]
                z = y['z']
                x = float(self.mast_x(base, z))
            out[k] = {'x': float(x), 'z': float(z), 'len': y['len'], 'on': on, 'mast': on.split('_')[0]}
        return out

    # ── 帆（側面帆圖的外框：方帆 ＝ 上緣帆桁長、下緣下一根帆桁長或船腰；三角帆 ＝ 三角形）──
    def sails(self):
        Y = self.yards()
        top = self.L.top_z
        S = {}

        def sq(name, up, lo_z, lo_w):
            u = Y[up]
            S[name] = {'kind': 'square', 'x': u['x'], 'z_head': u['z'], 'w_head': u['len'] * 0.92, 'z_foot': lo_z, 'w_foot': lo_w}
        for m, c, t, g in (('main', 'main_course', 'main_topsail', 'main_tg'), ('fore', 'fore_course', 'fore_topsail', 'fore_tg')):
            xm = Y[c]['x']
            rail = float(top(xm))
            sq(m + '-course', c, rail + 10, Y[c]['len'] * 0.92)             # 帆腳離舷頂 1 m
            sq(m + '-topsail', t, Y[c]['z'] + 4, Y[c]['len'] * 0.88)
            sq(m + '-topgallant', g, Y[t]['z'] + 3, Y[t]['len'] * 0.9)
        sq('mizzen-topsail', 'mizzen_topsail', Y['crossjack']['z'] + 3, Y['crossjack']['len'] * 0.85)
        sp = Y['spritsail']
        S['spritsail'] = {'kind': 'square', 'x': sp['x'], 'z_head': sp['z'], 'w_head': sp['len'] * 0.92, 'z_foot': sp['z'] - 46, 'w_foot': sp['len'] * 0.92}
        # 後桅三角帆：帆桁前端 → 後端，帆腳沿後桅往下到後甲板舷頂上 1 m（luff 沿帆桁、leech 從帆桁後端往下到帆腳後角）
        y = self.M['yards']['mizzen_lateen']
        a = math.radians(y['angle_deg'])
        c = Y['mizzen_lateen']
        f0 = y['sling_frac']
        fx, fz = c['x'] + math.cos(a) * y['len'] * f0, c['z'] - math.sin(a) * y['len'] * f0
        ax, az = c['x'] - math.cos(a) * y['len'] * (1 - f0), c['z'] + math.sin(a) * y['len'] * (1 - f0)
        foot_z = float(top(c['x'])) + 10
        S['mizzen-lateen'] = {'kind': 'lateen', 'fore': (fx, max(fz, foot_z)), 'peak': (ax, az), 'clew': (ax + 6, foot_z)}
        return S

    def sail_area_m2(self):
        A = 0.0
        m2 = self.plan['meters_per_cell'] ** 2
        for s in self.sails().values():
            if s['kind'] == 'square':
                A += (s['w_head'] + s['w_foot']) / 2 * (s['z_head'] - s['z_foot'])
            else:
                (x1, z1), (x2, z2), (x3, z3) = s['fore'], s['peak'], s['clew']
                A += abs((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1)) / 2
        return A * m2

    # ── 炮門：每舷的 (x 中心, z 下緣, 寬, 高, 甲板) ──
    def ports(self):
        out = []
        for deck, P in self.plan['ports'].items():
            for x in P['x']:
                zd = float(self.L.deck_z(deck, x))
                out.append({'deck': deck, 'x': x, 'w': P['w'], 'h': P['h'], 'sill': int(math.floor(zd + P['sill'])), 'gun': P['gun']})
        return out

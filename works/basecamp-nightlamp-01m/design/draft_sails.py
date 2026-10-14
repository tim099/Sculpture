# 新圖紙 17 帆 v1（階段十六，TASK-0538）：plan.json sails ＋ rig_points_yards.json（帆桁轉過的固定點）＋ standing_ropes.json（stays）＋ 現況 export list
#   ⇒ sails_plan.json（帆、帆自己的繩、要登記的固定點）、textures/ensign.png（旗）、verify_sails.json、sheet17_sails_v1.png
# 用法：python -I draft_sails.py <design> <組裝件 list> <船殼 list> <欄杆 list> <後桅 list> <主桅 list>
#   · 方帆：上緣兩角綁帆桁模型的 earing（model:<桅>/yard-<帆>/earing-P|S）、bind 邊 0；下兩角 free，
#     topsail 以上的 sheet 綁下一根帆桁同舷的 earing（帆桁轉，帆腳跟著轉）、course 的 sheet 往後、tack 往前綁到舷頂（造船規格 §7）。
#   · spanker：throat／peak 綁 gaff、clew／tack 綁 boom，三條邊釘住（bind 0,2,3）；三角帆：tack 在 stay 下端、head 在 stay 上 75% 那一格、clew free。
#   · 繫繩點：在那一欄最高的實心（欄杆或舷牆頂）、最外面那一格 —— 欄杆的登記在欄杆子作品、舷牆的登記在船殼（兩舷各一個，不鏡像）。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC = 160


def fx(v):
    s = '%.3f' % v
    if s.endswith('.000'):
        s = '%.3f' % (v + 0.001)
    return s


def pt(p):
    return ','.join(fx(c) for c in p)


class Sails:
    def __init__(s, design, lists):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['sails']
        s.Y = s.plan['yards']
        s.sha = {k: hashlib.sha256(open(p, 'rb').read()).hexdigest() for k, p in lists.items()}
        s.occ = DP.read_list(lists['assembly'])
        assert len(s.occ) == s.P['assembly_cells'], ('組裝件格數對不上', len(s.occ))
        s.hull = DP.read_list(lists['hull'])
        s.rails = DP.read_list(lists['rails'])
        s.mast = {'mizzen': DP.read_list(lists['mizzen']), 'main': DP.read_list(lists['main'])}
        yp = json.load(open(os.path.join(design, 'rig_points_yards.json'), encoding='utf-8'))['points']
        s.yp = {(p['member'], p['name']): p for p in yp}
        s.stays = {r['name']: r for r in json.load(open(os.path.join(design, 'standing_ropes.json'), encoding='utf-8'))['ropes']}
        sp = json.load(open(os.path.join(design, 'rig_points_standing.json'), encoding='utf-8'))['points']
        s.sp = {(p['link'], p['name']): p for p in sp}
        s.sails, s.ropes, s.points = [], [], []
        s.read = {}

    def braced(s, member, name):
        return np.array(s.yp[(member, name)]['braced'], float)

    def anchor_world(s, ref):
        link, name = ref.split('/', 1)
        return np.array(s.sp[(link, name)]['world'], float) + 0.5

    # ── 繫繩點：那一欄最高的實心、最外面那一格 ──
    def belay(s, name, x, side):
        cols = [(y, z) for (xx, y, z) in list(s.hull) + list(s.rails) if xx == x and ((y > YC) if side == 'S' else (y < YC))]
        zt = max(z for y, z in cols)
        ys = [y for y, z in cols if z == zt]
        y = max(ys) if side == 'S' else min(ys)
        cell = (x, y, zt)
        if cell in s.rails:
            owner, link = s.plan['rails']['work'], s.plan['rails']['link']
        else:
            owner, link = 'basecamp-nightlamp-01m', '船殼'
        nm = 'pin-%s' % name
        s.points.append({'owner': owner, 'link': link, 'name': nm, 'kind': 'belay', 'world': list(cell), 'local': list(cell)})
        return link + '/' + nm, np.array(cell, float) + 0.5

    def rope(s, name, a, b, slack, t, group, meta):
        s.ropes.append({'name': name, 'from': a, 'to': b, 'slack': slack, 'color': s.P['rope_color'], 'thickness': t, 'group': group, 'meta': meta})

    def square(self, S):
        s = self
        nm, mast = S['name'], S['mast']
        link = s.Y['links'][mast]
        hp, hs = s.braced(nm, 'earing-P'), s.braced(nm, 'earing-S')
        meta = {'kind': 'sail', 'mast': mast, 'sail': S['type']}
        corners = ['model:%s/yard-%s/earing-P' % (link, nm), 'model:%s/yard-%s/earing-S' % (link, nm)]
        if S.get('sheet_to'):
            lo = S['sheet_to']
            cs, cp = s.braced(lo, 'earing-S'), s.braced(lo, 'earing-P')
            corners += [pt(cs), pt(cp)]
            for side, tgt in (('S', 'earing-S'), ('P', 'earing-P')):
                s.rope('%s-sheet-%s' % (nm, side), 'sail:%s/clew_%s' % (nm, side.lower()), 'model:%s/yard-%s/%s' % (link, lo, tgt), 1, s.P['thick']['sheet_upper'],
                       'running/sheets', {'kind': 'sheet', 'sail': nm})
        else:
            B = S['course']
            zc = {}
            refs = {}
            for side in ('S', 'P'):
                refs['sheet-' + side] = s.belay('%s-sheet-%s' % (nm, side), B['sheet_x'], side)
                refs['tack-' + side] = s.belay('%s-tack-%s' % (nm, side), B['tack_x'], side)
            top = max(refs['sheet-S'][1][2], refs['tack-S'][1][2])
            cs = np.array([hs[0], hs[1], top + B['clew_above_rail']])
            cp = np.array([hp[0], hp[1], top + B['clew_above_rail']])
            corners += [pt(cs), pt(cp)]
            for side in ('S', 'P'):
                s.rope('%s-sheet-%s' % (nm, side), 'sail:%s/clew_%s' % (nm, side.lower()), refs['sheet-' + side][0], B['sheet_slack'], s.P['thick']['course'],
                       'running/sheets', {'kind': 'sheet', 'sail': nm})
            s.rope('%s-tack-S' % nm, 'sail:%s/clew_s' % nm, refs['tack-S'][0], B['tack_slack'], s.P['thick']['course'], 'running/tacks', {'kind': 'tack', 'sail': nm})
        s.sails.append({'name': nm, 'corners': corners, 'corner_names': ['head_p', 'head_s', 'clew_s', 'clew_p'], 'bind': [0], 'free': ['clew_s', 'clew_p'],
                        'fullness': s.P['fullness'], 'color': s.P['color'], 'meta': meta,
                        'design': {'head_p': hp.round(2).tolist(), 'head_s': hs.round(2).tolist(), 'clew_s': np.array(cs).round(2).tolist(), 'clew_p': np.array(cp).round(2).tolist()}})

    def spanker(s):
        G = s.Y['links']['mizzen']
        gp = [n for (m, n) in s.yp if m == 'spanker-gaff' and n.startswith('top')]
        bp = [n for (m, n) in s.yp if m == 'spanker-boom' and n.startswith('top')]
        last = lambda L: max(L, key=lambda n: int(n[3:]))
        first = lambda L: min(L, key=lambda n: int(n[3:]))
        c = ['model:%s/yard-spanker-gaff/%s' % (G, first(gp)), 'model:%s/yard-spanker-gaff/%s' % (G, last(gp)),
             'model:%s/yard-spanker-boom/%s' % (G, last(bp)), 'model:%s/yard-spanker-boom/%s' % (G, first(bp))]
        d = {'throat': s.braced('spanker-gaff', first(gp)), 'peak': s.braced('spanker-gaff', last(gp)),
             'clew': s.braced('spanker-boom', last(bp)), 'tack': s.braced('spanker-boom', first(bp))}
        s.sails.append({'name': 'spanker', 'corners': c, 'corner_names': ['throat', 'peak', 'clew', 'tack'], 'bind': [0, 2, 3], 'free': [],
                        'fullness': s.P['fullness'], 'color': s.P['color'], 'meta': {'kind': 'sail', 'mast': 'mizzen', 'sail': 'gaff'},
                        'design': {k: v.round(2).tolist() for k, v in d.items()}})

    def headsail(s, J):
        st = s.stays[J['stay']]
        lo = s.anchor_world(st['to'])        # stay 的下端（艏斜桅上）
        hi = s.anchor_world(st['from'])      # 上端（前桅）
        head = lo + (hi - lo) * J['head_frac']
        hc = tuple(int(math.floor(v)) for v in head)
        hname = '%s.head' % J['name']
        s.points.append({'owner': s.Y['works']['fore'], 'link': s.Y['links']['fore'], 'name': hname, 'kind': 'headsail-head', 'world': list(hc), 'local': list(hc)})
        # head 那一格的格心離 stay 的直線多遠
        hcc = np.array(hc, float) + 0.5
        u = (hi - lo) / np.linalg.norm(hi - lo)
        off = float(np.linalg.norm((hcc - lo) - u * ((hcc - lo) @ u)))
        clew = lo + (head - lo) * J['clew_along'] + np.array([0, 0, -J['clew_drop']])
        c = [st['to'], s.Y['links']['fore'] + '/' + hname, pt(clew)]
        s.sails.append({'name': J['name'], 'corners': c, 'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'],
                        'fullness': J['fullness'], 'color': s.P['color'], 'meta': J['meta'],
                        'design': {'tack': lo.round(2).tolist(), 'head': hcc.round(2).tolist(), 'clew': clew.round(2).tolist(), 'head_off_stay': round(off, 3)}})
        for side in ('S', 'P'):
            ref, w = s.belay('%s-sheet-%s' % (J['name'], side), J['sheet_x'], side)
            s.rope('%s-sheet-%s' % (J['name'], side), 'sail:%s/clew' % J['name'], ref, 1, s.P['thick']['sheet_upper'], 'running/sheets', {'kind': 'sheet', 'sail': J['name']})

    def flags(s):
        F = s.P['flags']
        for nm, G in F.items():
            m = G['mast']
            M = s.mast[m]
            zt = max(z for (x, y, z) in M)
            xs = [x for (x, y, z) in M if z == zt - G['below_truck']]
            x0 = (min(xs) + max(xs) + 1) / 2
            ztop = zt - G['below_truck'] + 0.5
            if G['shape'] == 'rect':
                c = [[x0, YC + 0.5, ztop], [x0 + G['length'], YC + 0.5, ztop], [x0 + G['length'], YC + 0.5, ztop - G['height']], [x0, YC + 0.5, ztop - G['height']]]
                s.sails.append({'name': nm, 'corners': [pt(p) for p in c], 'corner_names': None, 'bind': [3], 'free': [1, 2], 'fullness': G['fullness'],
                                'color': G['color'], 'meta': G['meta'], 'texture': G.get('texture'), 'design': {'corners': c}})
            else:
                c = [[x0, YC + 0.5, ztop], [x0 + G['length'], YC + 0.5, ztop - G['height'] / 2], [x0, YC + 0.5, ztop - G['height']]]
                s.sails.append({'name': nm, 'corners': [pt(p) for p in c], 'corner_names': None, 'bind': [2], 'free': [1], 'fullness': G['fullness'],
                                'color': G['color'], 'meta': G['meta'], 'design': {'corners': c}})

    def build(s):
        for S in s.P['square']:
            s.square(S)
        s.spanker()
        for J in s.P['headsails']:
            s.headsail(J)
        s.flags()


def ensign_png(path):
    """旗：黑底、正中一盞暖黃的提燈（船名「夜燈」）。30×20 像素畫，左上角 ＝ 角 0（旗桿那一側的上角）。"""
    W, H = 30, 20
    im = Image.new('RGBA', (W, H), (20, 20, 22, 255))
    d = ImageDraw.Draw(im)
    frame, glass, glow = (70, 62, 52, 255), (255, 204, 85, 255), (150, 105, 40, 255)
    cx = 14
    d.rectangle([cx - 1, 3, cx + 1, 3], fill=frame)              # 提環
    d.point([(cx - 2, 4), (cx + 2, 4)], fill=frame)
    d.rectangle([cx - 4, 5, cx + 4, 6], fill=frame)              # 頂蓋
    d.rectangle([cx - 3, 7, cx + 3, 13], fill=glass)             # 燈罩
    d.rectangle([cx - 1, 9, cx + 1, 11], fill=(255, 245, 200, 255))   # 火
    d.line([(cx - 4, 7), (cx - 4, 13)], fill=frame)
    d.line([(cx + 4, 7), (cx + 4, 13)], fill=frame)
    d.rectangle([cx - 4, 14, cx + 4, 15], fill=frame)            # 底座
    for (x, y) in ((cx - 6, 9), (cx + 6, 9), (cx - 6, 11), (cx + 6, 11), (cx, 1), (cx - 5, 16), (cx + 5, 16)):
        d.point((x, y), fill=glow)                               # 光暈
    im.save(path)
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def render_sheet(S, path):
    X0, X1, Z1 = 40, 1000, 560
    img = np.full((Z1, X1 - X0, 3), 250, np.uint8)
    for (x, y, z) in S.occ:
        if X0 <= x < X1 and z < Z1:
            img[Z1 - 1 - z, x - X0] = (215, 208, 196)
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    for sl in S.sails:
        ds = sl['design']
        pts = ds['corners'] if 'corners' in ds else [ds[k] for k in (sl['corner_names'] or [])]
        poly = [(p[0] - X0, Z1 - 1 - p[2]) for p in pts]
        dr.polygon(poly, outline=(40, 40, 40), fill=(110, 100, 92) if not sl['meta'].get('kind') == 'flag' else (200, 150, 50))
    dr.text((6, 4), 'sheet 17 v1  sails (starboard profile, design corners before cloth sim)', fill=(0, 0, 0))
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    keys = ('assembly', 'hull', 'rails', 'mizzen', 'main')
    S = Sails(design, dict(zip(keys, sys.argv[2:7])))
    S.build()
    tex = os.path.join(design, 'textures')
    os.makedirs(tex, exist_ok=True)
    tsha = ensign_png(os.path.join(tex, 'ensign.png'))
    v = {'base': S.sha, 'sails': len(S.sails), 'ropes': len(S.ropes), 'points': len(S.points), 'ensign_png_sha256': tsha,
         'design': {sl['name']: sl['design'] for sl in S.sails}, 'belay': [(p['name'], p['link'], p['world']) for p in S.points]}
    out = {'sails': S.sails, 'ropes': S.ropes, 'points': S.points}
    p = os.path.join(design, 'sails_plan.json')
    json.dump(out, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    v['sails_plan_sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    json.dump(v, open(os.path.join(design, 'verify_sails.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(S, os.path.join(design, 'sheet17_sails_v1.png'))
    print(json.dumps({k: v[k] for k in ('sails', 'ropes', 'points', 'belay')}, ensure_ascii=False))
    for sl in S.sails:
        print(sl['name'], json.dumps(sl['design'], ensure_ascii=False))


if __name__ == '__main__':
    main()

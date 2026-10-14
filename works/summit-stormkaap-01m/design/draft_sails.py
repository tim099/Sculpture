# 新圖紙 10 帆（TASK-0547 階段十）：plan.json 的 sails ⇒ 帆 10 面（＋破帆貼圖）、帆腳索、風、帆與帆自己的繩的 meta、verify_sails.json。
# 用法：python -I -X utf8 -B draft_sails.py <design 資料夾>
#   · 從夜隼號 draft_sails.py（TASK-0529 階段十一）改。點、碰撞照 draft_running.Run（船＋桅＋channels＋fife＋帆桁轉好）；動索的 pin 不再用。
#   · 方帆：角 head_p、head_s（帆桁模型的 earing）、clew_s、clew_p（座標）；邊 0 釘住、clew free。
#     course：clew ＝ earing 往中線收 spread、z ＝ max(帆桁高 − depth_over_length × 桁長, 那一欄甲板面 ＋ min_above_deck)；sheet、tack 照 plan 的固定點。
#     spritsail：clew ＝ earing 往中線收、z ＝ 帆桁高 − depth_over_length × 桁長；sheet 落艏樓 kevel。
#     topsail 以上：clew ＝ 下一根帆桁同舷 earing ＋ dz，sheet 綁那個 earing；後上桅帆的 clew 在帆桁正下方的平台上、sheet 綁平台前緣中線。
#   · lateen：角 tack（earing-F）、peak（earing-A）、clew（座標）；邊 0（沿帆桁）釘住、clew free；sheet 兩舷落艉樓 kevel。
#   · 貼圖：每面一張像素畫（textures/<帆名>.png，最長邊 max_px），底色＋雜訊＋補丁、圓洞（alpha 0）、帆腳撕爛；亂數種子 ＝ 帆名的 crc32 ⇒ 重跑一樣。
#     圖的左上角 ＝ 角 0、欄沿 角 0→角 1、列沿 角 0→角 3（三角帆 角 0→角 2）—— CLI help 寫的對應。
#   · meta（造船規格 §9.1）：帆 kind=sail、mast、sail（＋set）；帆自己的繩 kind=sheet／tack、sail=<帆名> ⇒ sails_meta.tsv（work sub=meta file=）。
#   · 檢查：平的布（模擬之前）每面 60×60 取樣、離釘住的邊 < 1.2 格的不算，落在實心的數（按件分）；帆腳索碰撞同動索（中段要 0）。
#   · 重跑逐位元組相同。
import sys, os, json, math, zlib, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_running
from draft_running import Run, G

draft_running.LINKKEY.update({'channels': 'channels_S', 'channels-鏡像': 'channels_P'})


def seg_dist(p, a, b):
    p, a, b = np.asarray(p), np.asarray(a), np.asarray(b); ab = b - a
    t = np.clip((p - a) @ ab / (ab @ ab), 0, 1); return float(np.linalg.norm(p - (a + t * ab)))


def texture(name, w_cells, h_cells, T, tri=False):
    sc = T['max_px'] / max(w_cells, h_cells)
    W, H = max(8, int(round(w_cells * sc))), max(8, int(round(h_cells * sc)))
    rng = np.random.default_rng(zlib.crc32(name.encode('utf-8')))
    base = np.array(T['base'], float)
    img = np.zeros((H, W, 4), np.uint8)
    rgb = base + rng.integers(-T['noise'], T['noise'] + 1, size=(H, W, 1))
    # 補丁（深一點的方塊）
    for _ in range(max(1, W * H // 1500)):
        x0, y0 = rng.integers(0, W - 4), rng.integers(0, H - 4); pw, ph = rng.integers(3, 9), rng.integers(3, 9)
        rgb[y0:y0 + ph, x0:x0 + pw] = np.array(T['patch'], float) + rng.integers(-6, 7)
    img[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8); img[:, :, 3] = 255
    yy, xx = np.mgrid[0:H, 0:W]
    n = max(1, int(round(W * H / 10000 * T['holes_per_10k_px'])))
    for _ in range(n):
        cx, cy = rng.uniform(0.1 * W, 0.9 * W), rng.uniform(0.15 * H, 0.95 * H)
        r = rng.uniform(*T['hole_r'])
        img[(xx - cx) ** 2 + ((yy - cy) * rng.uniform(0.7, 1.3)) ** 2 <= r * r, 3] = 0
    # 帆腳撕爛：隨機漫步的鋸齒邊（🩸 第一版每一欄各自隨機 ⇒ 看起來像一排梳齒）＋ 幾道從帆腳往上、越上越窄的撕裂口
    walk = np.cumsum(rng.integers(-1, 2, size=W)); walk = walk - walk.min()
    rag = np.clip(np.round(walk * T['tatter_px'] / max(1, walk.max())), 0, T['tatter_px']).astype(int)
    for x in range(W):
        if rag[x]: img[H - rag[x]:, x, 3] = 0
    for _ in range(int(rng.integers(1, 4))):
        x0 = rng.uniform(0.1 * W, 0.9 * W); ln = rng.uniform(0.12, 0.35) * H; wd = rng.uniform(1.0, 2.5)
        for k in range(int(ln)):
            hw = wd * (1 - k / ln); xc = x0 + rng.uniform(-0.6, 0.6)
            img[H - 1 - k, max(0, int(xc - hw)):min(W, int(xc + hw) + 1), 3] = 0
    if tri:   # 三角帆：只畫 角0–角1–角2 那一半（欄沿 0→1、列沿 0→2 ⇒ u + v ≤ 1）
        img[(xx / (W - 1) + yy / (H - 1)) > 1.0, 3] = 0
    return Image.fromarray(img, 'RGBA'), (W, H)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8')); S = plan['sails']
    r = Run(d); r.yard_anchors(); r.mast_anchors(); r.build()
    run_names = {x['name'] for x in r.ropes}; r.ropes = []
    NY = r.w.NY; YC = r.YC
    for a in json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))['anchors']['channels']:
        c = [a['world'][i] + 0.5 for i in range(3)]
        r.pt['channels/' + a['name']] = c; r.pt['channels-鏡像/' + a['name']] = [c[0], NY - c[1], c[2]]
    side_pt = lambda tpl, sd: (tpl % sd) if '%s' in tpl else (tpl if sd == 'S' else tpl.replace('channels/', 'channels-鏡像/'))
    sails = []; meta = []; tex = {}
    td = os.path.join(d, 'textures'); os.makedirs(td, exist_ok=True)
    for f in os.listdir(td): os.remove(os.path.join(td, f))

    def sail(name, corners, names, world, bind, free, fullness, note, smeta, tri=False):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'corners_world': [[round(float(c), 4) for c in w] for w in world],
                      'bind': bind, 'free': free, 'fullness': fullness, 'color': S['color'], 'note': note, 'texture': 'textures/%s.png' % name})
        for n, w in zip(names, world): r.pt['sail:%s/%s' % (name, n)] = list(w)
        Wd = [np.array(w, float) for w in world]
        wc = float(np.linalg.norm(Wd[1] - Wd[0])); hc = float(np.linalg.norm(Wd[-1] - Wd[0]) if not tri else np.linalg.norm(Wd[2] - Wd[0]))
        im, wh = texture(name, wc, hc, S['texture'], tri)
        im.save(os.path.join(td, name + '.png'), optimize=False)
        tex[name] = {'px': list(wh), 'sha256': hashlib.sha256(open(os.path.join(td, name + '.png'), 'rb').read()).hexdigest()}
        meta.append(('sail', name, smeta))

    def sheet(name, fr, to, kind, sname, thick, slack=None, group=None):
        r.rope(name, fr, to, 'brace', group or ('running/sheets' if kind == 'sheet' else 'running/tacks'), slack)
        r.ropes[-1]['kind'] = kind; r.ropes[-1]['thickness'] = thick
        meta.append(('rope', name, {'kind': kind, 'sail': sname}))

    C = S['course']; Tk = S['sheet_thickness']
    for nm, spec in S['square'].items():
        P = r.Y[nm]; L = P['meta']['length_m'] * 10; zy = P['at'][2]
        hp, hs = r.ymodel(nm, 'earing-P'), r.ymodel(nm, 'earing-S')
        sm = {'kind': 'sail', 'mast': spec['mast'], 'sail': spec['type']}
        if 'set' in spec: sm['set'] = spec['set']
        if spec['lower'] is None:
            K = C if nm != 'spritsail' else S['spritsail']
            zf = zy - K['depth_over_length'] * L
            if nm != 'spritsail':
                dt = r.w.deck_top(int(P['at'][0]))
                zf = max(zf, dt[0] + 1 + C['min_above_deck'])
            def clew(e): return [e[0], YC + 0.5 + K['spread'] * (e[1] - YC - 0.5), zf]
            cs, cp = clew(r.pt[hs]), clew(r.pt[hp]); note = 'course 型：sheet／tack 照 plan'
        elif spec['lower'] == 'top':
            # 🩸 第一版帆角收在平台的 rim-fwd（桅軸前 3 格）⇒ 帆從前面的帆桁斜到後面，整張穿過上桅（平的布 294 個取樣）
            #    ⇒ 帆角就在帆桁正下方（x ＝ 帆桁）、中線兩側 half_spread、平台頂面上 dz；sheet 綁平台前緣中線
            M = S['mizzen_topsail_clew']; tf = r.pt[M['sheet']]
            cs = [P['at'][0], YC + 0.5 + M['half_spread'], tf[2] + S['mizzen_topsail_clew_dz']]
            cp = [P['at'][0], YC + 0.5 - M['half_spread'], tf[2] + S['mizzen_topsail_clew_dz']]
            note = '後上桅帆：帆角在帆桁正下方的平台上（沒有 crossjack）'
        else:
            ls, lp = r.ymodel(spec['lower'], 'earing-S'), r.ymodel(spec['lower'], 'earing-P')
            cs = [r.pt[ls][0], r.pt[ls][1], r.pt[ls][2] + S['topsail_clew_dz']]; cp = [r.pt[lp][0], r.pt[lp][1], r.pt[lp][2] + S['topsail_clew_dz']]
            note = 'sheet 綁下一根帆桁（%s）同舷的 earing' % spec['lower']
        sail(nm, [hp, hs, G(cs), G(cp)], ['head_p', 'head_s', 'clew_s', 'clew_p'], [r.pt[hp], r.pt[hs], cs, cp], '0', 'clew_s,clew_p',
             S['fullness']['square'], note + '（階段十）', sm)
        for sd, cl in (('S', 'clew_s'), ('P', 'clew_p')):
            a = 'sail:%s/%s' % (nm, cl)
            if nm in ('main-course', 'fore-course'):
                sheet('%s-sheet-%s' % (nm, sd), a, side_pt(C[nm]['sheet'], sd), 'sheet', nm, Tk['course'], C['sheet_slack'])
                sheet('%s-tack-%s' % (nm, sd), a, side_pt(C[nm]['tack'], sd), 'tack', nm, Tk['course'], C['tack_slack'])
            elif nm == 'spritsail':
                sheet('%s-sheet-%s' % (nm, sd), a, S['spritsail']['sheet'] % sd, 'sheet', nm, Tk['course'])
            elif spec['lower'] == 'top':
                sheet('%s-sheet-%s' % (nm, sd), a, S['mizzen_topsail_clew']['sheet'], 'sheet', nm, Tk['topsail'])
            else:
                sheet('%s-sheet-%s' % (nm, sd), a, r.ymodel(spec['lower'], 'earing-' + sd), 'sheet', nm, Tk['topsail'])
    # lateen
    Lt = S['lateen']; nm = Lt['name']
    tk, pk = r.ymodel(nm, 'earing-F'), r.ymodel(nm, 'earing-A')
    yv = r.Y[nm]['at'][1]
    zc = r.w.deck_top(Lt['clew_x'])[0] + 1 + Lt['clew_above_deck']
    clew = [Lt['clew_x'] + 0.5, yv, zc + 0.5]
    sail(nm, [tk, pk, G(clew)], ['tack', 'peak', 'clew'], [r.pt[tk], r.pt[pk], clew], '0', 'clew', S['fullness']['lateen'],
         'lateen：沿帆桁那條邊釘住、後下角 free（階段十）', {'kind': 'sail', 'mast': 'mizzen', 'sail': 'gaff'}, tri=True)
    for sd in ('S', 'P'):
        sheet('%s-sheet-%s' % (nm, sd), 'sail:%s/clew' % nm, Lt['sheet'] % sd, 'sheet', nm, Tk['lateen'])
    # 平的布碰撞
    lab, names = r.w.lab, r.w.names
    cloth = {}
    for sl in sails:
        W = [np.array(w, float) for w in sl['corners_world']]; n = len(W)
        bound = [int(b) for b in sl['bind'].split(',') if b != '']
        pts = []
        if n == 4:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1, 60):
                    pts.append((1 - u) * (1 - v) * W[0] + u * (1 - v) * W[1] + u * v * W[2] + (1 - u) * v * W[3])
        else:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1 - u, max(2, int(60 * (1 - u)))):
                    pts.append(W[0] + u * (W[1] - W[0]) + v * (W[2] - W[0]))
        hit = {}
        for p in pts:
            if any(seg_dist(p, W[b], W[(b + 1) % n]) < 1.2 for b in bound): continue
            v = lab[tuple(int(math.floor(x)) for x in p)]
            if v: hit[names[v]] = hit.get(names[v], 0) + 1
        cloth[sl['name']] = hit
    mid, land = r.collide()
    with open(os.path.join(d, 'sails_meta.tsv'), 'w', encoding='utf-8', newline='\n') as fo:
        fo.write('# 階段十：帆與帆自己的繩的 meta（造船規格 §9.1）—— senate cmd sculpture --arg op=work --arg sub=meta --arg file=<這個檔的絕對路徑>\n')
        for part, name, m in meta: fo.write('%s\t%s\t%s\n' % (part, name, json.dumps(m, ensure_ascii=False, sort_keys=True)))
    V = {'wind': S['wind'], 'seconds': S['seconds'], 'sails': sails, 'ropes': r.ropes, 'textures': tex, 'meta': [list(x) for x in meta],
         'flat_cloth_hits': cloth, 'rope_hits_mid': mid, 'rope_landing_cells': land,
         'landing_over_bound': sorted(k for k, x in land.items() if x['over'])}
    with open(os.path.join(d, 'verify_sails.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('flat_cloth_hits', 'rope_hits_mid', 'landing_over_bound', 'textures')}, ensure_ascii=False, indent=1))
    print('sails', len(sails), 'ropes', len(r.ropes), 'meta', len(meta))
    print({s['name']: s['corners_world'] for s in sails})


if __name__ == '__main__':
    main()

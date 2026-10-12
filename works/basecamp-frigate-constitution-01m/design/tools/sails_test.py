# 掛帆試試（2026-10-11，TASK-0503 的帆）：方帆 11、spanker、三角帆 3 ⇒ design/sails_test.json；--apply 一條一條下 CLI
# 用法：python -I sails_test.py <design 資料夾> [--apply]
#   · 方帆：上緣（邊 0）整條釘在帆桁的兩個 earing 之間；下兩角 free，帆腳索（sheet）綁到下一根帆桁同舷的 earing
#   · course：下兩角 free，sheet 往後、tack 往前綁到舷牆 pin rail 的 belaying pin（S 繫繩欄／P 繫繩欄-鏡像）
#   · spanker：throat、peak（gaff）、clew、tack（boom）四角都釘；gaff、boom、桅那三條邊釘住，只有後緣（leech）自由
#   · 三角帆：tack 釘在 bowsprit／jibboom 那個 stay 下端的固定點，head 釘在 stay 上（前桅子作品裡登記一個點），clew free、兩舷各一條 sheet 到前甲板的 pin
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
APPLY = '--apply' in sys.argv
PRE = 'basecamp-frigate-constitution-01m'
ASM = PRE + '-assembly'
YC = 160
L = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅'}
SAIL_C, RUN_C = '#f2ead8', '#a08458'           # 帆布、動索（沒上焦油的麻）
WIND, SECONDS = '4.5,-1.5,0', 4                 # 從右舷後方吹來（往 +x、−y）；v1 用 7,-3,0（7.6 m/s）⇒ 方帆鼓 76–106 格、像降落傘 ⇒ 降

YP = {q['name']: q['world'] for q in json.load(open(os.path.join(D, 'rig_points_yards.json'), encoding='utf-8'))['points']}
RS = {a['link'] + '/' + a['name']: a['world'] for a in json.load(open(os.path.join(D, 'rig_standing.json'), encoding='utf-8'))['anchors']}
BP = {q['name']: q['world'] for q in json.load(open(os.path.join(D, 'rig_points_belaying.json'), encoding='utf-8'))['points'] if q['side'] == 'S' and not q.get('via')}
for k in ('pinrail-4.pin-3', 'pinrail-8.pin-3', 'pinrail-11.pin-3', 'pinrail-13.pin-3', 'pinrail-13.pin-5'):
    assert k in BP, k

xyz = lambda p: '%g,%g,%g' % tuple(p)
sails, ropes, anchors, stays = [], [], [], []


def sail(name, corners, names, bind, free, fullness, note):
    sails.append({'name': name, 'corners': '|'.join(corners), 'corner_names': '|'.join(names), 'bind': bind, 'free': free,
                  'fullness': fullness, 'color': SAIL_C, 'note': note})


def rope(name, a, b, th=0.4, slack=1.0, note=''):
    ropes.append({'name': name, 'from': a, 'to': b, 'thickness': th, 'slack': slack, 'color': RUN_C, 'note': note})


# ── 方帆 ──
SQUARE = {'fore': ['course', 'topsail', 'topgallant', 'royal'], 'main': ['course', 'topsail', 'topgallant', 'royal'], 'mizzen': ['topsail', 'topgallant', 'royal']}
LOWER = {'topsail': 'course', 'topgallant': 'topsail', 'royal': 'topgallant'}
COURSE = {'fore': {'foot_z': 145, 'sheet': 11, 'tack': 13}, 'main': {'foot_z': 150, 'sheet': 4, 'tack': 8}}
for m, lst in SQUARE.items():
    for s in lst:
        mem = '%s-%s' % (m, s)
        head = ['%s/%s.earing-P' % (L[m], mem), '%s/%s.earing-S' % (L[m], mem)]
        if s == 'course':
            e, eP = YP[mem + '.earing-S'], YP[mem + '.earing-P']
            C = COURSE[m]
            cs = (e[0], YC + round(0.8 * (e[1] - YC)), C['foot_z'])
            cp = (eP[0], YC + round(0.8 * (eP[1] - YC)), C['foot_z'])     # 2026-10-12 brace：左舷讀左舷自己的 earing（原本是右舷鏡過去，帆桁轉了就不對）
            sail(mem, head + [xyz(cs), xyz(cp)], ['head_p', 'head_s', 'clew_s', 'clew_p'], '0', 'clew_s,clew_p', 1.05,
                 'course：sheet 往後、tack 往前綁到舷牆 belaying pin')
            for sd, cl, lk in (('S', 'clew_s', '繫繩欄'), ('P', 'clew_p', '繫繩欄-鏡像')):
                rope('%s.sheet-%s' % (mem, sd), 'sail:%s/%s' % (mem, cl), '%s/pinrail-%d.pin-3' % (lk, C['sheet']), 0.5, slack=0.85, note='course sheet（收短 15% ⇒ 下角往後下拉；v1 slack 1 下角被風吹得往前往上）')
                rope('%s.tack-%s' % (mem, sd), 'sail:%s/%s' % (mem, cl), '%s/pinrail-%d.pin-3' % (lk, C['tack']), 0.5, slack=0.8, note='course tack（收短 20%；2026-10-12 照 kotoko：slack 1 時 tack 垂 21–26 格、下角被吹高 7–12 格）')
        else:
            low = 'crossjack' if (m == 'mizzen' and s == 'topsail') else LOWER[s]
            el, elP = YP['%s-%s.earing-S' % (m, low)], YP['%s-%s.earing-P' % (m, low)]
            cs = (el[0], el[1], el[2] + 3)
            cp = (elP[0], elP[1], elP[2] + 3)                                  # 同上：左舷讀左舷
            sail(mem, head + [xyz(cs), xyz(cp)], ['head_p', 'head_s', 'clew_s', 'clew_p'], '0', 'clew_s,clew_p', 1.05,
                 'sheet 綁到下一根帆桁（%s）同舷的 earing' % low)
            for sd, cl in (('S', 'clew_s'), ('P', 'clew_p')):
                rope('%s.sheet-%s' % (mem, sd), 'sail:%s/%s' % (mem, cl), '%s/%s-%s.earing-%s' % (L[m], m, low, sd), 0.35, note='topsail 以上的 sheet')

# ── spanker ──
sail('spanker', ['後桅/spanker-gaff.top8', '後桅/spanker-gaff.top120', '後桅/spanker-boom.top176', '後桅/spanker-boom.top8'],
     ['throat', 'peak', 'clew', 'tack'], '0,2,3', '', 1.05, 'gaff、boom、桅三條邊釘住，只有 leech 自由')

# ── 三角帆（stay 改拉直，head 落在 stay 上）──
HEAD = [('fore-topmast-staysail', 'fore-topmast-stay', '前桅/tm-stay-out', '艏斜桅/cap', 0.75, (690, 205)),
        ('jib', 'jib-stay', '前桅/tg-head', '艏斜桅/jibboom-end', 0.70, (770, 225)),
        ('flying-jib', 'flying-jib-stay', '前桅/royal-stay-out', '艏斜桅/flying-end', 0.80, (850, 250))]
for nm, stay, top, bot, f, (cx, cz) in HEAD:
    T, Hd = RS[bot], RS[top]
    h = [int(round(T[i] + f * (Hd[i] - T[i]))) for i in range(3)]
    anchors.append({'work': PRE + '-mast-fore', 'name': nm + '.head', 'at': h})
    stays.append(stay)
    # clew 要在 luff（tack → head 那條線）的下後方
    zl = T[2] + (T[0] - cx) / (T[0] - Hd[0]) * (Hd[2] - T[2])
    assert cz < zl - 40, (nm, cz, zl)
    sail(nm, [bot, '前桅/%s.head' % nm, xyz((cx, YC, cz))], ['tack', 'head', 'clew'], '0', 'clew', 1.06, 'luff（邊 0）沿 %s' % stay)
    for sd, lk in (('S', '繫繩欄'), ('P', '繫繩欄-鏡像')):
        rope('%s.sheet-%s' % (nm, sd), 'sail:%s/clew' % nm, '%s/pinrail-13.pin-5' % lk, 0.35, note='三角帆 sheet')

out = {'wind': WIND, 'sail_seconds': SECONDS, 'anchors': anchors, 'stays_straight': stays, 'sails': sails, 'ropes': ropes}
json.dump(out, open(os.path.join(D, 'sails_test.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('sails', len(sails), 'ropes', len(ropes), 'anchors', len(anchors))


def cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'persona=basecamp'] + sum([['--arg', a] for a in args], []),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print('✗', args[:3], (r.stdout + r.stderr)[-500:])
    return r.returncode, r.stdout


if APPLY:
    for a in anchors:
        cli(['sub=anchor', 'work=' + a['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=三角帆的 head（落在 stay 上；sails_test）'])
    for s in stays:
        cli(['sub=rope', 'work=' + ASM, 'name=' + s, 'slack=1'])
    cli(['sub=wind', 'work=' + ASM, 'wind=' + WIND, 'sail_seconds=%d' % SECONDS])
    for s in sails:
        args = ['sub=sail', 'work=' + ASM, 'name=' + s['name'], 'corners=' + s['corners'], 'corner_names=' + s['corner_names'], 'bind=' + s['bind'],
                'fullness=%g' % s['fullness'], 'color=' + s['color'], 'overwrite=1', 'note=' + s['note']]
        if s['free']:
            args.append('free=' + s['free'])
        cli(args)
    for r in ropes:
        cli(['sub=rope', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1', 'slack=%g' % r['slack'],
             'color=' + r['color'], 'thickness=%g' % r['thickness'], 'note=' + r['note']])
    rc, o = cli(['sub=sails', 'work=' + ASM])
    print('\n'.join(l for l in o.splitlines() if l.startswith('🔢') or 'broken' in l or '🔴' in l)[-1500:])

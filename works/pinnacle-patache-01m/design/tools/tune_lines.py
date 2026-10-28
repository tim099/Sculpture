# 聖羅曼號 步驟 3：掃線形的長度收縮參數（s_aft、s_fwd、aft_pow）對 1618 art.21 的 mura／cuadra 寬（只讀 plan、不寫檔）
#   python -I -X utf8 tools/tune_lines.py <design>
import itertools, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import lines as HL
import draft_lines as DL

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
base = HL.load_plan(design)
rows = []
for sa, sf, qa in itertools.product([0.45, 0.5, 0.55], [0.51, 0.55, 0.59], [1.2, 1.5, 2.0]):
    plan = HL.load_plan(design)
    plan['lines']['s_aft']['v'], plan['lines']['s_fwd']['v'], plan['lines']['aft_pow']['v'] = sa, sf, qa
    L = HL.Lines(plan)
    x0, ylo, S, dist = DL.hull_volume(L, plan)
    wall, col = DL.shell_colors(plan, S, dist)
    R = DL.readings(L, plan, S, wall, x0, ylo)
    o = R['ordenanza_check']
    err = abs(o['beam_mura'] - o['want_mura']) + abs(o['beam_cuadra'] - o['want_cuadra'])
    rows.append((err, sa, sf, qa, o['beam_mura'], o['want_mura'], o['beam_cuadra'], o['want_cuadra'], R['displacement_t_at_wl'], R['cavity_cells'], R['components_6']))
for r in sorted(rows)[:8]:
    print('err %.1f  s_aft %.2f s_fwd %.2f aft_pow %.1f  mura %d/%.1f cuadra %d/%.1f  disp %.1f t  cav %d comp %d' % r)

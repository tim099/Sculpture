# 階段六讀數（TASK-0611）：桅子作品結果帳（匯出 vs 清單）、帆桁模型（作品裡登記的 at／pivot／rotate／scale／meta）vs 設計、models_broken
#   用法：python -I -X utf8 tools/check_stage6.py <design> [--probe=<帆桁名>:<dz>]（反向對照：讀完作品之後把設計的那一根 at.z 偏 dz，要只報那一根）
import json, os, re, subprocess, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key  # noqa: E402

pl = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))
tot = [0, 0, 0, 0]
for k, m in pl['masts'].items():
    W = export_list(m['work'], None)
    D = np.loadtxt(os.path.join(design, 'masks', 'masts', k + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    mi, ex = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    c = sum(1 for q in set(cd) & set(cw) if cd[q] != cw[q])
    print('  %-9s 作品 %6d、設計 %6d、缺 %d、多 %d、色差 %d' % (k, len(W), len(D), mi, ex, c))
    tot = [tot[0] + len(W), tot[1] + mi, tot[2] + ex, tot[3] + c]
print('桅結果帳：%d 件、作品 %d 格、缺 %d、多 %d、色差 %d' % ((len(pl['masts']),) + tuple(tot)))

got = {}
broken = 0
for m in pl['masts'].values():
    out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=models', '--arg', 'work=' + m['work']],
                         capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    broken += int(re.search(r'models_broken = (\d+)', out).group(1)) if 'models_broken' in out else 0
    for line in out.splitlines():
        mm = re.search(r"`(yard-[^`]+)`.*?at ([-\d.]+),([-\d.]+),([-\d.]+)、pivot ([-\d.]+),([-\d.]+),([-\d.]+)(?:、rotate ([-\d.]+),([-\d.]+),([-\d.]+)°?)?(?:、scale ([-\d.,]+))?", line)
        if mm:
            g = mm.groups()
            sc = [float(v) for v in g[10].split(',')] if g[10] else [1.0]          # scale 1 時 CLI 不印
            got[g[0]] = {'at': [float(v) for v in g[1:4]], 'pivot': [float(v) for v in g[4:7]], 'rotate': [float(v) for v in g[7:10]] if g[7] else [0, 0, 0],
                         'scale': sc * 3 if len(sc) == 1 else sc, 'meta_line': line}
if probe:
    nm, dz = probe.split(':')
    for yd in pl['yards']:
        if yd['name'] == nm:
            yd['model']['at'][2] += float(dz)
bad = []
for yd in pl['yards']:
    md = yd['model']
    g = got.get(md['name'])
    if g is None:
        bad.append((md['name'], '作品裡沒有'))
        continue
    for f in ('at', 'pivot', 'rotate', 'scale'):
        if any(abs(a - b) > 1e-3 for a, b in zip(g[f], md[f])):
            bad.append((md['name'], f, g[f], md[f]))
    if 'kind=yard' not in g['meta_line'] or ('sail' in md['meta'] and 'sail=' + md['meta']['sail'] not in g['meta_line']):
        bad.append((md['name'], 'meta'))
print('帆桁模型：作品 %d 根、設計 %d 根、at／pivot／rotate／scale／meta 跟設計不同 %d %s；models_broken %d' % (len(got), len(pl['yards']), len(bad), bad[:3], broken))

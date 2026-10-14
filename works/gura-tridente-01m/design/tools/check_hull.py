# 階段二（TASK-0555）讀數：作品匯出 vs 清單（結果帳）、線形對照（每站每個高度的外緣 vs hull_lines 的半寬）、反向對照
#   用法：python -I -X utf8 tools/check_hull.py <design> [mark=船殼:end]
#   · 作品那一側一律從 CLI 匯出讀（export format=list links=none）—— ⛔ 不讀自己的清單當作品
import os, subprocess, sys, tempfile, json, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), '船殼:end')
sys.path.insert(0, design)
import hull_lines as HL

WORK = 'gura-tridente-01m'


def export_list(work, mark):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out,
                            '--arg', 'links=none', '--arg', 'mark=' + mark], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def load_lists(folder):
    rows = []
    for f in sorted(os.listdir(folder)):
        if f.endswith('.vox.txt'):
            rows.append(np.loadtxt(os.path.join(folder, f), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8'))
    return np.concatenate(rows)


def key(a):
    return (a[:, 0].astype(np.int64) * 1000 + a[:, 1]) * 1000 + a[:, 2]


W = export_list(WORK, mark)
D = load_lists(os.path.join(design, 'masks', 'hull'))
kw, kd = key(W), key(D)
cw = dict(zip(kw.tolist(), W[:, 3].tolist()))
cd = dict(zip(kd.tolist(), D[:, 3].tolist()))
miss = len(set(cd) - set(cw))
extra = len(set(cw) - set(cd))
cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
print('結果帳：作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(W), len(D), miss, extra, cdiff))

# 線形對照：右舷外緣（每個 (x, z) 最大的 dy）vs floor(hb)
plan = HL.load_plan(design)
L = HL.Lines(plan)
YC = L.YC
S = W[W[:, 1] >= YC]
outer = {}
for x, y, z in S[:, :3].tolist():
    k = (x, z)
    if y - YC > outer.get(k, -1):
        outer[k] = y - YC
probe_x = int(next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('probe_x=')), '-1'))
diffs, worst = [], (0, None)
for x in range(80, 720, 25):
    for z in range(6, 176, 5):
        if z > L.top_z(x + 0.5):
            continue
        h = float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0])
        if h < 0:
            continue
        want = math.floor(h) + (3 if x == probe_x else 0)
        got = outer.get((x, z))
        if got is None:
            continue
        dlt = got - want
        diffs.append(abs(dlt))
        if abs(dlt) > abs(worst[0]):
            worst = (dlt, (x, z, got, want))
print('線形對照：%d 點、|差| 最大 %d（%s）、差 ≥ 2 的 %d 點%s' % (len(diffs), max(diffs), worst[1], sum(1 for v in diffs if v >= 2),
      '（probe_x=%d：設計那一站 +3）' % probe_x if probe_x >= 0 else ''))

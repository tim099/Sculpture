# 來源：apex-one-reale-01m/design/tools/wio.py（照抄）；原始來源 calli-cosecha-01m/design/tools/wio.py（照抄；calli 的又抄自 gura-tridente-01m）
# 階段讀數共用：作品匯出（CLI export format=list）、讀清單、格子的鍵
import os, subprocess, tempfile
import numpy as np


def export_list(work, mark, links='none'):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out,
                            ] + (['--arg', 'links=' + links] if links else []) + (['--arg', 'mark=' + mark] if mark else []), capture_output=True, text=True, encoding='utf-8', errors='replace')
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

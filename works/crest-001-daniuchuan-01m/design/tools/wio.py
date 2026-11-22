# 出處：calli-cosecha-01m/design/tools/wio.py（依 crest-001-daniuchuan-01m 調整）：作品匯出、CLI 呼叫、讀清單
import os, subprocess, tempfile
import numpy as np

PERSONA = 'crest-001'
HULL = 'crest-001-daniuchuan-01m'
ASM = HULL + '-assembly'


def cli(*args, ok=(0,)):
    cmd = ['senate', 'cmd', 'sculpture']
    for kv in args:
        cmd += ['--arg', kv]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit(f'✗ exit {r.returncode}：{" ".join(args)}')
    return out


def export_list(work, mark=None, links='none'):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list',
               '--arg', 'work=' + work, '--arg', 'out=' + out]
        if links:
            cmd += ['--arg', 'links=' + links]
        if mark:
            cmd += ['--arg', 'mark=' + mark]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
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

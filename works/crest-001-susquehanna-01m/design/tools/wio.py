# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/wio.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 抄自三叉戟號 gura-tridente-01m/design/tools/wio.py（gura）。
# 階段讀數共用：作品匯出（CLI export format=list）、讀清單、格子的鍵
import os, subprocess, tempfile
import numpy as np


def export_list(work, mark):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out,
                            '--arg', 'links=none'] + (['--arg', 'mark=' + mark] if mark else []), capture_output=True, text=True, encoding='utf-8', errors='replace')
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

"""威尼斯 galeazza（TASK-1302）結果帳：作品實際匯出（export format=list）對設計清單逐格比（缺／多／色差）。

用法：python -I -X utf8 check_hull.py <匯出清單> <設計清單…> [--probe-shift=N]
  --probe-shift=N ⇒ 反向對照：把設計清單整份往 +x 推 N 格再比，尺要報出差（不該是 0）。
結果寫 verify_result.json（帶匯出檔的 sha256）。
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent


def load(p):
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int64, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a[:, :4]}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    shift = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--probe-shift=')), '0'))
    got = load(args[0])
    want = {}
    for p in args[1:]:
        for (x, y, z), c in load(p).items():
            want[(x + shift, y, z)] = c
    missing = [k for k in want if k not in got]
    extra = [k for k in got if k not in want]
    color = [k for k in want if k in got and got[k] != want[k]]
    res = {
        'export': args[0], 'export_sha256': hashlib.sha256(Path(args[0]).read_bytes()).hexdigest(),
        'design': args[1:], 'probe_shift': shift,
        'cells_export': len(got), 'cells_design': len(want),
        'missing': len(missing), 'extra': len(extra), 'color_diff': len(color),
        'samples': {'missing': missing[:5], 'extra': extra[:5], 'color': color[:5]},
    }
    if not shift:
        (D / 'verify_result.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in res.items() if k != 'samples'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""改了設計清單 ⇒ 作品對清單的差分：舊清單沒有、新清單有 ⇒ stampvox；舊有新無 ⇒ carvevox（帶原色守門）；同格換色 ⇒ 先刻再貼。
出處：calli-cosecha-01m/design/tools/delta_apply.py 的做法（自己寫的簡版，persona summit）。
用法：python -I -X utf8 tools/apply_delta.py <work> <舊清單> <新清單> <暫存資料夾>
"""
import subprocess
import sys
from pathlib import Path


def load(p):
    out = {}
    for l in Path(p).read_text(encoding='utf-8').splitlines():
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(',')[:4])
            out[(x, y, z)] = c
    return out


def cli(*args):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'persona=summit', *sum((['--arg', a] for a in args), [])],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(r.stdout[-2000:])
    return r.stdout


def main():
    work, old, new, tmp = sys.argv[1], load(sys.argv[2]), load(sys.argv[3]), Path(sys.argv[4])
    rem = {k: v for k, v in old.items() if k not in new or new[k] != v}
    add = {k: v for k, v in new.items() if k not in old or old[k] != v}
    tmp.mkdir(parents=True, exist_ok=True)
    if rem:
        p = tmp / f'{work}_rem.txt'
        p.write_text(''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(rem.items())), encoding='ascii')
        cli('op=carvevox', f'work={work}', f'voxels={p.as_posix()}', 'at=0,0,0', 'share=0')
    if add:
        p = tmp / f'{work}_add.txt'
        p.write_text(''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(add.items())), encoding='ascii')
        out = cli('op=stampvox', f'work={work}', f'voxels={p.as_posix()}', 'at=0,0,0', f'expect_pixels={len(add)}', 'share=0')
        assert f'placed = {len(add)}' in out or f'placed={len(add)}' in out.replace(' ', ''), out[-800:]
    print(f'{work}: carved {len(rem)}, stamped {len(add)}')


if __name__ == '__main__':
    main()

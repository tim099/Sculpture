# 下 senate cmd sculpture 的小工具：每一刀照實印 rc 與讀數；失敗就丟例外（⛔ 不靜默往下跑）。
import subprocess, re, json, sys

PERSONA = 'erina'
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def run(args, ok_rc=(0,), quiet=False):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok_rc:
        raise RuntimeError('rc=%d %s\n%s' % (r.returncode, ' '.join(args[:5]), out[-1500:]))
    if not quiet:
        print('  rc=%d %s' % (r.returncode, ' '.join(a[:60] for a in args[:4])))
    return r.returncode, out


def val(out, key):
    m = re.search(r'🔢 %s = (.*)' % re.escape(key), out)
    return m.group(1).strip() if m else None


def ensure_work(wid, title, size, parent, mpv, tags='sub'):
    rc, out = run(['op=work', 'sub=show', 'work=' + wid], ok_rc=(0, 2, 5), quiet=True)
    if rc != 0:
        run(['op=work', 'sub=create', 'persona=' + PERSONA, 'id=' + wid, 'title=' + title, 'size=' + ','.join(map(str, size)), 'parent_work=' + parent, 'tags=' + tags])
    run(['op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + wid, 'meters_per_voxel=%g' % mpv, 'tags=' + tags, 'size=' + ','.join(map(str, size))])


def stamp(wid, path, cells, at=(0, 0, 0)):
    rc, out = run(['op=stampvox', 'persona=' + PERSONA, 'work=' + wid, 'voxels=' + path.replace('\\', '/'), 'at=' + ','.join(map(str, at)),
                   'expect_pixels=%d' % cells, 'draft=0', 'share=0'])
    placed = val(out, 'placed') or val(out, 'placed_voxels')
    print('  stamp %s cells %d placed %s' % (wid, cells, placed))
    if placed is None or int(placed.replace(',', '')) != cells:
        raise RuntimeError('placed 對不上：' + out[-1200:])
    return out


def anchor(wid, name, at, note=''):
    run(['op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + wid, 'name=' + name, 'at=' + ','.join('%g' % c for c in at), 'overwrite=1'] + (['note=' + note] if note else []), quiet=True)


def xyz(v):
    return ','.join('%g' % c for c in v)

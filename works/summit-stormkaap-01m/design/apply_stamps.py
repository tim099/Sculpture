# 照 verify_*.json 的 stamp_order 一刀一刀下 CLI（stampvox／carvevox），每刀讀回 placed（carvevox 讀 carved），對不上就停。
# 用法：python -I -X utf8 -B apply_stamps.py <design 資料夾> <verify json 檔名> <作品 id> [--key <stamp_order 的鍵>] [--from N] [--to M（不含）] [--dry]
#   · stamp_order 是 list ⇒ 全部；是 dict ⇒ 只跑 --key 那一份。
#   · 每項 {name, file, at, expect_pixels, op?(stampvox), overwrite?}。
#   · 停下來時印「從第 N 項接」—— 夜隼號學過：停了先看已經落地幾刀，⛔ 不要整支重跑。
#   · 讀回走 stdout 的「🔢 placed = N」（carvevox 是「🔢 carved_count」或 placed —— 兩個都試，照實際印的）。
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, vfile, work = os.path.abspath(sys.argv[1]), sys.argv[2], sys.argv[3]
args = sys.argv[4:]
key = args[args.index('--key') + 1] if '--key' in args else None
start = int(args[args.index('--from') + 1]) if '--from' in args else 0
end = int(args[args.index('--to') + 1]) if '--to' in args else None   # 不含
dry = '--dry' in args
V = json.load(open(os.path.join(D, vfile), encoding='utf-8'))['stamp_order']
L = V[key] if isinstance(V, dict) else V


def cli(a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', x] for x in a], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


total = 0
for i, o in enumerate(L):
    if i < start: continue
    if end is not None and i >= end: break
    op = o.get('op', 'stampvox')
    path = os.path.join(D, o['file']).replace('\\', '/')
    a = ['op=' + op, 'persona=summit', 'work=' + work, 'voxels=' + path, 'at=' + ','.join(str(v) for v in o.get('at', [0, 0, 0])),
         'expect_pixels=%d' % o['expect_pixels'], 'draft=0']
    if o.get('overwrite'): a.append('overwrite=1')
    if dry:
        print(i, o['name'], op, o['expect_pixels']); continue
    rc, out = cli(a)
    m = re.search(r'🔢 (?:placed|carved_count|carved) = (\d+)', out)
    got = int(m.group(1)) if m else -1
    if rc != 0 or got != o['expect_pixels']:
        print('✗ 第 %d 項 %s：rc=%d placed=%d 預期 %d —— 從第 %d 項接（先看這一刀落地了沒）' % (i, o['name'], rc, got, o['expect_pixels'], i))
        print(out[-1500:])
        sys.exit(1)
    total += got
    print('%3d %-14s %s %7d ✓' % (i, o['name'], op, got))
print('完成第 %d～%d 項，合計 %d 格' % (start, (end if end is not None else len(L)) - 1, total))

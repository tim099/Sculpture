# 改了清單之後只落差分：匯出作品現況（export format=list）→ 跟新清單比 → carvevox 刻掉多的與換色的（帶顏色守門）→ stampvox 補缺的與換色的。
# 落完再匯出一次，跟新清單逐格比（缺 0／多 0／色差 0 才算完）。
# 用法：python -I -X utf8 -B restamp.py <作品 ID> <新清單>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

D = os.path.dirname(os.path.abspath(__file__))
wid, newp = sys.argv[1], os.path.join(D, sys.argv[2])
tmp = os.path.join(D, 'lists', '_now_%s.txt' % wid)


def read(p):
    out = {}
    for ln in open(p, encoding='utf-8'):
        if not ln.strip() or ln[0] == '#':
            continue
        x, y, z, c = map(int, ln.split(','))
        out[(x, y, z)] = c
    return out


def now():
    cli.run(['op=export', 'work=' + wid, 'format=list', 'out=' + tmp.replace('\\', '/')], quiet=True)
    return read(tmp)


A, B = now(), read(newp)
rm = {k: v for k, v in A.items() if k not in B or B[k] != v}
add = {k: v for k, v in B.items() if k not in A or A[k] != v}
print('%s：現況 %d、新 %d ⇒ 刻 %d、補 %d' % (wid, len(A), len(B), len(rm), len(add)))
if rm:
    p = os.path.join(D, 'lists', '_carve_%s.txt' % wid)
    open(p, 'w', encoding='utf-8').write(''.join('%d,%d,%d,%d\n' % (k + (v,)) for k, v in sorted(rm.items())))
    rc, out = cli.run(['op=carvevox', 'persona=erina', 'work=' + wid, 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(rm), 'draft=0', 'share=0'])
    print('  carved', cli.val(out, 'carved') or cli.val(out, 'placed') or cli.val(out, 'carved_count'))
    os.remove(p)
if add:
    p = os.path.join(D, 'lists', '_add_%s.txt' % wid)
    open(p, 'w', encoding='utf-8').write(''.join('%d,%d,%d,%d\n' % (k + (v,)) for k, v in sorted(add.items())))
    cli.stamp(wid, p, len(add))
    os.remove(p)
C = now()
os.remove(tmp)
miss = sum(1 for k in B if k not in C); extra = sum(1 for k in C if k not in B); dc = sum(1 for k in B if k in C and B[k] != C[k])
print('  讀回：缺 %d、多 %d、色差 %d' % (miss, extra, dc))
if miss or extra or dc:
    raise SystemExit('對不上')

# Step 4 落格：船殼分塊貼上 → 砲門／艉窗刻除 → 塗裝覆寫
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from wio import cli, export_list, PERSONA, HULL


def count_lines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    cur = export_list(HULL, links='none')
    if len(cur) == 0:
        cli('op=work', 'sub=mark', f'persona={PERSONA}', f'work={HULL}', 'name=船殼', 'phase=begin', 'upto=start', 'overwrite=1')
        for hp in sorted(glob.glob(os.path.join(DESIGN, 'masks', 'hull', 'hull_*.vox.txt'))):
            n = count_lines(hp)
            out = cli('op=stampvox', f'persona={PERSONA}', f'work={HULL}',
                      'voxels=' + os.path.abspath(hp).replace('\\', '/'),
                      'at=0,0,0', f'expect_pixels={n}', 'draft=0', 'share=0')
            m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
            got = int(m.group(1).replace(',', '')) if m else None
            assert got == n, f'placed {got} != {n}'
            print(f'✓ stamp {os.path.basename(hp)}: {got}')
        cli('op=work', 'sub=mark', f'persona={PERSONA}', f'work={HULL}', 'name=船殼', 'phase=end', 'overwrite=1')
    else:
        print(f'· 船殼已有 {len(cur)} 格，檢查砲門與塗裝')

    carve_p = os.path.join(DESIGN, 'masks', 'ports', 'carve.vox.txt')
    cur_map = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    todo_carve = []
    with open(carve_p, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            x, y, z, c = map(int, l.split(','))
            if (x, y, z) in cur_map:
                todo_carve.append((x, y, z, cur_map[(x, y, z)]))

    if todo_carve:
        cli('op=work', 'sub=mark', f'persona={PERSONA}', f'work={HULL}', 'name=砲門', 'phase=begin', 'overwrite=1')
        nc = count_lines(carve_p)
        assert len(todo_carve) == nc, f'todo_carve {len(todo_carve)} != {nc}'
        out = cli('op=carvevox', f'persona={PERSONA}', f'work={HULL}',
                  'voxels=' + os.path.abspath(carve_p).replace('\\', '/'),
                  'at=0,0,0', f'expect_pixels={nc}', 'share=0', 'note=步驟 4：兩重砲門與雙層艉窗刻除')
        print(f'✓ carve ports/windows: {nc}')

    paint_p = os.path.join(DESIGN, 'masks', 'ports', 'paint.vox.txt')
    cur_map2 = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    todo_paint = 0
    with open(paint_p, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            x, y, z, c = map(int, l.split(','))
            if cur_map2.get((x, y, z)) != c:
                todo_paint += 1
    if todo_paint:
        np_ = count_lines(paint_p)
        cli('op=stampvox', f'persona={PERSONA}', f'work={HULL}',
            'voxels=' + os.path.abspath(paint_p).replace('\\', '/'),
            'at=0,0,0', 'overwrite=1', f'expect_pixels={np_}', 'draft=0', 'share=0', 'note=步驟 4：雙黑護木、朱漆戰棚、龍目與花屁股')
        print(f'✓ paint hull: {np_} ({todo_paint} changed)')
        cli('op=work', 'sub=mark', f'persona={PERSONA}', f'work={HULL}', 'name=砲門', 'phase=end', 'overwrite=1')

    print(cli('op=stats', f'work={HULL}', 'structure=1', 'mirror=y:128'))


if __name__ == '__main__':
    main()

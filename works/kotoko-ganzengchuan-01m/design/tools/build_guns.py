# 福建趕繒船 步驟 9 落格（TASK-1314）：
#   1. 於船殼 (x=80..92 z>60, x=288..300 z>50) 冪等刻除迴旋砲淺豁口與朱漆護邊，重驗船殼 structure=1 mirror=y:96
#   2. 掛載 8 門 4l 主砲（甲板-main）＋ 4 門 pierrier 迴旋砲與 4 具叉架座雙生（甲板-poop / 甲板-fore）
import json
import os
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')

PERSONA = 'kotoko'


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


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


def load_vox_map(path):
    res = {}
    with open(path, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            x, y, z, c = map(int, l.split(','))
            res[(x, y, z)] = c
    return res


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, os.path.join(design, 'tools'))
    from wio import export_list

    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    GB = plan['guns_build']
    HULL = GB['hull']
    ASM = GB['assembly']
    PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
    NAMES = {'4l': '4 磅長砲（pinnacle 專用件 ×0.5）', 'pierrier': '佛郎機迴旋砲 pierrier（apex 共用件 ×0.5）'}

    # 1. 冪等刻除迴旋砲舷頂淺豁口＋朱漆護邊
    cur_hull = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    want_carve = load_vox_map(os.path.join(design, 'masks', 'guns', 'swivel_carve.vox.txt'))
    todo_carve = {k: cur_hull[k] for k in want_carve if k in cur_hull}
    if todo_carve:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'carve.txt').replace('\\', '/')
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                for k in sorted(todo_carve):
                    f.write(f'{k[0]},{k[1]},{k[2]},{todo_carve[k]}\n')
            out = cli('op=carvevox', f'persona={PERSONA}', f'work={HULL}', f'voxels={p}', 'at=0,0,0',
                      f'expect_pixels={len(todo_carve)}', 'note=步驟 9：刻通艏／艉迴旋砲舷頂豁口')
            print('✓ carvevox 迴旋砲豁口：', len(todo_carve), '格')
    else:
        print('· 迴旋砲豁口已刻過（跳過）')

    want_paint = load_vox_map(os.path.join(design, 'masks', 'guns', 'swivel_paint.vox.txt'))
    cur_hull2 = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    todo_paint = {k: c for k, c in want_paint.items() if k in cur_hull2 and cur_hull2[k] != c}
    if todo_paint:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'paint.txt').replace('\\', '/')
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                for k in sorted(todo_paint):
                    f.write(f'{k[0]},{k[1]},{k[2]},{todo_paint[k]}\n')
            cli('op=stampvox', f'persona={PERSONA}', f'work={HULL}', f'voxels={p}', 'at=0,0,0',
                'overwrite=1', f'expect_pixels={len(todo_paint)}', 'note=步驟 9：迴旋砲豁口朱漆護邊')
            print('✓ paint 迴旋砲護邊：', len(todo_paint), '格')
    else:
        print('· 迴旋砲護邊已上色（跳過）')

    # 2. 掛載 12 門砲 ＋ 4 具 pierrier-mount 雙生
    ok = bad = 0
    for r in PL:
        t = GB['types'][r['type']]
        s = float(t['scale'])
        meta = dict(t['meta'])
        meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'], 'id': r['id']})
        note = '%s（步驟 9 TASK-1314；%s 舷、%s %s；back %s、砲口伸出 %s）' % (
            NAMES[r['type']], r['side'], r['deck'],
            ('第 %d 門' % r['port']) if isinstance(r['port'], int) else '舷頂 ' + str(r['port']),
            num(float(r['back'])), num(float(r['muzzle_beyond'])))
        base = ['op=work', 'sub=model', f'persona={PERSONA}', 'work=' + GB['deck_works'][r['deck']],
                'name=' + r['name'], 'source_work=' + t['work'],
                'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])),
                'scale=' + xyz([s, s, s]), 'overwrite=1',
                'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'note=' + note]
        if r['side'] == 'P':
            base.append('mirror=y')
        todo = [base]
        if t.get('mount_work'):
            twin = ['op=work', 'sub=model', f'persona={PERSONA}', 'work=' + GB['deck_works'][r['deck']],
                    'name=' + r['name'] + '座', 'source_work=' + t['mount_work'],
                    'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']), 'rotate=0,0,' + num(float(r['phi'])),
                    'scale=' + xyz([s, s, s]), 'overwrite=1',
                    'meta=' + json.dumps({'kind': 'gunmount', 'mount_of': r['id'], 'id': r['id'].replace('gun-', 'gunmount-')}, ensure_ascii=False, separators=(',', ':')),
                    'note=佛郎機迴旋砲座（叉架＋插銷；Ship_Guns §4.2.1 雙生）']
            if r['side'] == 'P':
                twin.append('mirror=y')
            todo.append(twin)
        for a_ in todo:
            out = cli(*a_, ok=(0, 1))
            if 'exit_code = 0' in out or '✓' in out:
                ok += 1
            else:
                bad += 1
                print('✗', r['name'], out[-500:])
    print(f'模型掛載 ok={ok}, bad={bad}（設計 12 門＋4 座＝16 件）')
    assert bad == 0

    print('=== hull stats ===')
    print(cli('op=stats', f'work={HULL}', 'structure=1', 'mirror=y:96'))
    print('=== assembly models ===')
    print(cli('op=work', 'sub=models', f'work={ASM}'))


if __name__ == '__main__':
    main()

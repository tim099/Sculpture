# 階段八 v1.2（2026-10-11，Tim：「船頭的炮窗 試著雕刻成垂直的吧」）：作品現況 → 新設計 的差異清單
#   新設計 ＝ 階段八之前（world_upto）− carve_boxes ＋ lining ＋ touchup_fill，再蓋 touchup_paint（都是 draft_ports.py／draft_ports_touchup.py 重產的 v1.2）
#   ⇒ masks/ports/v12_carve.vox.txt（現況有、新設計沒有；行尾帶現況顏色 ＝ carvevox 守門）
#      masks/ports/v12_add.vox.txt  （新設計有、現況沒有 ⇒ stampvox）
#      masks/ports/v12_paint.vox.txt（兩邊都有、顏色不同 ⇒ stampvox overwrite=1）
#      masks/ports/v12.json（格數、sha256、套完應有的總數、差異落在哪幾個砲門）
#   套進作品走草稿：carvevox → stampvox → stampvox overwrite=1（draft=1）⇒ 看過 OK 才 apply（一筆 workedit）。
# 用法：python -I draft_ports_v12.py <design 資料夾>（先跑 draft_ports.py、draft_ports_touchup.py）
import sys, os, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from draft_ports_touchup import compose, load_list   # noqa: E402
from replay import replay                            # noqa: E402


def main():
    design = sys.argv[1]
    W = os.path.dirname(os.path.abspath(design))
    out = os.path.join(design, 'masks', 'ports')
    target = compose(design)
    fill = load_list(os.path.join(out, 'touchup_fill.vox.txt'))
    assert all(c not in target for c in fill)
    target.update(fill)
    paint = load_list(os.path.join(out, 'touchup_paint.vox.txt'))
    assert all(target.get(c) == 36 for c in paint), '白帶補漆蓋的不是黑外板'
    target.update(paint)
    now = {k: v[0] for k, v in replay(W).items()}

    carve = {c: now[c] for c in now if c not in target}
    add = {c: target[c] for c in target if c not in now}
    recolor = {c: target[c] for c in target if c in now and now[c] != target[c]}
    vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))

    def port_of(c):
        x, _, z = c
        for p in vp['ports']:
            rows = {int(zz): v for zz, v in p['x_rows'].items()}
            if min(rows) - 1 <= z <= max(rows) + 1 and min(v[0] for v in rows.values()) - 1 <= x <= max(v[1] for v in rows.values()) + 1:
                return p['n']
        return None
    res = {'note': '階段八 v1.2：作品現況 → 新設計（船頭砲門兩側垂直）的差異；套進作品走草稿', 'now_voxels': len(now), 'target_voxels': len(target)}
    for name, cells, note in (('v12_carve', carve, '現況有、新設計沒有 ⇒ carvevox（行尾 ＝ 現況顏色，守門）'),
                              ('v12_add', add, '新設計有、現況沒有 ⇒ stampvox'),
                              ('v12_paint', recolor, '兩邊都有、顏色不同 ⇒ stampvox overwrite=1')):
        p = os.path.join(out, name + '.vox.txt')
        body = '\n'.join('%d,%d,%d,%d' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格，at=0,0,0）\n' % (name, note, len(cells)) + body + '\n')
        by = {}
        for c in cells:
            k = str(port_of(c))
            by[k] = by.get(k, 0) + 1
        res[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'by_port': dict(sorted(by.items())),
                     'colors': dict(sorted({str(v): sum(1 for u in cells.values() if u == v) for v in set(cells.values())}.items()))}
    res['expect_after'] = len(now) - len(carve) + len(add)
    assert res['expect_after'] == len(target)
    json.dump(res, open(os.path.join(out, 'v12.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

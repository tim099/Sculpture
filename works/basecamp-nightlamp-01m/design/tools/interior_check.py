# 階段九 船殼內部的讀數（跟 draft_interior.py 不共用量法）
# 用法：python -I interior_check.py <design 資料夾> <刻之前的 export list> <之後的 export list> [--drop <清單名>[,<清單名>…]]
#   · 結果帳：之後 ＝ 之前 ＋ wall_fill／fill_cavities／ceiling／bands，再把 recolor 蓋上去（逐格含顏色）。
#   · 砲門透光：每個砲門開口那幾欄 (X, Z)，兩舷從船外一路到中線附近（dy 3..75）之後都沒有實心（刻之前也是透光的）。
#   · 艙內看得到的外板漆：艙內 ＝ 同一列兩舷之間的空格、跟種子（plan interior.seed）6 連通的那一塊；碰到的格面有幾面是黑／鏽褐／白（36／100／255）；砲門開口那幾欄另計。
#   · 甲板那幾層高度上沒有東西擋：每層甲板面 D(X) 那一格（走的那一格）在船中 X 340 兩舷之間，之後沒有新長出來的實心（甲板是下一階段的事）。
#   · --drop：假裝那幾份清單沒落（反向對照；內板後面還有牆裡填實，要兩份一起拿掉才看得到漆）。
import sys, os, json
import numpy as np
from scipy import ndimage


def read_list(p):
    out = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.strip()
        if ln and ln[0] != '#':
            x, y, z, c = (int(v) for v in ln.split(',')[:4])
            out[(x, y, z)] = c
    return out


def main():
    a = sys.argv[1:]
    drop = None
    if '--drop' in a:
        i = a.index('--drop')
        drop = a[i + 1]
        del a[i:i + 2]
    design, before_p, after_p = a
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    seed = tuple(plan['interior']['seed'])
    before, after = read_list(before_p), read_list(after_p)
    lists = {n: read_list(os.path.join(design, 'masks', 'interior', n + '.vox.txt')) for n in ('wall_fill', 'fill_cavities', 'ceiling', 'bands', 'recolor')}
    if drop:
        gone = set()
        for n in drop.split(','):
            gone |= set(lists[n])
        after = {c: v for c, v in after.items() if c not in gone or c in before}
    out = {'drop': drop}
    exp = dict(before)
    for n in ('wall_fill', 'fill_cavities', 'ceiling', 'bands'):
        exp.update(lists[n])
    exp.update(lists['recolor'])
    out['ledger'] = {'after': len(after), 'expected': len(exp), 'missing': sum(1 for c in exp if c not in after),
                     'extra': sum(1 for c in after if c not in exp), 'color_diff': sum(1 for c, v in exp.items() if c in after and after[c] != v)}
    vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
    blocked = 0
    for p in vp['ports']:
        for x in range(p['X'][0], p['X'][1] + 1):
            for z in range(p['Z'][0], p['Z'][1] + 1):
                for side in (1, -1):
                    if any((x, 160 + side * d, z) in after for d in range(3, 76)):
                        blocked += 1
    out['port_columns_blocked'] = blocked
    # 艙內看得到的漆
    A = np.array(list(after.keys()))
    lo = A.min(0) - 1
    hi = A.max(0) + 2
    g = np.zeros(hi - lo, np.uint8)
    for c, v in after.items():
        g[c[0] - lo[0], c[1] - lo[1], c[2] - lo[2]] = v
    # 「艙內」＝ 同一列（X, Z）兩舷之間的空格（兩邊 y 都還有實心）—— 還沒鋪甲板，種子跟船外的空氣經頂上相通，⛔ 不能拿 6 連通當艙內
    solid = g > 0
    has_lo = np.maximum.accumulate(solid, axis=1)
    has_hi = np.maximum.accumulate(solid[:, ::-1, :], axis=1)[:, ::-1, :]
    between = ~solid & has_lo & has_hi
    lab, _ = ndimage.label(between)
    k = lab[seed[0] - lo[0], seed[1] - lo[1], seed[2] - lo[2]]
    out['seed_in_between'] = bool(k > 0)
    ia = lab == k
    paint = np.isin(g, (36, 100, 255))
    portxz = np.zeros(g.shape[0::2], bool)
    for p in vp['ports']:
        portxz[p['X'][0] - lo[0]:p['X'][1] - lo[0] + 1, p['Z'][0] - lo[2]:p['Z'][1] - lo[2] + 1] = True
    port3 = np.broadcast_to(portxz[:, None, :], g.shape)
    n = n_port = 0
    for ax in range(3):
        for s in (1, -1):
            sh = np.roll(paint, s, axis=ax)
            f = ia & sh
            n += int((f & ~port3).sum())
            n_port += int((f & port3).sum())
    out['interior_paint_faces'] = {'outside_port_columns': n, 'in_port_columns': n_port}
    # 甲板面那一格（船中 X 340）兩舷之間，之後新長出來的實心
    dk = json.load(open(os.path.join(design, 'decks.json'), encoding='utf-8'))
    x = 340
    rows = {}
    for name, arr in dk['decks'].items():
        z = arr[x - dk['X0']]
        new = [y for y in range(100, 221) if (x, y, z) in after and (x, y, z) not in before]
        inner = [y for y in new if lists['ceiling'].get((x, y, z)) is None and lists['bands'].get((x, y, z)) is None and lists['wall_fill'].get((x, y, z)) is None]
        rows[name] = {'Z': z, 'new_cells_across': len(new), 'not_lining': len(inner)}
    out['deck_rows_X340'] = rows
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

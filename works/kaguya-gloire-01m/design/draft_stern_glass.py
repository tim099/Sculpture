# 光榮號 船尾窗的玻璃（Tim 2026-10-20「參考 憲法號 把妳的船的玻璃做成子模組 套用玻璃材質吧」；造船規格 §9.5「窗的玻璃」，TASK-0753）
#   抄自憲法號 basecamp-frigate-constitution-01m/design/draft_stern_glass.py（basecamp）；改：
#     - 光榮號的玻璃早就雕了（階段三 draft_ports.py：窗的最外一格刻掉、第二格漆 87）⇒ 不重新算窗，照現有的玻璃格做；
#       那 300 格落在鐵甲帶（-armor）裡 ⇒ 先 `work sub=split` 拆成 -stern-glass（外觀不變由引擎證明），這支只產清單
#     - 後面是 4～15 格厚的牆（鐵甲 ＋ 木 4 ＋ 內面 177）⇒ 刻穿到艙裡（規格：玻璃後面要是空的）
#     - 圓船尾：上下（往上外傾 1～2 格）、左右（弧面 ±1 格）相鄰的玻璃前後錯開 ⇒ 錯開的那段補玻璃（從斜的角度看不露縫）
#   讀：作品現在的格（export，links=none）：船殼 kaguya-gloire-01m、鐵甲帶 -armor、玻璃 -stern-glass（還沒拆就讀鐵甲帶的 87）
#   寫：masks/stern_glass/split.vox.txt（拆件 voxels=）、hull_carve.vox.txt／armor_carve.vox.txt（carvevox，帶顏色守門）、
#       fill.vox.txt（stampvox at=0,0,0 落在 -stern-glass）、verify_stern_glass.json
#   用法：python -I -X utf8 draft_stern_glass.py <design>            讀數：照現在的作品量，只寫 verify（做完了 ⇒ 拆、刻、補都 0）
#         python -I -X utf8 draft_stern_glass.py <design> --before   重產清單：船殼、鐵甲帶重播到動手之前（BEFORE 的事件），寫 masks
#   ⚠ masks 只在「玻璃還沒拆」的狀態下寫（落刀事件記著清單的 sha256；照做完的作品重產會寫成空清單，出處就斷了）
import sys, os, json, hashlib, subprocess, tempfile
from collections import defaultdict

GLASS = 87                                  # 階段三的玻璃色（plan.json stern.src「玻璃 87」）—— 拆件不換色
REGION = '100..180,140..260,85..140'        # 兩排船尾窗（plan.json stern：x_max 175、half 40）
WORKS = {'hull': 'kaguya-gloire-01m', 'armor': 'kaguya-gloire-01m-armor', 'glass': 'kaguya-gloire-01m-stern-glass'}
BEFORE = {'hull': '185634_573_068cf1.json', 'armor': '184935_937_96b0a6.json'}   # 2026-10-15 那兩件最後一刀（之後就是這次的拆、刻）


def export(work, mark=None):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work,
                            '--arg', 'links=none', '--arg', 'region=' + REGION, '--arg', 'out=' + out]
                           + (['--arg', 'mark=' + mark] if mark else []),
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            if mark:
                raise SystemExit('匯出失敗（%s mark=%s）：%s' % (work, mark, (r.stdout + r.stderr)[-600:]))
            return None
        cells = {}
        for ln in open(out, encoding='utf-8'):
            if ln.startswith('#') or not ln.strip():
                continue
            v = [int(t) for t in ln.split(',')]
            cells[(v[0], v[1], v[2])] = v[3]
        return cells


def main(design, before):
    if before:
        H, A, G = export(WORKS['hull'], BEFORE['hull']), export(WORKS['armor'], BEFORE['armor']), None
    else:
        H, A, G = export(WORKS['hull']), export(WORKS['armor']), export(WORKS['glass'])
    split = G is None
    if split:
        G = {k: c for k, c in A.items() if c == GLASS}
        A = {k: c for k, c in A.items() if c != GLASS}
    # 每一欄窗 (y, z) 的玻璃面 ＝ 最靠船尾那一格（x 最小；補縫的格在它後面）
    face = defaultdict(lambda: 10 ** 9)
    for (x, y, z) in G:
        face[(y, z)] = min(face[(y, z)], x)
    # 補縫：相鄰的兩欄，靠船尾的那一欄往船頭補到另一欄的玻璃面
    fill = {}
    for (y, z), x in face.items():
        for k in ((y + 1, z), (y - 1, z), (y, z + 1), (y, z - 1)):
            if k in face and face[k] > x:
                for xx in range(x + 1, face[k] + 1):
                    fill[(xx, y, z)] = GLASS
    # 刻穿：玻璃面後面連續的牆（船殼、鐵甲），一直到艙裡第一格空氣
    hull_carve, armor_carve, runs = {}, {}, defaultdict(int)
    for (y, z), x in face.items():
        xx, n = x + 1, 0
        while True:
            p = (xx, y, z)
            if p in H:
                hull_carve[p] = H[p]
            elif p in A:
                armor_carve[p] = A[p]
            elif p in G:
                pass
            else:
                break
            xx, n = xx + 1, n + 1
        runs[n] += 1
    fill = {p: c for p, c in fill.items() if p not in G}
    out = os.path.join(design, 'masks', 'stern_glass')
    os.makedirs(out, exist_ok=True)

    def dump(name, cells, head):
        if split:                                   # 只有動手之前的狀態才寫清單（見檔頭 ⚠）
            with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as f:
                f.write(head)
                for (x, y, z), c in sorted(cells.items()):
                    f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return len(cells)

    R = {
        'split_pending': split,
        'glass_cells': len(G), 'glass_columns': len(face),
        'split': dump('split.vox.txt', G if split else {}, '# 光榮號 船尾窗玻璃：從鐵甲帶拆出來的格（work sub=split voxels=；色 87）\n'),
        'hull_carve': dump('hull_carve.vox.txt', hull_carve, '# 光榮號 船尾窗玻璃後面的船殼牆（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n'),
        'armor_carve': dump('armor_carve.vox.txt', armor_carve, '# 光榮號 船尾窗玻璃後面的鐵甲（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n'),
        'fill': dump('fill.vox.txt', fill, '# 光榮號 船尾窗玻璃補縫（stampvox at=0,0,0 落在 -stern-glass；色 87）\n'),
        'wall_behind_run': {str(k): v for k, v in sorted(runs.items())},
        'front_not_empty': sum(1 for (y, z), x in face.items() if (x - 1, y, z) in H or (x - 1, y, z) in A),
        'mirror_diff': sum(1 for (x, y, z) in G if (x, 400 - y, z) not in G),
    }
    if split:
        print(json.dumps(R, ensure_ascii=False))
        return
    R['masks_sha256'] = {n: hashlib.sha256(open(os.path.join(out, n), 'rb').read()).hexdigest()
                         for n in sorted(os.listdir(out)) if n.endswith('.vox.txt')}
    json.dump(R, open(os.path.join(design, 'verify_stern_glass.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else os.path.dirname(os.path.abspath(__file__)), '--before' in sys.argv)

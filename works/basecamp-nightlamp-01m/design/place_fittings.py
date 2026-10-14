# 階段十八：甲板上的配件（外部模型）—— 舵輪（← 憲法號 -wheel）、羅經櫃、主絞盤（← 餘燼號 -binnacle、-capstan），都是 0.02 m、scale 0.2
#   輸入：plan.json fittings、組裝件 export list、各配件來源 export list、所在甲板子作品 export list
#   ⇒ fittings_placement.json、verify_fittings.json
# 用法：python -I place_fittings.py <design> <組裝件 list> <scratch 資料夾（放 <key>.txt 與甲板 list）>
#   · at ＝ (x, 160.5, 那一層在那一欄走的那一格)、pivot ＝ 來源的底面中心（照餘燼號的擺法）；碰到就往上 1 格再試（最多 3 格）。
#   · 碰撞：模型每一格的格心＋八個角（往裡縮 0.05 來源格）換到組裝件，不准落在實心裡。
import sys, os, json, hashlib, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    F = plan['fittings']
    occ = DP.read_list(sys.argv[2])
    assert len(occ) == F['assembly_cells'], ('組裝件格數對不上', len(occ))
    sd = sys.argv[3]
    place, log = [], {}
    e = F['inset']
    offs = np.array([(dx, dy, dz) for dx in (-0.5 + e, 0.5 - e) for dy in (-0.5 + e, 0.5 - e) for dz in (-0.5 + e, 0.5 - e)] + [(0, 0, 0)])
    for it in F['items']:
        src = DP.read_list(os.path.join(sd, it['key'] + '.txt'))
        deck = DP.read_list(os.path.join(sd, it['deck_list']))
        g = np.array(sorted(src), float) + 0.5
        pts = (g[:, None, :] + offs[None, :, :]).reshape(-1, 3)
        x, y = it['x'], it['probe_y']
        zw = max(z for (xx, yy, z) in deck if xx == x and yy == y) + 1
        sc, pv = it['scale'], np.array(it['pivot'], float)
        tried = []
        for z0 in range(zw, zw + 4):
            at = np.array([x + 0.5 if it.get('x_center_cell') else x, 160.5, z0], float)
            q = at + sc * (pts - pv)
            h = sum(1 for k in set(map(tuple, np.floor(q).astype(int))) if k in occ)
            tried.append([z0, h])
            if h == 0:
                break
        assert h == 0, (it['name'], '放不下', tried)
        w = at + sc * (g - pv)
        box = [np.round(w.min(0) - sc / 2, 2).tolist(), np.round(w.max(0) + sc / 2, 2).tolist()]
        place.append({'name': it['name'], 'host': it['host'], 'link': it['link'], 'source_work': it['source_work'], 'at': at.round(3).tolist(),
                      'pivot': it['pivot'], 'rotate': [0, 0, 0], 'scale': [sc, sc, sc], 'meta': it['meta'], 'box': box})
        log[it['name']] = {'deck_walk_z': zw, 'tried': tried, 'box': box, 'source_cells': len(src),
                           'source_sha256': hashlib.sha256(open(os.path.join(sd, it['key'] + '.txt'), 'rb').read()).hexdigest()}
    pp = os.path.join(design, 'fittings_placement.json')
    json.dump({'placements': place}, open(pp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    v = {'base': hashlib.sha256(open(sys.argv[2], 'rb').read()).hexdigest(), 'items': log, 'placement_sha256': hashlib.sha256(open(pp, 'rb').read()).hexdigest()}
    json.dump(v, open(os.path.join(design, 'verify_fittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

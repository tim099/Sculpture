# 澤漢號 plan.json 的 decks_build（步驟 5：甲板、艙口、break、梯子）＋ 前桅／艏斜桅挪位 —— 一次性產生；只換這幾格。
#   用法：python -I -X utf8 plan_stage5.py <design 資料夾>
import sys, os, json


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    rows = {r['key']: r for r in plan['masts']['rows']}
    rows['fore']['x_step'] = 352
    rows['fore']['src'] = rows['fore']['src'].replace('x：VY 艏柱後 0.064 L 是在甲板高量的 ⇒ 往船尾挪到 x 344 讓桅腳落在船裡（設計決定）',
                                                      'x：VY 艏柱後 0.064 L（在甲板高量 ⇒ x 351）⇒ 352，穿過船首樓（步驟 5：v1 放 x 344 跟船首樓 break x 345 疊在一起）')
    rows['bowsprit']['x_step'] = 360
    tail = '；腳在船首樓甲板 x 360（前桅 x 352 前面）'
    if not rows['bowsprit']['src'].endswith(tail):          # 重跑不重複接
        rows['bowsprit']['src'] += tail
    plan['decks_build'] = {
        'src': '設計決定（遊戲用的大致構造，照 Ship_Decks §9.2–9.3；結構照拉貝爾號 draft_decks）',
        'plank': {'interior': 177, 'weather': 209, 'weather_decks': ['main', 'quarter', 'forecastle']},
        'beam': {'every': 10, 'w': 2, 'depth': {'hold': 1, 'main': 2, 'quarter': 2, 'forecastle': 2}, 'color': 136,
                 'src': 'VY p.141：甲板樑間距 3½ 呎（≈ 10 格，OCR）；深 0.2 m（設計決定）'},
        'trim': 141,
        'hatches': [
            {'name': '後艙口', 'x0': 157, 'x1': 167, 'half': 5, 'decks': ['main']},
            {'name': '主艙口', 'x0': 222, 'x1': 236, 'half': 7, 'decks': ['main']},
            {'name': '前艙口', 'x0': 299, 'x1': 311, 'half': 5, 'decks': ['main']}],
        'hatch_src': '設計決定：散貨船的三個貨艙口 —— 主艙口在主桅（x 211）前面、最大（1.5 m 見方）；後、前艙口夾在砲之間（砲 x 145–151、175–181、240–246、275–281）；貨艙梯子的井另開（x 254–268）',
        'coaming_h': 2,
        'mast_r': {'fore': 2.5, 'main': 3, 'mizzen': 2},
        'breaks': [
            {'name': '後甲板前緣', 'x': 121, 'lo': 'main', 'up': 'quarter', 'doors_dy': [0], 'rail_h': 5, 'bulkhead': True},
            {'name': '船首樓後緣', 'x': 345, 'lo': 'main', 'up': 'forecastle', 'doors_dy': [0], 'rail_h': 5, 'bulkhead': True}],
        'break_src': '設計決定：後甲板（halfdek）底下是船長室（主甲板船尾那一段，頭頂 16–18 格）⇒ x 121 一道艙壁、中線一扇門；船首樓底下是廚房與水手艙（W 的 pinas：kot）⇒ x 345 一道艙壁、中線一扇門；兩道都在樓甲板邊上做 5 格胸牆、梯子頭留口',
        'ladders': {
            'rise': 3, 'run': 2, 'tread_half': 3, 'color': 136,
            'list': [
                {'name': 'hold', 'lo': 'hold', 'up': 'main', 'xs': 252, 'dir': 1, 'dy': 0, 'well': True, 'well_keep_fwd': 1,
                 'well_keep_src': '照拉貝爾號步驟 16：井最前一欄的兩角留成甲板（遊戲走路格從井邊接到梯頭那一塊）',
                 'well_to': 20, 'head_x': 274,
                 'well_to_src': '主甲板離貨艙地板 29 格 ⇒ 9 階、hi 在 xs ＋ 18 ⇒ 井開到 ＋20、head 在 ＋22（v1 照拉貝爾號的 ＋16／＋18 ⇒ hi 在主甲板板底下）'},
                {'name': 'quarter-P', 'lo': 'main', 'up': 'quarter', 'xs': 136, 'dir': -1, 'dy': -12, 'head_x': 118},
                {'name': 'quarter-S', 'lo': 'main', 'up': 'quarter', 'xs': 136, 'dir': -1, 'dy': 12, 'head_x': 118},
                {'name': 'forecastle-P', 'lo': 'main', 'up': 'forecastle', 'xs': 329, 'dir': 1, 'dy': -12, 'head_x': 348},
                {'name': 'forecastle-S', 'lo': 'main', 'up': 'forecastle', 'xs': 329, 'dir': 1, 'dy': 12, 'head_x': 348}],
            'src': '設計決定：每 3 格一階、每階 2 格、踏板 7 寬（同拉貝爾號）；貨艙梯子在主甲板開井；後甲板、船首樓的梯子靠在 break 外面、頭踩上樓甲板。每一層要讓人走得到的甲板都有梯子（Ship_Decks §9.3）'}}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

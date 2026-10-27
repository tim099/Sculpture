# 澤漢號 plan.json 的 gear_build、fit_build（步驟 10：彈藥庫、小艇架、小艇、羅經櫃、主絞盤、艙蓋、廚房、船長室）—— 一次性產生；只換這兩段。
#   用法：python -I -X utf8 plan_stage10.py <design 資料夾>（要先有 rigging_plan.json：繩梯的 foot／head 從那裡抄來量）
import sys, os, json

H = 'abigail-fluyt-01m'


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
    plan['gear_build'] = {
        'assembly': H + '-assembly',
        'magazine': {'work': H + '-magazine', 'link': '彈藥庫', 'title': '澤漢號 彈藥庫（kruitkamer）', 'x0': 124, 'x1': 152, 'floor': 8, 'ztop': 35,
                     'door': 'fore', 'door_w': 5, 'door_head': 3, 'pos': 'aft', 'cap': 20,
                     'cap_src': '照砲數換算（收穫號照憲法號每門約 2.6 桶）：本船 8 門 4 磅＋6 門迴旋砲 ≈ 20 桶（2,000 磅）—— ⚠ 換算，不是史料',
                     'colors': {'copper': 168, 'oak': 136, 'dark': 104, 'pine': 177},
                     'barrel': {'work': 'basecamp-frigate-constitution-01m-powder-barrel', 'scale': 0.2, 'pivot': [11, 11, 0], 'd': 22, 'h': 27, 'mpv': 0.02, 'pitch': 4.6, 'tier': 7, 'aisle': 2},
                     'aisle_src': '走道 2（拉貝爾號 1、收穫號 3）：福祿特平底、貨艙後段夠寬',
                     'src': '設計決定：貨艙後段（貨艙地板 x 117 起）x 124–152、地板 z 8（貨艙地板上一格）、頂 z 35（主甲板樑下）；門開在船頭那道艙壁、朝貨艙；做法照拉貝爾號／收穫號 draft_gear（銅皮 168、松木地板 177、橡木框 136、門洞 5 格寬；Ship_Magazine §8）'},
        'skids': {'work': H + '-boat-skids', 'link': '小艇架', 'title': '澤漢號 小艇架（主甲板兩座橫架）', 'deck': 'main', 'xs': [262, 288], 'y_half': 9, 'post_dy': 8, 'beam_z': 47,
                  'color': 136, 'z_lo': 36,
                  'src': '設計決定：小艇擱在主桅與前艙口之間、跨過貨艙梯子的井（x 254–272）與第 4 門砲；橫樑 z 47–48（4 磅砲頂約 z 46）、立柱 |dy| 7–8（井的圍板在 |dy| 6、井的艙蓋到 |dy| 6 ⇒ v1 立柱 |dy| 6–7 跟艙蓋撞 4 格）'},
        'models': [
            {'name': '小艇', 'host': H + '-deck-main', 'work': 'basecamp-ember-01m-boat', 'at': [275, 96.5, 49], 'pivot': [90, 26, 0], 'scale': 0.222, 'rotate': 0,
             'meta': {'kind': 'boat', 'boat': 'cutter', 'length_m': 4},
             'src': '設計決定：甲板上一艘小艇 ⇒ 餘燼號 cutter（9 m）縮成 4 m（同拉貝爾號的 scale ⇒ 同一份網格；福祿特的小艇長度查不到）；擱在小艇架上 x 255–295；z 明寫 49（橫樑頂 48 ＋ 1；砲是模型、量不到）'},
            {'name': '羅經櫃', 'host': H + '-deck-quarter', 'work': 'summit-night-falcon-01m-binnacle', 'at': [92, 104.5, None], 'pivot': [9, 13, 0], 'scale': 0.2, 'rotate': 0,
             'meta': {'kind': 'binnacle'}, 'src': '沿用夜隼號羅經櫃（拉貝爾號也用）；後甲板、後桅（x 110）後面右舷 dy +8'},
            {'name': '主絞盤', 'host': H + '-deck-main', 'work': 'basecamp-ember-01m-capstan', 'at': [190.5, 96.5, None], 'pivot': [40, 40, 0], 'scale': 0.2, 'rotate': 0,
             'meta': {'kind': 'capstan'},
             'src': '沿用餘燼號主絞盤（收穫號同 scale 0.2）；主甲板中線、後艙口（x 157–167）與主桅（x 211）之間 —— 船首樓底下太短（主甲板到 x 366、還有前桅），拉貝爾號那種橫跨船寬的 windlass 放不下、放在露天又會切斷主甲板 ⇒ 直立絞盤（設計決定）'}],
        'z_src': 'at 的 z 給 null ⇒ 產生程式量：模型最底層那幾格腳下最高的實心 ＋ 1（同收穫號）',
        'foot_reach': 12, 'foot_src': '遊戲判斷模型掉不掉：外框中心往下 12 格內要有實心（Blockside/src/js/10_ship.js:47）'}
    climbs = [{'name': r['name'], 'foot': r['foot'], 'head': r['head']} for r in RP['ratline_sets'] if r.get('climb')]
    plan['fit_build'] = {
        'src': '步驟 10：艙蓋（門）、廚房、船長室、下桅繩梯的落腳點 —— 拉貝爾號步驟 16 那一套（draft_fit.py），本船跟步驟 10 一起做',
        'assembly': H + '-assembly',
        'hatches': {'host': H + '-deck-main', 'colors': {'plank': 209, 'frame': 136, 'iron': 73}, 'list': [
            {'name': '艙蓋-後', 'work': H + '-hatch-aft', 'title': '澤漢號 後艙口艙蓋（門：kind=door）', 'x0': 156, 'x1': 168, 'y0': 90, 'y1': 102, 'z': 41, 'open_deg': 100},
            {'name': '艙蓋-主', 'work': H + '-hatch-main', 'title': '澤漢號 主艙口艙蓋（門：kind=door）', 'x0': 221, 'x1': 237, 'y0': 88, 'y1': 104, 'z': 39, 'open_deg': 100},
            {'name': '艙蓋-井', 'work': H + '-hatch-well', 'title': '澤漢號 貨艙梯子井的艙蓋（門：kind=door）', 'x0': 253, 'x1': 273, 'y0': 90, 'y1': 102, 'z': 39, 'open_deg': 30},
            {'name': '艙蓋-前', 'work': H + '-hatch-fore', 'title': '澤漢號 前艙口艙蓋（門：kind=door）', 'x0': 298, 'x1': 312, 'y0': 90, 'y1': 102, 'z': 41, 'open_deg': 100}],
            'src': 'Ship_Fittings §9.7：主甲板離水線 0.6 m（z 36 對 30），四個開口（後、主、前艙口與貨艙梯子的井）都露天、通到船艙 ⇒ 都要門（沒有門的開口遊戲不當進水口）。從作品量圍板頂：後 39–40、主 38、前 39–40、井 36–38（梯頭那一端沒有圍板）⇒ 蓋子比開口每邊大一格、蓋底 ＝ 圍板頂最高那一層 ＋ 1（後、前 41，主、井 39）；鉸鏈沿 +x 在左舷那一邊（往上掀）。井的蓋子在小艇架橫樑（z 47）底下 ⇒ 掀 30°（到 z 45.5），其他照預設 100'},
        'galley': {'host': H + '-deck-main', 'name': '爐灶', 'work': 'kaguya-gloire-01m-galley', 'at': [359, 104, None], 'pivot': [22, 16, 0], 'scale': 0.18, 'rotate': 0,
                   'below_z': 57, 'meta': {'kind': 'galley', 'deco': None},
                   'src': 'Ship_Fittings §9.13：荷蘭船的廚房（kombuis）在船首樓底下（W 的 pinas：bak 底下）⇒ 光榮號的爐灶縮 0.18（拉貝爾號同一個 ⇒ 同一份網格）；主甲板 x 355–363、右舷 dy +5..+11（前桅 x 352 在中線）；爐門朝船尾 ⇒ 廚師站在前桅與爐灶之間（x 353），從船首樓 break 中線的門（x 345）進來'},
        'windlass': {'skip': True, 'src': '不做：船首樓底下的主甲板只到 x 366、前桅在 x 352 ⇒ 橫的 windlass 放不下；改成 gear_build 的直立主絞盤'},
        'room': {'work': H + '-cabin-room', 'title': '澤漢號 船長室（後甲板底下；艙壁＋門洞）', 'host': H + '-deck-main', 'link': '艙房', 'name': 'cabin', 'wall_x': 88, 'z_lo': 42,
                 'door_y': [94, 98], 'door_top': 55, 'box': {'x': [89, 102], 'y': [85, 107], 'z_lo': 42}, 'door': [88, 96, 42], 'colors': {'plank': 177, 'frame': 136},
                 'src': 'Ship_Decks §9.2：後甲板底下（主甲板船尾那一段，頭頂 15–17 格）x 88 一道橫艙壁隔出船尾的舵艙（steerage，舵柄在那裡）與前面的船長室；主甲板舷弧在 x 89–102 是平的 z 41（x 103 起 40；v1 框到 103 ⇒ 沒地板 23 格）⇒ 框 x 89–102、y 85–107、地板 z 42（1.4 × 2.3 m；門開在長邊、病床 1.9 m 只能沿 y 擺，⚠ 配置頁可能寫放不下）；門開在艙壁中線（0.5 m 寬）—— 設計決定'},
        'ratlines': {'list': climbs, 'src': '步驟 8 的繩梯（rigging_plan.json）：這裡只量落腳點站不站得住、在不在模型外框裡'}}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

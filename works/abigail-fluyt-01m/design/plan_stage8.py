# 澤漢號 plan.json 的 rigging（步驟 8：channels、靜索、ratlines、帆、旗）—— 一次性產生；只換這一段。
#   用法：python -I -X utf8 plan_stage8.py <design 資料夾>
import sys, os, json


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    plan['rigging'] = {
        'src': '數值照 Ship_Rigging §6–7（繩的色、粗、slack；預設風 4.5,−1.5,0）；側支索根數照 W p.~84（pinas 134 呎：主 7、前 6、後 4 根 putting）照船長比例縮〔估〕',
        'colors': {'standing': '#2b2620', 'running': '#a08458', 'sail': '#f2ead8', 'channel': 136, 'deadeye': 36},
        'channels': {'shrouds': {'fore': 4, 'main': 5, 'mizzen': 3}, 'backstays': {'fore': 1, 'main': 1}, 'spacing': {'fore': 3, 'main': 5, 'mizzen': 5},
                     'first_aft': 2, 'first_aft_by_mast': {'fore': -5}, 'width': 3, 'below_rail': 0,
                     'src': '設計決定：channels 在舷頂那兩格的舷外（砲門頂上面，Ship_Setup §3）；前桅在船首樓（x 345–385）裡 ⇒ deadeye 從桅前 5 格起、間距 3（x 357／354／351／348 ＋ backstay 345），都落在船首樓的高舷牆上；後桅在後甲板（x ≤ 121）裡；兩舷一件'},
        'topmast_shrouds': 3, 'topmast_shroud_dx': 4,
        'thick': {'shroud': 0.9, 'topmast_shroud': 0.6, 'futtock': 0.5, 'backstay': 0.6, 'stay': 1.1, 'tm_stay': 0.8, 'bobstay': 1.0, 'sheet': 0.4, 'course_sheet': 0.5, 'tack': 0.5},
        'thick_src': '設計決定：拉貝爾號的粗細照本船桅徑放大約 1.25',
        'ratlines': {'step': 4, 'start': 5, 'stop': 12, 'min_span': 4, 'th': 0.25, 'tm_step': 4, 'tm_start': 3, 'tm_stop': 8, 'tm_th': 0.2,
                     'climb_deck': {'fore': 'forecastle', 'main': 'main', 'mizzen': 'quarter'},
                     'src': 'Ship_Rigging §6：橫繩組（sub=ratlines），每 4 格一道；前、主桅下桅標繩梯 climb=1（foot 舷牆內側的甲板、head 桅樓平台這一舷的邊）；上桅、後桅不標'},
        'sails': {'fullness': 1.05, 'course_clew_above_rail': 3, 'course_in': 0.9, 'clew_in': 0.1, 'sprit_drop': 24, 'sheet_aft': {'fore': 27, 'main': 36},
                  'tack_fwd': {'fore': 24, 'main': 30}, 'belay_x_max': 380, 'sprit_belay_x': 370, 'bs_shroud_x': 376,
                  'lateen_clew': {'mizzen': [62, 76]}, 'lateen_tack': {'mizzen': ['main', 140]}, 'lateen_sheet_x': 56,
                  'src': '設計決定：拉貝爾號的繫索距離照帆桁長放大 1.5；course 帆腳在舷頂上 3 格；lateen 的 clew 在帆桁後端下面、後甲板舷牆上方，sheet 綁到船尾舷頂兩舷，tack 從帆桁前端綁到主甲板 x 140（後甲板 break 前面）'},
        'bobstay_head_z': 44, 'bobstay_at': 0.7,
        'bobstay_src': '設計決定：bobstay 從 knee 前端外一格（z 44）綁到艏斜桅 70% 處 ⇒ 不貼 knee 往前斜的前緣、從紅獅前面過（紅獅往後挪到 knee 前端後 12 格）；v1 z 40、0.75 ⇒ 穿 knee 9 格、穿獅子；試過 z 30–48 × 0.45–0.75 只有這一組兩邊都 0',
        'flags': {'ensign': [24, 16], 'pennant': [36, 3], 'pennant_color': '#c8303c',
                  'src': '設計決定：荷蘭三色旗（紅白藍，1660 年代的商船旗）掛在後桅 lateen 帆桁後端；主桅頂一條紅長旗'},
        'wind': [4.5, -1.5, 0], 'sail_seconds': 3}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

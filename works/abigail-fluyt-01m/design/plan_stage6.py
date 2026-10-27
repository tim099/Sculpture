# 澤漢號 plan.json 的 deco（步驟 6）—— 一次性產生；只換這一段。
#   用法：python -I -X utf8 plan_stage6.py <design 資料夾>
import sys, os, json


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    plan['deco'] = {
        'src': '設計決定（照 Ship_Fittings §9.9；船首喙的作法照拉貝爾號）',
        'head': {'ext': 18, 'z_from': 20, 'z_full': 44, 'z_tip_top': 50, 'ext_upper': 3, 'z_top': 60, 'color': 177, 'gold': 248, 'rail_color': 36,
                 'rails': [{'z_hull': 62, 'z_tip': 49, 'mid_dx': 8, 'mid_dy': 11, 'tip_back': 3},
                           {'z_hull': 56, 'z_tip': 46, 'mid_dx': 8, 'mid_dy': 10, 'tip_back': 5}],
                 'src': '設計決定：knee of head 伸出艏柱 1.8 m（福祿特的船首喙短小，W 的 pinas galjoen 是 22 呎 ⇒ 本船小很多）、中線 3 格厚、前端上緣金；head rail 每舷兩根，從船首樓舷牆掃到 knee 前端；前端落在 knee 頂 z 50 以下（v1 z_tip 51／48 ⇒ 第一根前端浮在 knee 上方，組裝件多 2 個元件）'},
        'figurehead': {'back': 12, 'red': 160, 'gold': 248, 'tongue': 224,
                       'src': 'W p.85（pinas）：船艏獅子（leeuw）〔查〕；荷蘭船的紅獅、金鬃、金冠（設計決定）；1.5 m 長、1.1 m 高，趴在 knee 上（前端往後 12 格，讓 bobstay 從獅子前面過；v1 back 4 ⇒ bobstay 穿過獅子）'},
        'emblem': {'z_top': 66, 'gold': 248, 'red': 160,
                   'src': '設計決定：窄 hek 上兩扇窗上面一隻金色海公雞（船名 Zeehaen ＝ 海公雞／海雞）、紅冠；W p.83：船艉平板上照慣例裝紋章（wapen）〔查，pinas〕'},
        'false_ports': {'at': [[86, 50], [356, 52]], 'r': 2.5, 'hole': 36, 'rim': 160,
                        'src': 'W p.160：商船船頭船尾常開圓洞當假砲門（ronde gaten om voor looze poorten te dienen）〔查〕⇒ 兩舷船尾（後甲板底下）、船頭（船首樓底下）各一個，直徑 0.5 m、黑洞紅框（換色，不開洞）'},
        'lantern': {'source': 'gura-tridente-01m-lantern', 'scale': 0.5, 'src': '照拉貝爾號：三叉戟號的船尾燈 0.5 倍，站在 hek 頂中間（kind=light）'}}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

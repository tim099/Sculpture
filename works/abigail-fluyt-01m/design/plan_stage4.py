# 澤漢號 plan.json 的 paint、stern（步驟 4：塗裝、船尾窗）—— 一次性產生；只換這兩段，其他原封不動。
#   用法：python -I -X utf8 plan_stage4.py <design 資料夾>
import sys, os, json


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    plan['paint'] = {
        'base': 177, 'black': 36, 'frieze': 45, 'gold': 248, 'reveal': 160, 'glass': 87,
        'wales': {'rows': [{'name': 'lower barghout', 'deck': 'main', 'dz': -7, 'h': 3, 'color': 36},
                           {'name': 'upper barghout', 'deck': 'main', 'dz': -1, 'h': 3, 'color': 36}],
                  'src': 'W p.159（gemeene Fluit）：舷側一串 barghout（wale，12 duim ≈ 3 格）與 vulling（夾板）交錯〔查〕；本船單層甲板、乾舷低 ⇒ 只留兩道：水線上一道、甲板那一道（甲板 −7..−5、−1..＋1，照舷弧）〔估〕；黑色是設計決定'},
        'frieze_src': '設計決定：upper barghout 以上到舷頂下一格漆深綠（45）—— 17 世紀荷蘭船上部常見綠、紅、黃的漆（⚠ 沒核到福祿特的配色）；砲門框紅 160；舷頂最上一格黑',
        'transom_src': '設計決定：wing transom（wulf）以上的窄 hek 綠底、wulf 那一列與頂下一列金 248；hek 上的雕飾板在步驟 6',
        'stern_x_max': 70}
    plan['stern'] = {'rows': [{'deck': 'main', 'ref_x': [56, 70], 'n': 2, 'w': 5, 'h': 5, 'half': 10, 'sill': 8, 'kind': 'window',
                               'src': '設計決定：船長室（後甲板底下、主甲板船尾那一段，甲板 z 42）在窄 hek 上兩扇窗，下緣離地板 0.8 m（wulf z 46 之上）'}]}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

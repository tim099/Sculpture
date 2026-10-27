# 澤漢號 plan.json 的 rudder_anchor_build（步驟 11：舵、舵柄、錨、錨鏈孔）—— 一次性產生；只換這一段。
#   用法：python -I -X utf8 plan_stage11.py <design 資料夾>
import sys, os, json

H = 'abigail-fluyt-01m'


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    plan['rudder_anchor_build'] = {
        'rudder': {'work': H + '-rudder', 'title': '澤漢號 舵（沿艉柱，0.1 m）', 'model': '舵', 'half_t': 1, 'z_top': 52,
                   'width': [[0, 12], [18, 12], [30, 8], [40, 5], [52, 4]], 'below': 182, 'above': 36, 'iron': 73, 'strap_every': 8, 'waterline_z': 30,
                   'max_deg': 35, 'bevel': 1,
                   'src': '設計決定：舵沿艉柱後緣（lines.x_post，斜 9°）從龍骨底到 wulf 上面一點（z 52：舵頭從窄 hek 的舵孔 hennegat 進船裡、接舵柄；在 hek 的海公雞 z 57–66 底下）；3 格厚、舵葉 1.2 m 往上收到 0.4 m 的舵頭；水線下白、上黑、每 8 格一道鐵箍；max_deg 35、bevel 1 照拉貝爾號'},
        'tiller': {'work': H + '-tiller', 'title': '澤漢號 舵柄（helmstok）', 'model': '舵柄', 'host': H + '-deck-main', 'x_stock': 58, 'z_deck': 43, 'z': 50, 'x_end': 84, 'color': 136, 'stock_color': 141,
                   'src': '設計決定：福祿特在後甲板底下的舵艙（stierplecht）用 whipstaff（kolderstok）推舵柄 —— 舵柄做成獨立模型 kind=tiller（Ship_Helm 操舵鏈；whipstaff 不另做）：舵頭在 hek 內側（x 58、1×3、主甲板 z 43 到 z 50），舵柄沿中線往前到 x 84（2.6 m，船長室艙壁 x 88 前面）、高 z 49–50；轉軸垂直、跟舵同一個舵角'},
        'anchor': {'gear_work': H + '-anchor-gear', 'gear_title': '澤漢號 錨架（兩舷 billboard）', 'gear_link': '錨架', 'work': 'basecamp-frigate-constitution-01m-anchor',
                   'scale': 0.5, 'pivot': [23.5, 16.5, 56.5], 'x_try': [360, 362, 364, 366, 368], 'z_try': [68, 69, 70, 71, 72, 73, 74], 'z_hull': 60,
                   'd_step': 0.5, 'd_max': 20, 'ledge_half': 6, 'ledge_out': 2, 'ledge_t': 2, 'color': 136,
                   'src': '沿用共用錨元件（Ship_Game §9 anchor）縮 0.5（錨幹約 2.9 m，設計決定：約 260 噸的船；拉貝爾號 45 噸用 0.3）、meta anchor=bower；兩舷各一、吊在船首樓舷外（照拉貝爾號：錨臂順著船殼切線、往外推到零碰撞，錨冠底下一塊 billboard 托板；錨環在船首樓舷牆頂上下（v1 z 58–64 ⇒ 錨冠托板落在 z 29，就在水線上））；x 在前桅 channels（x 343–359）前面。⚠ 沒有 cathead'},
        'hawse': {'x': 372, 'z': 50, 'src': '設計決定：錨鏈孔在船頭、主甲板上方（只登記固定點 hawse-S／P，⚠ 沒有開孔）'}}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

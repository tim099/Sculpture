# 光榮號 plan.json 加 `engine` 一節（階段十：機艙）—— 自己寫的；照拿破崙號 plan.json engine 的欄位，數字換成光榮號的。
#   用法：python -I -X utf8 tools/plan_engine.py <design>（重跑 ⇒ 同一份）
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plan_io

D = os.path.abspath(sys.argv[1])
P = plan_io.load(D)
P['engine'] = {
    'src': ('Tim 2026-10-18（/scp-shipbuilding）：「參考拿破崙號 補上光榮號的細節與meta吧 然後匯入遊戲」「金屬部件參考拿破崙號 設定為光滑金屬質感」。'
            '史料 RES §5：一具臥式回行連桿（HRCR）雙缸單脹主機（FR「two-cylinder horizontal」、Navypedia single-expansion）、設計 2,500 ihp（Campbell）、試航 2,699 hp、'
            '名義 900 ch（FR／Scientific American）；八座橢圓鍋爐（Indret；EN-Class 引 Gille、FR）；一根煙囪在前桅與主桅之間；單軸六葉 5.8 m；'
            '試航 13.5 kn（1860-08-20／21，EN-Gloire、FR 引 Battesti）、其他說法 13.1／12.3／11.75（實用 11）；煤 675 t。'
            '機艙與鍋爐的位置、各件尺寸都沒查到 ⇒ 設計決定（遊戲用：外觀＋給遊戲判斷壞了沒有＋第一人稱走得出來）'),
    'room': {'x': [400, 650], 'deck_under': 86, 'src': 'decks.rows orlop skip [400, 650]（階段四定的機艙）；下砲甲板的樑底 z 86'},
    'colors': {'iron': 36, 'steel': 73, 'brass': 248, 'fire': 232, 'brick': 132},
    'engine': {
        'x': [404, 462],
        'bed_top': 12,
        'cyl': {'xs': [418, 446], 'r': 10, 'y': [140, 180], 'z': 41, 'chest': {'half_x': 5, 'y': [150, 170], 'h': 4},
                'support': {'half_x': 8, 'y': [146, 174]}},
        'crank': {'xs': [418, 446], 'throw': 9, 'web_half': 3, 'web_t': 2, 'pin_r': 2, 'half_x': 4},
        'rods': {'dz': 13, 'r': 1},
        'crosshead': {'y': [232, 238], 'half_x': 4, 'z': [26, 56]},
        'guide': {'y': [239, 243], 'half_x': 8, 'z_top': 58},
        'conrod': {'y': [212, 231]},
        'pedestals_x': [405, 432, 459],
        'meta': {'kind': 'engine', 'engine': 'direct', 'cylinders': 2, 'ihp': 2500, 'nhp': 900, 'kn': 13, 'kn_max': 13.5, 'maker': 'FCM',
                 'material': 'iron', 'render': 'smooth'},
        'src': ('設計決定：HRCR ＝ 兩缸臥在左舷（缸軸沿 y、在軸心高度 z 41）、活塞桿每缸兩根從軸的上下（z 41 ± 13）跨過去、接右舷導軌上的十字頭，連桿從十字頭「回」到軸上的曲柄 ⇒ '
                '曲軸就是螺旋槳軸（direct：直接驅動、沒有齒輪）；缸徑 2.0 m、行程照曲柄半徑 0.9 m 都是推的（沒查到）。kn 取 13（EN infobox；TASK-0696 照單：史料 13 節，試航 13.5、實用 11–12.3）、kn_max 取官方試航 13.5；'
                'maker ＝ Forges et Chantiers de la Méditerranée（Scientific American via NavEnc，次級來源）。曲柄做成會轉的外部模型（kind=gear，同拿破崙號的齒輪）：'
                '跟螺旋槳同軸 ⇒ spin_k 6（rpm × 6 ＝ 每秒幾度）')},
    'crank_model': {'work': 'kaguya-gloire-01m-engine-crank', 'model': '曲柄', 'host': '機艙-主機',
                    'meta': {'kind': 'gear', 'gear': 'crank', 'spin': 'rpm', 'spin_mode': 'rate', 'spin_k': 6}},
    'shaft': {'y': 200, 'z': 41, 'r': 2, 'x': [168, 462], 'plummer_from': 240, 'plummer_every': 30,
              'work': 'kaguya-gloire-01m-shaft', 'link': '螺旋槳軸', 'meta': {'kind': 'shaft', 'material': 'iron', 'render': 'smooth'},
              'src': ('軸心 z 41 ＝ 螺旋槳 hub；aft ＝ x 168 ＝ 螺旋槳模型的 shaft-fwd（Blockside：螺旋槳接 aft 離 hub／shaft-fwd 24 格內的那根軸）；'
                      '穿 deadwood 那一段是船殼（遊戲照兩端連線借船殼的格）；往前接到主機（曲軸 ＝ 這根軸，fwd ＝ x 462 推力座）；每 30 格一座軸承座落到船底；從後彈藥庫地板（z 44）底下過')},
    'boilers': {'work': 'kaguya-gloire-01m-boilers', 'link': '機艙-鍋爐', 'funnel': '煙囪', 'boilers': 8,
                'xs': [[541, 564], [567, 590], [593, 616], [619, 642]], 'y_in': 189, 'width': 32, 'z': [13, 50], 'crown': 5,
                'uptake_z': [51, 88], 'funnel_x': 563, 'funnel_r': 13,
                'meta': {'kind': 'boiler', 'boilers': 8, 'funnel': '煙囪', 'material': 'boiler', 'render': 'smooth'},
                'src': ('史料：8 座橢圓鍋爐、一根煙囪。排法是設計決定：船只有一根煙囪 ⇒ 八座一組、煙囪正下方；一條沿中線的燒火通道（y 189–211，2.3 m；'
                        '拿破崙號階段十四的研究：爐口前 2.4–3 m，推）、兩舷各四座爐門朝中線；每座 2.4 × 3.2 m、高 3.8 m、頂收圓（crown 5）；'
                        '頂上 smoke box 一整片（z 51）收成煙囪的圓（x 563、半徑 13），接到煙囪底（z 89）；'
                        'material=boiler（鐵殼＋滿水，照拿破崙號 2026-10-17：iron 會多好幾千噸）＋render=smooth')},
    'floor': {'work': 'kaguya-gloire-01m-deck-engine', 'link': '甲板-engine', 'z': 12, 'x': [400, 650], 'hole': 10, 'plate': 73,
              'src': '照拿破崙號階段十四：機艙鐵地板、板面 z 12（站 z 13 ＝ 鍋爐底）、(x, y) 都是 10 的倍數不鋪（排水孔）；甲板 meta level −1'},
    'access': {'work': 'kaguya-gloire-01m-ladders-engine', 'link': '甲板-lower/梯子-機艙', 'host_work': 'kaguya-gloire-01m-deck-lower',
               'ladders': {'engine-S': [207, 533, 1], 'engine-P': [193, 533, 1]},
               'src': '照拿破崙號階段十三：主艙口（x 505–533）裡兩座鐵梯（每 3 格一階、往前 1 格），從機艙地板爬到砲甲板、往船頭出艙口；.decks ＝ engine,lower'},
}
plan_io.save(D, P)
print('engine 一節寫進 plan.json')

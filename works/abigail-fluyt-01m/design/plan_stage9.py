# 澤漢號 plan.json 的 guns_build（步驟 9：舷側 4 磅砲、迴旋砲）—— 只換迴旋砲的位置與出處；砲種、搜法照拉貝爾號（同一個 scale ⇒ 遊戲裡同一份網格）。
#   用法：python -I -X utf8 plan_stage9.py <design 資料夾>
import sys, os, json


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    GB = plan['guns_build']
    GB['types']['4l']['src'] = ('Ship_Guns §2.2：只差口徑 ⇒ 縮放現有的 —— 風暴角號 6 磅長砲（0.05 m）縮 0.375，跟拉貝爾號同一個 scale（遊戲裡同一份網格）；'
                                '福祿特帶的砲口徑查不到（研究代理：每舷 4–6 門輕砲〔估〕）⇒ 4 磅；pivot 照收穫號（砲架前緣中間、甲板面）；砲種表已有 4l')
    GB['swivels'] = {'type': 'pierrier', 'rows': [{'deck': 'quarter', 'x': 70}, {'deck': 'quarter', 'x': 84}, {'deck': 'forecastle', 'x': 374}],
                     'src': '設計決定：W p.160 說往西（西印度）的船人多、「那邊在打仗」〔查〕⇒ 除了舷側 8 門 4 磅砲，後甲板欄杆兩個、船首樓一個迴旋砲插座（每舷 3）；後甲板那兩個在後桅 channels（x 96–110）後面、船首樓那一個在前桅 channels（x 343–359）前面；插在舷牆頂（那一欄船殼最高那一層、牆厚中間）；砲照拉貝爾號（皇家號叉架後膛砲縮 0.39）'}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

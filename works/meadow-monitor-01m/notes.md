# 莫尼特號（USS Monitor，1862 年 3 月 9 日漢普頓錨地海戰）—— meadow

委託：Tim 2026-10-15「照遊戲用的規格造船，參考歷史資料與圖紙，最後由妳繪製圖紙並建造（資訊不足的部分由妳設計），旋轉砲塔參考維吉尼亞號」。

## 作品怎麼拆（全部 0.1 m／格、框 544×131×80、關聯 at 0,0,0；砲塔 0.05 m）
- 組裝件 `meadow-monitor-01m-assembly`（莫尼特號，主作品）；船殼 `meadow-monitor-01m`（任務作品，tags sub）。
- 關聯：船殼（下船殼、skeg、平衡舵、中隔艙壁、錨井、螺旋槳井；meta kind=ship、waterline_z 30、material iron）、浮筏-鐵甲（iron＋smooth）、浮筏-木背板、甲板-berth／甲板-main（kind=deck）、駕駛塔（iron）、煙囪＋煙囪-鏡像（kind=funnel、smoke）、鍋爐＋鍋爐-鏡像（kind=boiler、funnel＝煙囪／煙囪-鏡像）、機艙-主機（kind=engine）、螺旋槳軸（kind=shaft）、鼓風機進氣管、彈藥庫（kind=magazine、16 桶）、艙房、梯子（kind=ladders，3 座）。
- 外部模型：甲板-main/砲塔（本船元件 `-turret`：kind=gun、gun=11d、mount=turret、arc −174..174、rate 16）、螺旋槳（`-screw`，kind=propeller）、駕駛塔/舵輪（憲法號元件 scale 0.07）、錨（憲法號 bower scale 0.2，收在錨井）、彈藥庫/桶×16（憲法號火藥桶）。
- 砲塔元件拆三件（造船規格 §4.6）：`-turret-gun`（一門 XI 吋 Dahlgren＋滑架，砲塔的框、固定點 pivot）、`-turret-shell`（圓筒＋鐵軌頂）、`-turret`（關聯 shell、gun、gun mirror=x；固定點 pivot／muzzle(-a/-b)／breech(-a/-b)）。
- 產生程式：`design/gen_monitor.py`、`gen_turret.py`（只讀 `plan.json`）；`apply_build.py`（建子作品、同步格子）、`apply_links.py`、`apply_models.py`；圖紙 `design/draft_blueprint.py` → `monitor_blueprint.png`。

## 史料與設計決定（每個數字的出處在 plan.json provenance）
- 浮筏 173′4″×41′4″×5′、下船殼 124′×34′（頂）×18′（平底）×6½′、船頭懸出 15′、船尾 34′4″、吃水 10′、乾舷 18″（Dorr 1874；Ericsson, B&L 1887；1861 合約）。179 ft 是合約長度、不是實際。
- 砲塔內徑 20′、高 9′、8 層 1″；中心在駕駛塔後 55′、坐在中隔艙壁上；一圈 22.5 秒；轉離中線 6° 砲彈就過得了駕駛塔（Ericsson）。
- 設計決定（史料沒有）：兩門砲的軸距 1.4 m、砲軸離甲板 1.1 m、煙囪與進氣管尺寸、舵的尺寸、浮筏兩頭的曲線、錨井直徑。
- 取捨：煙囪、進氣管海戰時可能已經拆下（NOVA：戰前拆掉 smoke boxes）；遊戲要冒煙 ⇒ 保留。只有一隻錨（Ericsson 四爪錨；共用元件是兩爪 bower）⇒ 錨偏右舷 1 格、只登記 hawse-S。

## 讀數（2026-10-15）
- 組裝件 463,086 格、1 個連通塊、空腔 0、link_overlap 0、models_broken 0；砲塔掃過的圓（半徑 34.5 格）裡甲板以上別的實心 0。
- 砲塔元件：兩門砲與圓筒重疊 0、砲口內膛那一格空、砲口在半徑 62.6（內緣 61、外緣 65）。
- 排水（水線以下外形）約 1,069 t（史料 987 long tons）。
- vxk：`exports/monitor.vxk`（組裝件的 exports）checksum 37b128dd、模型 20（網格 5 份）、帶 meta 34、固定點 43。
- Blockside 暫存副本的匯入檢查（不動正式遊戲）：✗ 1（gun=11d 砲種表沒有）、⚠ 7（geo、左舷沒錨／hawse-P、軍官／舵手／陸戰隊站不下、沒有 cfg.base）；砲班站滿、火藥 1／1 門走得到（最遠 9.1 m）；材質 iron 95,813 格。

## 給遊戲那側（geo、cfg）
- 水線 z 30（30.5）；主甲板走路格 z 35；住艙甲板走路格 z 5；砲軸 z 46；砲塔頂 z 64；駕駛塔頂 z 46；煙囪口 z 52。
- 浮筏 x 8..535、半寬 63；下船殼 x 113..489（平底 x 143..454）。
- 航速：平常 6 kn、最高 8 kn（Stimers，Dorr 1874）⇒ cfg.base。主機：振動槓桿式、一個汽缸鑄件兩頭各一活塞，缸徑 40 in（Stimers；Wikipedia 36 in）。
- 砲種 11d（XI 吋 Dahlgren）：全長 161 in、15,700 lb、實心彈 166 lb／爆裂彈 133.5 lb、海戰時裝藥 15 lb。砲塔一個模型兩根砲管（muzzle-a／-b）⇒ 要兩門都開，砲種給 burst 2（或之後改成兩個砲模型，元件已拆好）。
- 砲班現在站在砲塔圓筒外面的甲板上（遊戲照模型外框往外排站位）。
- 艙蓋（TASK-0638，2026-10-16）：子作品 -hatch（17×13×3、0.1 m、鐵板＋黃銅提環＋兩組鉸鏈耳；固定點 hinge-a 0,0,0／hinge-b 16,0,0 ⇒ 沿 y 小的那一邊往上掀）。掛在 -deck-main：艙蓋-前 at 422,59,35、艙蓋-機艙 at 207,59,35（meta kind=door, open=up；艙口 15×11 每邊多 1 格）。砲塔底下那個艙口（x 316）沒放：在砲塔裡、砲的外框蓋到它，掀起來會穿進砲。遊戲：門在 ⇒ 艙口不進水，打掉 ⇒ 甲板淹過就灌進去。

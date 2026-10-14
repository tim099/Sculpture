# 三叉戟號（Tridente）—— 一級戰列艦，參考聖特立尼達號（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-14（TASK-0553 傘，子單 TASK-0554～0563）：「小鯊魚 接著建造屬於你的船吧 船型用最大的一級戰列艦（圖紙可以參考 聖特立尼達號 Nuestra Señora de la Santísima Trinidad）然後細節與圖紙全部交給妳設計規劃 GO」；補充「規格是遊戲用的」「同時開 task 管理建造進度」。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫這些遊戲用得到的大致構造。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 座標約定
- 空間 1100×400×800；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 200 格**，鏡像 y ↔ 400 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 200。
- 「在不在船裡」：|y − 200| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱；遊戲取船寬中心 size/2 ＝ 200。
- 0.1 m／格（書卡 meters_per_voxel 已記）—— 遊戲裡每艘船要同一個比例。

## 設計方向（開工時的決定）
- 船名「三叉戟號」：聖特立尼達（三位一體）× 鯊鯊的三叉戟。
- **船殼照自己的線形從頭產生**（`design/hull_lines.py`），不從餘燼號拉伸：聖特立尼達號寬 16.2 m、四層砲列；餘燼號沿用憲法號 13.3 m 的寬。
- 沿用現成零件當模型：砲、舵輪、火藥桶、燈籠、羅經櫃、絞盤、小艇（遊戲已認得的砲種代碼優先）。

## 階段一 新圖紙 01／02（2026-10-14，TASK-0554）
查證：兩個獨立研究 agent 並排 ⇒ `references/research_2026-10-14.md`（互相不同意的照列、寫明本設計取哪個）。
設計 `design/plan.json`（每個數字的 `src`：參考資料附出處／設計決定）；程式：
- `hull_lines.py`：線形 ⇒ 每個 (x, z) 的半寬。船中剖面（平底＋圓舭＋tumblehome 每舷 2 m）× 長度方向收縮（船頭橢圓、上鈍下尖；船尾到 wing transom 以下收到艉柱，以上留 transom 寬 0.78）；兩端圓底往上抬成 deadwood（剖面往 V 形＋酒杯形 garboard 收）；forefoot 圓弧 r 70；艉柱後傾 8°、counter 往後挑 10 格、船尾面後傾 10°。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`verify_lines.json`、`masks/hull/hull_01..05.vox.txt`（船殼清單，at 0,0,0）。船殼 ＝ 線形實心往裡留 4 格牆（外板 1、肋骨 141 ×2、內板 177）；舷頂以上多算 12 層再切 ⇒ 舷頂不變成蓋子。外板：水線 z 79 以下銅 168、以上黑 36。
- `layout.py`＋`draft_layout.py` ⇒ `sheet02_layout_v1.png`（甲板、四層砲門、桅與帆桁、正面）、`verify_layout.json`。

| 項目 | 讀數 | 參考 |
|---|---|---|
| 砲甲板長（z 89 量） | 61.44 m（614.4 格） | eslora 61.43–61.44 m（Mejías Tavero 1797／es.wikipedia） |
| 最大寬（含外板） | 16.3 m（163 格） | 16.16–16.25 m |
| 龍骨 | 52.83 m | 51.50／51.83／52.38 m（三個出處） |
| 設計水線 | z 79（平龍骨 7.9 m） | 吃水後 8.20–8.24、前 7.50–7.52 m |
| 排水量（水線下實心 × 1.025） | 4,952 t（+1.0%） | 4,902 t（es.wikipedia；另有 4,950／5,432） |
| 船殼牆 | 1,153,334 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（船中 z，舷弧往船尾 +4、往船頭 +6）：orlop 66、下砲甲板 89、中 112、上 135、上甲板（QD＋FC 接成第四層砲列）158、poop 180（x ≤ 228）。間距 23（同憲法號／餘燼號）；下砲甲板砲門下緣 z 95 ＝ 離水線 1.6 m（Mejías Tavero 1.58 m）。
- 砲門每舷 16／17／18／17（1805 年 32×36、34×24、36×12、18×8＋16 obús 照 ÷2 —— 砲門數沒有出處）；舷側 136 ＋ 追擊 4 ＝ 140。間距 22–27、層與層上下隔 14、砲門上緣離上一層甲板 ≥ 9。
- 桅：**本船 1793 年的桅帆表**（Mejías Tavero，UPC 論文 Fig. 15）：主桅 41.74 m、主上桅 22.71、主頂桅 16.07、主帆桁 34.69、主上桅帆桁 27.16、前桅 38.28、前帆桁 30.37、前上桅 20.76、後桅 28.00、艏斜桅 22.57、jib-boom 15.60；表裡沒有的照比例推（design）。主桅頂離水線 64.9 m（Victory 62.5 m）。⚠ 不保證是 1805 那一套。
- 外觀（之後的階段）：黑船殼、每層砲門一條紅帶、上下白線（Trafalgar 目擊「four distinct lines of red, with a white ribbon between them」＋ RMG Haines 模型）。

讀數與反向對照：
- 半寬 +3 ⇒ 最大寬 163 → 169、每個站位每個高度 +3（船頭舷頂 +2，tumblehome 上取整）。
- 下砲甲板第 5 個砲門往前推 3 ⇒ 間距讀數 22 → 19／25。
- 產生程式重跑：9 個輸出檔逐位元組相同。

⚠ 已知、之後的階段處理：船尾是一整片平的 transom＋counter（船尾廊與 quarter galleries 在 TASK-0558）；船頭是圓的艏柱（beakhead／head 在 TASK-0558）；最大寬那一格的高度 z 96 沒有出處（設計決定）。

## 階段二 船殼落格（2026-10-14，TASK-0555）
- 標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py gura-tridente-01m 0 masks/hull/hull_01..05.vox.txt`（5 刀：250,000 ×4 ＋ 153,334，每刀讀回 placed ＝ 清單格數）→ `船殼:end`。
- **結果帳**（`design/tools/check_hull.py`：作品那側從 `export format=list links=none mark=船殼:end` 讀）：作品 1,153,334 ＝ 設計 1,153,334，缺 0、多 0、色差 0。
- **結構**（引擎 `stats structure=1 mirror=y:200`）：1 元件、封閉空腔 0、鏡像差 0／0／0。
- **線形對照**：右舷外緣（每個 (x, z) 最大的 dy）vs `hull_lines.hb` 取 floor，x 80..720 每 25、z 6..176 每 5，836 點、差 0。反向對照：設計那一站（x 430）+3 ⇒ 報 3（34 點，那一站每個高度）。
- **組裝件** `gura-tridente-01m-assembly`「三叉戟號（組裝）」：0.1 m、1100×400×800（parent 船殼，沒標 sub ＝ 主作品）；關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=79`（遊戲 `hullZW` 讀它）。
- 過程圖：`overlays/stage2_hull_{bowq,sternq,side,top}.png`（鏡頭：yaw 30 ＝ 船頭四分之三、150 ＝ 船尾四分之三、90 ＝ 側面）。
- ⚠ 看得到的：船殼是一整片黑（紅帶、白線、砲門在階段三）；舷頂是 4 層色的切面（cap rail 之後）；艙裡是空的（甲板在階段四）。

## 階段三 砲門四層、塗裝、船尾窗（2026-10-14，TASK-0556）
設計 plan.json `paint`、`stern`；產生 `design/draft_ports.py`（船殼照 draft_lines.hull_volume ＝ 作品，階段二證過）⇒ `masks/ports/carve.vox.txt`（50,651，帶刻之前的顏色守門）、`masks/ports/paint.vox.txt`（87,786，換色）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 砲門 ＝ `layout.ports`（每舷 16／17／18／17、兩舷同一組 x）：開口 (x, z) 範圍裡、那一舷 |dy| ≥ 6 的牆全刻（4 格牆刻穿；船頭那幾個在斜的牆上會刻得長一點）。外擴 1 格的那一圈牆（含內板那一面）漆紅 ＝ 砲門的 reveal。
- 塗裝：外板那一層（EDT ≤ 1，所以船頭朝前、船尾面都算）照高度換色、只換黑 36（銅底不動）—— 每層砲門一條紅帶 ＝ 砲門下緣 − 2 .. 上緣 ＋ 2（照甲板舷弧），帶的上下各一列白 255。**紅 192**（渲染比過：跟銅 168 分得開；聖特立尼達號「glowing red」）。
- 船尾面（每個 (y, z) 從最後面往前那一段牆）：四列窗 —— 中砲甲板 7、上砲甲板 7、上甲板 7、poop 5，寬 7（奇數 ⇒ 中間那扇以 y 200 為中心）、高 9／8；窗 ＝ 刻掉最外一格、第二格換玻璃 87（海藍）、外一圈金框 248。中砲甲板那一列第 2、6 個是船尾追擊砲門（整段牆刻穿、不放玻璃）。
- 🩸 第一版鏡像差 2,232：窗的 y 用 `round()`（Python 取偶）⇒ 中間那扇落在 196..202（應該 197..203）；而且寬 6 的窗不可能以第 200 格為中心 ⇒ 改成對稱取整＋寬一律奇數（程式加斷言）⇒ 0。
- 落格：`砲門:begin` → carvevox（顏色守門，carved 50,651）→ stampvox overwrite=1（placed 87,786）→ `砲門:end`。

讀數（`design/tools/check_stage3.py`，作品從 export 讀）：
- **結果帳**：作品 1,102,683 ＝ 設計（船殼 − 刻 ＋ 換色），缺 0、多 0、色差 0。
- 136 個砲門開口（兩舷）從船外往船中看：看不穿的 0。**反向對照**：同一把尺量 `船殼:end`（還沒開）⇒ 136 個全報；產生程式 `--probe=skip_port=middle:9` ⇒ 只報中砲甲板第 9 個（兩舷各 396 格）。
- 帶子高度裡外板還是黑的（含船頭朝前的面）：0。引擎 stats：1 元件、空腔 0、鏡像差 0。
- 換色：紅 74,005、白 11,378、玻璃 1,477、金 926；刻掉：外板 13,753、肋骨 24,622、內板 12,276。
- 過程圖：`overlays/stage3_ports_{bowq,sternq,side,astern}.png`。
- ⚠ 看得到的：艙裡沒甲板 ⇒ 從砲門看得到對面的牆；舷頂還是 4 層色的切面；船尾是平的大 transom（陽台、quarter galleries 在 TASK-0558）。

## 階段四 甲板、艙口、梯子（2026-10-14，TASK-0557）
設計 plan.json `decks_build`；產生 `design/draft_decks.py` ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（遊戲用的大致構造）：每層 ＝ 那個高度的艙裡（外形實心扣掉 4 格牆）鋪一格甲板板（砲甲板 177、上甲板與 poop 250）＋橫樑（每 16 格、2 寬 3 深、136）；高度照 `layout.deck_z`（舷弧）。poop 只到 x 228，前緣一道艙壁（兩道門 |dy| 16）＋poop 上的胸牆（梯頭留口）。
- 開口：艙口三個疊在中線（後 300–318、主 470–500、前 585–605，|dy| ≤ 12；orlop 到上甲板每層都開）＋圍欄 2 格；梯子口；桅孔 ＝ `layout.mast_hit`（桅階段用同一支 ⇒ 剛好填滿；後桅腳立在 orlop、那層不開）。
- 梯子：兩層之間前後各一座（after／fore），層與層錯開（x 340／520 ↔ 372／552，這一層的梯子不站在下一層梯子的開口上）；上甲板 → poop 兩舷各一座（|dy| 30，往船尾爬，梯頂踩上 poop 在 x 226）。每 3 格一階、每階 2 格（約 56°），踏板 7 寬、兩側 stringer 接到上下兩層。
- 子作品（parent 船殼、tags sub、0.1 m、1100×400×800、at 0,0,0）：`-deck-{orlop,lower,middle,upper,spar,poop}`、`-ladders-{lower,middle,upper,spar,poop}`；梯子掛在它上面那一層甲板裡（關聯 `梯子`，meta `kind=ladders`），固定點 `<梯名>.foot／lo／hi／head`（腳踩的那一格）。組裝件關聯 `甲板-<層>`。
- 🩸 第一版組起來有 **2 個封閉空腔、179 格**：船尾最後一欄（x 79）的 poop 甲板板因舷弧取整比旁邊高一格，底下夾著 x 80 的橫樑與船尾牆（176 格）；orlop 船尾龍骨上方 3 格。各部件自己量都沒事（空腔要組起來才出現）⇒ 產生程式最後一步：船殼＋甲板＋梯子組起來找封閉空腔、填進高度最近的那一層（橫樑色）；`tools/delta_list.py` 只補新增的格（poop 176、orlop 3）。

讀數：
- 子作品結果帳（`tools/check_decks.py`，每件從匯出讀）：11 件、581,397 格，缺 0、多 0、色差 0。
- 跟船殼重疊 0、彼此重疊 0、梯子跟甲板重疊 0；每件鏡像差 0。
- 梯子點（從組裝件 `export format=parts` 讀，就是遊戲讀的那一份）：10 座、40 點、跟設計（格心）差 0；每個點那一格是空的、腳下實心、頭頂 14 格空。**反向對照**：`draft_decks.py --probe=drop_ladder=fore-upper` ⇒ 9 座、少的正是那一座。
- 組裝件：1,684,080 格、1 元件、空腔 0、link_overlap 0、鏡像差 0。
- 過程圖：`overlays/stage4_decks_nohull_bowq.png`（拿掉船殼看甲板）、`stage4_decks_sternq.png`。

## 階段五 船頭與船尾裝飾（2026-10-14，TASK-0558）
設計 plan.json `stern_deco`、`rudder`、`head`；產生程式都只讀「階段五之前」的組裝件（`design/deco_base.py`：`links=船殼,甲板-*`，梯子跟著甲板組；本階段的關聯加上去之後重跑讀到的還是同一份）：
`draft_stern_deco.py`（陽台、quarter gallery、名牌與徽）、`draft_rudder.py`、`draft_lantern.py`、`draft_head.py`（knee＋格柵、一舷裝飾、船首像、錨位置）⇒ `masks/{stern,rudder,head,lantern}/*.vox.txt`（**各子作品自己的座標**）、`*_placement.json`（框、關聯 at、鏡像 at）、`verify_*.json`、`sheet05_stern_v1.png`、`sheet06_head_v1.png`；落格 `tools/build_stage5.py`（`--redo` ＝ undo 到 0、改框、重貼、重接關聯）、`tools/build_lantern.py`；結果帳 `tools/check_stage5.py`。
- 作品名稱照新規則（Tim 2026-10-14）：組裝件「三叉戟號」（主作品）、船殼「三叉戟號 船殼」＋ `tags=sub`。

船尾：
- **陽台三層＋頂簷**（`-stern-walk` 13,723）：中砲甲板、上砲甲板、上甲板那三列窗外（UPC 論文 Mullan 114 砲艦三層窗／陽台）；地板 ＝ 那一層甲板面那兩格、從船尾面往後 12 格；欄杆 10 格（底檻、金欄柱每 2 格、黑扶手 2 深）、金托架每 12 格、金柱在第 2–3／5–6 扇窗之間；poop 甲板高度一道頂簷（金邊）。
- **quarter gallery**（`-quarter-gallery` 右舷一件 41,405、62×34×102；關聯 `後廊-S` at 62,241,99、`後廊-P` at 62,126,99 mirror=y）：x ≤ 124（上甲板第 1 個砲門 x 128 之前）、比船側往外 8 格、前端四分之一圓；船尾面那一段往裡包 3 格、往後跟陽台欄杆齊（陽台佔到的格一律讓給陽台）；三層紅牆、各層 3 扇側窗＋1 扇後窗（玻璃 87 凹 1、金框）、金腰線對齊陽台地板；底下黑身金箍的垂飾收到 z 99、頂上黑圓頂金肋＋金尖。
- **名牌與徽**（`-stern-deco` 741）：counter 紅帶上 **TRIDENTE**（5×7 金字凸 1、上下金線兩頭收尖；從船尾看由 −y 往 +y 寫）；taffrail 中線扇貝形徽（黑底金邊金肋、r 12）＋金三叉戟（像素圖 15×21，齒尖伸出扇面）。
- **舵**（`-rudder` 6,638）：前緣貼著現況艉柱、寬 2.2 → 1.5（水線）→ 0.6 m，頂端順著 counter 收進去（z 1–93）；厚 5／3 格；銅 5,882、黑 374、六道 pintle 帶（深銅 136）382 —— 艉柱兩側只貼 |dy| ≤ 8。
- **船尾燈**（`-lantern`，**0.05 m**、17×17×36、4,128 格）：八角、金腳金杯、琥珀玻璃 245＋金框柱、黑頂金肋、金尖；固定點 `base`／`wick`／`bail`；組裝件模型 `lantern-P`／`lantern-S`（scale 0.5、pivot 腳底、站在 taffrail 頂 z 207、|dy| 40），meta `kind=light`（造船規格 §9：遊戲在 wick 放點光源）。

船頭：
- **knee of the head＋格柵平台**（`-head-knee` 20,472 ＝ knee 16,825 ＋ 平台 3,647）：cutwater 從 forefoot z 25 往前上方掃到 z 160（比艏柱前緣往前 6.65 m，前端 x 785.5）；上緣從艏柱 z 148 升到 162；厚 7 → 5 → 3；水線下銅。平台 ＝ knee 上緣那兩格、兩道 head rail 之間、船殼外面（深淺木色棋盤格）。固定點 `bobstay-1／2／3`（cutwater 前緣中線 z 112／126／140，之後 bobstay 綁這裡）。
- **船頭裝飾一舷**（`-head-side` 2,115、85×49×91；關聯 `船頭裝飾` at 694,201,95、`船頭裝飾-鏡像` at 694,151,95 mirror=y）：上下兩道金 cheek（凸 1，從 x 703 包到 knee、x 761 收）、trailboard 金波浪、**knee 上半水平放的金三叉戟**（36×11）、每舷 2 個 hawse（金圈＋黑孔，z 104、|dy| 11／21）、head rails（main rail＋底下紅板、upper rail 往船尾抬到 cathead 底下、每 10 格黑立柱；1,003）、cathead（55° 外伸、上翹 8°、18 格、5×5、端面金；455）。
- **船首像**（`-figurehead` 3,314）：躍出的藍鯊（原創）—— 往前上方 35°、尾巴落在 knee 上緣前端；上藍 83 下白、張嘴一排白牙、黑眼白點、背鰭／胸鰭／尾鰭；放大 1.25（約 3.7 m）。
- **錨**：直接關聯憲法號 `-anchor`（47×33×58）—— 吊環頂在 cathead 端正下方：`錨-S` at 685,235,125、`錨-P` at 685,133,125 mirror=y（第一個候選往 +y 挪 2 格就兩舷都不撞）。

讀數：
- **子作品結果帳**（`tools/check_stage5.py`，每件從匯出讀）：8 件、92,536 格，缺 0、多 0、色差 0。
- **組裝件結果帳**：階段五之前 1,684,080 ＋ 每件照 placement 放（鏡像那兩條在框裡翻）＋ 兩隻錨 ＝ 設計 1,818,288 ↔ 組裝件 1,818,288，缺 0、多 0、色差 0。
- 組裝件 stats：1 元件、空腔 0、link_overlap 0、models_broken 0；鏡像差 30／37／0 ＝ 名牌 TRIDENTE 那 67 格（產生程式自己量的不對稱也是 67），其他全部兩舷對稱。
- 產生程式各自量：跟現況重疊 0、浮空 0（船首像鰭尖只靠斜角的零碎格拿掉，v1 8 格、定稿 0）、空腔 0、左舷鏡過去撞到 0。
- **反向對照**：`後廊-P` at.y 126 → 127 ⇒ 鏡像差 905／4,904／1,011 對、link_overlap 3,992（偏進船殼）；改回 ⇒ 30／37／0、0、1,818,288。
- 產生程式從現讀的組裝件重跑：12 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage5_stern_{sternq,astern,rudder}.png`、`stage5_head_{bowq,front,figurehead}.png`、`stage5_ship_bowq.png`。

🩸 這一階段撞到的：
- 船尾面半寬量短：中砲甲板那列的兩個船尾追擊砲門刻穿了牆 ⇒「從中線往外連續的平面」在砲門那裡斷掉 ⇒ gallery 往裡包到陽台上（重疊檢查擋下）⇒ 改取那一列最外面那格。
- 船尾轉角：陽台地板照船尾面往後填，轉角那幾欄會填進 gallery 的範圍 ⇒ 陽台佔到的 |dy| 一律讓給陽台。
- 只靠斜角接上的像素：徽的三叉戟倒鉤 12 格浮空（6 連通）⇒ 齒頭改實心三角；head rails 的紅板從平台上一格起、跟平台只隔一個斜角 ⇒ 890 格浮空 ⇒ 從平台面那一格起。
- **錨的鏡像差 2 格**：算 mirror at.y 用了「格子的 max ＋ 1」當框高（31），引擎在作品框（33）裡翻 ⇒ 左舷錨偏 2 格、跟左舷船頭裝飾重疊 2 格。產生程式自己的檢查**用同一個錯的框**量放法跟碰撞 ⇒ 報 0；是引擎 stats 的 link_overlap 2 抓到的 ⇒ `deco_base.work_size` 讀作品真正的框。
- trailboard 的三叉戟 v1 順著斜的 trailboard 剪切、側面看像一團金線 ⇒ 改水平放在 knee 上半那塊黑面，trailboard 改波浪；船首像 v1 長 3 m、側面看比錨還小 ⇒ 1.25 倍。
- 工具：沒有關聯的作品 export 帶 `links=` 會被擋（錨）⇒ 不帶；build 工具算 works 夾往上多爬一層 ⇒ 第二次跑時「作品ID已存在」。

⚠ 看得到的／留給之後：
- quarter gallery 是實心的（窗是玻璃，沒開孔）；陽台跟船艙不通（船尾窗是玻璃）。
- 艏斜桅還沒做：它在艏柱頂 x 718–721、z ≈ 184–196 會切過船頭舷牆頂（桅階段開孔）；gammoning 綁 knee 上緣靠艏柱那段。
- 錨照憲法號的大小（一級艦的錨應該更大）；憲法號 -anchor 沒記 meters_per_voxel（關聯是逐格貼，不受影響）。

## 階段六 桅與帆桁（2026-10-14，TASK-0559）
設計 plan.json `masts_build`（`masts` 的 boom 改 135）；產生 `design/draft_masts.py`（讀「階段六之前」：`deco_base.stage6_base` ＝ 船殼讀標記 `艏斜桅開口:begin` ＋ 甲板 ＋ 階段五的部件）⇒ `masks/masts/{main,fore,mizzen,bowsprit}.vox.txt`（世界座標）、`masks/masts/hull_carve.vox.txt`、`masks/yards/<帆桁>.vox.txt`（子作品座標）、`masts_placement.json`、`verify_masts.json`、`sheet07_masts_v1.png`；落格 `tools/build_masts.py`（hull／masts／yards／models）；讀數 `tools/check_stage6.py`。
- **桅**（每根一件子作品、整船的框、at 0,0,0；組裝件關聯 `主桅`、`前桅`、`後桅`、`艏斜桅`）：下桅在甲板那一段照 `layout.mast_hit`（甲板孔就是它開的 ⇒ 剛好填滿），上甲板以上收到 masthead（0.8）、每 12 格一圈黑箍；上桅在下桅前面、頂桅在上桅前面（各自的 masthead 黑）；tops（平台 2 格厚、前緣圓、黑邊、深色木 104）＋ trestletrees／crosstrees；兩個 cap；上桅頂的 crosstrees；頂上白 truck。
  - 主桅 50,618（truck z 728 ＝ 水線上 64.9 m）、前桅 38,919（667）、後桅 19,347（562）。桅腳照 plan 往上找第一層整圈都空的：前桅 z 22（船頭 deadwood 往上收、實心到 21）、後桅 z 69（立在 orlop 上；舷弧讓 x 222 的甲板面高 2 格）。
  - 艏斜桅 18,313：根部 (690, 172)、32°、粗 5.5 → 3.8、尖 x 882；jib-boom 疊在上面（從 70% 起、粗 2.5 → 1.5、尖 x 953、z 344）；兩個 cap；根部底下一塊墊木到上甲板 560 格（不然根部懸空）。穿過船頭舷牆頂 ⇒ 船殼 `艏斜桅開口:begin` → carvevox 21 格（顏色守門）→ `:end`。
- **帆桁 14 根**（每根一件子作品 `-yard-<名>`、parent ＝ 它的桅子作品、0.1 m；子作品裡放沒轉、沿 y 的帆桁；模型掛在桅子作品裡：scale 1、`rotate=0,0,θ`、pivot ＝ 帆桁中心那一格的格心）：
  - 方帆桁 12：前桅 course 305／topsail 239／topgallant 151／royal 99、主桅 347／273／171／111、後桅 crossjack 239／topsail 171／topgallant 111、艏斜桅底下 spritsail 223（長照 plan.masts，取奇數 ⇒ 有正中那一格）；粗 ＝ 長 ÷ 50、Steel 1794 錐度；黑、兩端一格原木。
  - brace 角照憲法號：course／crossjack −20、topsail −22、topgallant −24、royal −26；spritsail 0。
  - spanker gaff（150、往船尾上翹 35°、jaws z 278）、boom（**135**、上翹 3°、jaws z 204）：角度做進格子；pivot ＝ 後桅在 jaws 高度的軸心那一格（繞桅轉）。boom 從 plan 的 215 縮到 135：taffrail 中線有船尾徽（x 71–72、z 207–228），boom 要停在 x 84、jaws 抬到 204 才過得了 taffrail 頂 z 206。
  - 固定點：pivot、sling、arm-P／S、earing-P／S、jackstay-P／S 每 8 格；gaff throat、peak、top-8…；boom jaws、end、foot-8…（共 364）。
  - meta：`kind=yard, mast, yard, length_ft, diameter_in, pivot_anchor=pivot, turn_axis=z, rotate_z_deg`＋ `sail`（帆名 `<桅>-<帆>`；gaff／boom ＝ `spanker`；crossjack、spritsail 沒有帆）—— 帆階段（TASK-0560）照這些名字開帆。

讀數：
- **子作品結果帳**（`tools/check_stage6.py`）：18 件（桅 4、帆桁 14）、161,353 格，缺 0、多 0、色差 0。
- **船殼結果帳**：現在 1,102,662 ＝ `艏斜桅開口:begin` 1,102,683 − 刻 21，缺 0、多 0、色差 0；刻掉那 21 格刻之前的顏色 21／21 對得上。
- **組裝件結果帳**：設計 1,945,464（船殼 1,102,662 ＋ 甲板與階段五 715,605 ＋ 四根桅 127,197）↔ 組裝件，缺 0、多 0、色差 0；stats 1 元件、空腔 0、link_overlap 0、鏡像差 30／37／0（名牌，跟階段五一樣）。
- 產生程式各自量：甲板孔沒填滿 0、桅撞到別的東西 0（船殼以外）、彼此重疊 0、每根左右不對稱 0、浮空 0、空腔 0；帆桁 14 根各自對稱 0。
- **帆桁模型**（組裝件 `export format=parts`，遊戲讀的那一份）：14 根、364 點、跟產生程式算的最大差 0.0005 格；meta 0 不同；state 全 ok。
- **反向對照**：主桅 course 的 rotate −20 → −15 ⇒ arm-S (491.33, 362.13) → (477.02, 366.64)、移 15.0 格 —— 跟產生程式 `--probe=main-course:-15` 預測的一樣（到小數第三位）；改回 −20 ⇒ 回到原值。
- 產生程式從現讀組裝件重跑：20 檔逐位元組相同（船殼讀的是標記 `艏斜桅開口:begin`）。
- 過程圖：`overlays/stage6_masts_{bowq,side,sternq}.png`、`stage6_main_top.png`、`stage6_bowsprit.png`（近照用 models=0：region 只裁格子、模型照畫）。

🩸 這一階段撞到的：
- **晚綁定**：每根桅的軸心／半徑函式寫在 `for key in …` 迴圈裡，迴圈跑完全部指到最後一根（後桅）⇒ 主桅、前桅的 topsail 以上帆桁擺到後桅那邊（圖紙一眼看到紅點跑錯桅）⇒ 每根桅包成一個函式 `build(key)`。
- 桅腳：plan 的 heel 照「船中」想；前桅那裡船底實心到 z 21、後桅那裡 orlop 因舷弧高 2 格 ⇒ 撞到 631／60 格（全是船殼與 orlop 甲板）⇒ 往上找第一層整圈都空的。
- 工具：carvevox 回的是 `placed`（不是 carved）⇒ 刻成功了但 end 標記沒打、我手補；第一次補標記 exit 1、再打一次就好（沒查原因）。

⚠ 看得到的／留給之後：
- royal 帆桁很細（前桅 royal 粗 0.98 格 ⇒ 截面一格）；帆桁轉 20° 之後中段靠後那一小段會穿進桅（網格互穿，同憲法號）。
- 還沒有：繩（靜索、ratlines、動索）、帆、channels、fife rails、bobstays（knee 上的 `bobstay-1／2／3` 已登記）。

## 階段七 索具與帆（2026-10-14 傍晚套用、晚上驗收，TASK-0560）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（讀 `deco_base.stage7_base` ＝ 船殼＋甲板＋階段五＋四根桅；帆桁上的點讀 verify_masts.json）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落格 `tools/rigging_apply.py`（channels／anchors／ropes／sails／sailropes／wind／meta）。
- channels（`-channels` 右舷一件 5,487 格、關聯 `channels`／`channels-鏡像` mirror=y）：每根桅一塊板（上甲板砲門頂往上）、外緣 deadeye；跟現況重疊 0。
- 固定點 164（船殼 14：belay、bowsprit shroud；channels 31；主 38、前 40、後 33；艏斜桅 8）。
- 繩 418：shrouds 46、topmast shrouds 28、futtock 28、topgallant shrouds 12、backstays 16、stays 9、bowsprit 5、ratlines 246（下 146、上 100，一階一條子繩）、sheets 24、tacks 4；分組 standing／ratlines／running。
- 帆 15：方帆 10（綁帆桁模型的 earing）、spanker（gaff＋boom）、fore-topmast-staysail、jib、旗 2（ensign：西班牙海軍旗 1785 像素畫、掛 gaff 頂；pennant 主桅頂）；預設風 4.5,−1.5,0、4 秒。
- meta 43 筆（帆 13＋旗 2＋帆自己的 sheet／tack 28）。
- 讀數（套用後）：ropes_broken 0、sails_broken 0、models_broken 0；`sub=meta part=sail` 15 面都有；最鼓 −91.56 格（憲法號 −96.6）。

讀數（`tools/check_stage7.py`，2026-10-14 晚上）：
- **channels 結果帳**：清單 5,487 ↔ 子作品 5,487，缺 0、多 0、色差 0。
- **組裝件結果帳**：設計 1,956,438（階段七之前 1,945,464 ＋ channels 右 5,487 ＋ 左 5,487；左舷照清單自己翻：框高 27、at 125）↔ 組裝件（links=all）1,956,438，缺 0、多 0、色差 0；設計那一份自己重疊 0；兩舷 y 249..275 ↔ 125..151，加起來都是 400。
- **固定點**：plan 164 ↔ 六件作品的 anchors.json，缺 0、多 0、位置不同 0。
- **繩**：plan 418 ↔ 組裝件 ropes.json，缺 0、多 0、欄位（from／to／group／thickness／slack／color、enabled）不同 0、meta 不同 0。**帆**：15 ↔ 15，角（端點、名字、釘不釘）／bind／色／fullness／貼圖不同 0、meta 不同 0；預設風、秒數跟 plan 一樣。
- **帆自己的繩**（任一端 `sail:`）：28 條，沒有 meta 0、kind 不是 sheet／tack 0、meta 的 sail ≠ 端點那面帆 0。帆 15 面都有 meta（旗 2：ensign、pennant）。
- **引擎**：ropes 418（子繩 246）broken 0、ungrouped 0；sails 15 broken 0；`sub=meta part=rope` 有 28、沒有 390（＝ 418）。
- **反向對照**：
  - 真的拿掉一次（CLI `sub=meta meta=none`，`fore-course.sheet-S`）⇒ 檢查 ⑤ 沒有 meta **1**、引擎 meta_rope_without 391；加回 ⇒ 0／390（meta_log.jsonl 兩筆）。
  - 同一支比對拿副本動手腳：tack 的 sail 改錯 ⇒ 1；一條繩鬆緊 +0.01 ⇒ 1；帆一角釘／不釘對調 ⇒ 1（方帆、ensign 各一次）；channels 固定點偏 1 ⇒ 1；組裝件一格改色 ⇒ 色差 1；鏡像那件 y 錯 1 ⇒ 缺 318、多 713。
- 產生程式從現讀組裝件重跑：4 檔（channels.vox.txt、rigging_plan.json、verify_rigging.json、ensign.png）sha256 跟 HEAD 的 blob 逐位元組相同（git 標 M 只是 autocrlf 換行，已還原）。
- 過程圖：`overlays/stage7_sails_{side,bowq,sternq,bow}.png`（＋ 傍晚那張 `stage7_wip_sails_bowq.png`）。帆形狀看過：方帆順風往船頭鼓、spanker 與旗在 gaff 上、三角帆從艏斜桅拉到前桅 —— 不細修。

🩸 這一階段撞到的：
- 量具自己錯：第一次跑帆報「欄位不同 2」（ensign、pennant）。是 check 的錯，不是船的錯：旗的 free 寫序號（int）、方帆寫角名（字串），我拿字串比 ⇒ 序號全當成「釘」。改成一律當字串比，並補一個 ensign 的反向對照，確認 int 那條路也抓得到。

⚠ 看得到的／留給之後：
- crossjack、spritsail 帆桁沒有帆（照 1793 表的平常帆裝）；main／mizzen staysail 沒做。
- 帆桁轉 20° 之後中段穿進桅（網格互穿，同階段六）；帆是布料模擬，鼓的樣子跟風、秒數有關（預設 4.5,−1.5,0、4 秒）。

## 階段八 砲（2026-10-14 晚上落格、驗收，TASK-0561）
設計 plan.json `guns`；產生 `design/draft_guns.py`（做法照風暴角號 draft_guns.py ＋ 造船規格 §4.2：橫向對準砲門中線、從牆外沿砲口方向每 0.5 格往裡退，退到模型每一格的格心＋八角都不在實心裡；排序 輪子著地 ＞ 砲口伸出 ≥ 0.5 ＞ 置中 ＞ 推得出去）⇒ `verify_guns.json`、`masks/guns/pads_{lower,middle,upper}.vox.txt`；落格 `tools/apply_guns.py`（pads／models／meta）；讀數 `tools/check_stage8.py`。
- 砲一門一個外部模型，**借現成的砲子作品**（匯入自動 credit），不新做：下層 36 磅 ← 餘燼號 -gun-long32（32l）、中層 24 磅 ← 憲法號 -gun-24（24l，0.1 m、scale 1）、上層 12 磅 ← 風暴角號 -gun-12l（12l）、第四層 8 磅 ← 風暴角號 -gun-6l（6l）＋ obús ← 憲法號 -gun-carronade32（32c）、追擊 ← 憲法號 -gun-long18（18chase）；0.05 m 的 scale 0.5。六件都左右對稱 0 ⇒ P 舷一律 mirror=y。
- 第四層 17 門：單數號 8 磅、雙數號 obús（9＋8）。
- 船尾追擊 2：中砲甲板船尾窗那一列的兩個砲門（rotate 90）。船頭追擊 2：**沒有開船頭砲門** ⇒ 借上砲甲板第 18 個砲門照角度搜（5°～35°，取推得出去的最大角）⇒ 只推得出 **5°**；那個砲門的 12 磅讓給它。
- 合計 **138**（12l 34、24l 34、32l 32、6l 18、32c 16、18chase 4）；1805 年 140 —— 差的就是船頭那兩門（已知偏差）。
- pivot ＝ 砲架底層最前緣、軸線中間、z 0；模型掛在所在甲板的子作品（`甲板-<層>/砲-S01`…、`甲板-middle/追擊砲-船尾-S`）。
- 讀數（draft）：138 門全放得進去；第一版 12 門輪子一半懸空 —— 甲板舷弧取整是一階一階的，一階落在砲架底下 ⇒ 照風暴角號補墊木（甲板板色、放在那一層甲板子作品）：下層 20、中層 48、上層 16 格；墊完懸空 0、砲口沒伸出 0。
- 重跑（不用快取、從引擎重讀現況）：verify_guns.json 與三份墊木清單逐位元組相同。
- 預覽 preset 9 組（造船規格 §2）：只看船殼、剖半-看右舷／左舷內側、不掛帆、只看桅與索具、只看甲板-lower／middle／upper／spar。
- 砲種代碼：提案在酒館 seq 24438（新代碼只有 12l、6l，風暴角號本來就要）；Tim 2026-10-14「繼續造船、要用在遊戲內」⇒ 照提案落格。遊戲遇到不認得的代碼當長砲（`10_ship.js` modelKind：`GUN_CODE[mt.gun] || 'long'`）⇒ 12l、6l 在 ame 加進砲種表之前照 24 磅算。代碼要改 ⇒ 改 plan `guns.types.*.code` → 重跑 draft → `apply_guns.py meta`。

落格：三層甲板子作品打標記 `階段八墊木:begin` → stampvox 墊木（下 20、中 48、上 16，placed ＝ 清單格數）→ `:end`；138 個模型（`apply_guns.py models`，IOException 重試 0）。

讀數（`tools/check_stage8.py`）：
- **墊木結果帳**：三層甲板 現在 ＝ `階段八墊木:begin` ＋ 墊木清單，缺 0、多 0、色差 0；墊木跟 begin 重疊 0。
- **parts（遊戲讀的那一份）**：砲 138 門，找不到 0、state 不是 ok 0、meta 不同 0；muzzle／breech 跟 draft 算的最大差 0.0005 格。
- **碰撞（獨立的尺）**：每門的變換從引擎匯出的固定點反推（最小平方仿射，殘差 0.0000），把來源砲每一格（格心＋八角）搬上船，對現讀組裝件 links=all ＋ 其他模型外框 ＋ 已量過的砲 ⇒ 碰到 0。
- **砲口在船殼外**：沒伸出 0。**輪子著地**：懸空 0。
- **反向對照**：砲-S08@甲板-lower 往外推 2 格 ⇒ 碰撞 1,755 個取樣點；往船頭推 2 格 ⇒ 0（兩門之間有空）；抬高 1 格 ⇒ 懸空 192／192；meta 改 gun=xx ⇒ meta 不同 1。
- 引擎：models 154（砲 138 ＋ 帆桁 14 ＋ 燈籠 2）models_broken 0；組裝件 1,956,522 格（＝ 階段七 1,956,438 ＋ 墊木 84）、1 元件、空腔 0、link_overlap 0。
- 過程圖：`overlays/stage8_guns_{lower_deck,side,section}.png`。

🩸 這一階段撞到的：
- **量具的浮點邊界**：check 第一版報 124 門輪子懸空，draft 說 0。錯在 check：仿射是最小平方解的，輪底那層 z 剛好是整數（93.0）⇒ 解出來 92.99999… ⇒ floor 多掉一格，看到甲板板底下的空氣。輪底取樣改用格心（z 0.5），並補「抬高 1 格要全報」的反向對照，證明修過的尺抓得到。兩把尺打架的時候，先查尺。
- 甲板舷弧取整是一階一階的 ⇒ 一階落在砲架底下（墊木，見上）。

⚠ 看得到的／留給之後：
- 船頭追擊砲只偏 5°（借舷側砲門）；要更像追擊砲得在船頭開砲門（改船殼），目前不做。
- 砲具與砲索（造船規格 §4.4：環首螺栓、breeching、side tackle、train tackle）還沒做。

## 階段九 遊戲必要零件：彈藥庫、舵輪、羅經櫃、主絞盤、小艇、甲板 meta（2026-10-14 晚上，TASK-0562）
Tim 2026-10-14：「繼續造船吧，要用在遊戲內所以要有對應的炮跟必要零件」。設計 plan.json `magazines`、`fittings`；產生 `design/draft_magazines.py`（改自餘燼號 draft_magazine_mid.py，basecamp）⇒ `masks/magazines/{aft,fore}.vox.txt`、`magazines_placement.json`、`verify_magazines.json`；`design/draft_fittings.py` ⇒ `verify_fittings.json`；落格 `tools/apply_stage9.py magazines|fittings`；讀數 `tools/check_stage9.py`。
- **彈藥庫兩間**（子作品 `-magazine-aft`／`-magazine-fore`，0.1 m、parent 船殼、tags sub）：orlop 底下的貨艙（本船從艙底一路空到 orlop，沒有中線支柱）⇒ 自己鋪地板（z 30）與天花板（z 49），房高 1.8 m（同憲法號、餘燼號）；銅皮 168 包船殼側與艙壁、松木 177 地板每 6 格一道橡木壓條、天花板每 8 格一道樑；門 5 格寬、朝船中。
  - 後 x 236–296（後桅站在 orlop 上、後艙口 x 300 之前）23,483 格；前 x 562–632（前桅 x 650 桅腳 z 10 之後）21,951 格。
  - 桶：照砲數換算（憲法號 54 門 138 桶 ⇒ 140 門 ≈ 358 桶，⚠ 不是史料），兩間各 179、全在地板層（地板層容量 306／260，不用上架）；火藥桶引用憲法號 -powder-barrel（scale 0.2、meta kind=powder、powder_lb=100）。
  - 組裝件關聯 `彈藥庫-後` @236,128,30、`彈藥庫-前` @562,131,30，meta kind=magazine、pos=aft／fore、powder_lb=17,900；固定點 blast（房間空氣重心最近的一格）、door。
- **甲板零件**（外部模型掛 `甲板-spar`，pivot、scale 照餘燼號）：
  - `舵輪`（憲法號 -wheel 雙舵輪，kind=wheel）at 246,200.5,160：poop 前緣 x 228 前面、外框後緣 236.9 ⇒ 留 0.9 m 給舵手站（v1 從 x 236 起搜 ⇒ 只剩 1.4 格；pivot 是舵輪中心不是後緣）；舵索 2 條（#a08458、0.35、組 steering、meta kind=steering）鼓輪 → 正下方甲板面。
  - `羅經櫃`（餘燼號，kind=binnacle）at 262：舵輪正前方隔 6.5 格。
  - `主絞盤`（餘燼號，kind=capstan）at 409.5：後艙口與主桅之間的中線、四周 0.5 m 淨空（可擺範圍 x 332.5–456.5，取離 400 最近的）。
  - `小艇-S`／`小艇-P`（餘燼號 cutter 9 m，kind=boat、boat=cutter、length_m=9；P 舷 mirror=y）at 532.5,200.5±17：主艙口與前桅之間，擱在上甲板（本船上甲板整片平的、沒有船腰開口 ⇒ 不做艇架）；龍骨著地 244／340（舷弧讓兩頭翹起一點）。
  - 保留區：梯子在 spar 那一端（foot／head）前後 6、兩側 4 格（本船梯子在中線）。
- **甲板 meta**（造船規格 §9.3）：遊戲那側 `decks.py` 量六件甲板子作品的 vxk ⇒ `design/meta/decks.tsv` ⇒ `work sub=meta file=`：orlop 0、lower 1、middle 2、upper 3、spar 4、poop 5，厚 4；顯示名改成本船的（decks.py 的名字表是兩層砲甲板的船 ⇒ middle 沒有名字、upper 叫「上層砲甲板」）。

讀數（`tools/check_stage9.py`）：
- **彈藥庫結果帳**：兩間 清單 ↔ 子作品，缺 0、多 0、色差 0。**組裝件**：藏彈藥庫 1,956,522 ＋ 23,483 ＋ 21,951 ↔ 現在 2,001,956，缺 0、多 0、色差 0、重疊 0。
- **parts**：兩條關聯 meta kind／pos／powder_lb 對（17,900 ＝ 179 × 100）、blast 點跟算的相同；火藥桶 kind=powder 358／358、state 全 ok；甲板零件 5 件 meta 不同 0。
- **碰撞**：零件位置從引擎的外框反推（跟 draft 相同），每格格心＋八角碰到實心／其他模型外框 0。外框這把尺對小艇太粗（外框裡 137 格是艇底弧線底下的甲板板與艙口圍欄），以格子級為準。
- 引擎：組裝件 2,001,956 格、1 元件、空腔 0、link_overlap 0；模型 517（＋358 桶＋5）broken 0；繩 420 broken 0。
- **反向對照**（單子要的）：真的拿掉 `彈藥庫-前` 的 pos ⇒ parts 的 meta 少 1 欄；加回 ⇒ 跟原本相同。
- 重跑：draft_magazines（讀藏彈藥庫的現況）三份檔、draft_fittings（藏彈藥庫、不算本階段的零件與火藥桶）verify 逐位元組相同。
- 過程圖：`overlays/stage9_magazine_aft_open.png`（拿掉天花板看桶）、`stage9_deck_fittings.png`。

⚠ 留給之後：
- 桶數是照砲數換算的，不是史料；兩間各 17,900 磅 ⇒ 遊戲裡殉爆半徑照 powder_lb 算。
- 貨艙沒有梯子通下去（orlop 以下），跟憲法號、餘燼號一樣；彈藥庫門通到的是貨艙。
- 砲具與砲索（§4.4）還沒做；船頭追擊砲只偏 5°。

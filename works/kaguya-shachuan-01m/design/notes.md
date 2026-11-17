# 沙船（中式沿海沙船 Shachuan，約 60–90 噸，1666 長江口－台海淺水商船）—— 建造筆記（0.1 m／格）

委託：Tim 2026-11-17「/scp-task 1313 GO」（TASK-1313，pinnacle 開單；傘 TASK-1311 亞洲船②）。
驗收（TASK-1313）：Ship_Steps 步驟 1–11、14、15（pinnacle 開單時已刪 12 砲門蓋板：露天甲板輕砲；刪 13：全木帆船、沒有槳）。步驟 9 加讀 Ship_Turrets §4.5（佛郎機迴旋砲）。

## 方向（步驟 1；2026-11-17）
- 單上的步驟表 pinnacle 已照船種挑好：有帆（7、8）、露天輕砲＋迴旋砲（9 讀 Ship_Guns＋Ship_Turrets §4.5）、沒有封閉砲甲板（刪 12）、沒有槳／蒸汽／金屬船殼（刪 13）、不是大帆船的兩頭（不讀 Ship_Ends）。kaguya 核對過、照原樣打勾。
- ⚠ 單上的史料清單（天工開物、武備志、南船記、唐船之圖）是開單時列的方向，**還沒有一條查過出處** —— 步驟 3 逐條查、分〔查〕〔二手〕〔推〕〔設計〕。

## 座標與比例（步驟 2；2026-11-17）
- 0.1 m／格；框 288 × 192 × 288（28.8 × 19.2 × 28.8 m；調尺寸免費、不縮放內容）。x 船長、船頭 +x；y 中線格 96（鏡像 y ↔ 192 − y；P 舷 y < 96）；z 0 ＝ 船底板底面（沙船平底、沒有龍骨 ⇒ 以底板底面當 0）。
  - 理由：LOA 約 21 m ＋ 艏艉懸出的方台、舵 ⇒ x 288 留兩頭各約 3 m；寬 5.5 m ＋ 披水板 ＋ 硬帆的帆桁兩舷懸出 ⇒ y 192；主桅約為船長、離底約 22–24 m ＋ 旗 ⇒ z 288。
  - ⚠ 中式升降舵放下時會低於船底（沙船的舵本來就比底深）：z 0 是船底，舵放下那一段要另外看（步驟 11 讀 Ship_Helm 時決定是畫「升起」還是把框往下加；`work move` 可以整體平移）。
- 作品：組裝件 `kaguya-shachuan-01m-assembly`「沙船」（主作品，關聯 `船殼` at 0,0,0）；船殼 `kaguya-shachuan-01m`「沙船 船殼」（任務作品、tags sub、委託 ref TASK-1313、領薪 10）。兩件 meters_per_voxel 0.1（create 後 update 補、回讀 work.json 有；標題以 UTF-8 回讀正確）。
- 拆法（Ship_Setup §2）：船殼（底板、舷板、水密隔艙壁、舷牆、方艏方艉封板）一件；每層甲板一件子作品；每根桅一件、每根帆桁（硬帆的竹篾 batten）一件＋外部模型；披水板兩舷做一件、另一舷 mirror=y；舵、舵柄、錨、絞車各一件。

### 現有元件（`work sub=components` 2026-11-17，351 件；沒有任何中式船的元件）
| 用途 | 引用 | 備註 |
|---|---|---|
| 露天輕砲 | `pinnacle-patache-01m-gun-4l`（gun:4l） | 兩軸四輪砲架 —— 步驟 9 量甲板與舷牆高 |
| 佛郎機迴旋砲 | `apex-one-reale-01m-gun-pierrier`＋`-mount`（gun:pierrier） | 叉架後膛砲，佛郎機本來就是葡式 berço 的後膛砲，形制對得上 |
| 火藥桶 | `basecamp-frigate-constitution-01m-powder-barrel`（powder） | |
| 四爪鐵錨 | `kotoko-fusta-01m-anchor-grapnel`（anchor:bower） | 中式木椗（木爪＋石檔）沒有 ⇒ 步驟 11 決定新做或只用四爪錨 |
| 羅經 | `summit-night-falcon-01m-binnacle`（binnacle） | 中式羅盤放在針房，步驟 10 再定 |
| 燈 | `gura-tridente-01m-lantern`（light:amber） | |
| 門、艙蓋 | `gura-pinas-01m-door`、`meadow-monitor-01m-hatch` | |
| 灶 | `kaguya-gloire-01m-galley`（galley） | |
| 小艇 | `basecamp-ember-01m-boat`（9 m，縮放） | 沙船載的舢板約 4–5 m，縮放 ~0.5，步驟 10 定 |
| 絞盤 | `basecamp-ember-01m-capstan` | 中式是臥式絞車（起錨、起舵），步驟 10 決定 |
- 要新做（查不到現成的）：硬帆帆桁（竹篾 batten，yard=gaff）、開孔升降舵、舵柄、披水板、方艏彩繪等個性裝飾。

## 階段一 造船資料與新圖紙 01／02（步驟 3；2026-11-17）
- 史料：`references/research_shachuan_2026-11-17.md`（〔查〕《武備志》卷 117 沙船原文、《天工開物》漕舫尺度；〔二手〕《大清會典》／《唐船之圖》南京船／Needham & Worcester；〔推〕〔設計〕對齊 TASK-1313 60–90 t）。
- 產生程式：`design/plan.json`（每項附出處/設計決定）、`lines.py`（出處 `kiara-tunis-sandal-01m/design/lines.py`，改寫沙船平底硬舭、外張舷側、方艏翹頭、方艉虛梢）、`draft_lines.py`、`draft_layout.py`。
- **主尺寸與讀數（`verify_lines.json`、`verify_layout.json`）**：
  - 全長 LOA：`21.0 m`（`x 36..245`，210 格，〔設計〕落在 20–22 m）
  - 最大船寬：`5.5 m`（55 格，〔設計〕落在 5.2–5.8 m）；平底長 `13.0 m`（130 格）、平底最大寬 `3.7 m`（≈ 67% 全寬，對齊《天工開物》68%）
  - 設計水線：`z = 14`（`1.40 m`）；水線長 `19.2 m`、水線寬 `4.7 m`、排水量 **`87.38 t`**（船殼估重 `29.65 t`）
  - 兩端：方艏寬 `2.5 m`（`z=15` 起翹），方艉寬 `3.1 m`（`z=14` 封板，向上後斜懸出 1.2 m 虛梢至 `x=36`）
  - 結構預檢：`49,415` 格、`components_6 = 1`、`cavities = 0`、`mirror_diff = 0`
  - 配置：3 層甲板（底艙站面 `z=3`、主甲板 `z=23..28`、尾樓 `z=41`）、8 道水密隔艙（`x = 48, 72, 96, 120, 144, 168, 192, 216`）、兩舷披水板（`x = 134..156`）、6 門砲（`x=180` 兩舷 `long4` ×2 ＋ `x=64, 228` `pierrier` ×4 ＝ 1,600 kg）、三桅硬篷總面積約 `142.3 m²`（頭 `37.8`／大 `86.9`／尾 `17.6 m²`）。
- **可重現性與反向對照**：
  - `draft_lines.py` 與 `draft_layout.py` 連跑兩次，`masks/hull/hull_01.vox.txt`（sha256 `69d2418f...`）與 `sheet02_layout_v1.png`（sha256 `cd9c2d0b...`）均逐位元組相同（`True`）。
  - 反向對照：`--probe=half_beam=+3` ⇒ `beam 5.5 → 6.1 m`、舯 `x=148` 半寬 `26 → 29`、`displacement 87.38 → 90.63 t`（探針不寫檔）。
- 圖紙：`sheet01_lines_v1.png`、`sheet02_layout_v1.png` 均已生成並目視檢查（修正初版頭桅底端穿底、`≈` 缺字與硬篷上桁傾角後再驗）。

## 階段二／三 船殼落格、砲門缺口、塗裝與船尾窗（步驟 4；2026-11-17）
- 船殼落格：標記 `船殼` begin（`upto=start`）→ `tools/stamp_lists.py` 1 刀 `placed 49,415 == 49,415` → `船殼` end。
- `tools/check_hull.py`（`船殼:end`）：結果帳 49,415 ＝ 設計 49,415（缺 0、多 0、色差 0）；線形對照 259 點 |差| 最大 0；反向對照 `probe_x=148`（設計 +3）⇒ 報 9 點、|差| 最大 3。
- 砲門、塗裝、船尾窗（`draft_ports.py`）：
  - 前腰 `x=180`（177..182）兩舷各 1 門 4 磅砲缺口（`z=27..30`，紅框 `196`）；艉艙 2 扇船尾窗（`z=28..31`、金框 `248`，40 格玻璃清單 `masks/ports/glass.vox.txt` 留步驟 6）；主護木帶（`136/36`）、方艏朱紅牌額＋龍目（`182/36`）、方艉朱紅與深木飾面。
  - `carvevox` 204 格（already_empty 0）→ `stampvox overwrite=1` 1,851 格 → 標記 `炮門塗裝` end。
- `tools/check_stage3.py`：
  - 正向對照（`船殼:end`）：49,415 vs 預期 49,211 ⇒ 多 204、色差 1,851、開口實心 204。
  - 完稿（`炮門塗裝:end`）：作品 49,211 ＝ 預期 49,211（缺 0、多 0、色差 0）、開口實心 0。
  - 反向對照：`draft_ports.py --probe=skip_port` ⇒ 刻除 204 → 110、塗裝 1,851 → 1,777。
- `stats structure=1 mirror=y:96`：49,211 格、1 元件（6 連通）、封閉空腔 0、鏡像差 0。
- 過程圖：`overlays/stage4_hull_{bowq,sternq}.png`、`overlays/stage4_ports_{bowq,sternq}.png`（已目視檢查）。

## 階段四 甲板、水密隔艙、梯子、貨艙與舵艙（步驟 5；2026-11-17）
- 產生程式：`draft_decks.py`、`tools/build_decks.py`、`tools/check_decks.py`。
- **三層甲板與水密隔艙**（子作品 tags `sub`、`0.1 m/格`，`assembly` 關聯帶 `kind=deck`）：
  - `甲板-hold`（`level=0`, `floor="72:3,216:3"`, `thick=1`）：`7,251` 格，含 7 道橫向水密隔艙壁（`x=72, 96, 120, 144, 168, 192, 216`，連同艉封板共 8 道、分 9 艙）；中間 5 道中央留 `5×16` 格通路，前後封壁中央 `z=7` 留 1 格過水眼避免形成 3D 封閉空腔（初版過水眼 `z=3` 被 `x=71` 船底板擋住造成 6,338 格死腔，上移至 `z=7` 後 `cavities_filled = []`）。
  - `甲板-main`（`level=1`, `floor="46:23,206:23,244:28"`, `thick=3`）：`9,196` 格，開主艙口（`x=158..170, |dy|<=5`）、`lower` 梯井（`x=124..138`）及三桅孔。
  - `甲板-poop`（`level=2`, `floor="36:41,88:41"`, `thick=3`）：`2,680` 格，含尾樓前壁 `x=88`（中央舵艙門 `y=93..99`）與尾樓胸牆（`dy=+10` 留梯口）。
- **兩座梯子**（每座 4 個固定點 `foot/lo/hi/head`，關聯 `meta {"kind":"ladders"}`）：
  - `lower`（`hold` ⇄ `main`）：6 階、`210` 格，`foot [139,96,3]` → `head [123,96,23]`。
  - `poop`（`main` ⇄ `poop`）：5 階、`170` 格，`foot [101,106,23]` → `head [87,106,41]`。
- **空艙房**（`meta {"kind":"rooms"}`）：
  - `甲板-hold/艙房`「貨艙」（`[146,84,3]..[166,108,19]`，`door [144,96,3]`，淨高 1.7 m，內部實心 0、腳下全實心）。
  - `甲板-main/艙房`「舵艙」（`[60,86,23]..[86,106,37]`，`door [88,96,23]`，淨高 1.5 m，內部實心 0、腳下全實心）。
- **驗證讀數（`check_decks.py`、`stats`）**：
  - 5 件子作品（19,507 格）匯出結果帳缺 0／多 0／色差 0、與船殼重疊 0、彼此重疊 0；梯子 `parts` 匯出 8/8 點齊（差 0、空氣/腳下/頭頂 14 格問題 0）。
  - 組裝件 `stats`：68,718 格、`components = 1`、`cavities = 0`、`link_overlap = 0`。
  - 第一人稱走回有向圖（`x=36..247`）：可達 `14,817` 格、能走回 `14,817` 格、困住 `0` 格；反向對照 `--probe=drop_ladder=lower` ⇒ `hold` 立即失去連線（`reach["hold"] = []`）。
- 過程圖與預覽 preset：`sheet04_decks_v1.png`、`overlays/stage5_decks_{full,inside}.png`；組裝件存 preset `只看甲板與艙房`（`hide_links=船殼`）。

## 階段五 裝飾與窗玻璃（步驟 6；2026-11-17）
- 產生程式：`draft_deco.py`、`tools/build_deco.py`。
- **船尾窗玻璃**（`kaguya-shachuan-01m-stern-glass`，tags `sub`，組裝件關聯 `船尾窗玻璃` `meta {"material":"glass"}`）：50 格、2 個 6 連通整片窗面（補齊斜艉柱換行角格，不寫 `render`，跟船殼重疊 0）。
- **可隱藏裝飾模型**（外部模型均標 `meta {"deco":1}`，`models_drawn = 8`、`models_broken = 0`）：
  - `披水板-S`／`P`（`kaguya-shachuan-01m-leeboard` 814 格，2.2 × 2.3 m 上窄下寬刀板形，貼緊舯腰外側 `|dy|=28`，離 `x=180` 砲門 2.4 m）。
  - `方艏牌額`（`kaguya-shachuan-01m-deco-bow` 161 格，朱紅嵌金虎頭牌與頭伏獅角，掛於方艏 `x=244`）。
  - `船尾牌飾`（`kaguya-shachuan-01m-deco-stern` 85 格，黑底金框篆飾牌，掛於艉樓窗上 `x=40, z=34`）。
  - `護舷-S/P-114`、`護舷-S/P-196`（複用現有元件 `kiara-tunis-sandal-01m-fender`，0.1 m/格，前後腰各 2 件）。
- 過程圖：`overlays/stage6_deco_{bowq,sternq}.png`（已目視檢查，組裝件總計 `68,768` 格、`link_overlap = 0`）。

## 階段六 桅與帆桁（步驟 7；2026-11-17）
- 產生程式：`draft_masts.py`、`tools/build_masts.py`。
- **三根下桅**（子作品 tags `sub`、`0.1 m/格`，組裝件關聯 `turn=0, mirror=none`，`meta {"kind":"mast","mast":"fore"|"main"|"mizzen"}`）：
  - `桅-fore`（`kaguya-shachuan-01m-mast-fore`）：989 格，`x=222, heel_z=6..128`，前傾 5°。
  - `桅-main`（`kaguya-shachuan-01m-mast-main`）：2,367 格，`x=150, heel_z=3..173`，直立。
  - `桅-mizzen`（`kaguya-shachuan-01m-mast-mizzen`）：423 格，`x=56, heel_z=23..111`，後傾 2°。
  - 三桅與船殼・甲板重疊 0（穿甲板段已先避讓；組裝件總計 `72,547` 格、`link_overlap = 0`）。
- **六根硬篷帆桁**（各一件子作品＋外部模型掛進對應桅子作品，`scale=1, rotate=0,0,0`，固定點 `pivot/aft/fore/sling`，`meta` 帶 `kind=yard, mast, yard=gaff|boom, sail=<mast>-junk, pivot_anchor=pivot, turn_axis=z, rotate_z_deg=0`）：
  - 頭篷：`fore_gaff`（5.2 m, −15°, z 116.5）＋`fore_boom`（5.6 m, z 46.5）。
  - 大篷：`main_gaff`（7.6 m, −14°, z 160.5）＋`main_boom`（8.2 m, z 54.5 — 目視檢查後從 50.5 抬高至 54.5 以留 0.6 m 淨空越過尾樓舷牆 z=48）。
  - 尾篷：`mizzen_gaff`（3.8 m, −14°, z 100.5）＋`mizzen_boom`（4.2 m, z 56.5）。
- 過程圖：`overlays/stage7_masts_{bowq,sternq}.png`（`models_drawn = 14`、`models_broken = 0`）。


## 階段七 索具、帆與旗（步驟 8；2026-11-17）
- 索具程式：`design/tools/rigging_apply.py`（冪等重跑）；貼圖 `design/textures/ensign.png`（32×20 朱紅金邊菱形紋）、`pennant.png`（40×6 長旒）。
- 船尾旗桿子作品 `kaguya-shachuan-01m-ensign-staff`（37 格，0.1 m）掛於組裝件 `at=37,95,49`（踩在尾舷頂 `z=48` 之上，`link_overlap=0`）。
- 靜索與橫繩：頭桅 shrouds ×6、大桅 shrouds ×6、尾桅 shrouds ×4；stays ×3（`fore-stay`、`main-stay`、`mizzen-stay`）；`fore-lower-S/P`、`main-lower-S/P` 橫繩組（`climb=0`，中式無歐式桅樓）。
- 帆與動索：
  - 三面硬篷帆皆為四邊形 `kind=sail, sail=gaff`，各有 `sheet-S/P`、`tack`、`halyard`（`kind=sheet/tack/halyard, sail=<mk>-junk`）：
    - 1 段帆 `set=1`：`fore-junk`（mast=`fore`）
    - 2 段帆 `set=2`：`main-junk`（mast=`main`）
    - 3 段帆 `set=3`：`mizzen-junk`（mast=`mizzen`）
  - 旗：`ensign`（`kind=flag, flag=ensign, nation=ming`）、`pennant`（`kind=flag, flag=pennant, mast=main, nation=ming`）。
- 預覽風向量：`-4.5,-1.5,0` m/s（由艏吹向艉，`sail_seconds=3`），`ropecheck` 85 條繩 170 端全部 `ok`、`sails_drawn=5, sails_broken=0, models_drawn=14, link_overlap=0`。
- 過程圖：`overlays/stage8_rigging_{bowq,sternq}.png`（已實圖目檢）。


## 階段八 火砲（步驟 9；2026-11-17）
- 設計／落地程式：`design/gunsim.py`、`design/draft_guns.py`、`design/tools/build_guns.py`。
- 全船 6 門砲（掛於所在甲板子作品，全數外部模型、`models_drawn=24, models_broken=0`）：
  1. 前腰露天主甲板 `x=180` 兩門 4 磅砲 `砲M-S01 / P01`：引用 `pinnacle-patache-01m-gun-4l`（0.05 m ⇒ `scale=0.5`, `pivot=6.5,30,0`, `meta kind=gun, gun=4l`），`back=3.5`、`muzzle_beyond=3.75`、`support=1.0`、`axis_z=30.25`（砲口自船殼向外伸出 0.375 m 並通過實心檢核）。
  2. 尾樓 `x=64`（`迴旋砲P-S01 / P01`）與前舷頂 `x=228`（`迴旋砲M-S01 / P01`）共 4 門佛郎機迴旋砲：引用 `apex-one-reale-01m-gun-pierrier` ＋雙生座 `apex-one-reale-01m-gun-pierrier-mount`（0.05 m ⇒ `scale=0.5`, `pivot=5.5,18.5,0`；砲身 `kind=gun, gun=pierrier, mount=turret, arc="-80,80", rate=45`，雙生座 `kind=gunmount, mount_of=gun-N`），`-80°..+80°` 全掃角度與砲座對組裝件碰撞皆為 `0`。
- 對照與驗證：`repro_guns=True (a285d4362b79)`；正向對照 `--probe=push=砲M-S01:2` 觸發 `865` 碰撞樣本；兩舷鏡像對稱（`asymmetric_pairs=[]`）、砲與砲互撞 `0`。
- 過程圖：`overlays/stage9_guns_{bowq,sternq}.png`、`stage9_bow_zoom.png`（已實圖目檢）。


## 階段九 彈藥庫與甲板物件（步驟 10；2026-11-17）
- 設計／落地程式：`design/draft_gear.py`、`design/tools/build_gear.py`。
- **彈藥庫** `kaguya-shachuan-01m-magazine`（528 格，底艙艉端 `x=73..95`，`aft_wall=False` 避免艉尖封閉空腔；`blast=[85,96,9]`、`door=[95,96,3]`），關聯標 `kind=magazine, pos=aft, powder_lb=400, hoist="甲板-main/梯子#lower"`；庫內掛 4 只 `basecamp-frigate-constitution-01m-powder-barrel`（`scale=0.2, kind=powder, powder_lb=100`）。
- **主艙口格柵** `kaguya-shachuan-01m-grating-main`（0.05 m、756 格，外部模型 `scale=0.5`、`kind=grating`），置於 `主艙口` `x=158..170, y=91..101` 圍板頂齊平（`world_top=25`、圍板 `52/52`）。
- **甲板物件與門**（全數外部模型，`models_drawn=35, models_broken=0, link_overlap=0`）：
  - `舵艙門`（`gura-pinas-01m-door`、`kind=door, open=side`、`scale=[0.5, 0.643, 0.5]`、`at=[89,92,23]`）：緊貼尾樓前壁 `x=88` 門框每邊壓 1 格。
  - `爐灶`（`kaguya-gloire-01m-galley`、`scale=0.22`、`kind=galley`、`at=[108,82,23]`，具 `smoke` 固定點，露天通空）。
  - `小艇`（`basecamp-ember-01m-boat`、`scale=0.13`、`kind=boat, boat=sampan, length_m=2.3`、`at=[195.5,96.5,23]`）。
  - `絞盤`（`basecamp-ember-01m-capstan`、`scale=0.09`、`kind=capstan`、`at=[112.5,96.5,23]`）。
  - `羅經櫃`（`summit-night-falcon-01m-binnacle`、`scale=0.2`、`kind=binnacle`、`at=[64,96.5,41]`，尾樓甲板）。
  - `尾燈`（`gura-tridente-01m-lantern`、`scale=0.25`、`kind=light, light_color=#ffae52`、`at=[43.5,100.0,41]`）。
- 對照與驗證：`problems=[]`、10 件模型對實心/砲框碰撞皆 `0`、`support=1.0`；`repro_gear=True (1f1873b1e1ad)`；正向對照 `--probe=shift=舵艙門:-1` 檢出 `2184` 碰撞樣本。
- 過程圖：`overlays/stage10_gear_{bowq,sternq,deck}.png`（已實圖目檢）。


## 階段十 舵、舵柄與錨（步驟 11；2026-11-17）
- 設計／落地程式：`design/draft_rudder_anchor.py`、`design/tools/build_rudder_anchor.py`。
- **中式開孔升降舵** `kaguya-shachuan-01m-rudder`（`1333` 格，`components=1, cavities=0, on_solid=0, mirror_diff=0`）：
  - 垂直舵柱 `x=33..35, z=1..46`，水線下開 4 個菱形減力孔（`z=9, 15`, `x=24, 29`），外部模型掛於 `kaguya-shachuan-01m-assembly`（`at=34.5,96.5,1`、`pivot=34.5,96.5,1`），固定點 `stock-top=[34,96,46]`（距船尾格 `3` 格 ≤ 8 格）。
  - meta：`{"kind":"rudder","hinge_x":34.5,"hinge_y":96.5,"hinge_z":1,"axis_x":0,"axis_y":0,"axis_z":1,"max_deg":35,"turn_axis":"hinge","spin":"rudder","spin_k":35,"spin_min":-35,"spin_max":35,"spin_lag":0.3}`。
- **尾樓舵柄** `kaguya-shachuan-01m-tiller`（`28` 格、`on_solid_not_port=0`，尾樓尾板 `helm port` 刻除 `15` 格，含 `helm port` 標記），固定點 `spin-a=[34,96,43]`、`spin-b=[34,96,44]`，外部模型掛於 `deck-poop`，meta `kind=tiller, spin=rudder, spin_k=35, spin_min=-35, spin_max=35, spin_lag=0.3`。
- **四爪鐵錨 ×2 ＋ 錨架 ＋ 錨鏈孔**：
  - 引用共用件 `kotoko-fusta-01m-anchor-grapnel`（`0.05 m`, `scale=0.4`, `pivot=[9.5,9.5,0]`），`錨-S`（`at=[237.607,113.32,25], rotate=71.5`）與 `錨-P`（`at=[237.607,79.68,25], rotate=-71.5`），meta `kind=anchor, anchor=bower`。
  - 錨架 `kaguya-shachuan-01m-anchor-gear`（`234` 格，`on_solid=0, mirror_diff=0`），`foot_on_gear=True, foot_gap=0, gun_box_overlap=[]`；船殼固定點 `hawse-S=[241,108,32]`、`hawse-P=[241,84,32]`。
- 對照與驗證：`repro_rudder=True (839cb42e3f0d)`；正向對照 `--probe=shift=錨-S:-2` 檢出 `1254` 碰撞樣本。
- 過程圖：`overlays/stage11_rudder_sternq.png`、`stage11_anchors_bowq.png`（已實圖目檢，`models_drawn=39, models_broken=0, link_overlap=0`）。


## 階段十一 給遊戲的 meta、匯入與交船（步驟 14–15；2026-11-17）
- **遊戲 meta 與匯出 `.vxk`**：
  - `船殼` 關聯標 `kind=ship, waterline_z=14`；組裝件 `ropecheck` 85 條繩 170 端全 `ok`；`assembly stats` `73,380` 格、`1` 元件、`0` 空腔、`link_overlap=0`。
  - 自製非對稱／有孔／板片類元件（`披水板`、`中式開孔升降舵`、`舵柄`、牌飾、護舷）不適合作 `render=lathe/pole/wheel/shell`（`Ship_Render`），保持原體素網格。
  - 於獨立 Blockside worktree（`wt-bs-1313`，分支 `kaguya/shachuan-1313`）匯入 `shachuan`：`voxels=73380`、`checksum=2905144336`、指紋 `c:769c655c7b`。
- **Blockside 匯入／自檢讀數**（最終修補梯井與頭桅孔圍領後重匯）：
  - `admin.py ids --id shachuan` 已發齊全部 54 件物件 id，`彈藥庫 hoist` 改為 `ladders-1#lower`。
  - `admin.py ropebind`：繩 85 條、檔頭改 0 條、照外框猜 0 端、不靠 0 端。
  - `admin.py ladcheck --id shachuan`：2 座梯子 `✓ 2、✗ 0、⚠ 0`；甲板連通 3 層（h0 `42.8 m²`／d0 `59.9 m²`／d1 `12.8 m²`）`✗ 0、⚠ 0`。
  - `admin.py disp --id shachuan`：空載 `53.9` t／標準 `74` t／滿載 `87` t（載重 `13` t），符合 60–90 噸級距。
  - `admin.py shipcheck --id shachuan`：**`✗ 0`、`⚠ 6`**（6 筆 `⚠` 均為遊戲端 `config/game.json ships[]` 待填之 `geo` 與 `crew` 預設 fallback）；`ancbake` 與 `showlod` 已烘；`admin.py srccheck` 通過。
  - 第一人稱走回檢查（`check_decks.py`）：可達 `14,800` 格、能走回 `14,800` 格、**困住 `0` 格**。
- **給遊戲端填 `geo` / `crew` 的實測高度與範圍**（單位：0.1 m 格）：
  - 船殼外框：`x=36..245`（全長 `21.0 m`）、`y=69..123`（寬 `5.5 m`）、`z=0..48`
  - 設計水線：`waterline_z = 14`（`1.4 m`）
  - 各層甲板站面：`hold z=3`、`main z=23..28`（前段翹起）、`poop z=41`
  - 火砲砲軸高度：主腰 `4l` `axis_z=30.25`；前舷頂 `pierrier` `axis_z=39.75`；尾樓 `pierrier` `axis_z=52.75`
  - 三桅頂端高度：`fore z=127.5`、`main z=173.0`、`mizzen z=110.9`
  - 硬篷帆頂（peak）：`fore-junk z=126.5`、`main-junk z=174.5`、`mizzen-junk z=107.5`
  - 建議遊戲端船員：`climb=0` 無歐式桅樓，`crew` 可設 `top: 0, marines: 0, officers: 1, helm: 1, monkeys: 1, handsK: 0.25`。
- **Ship_Game §10 檢查表與 checksum 摘要**：
  - `.vxk checksum = 2905144336`（`73,380` 格、`c:769c655c7b`）；適用項全數通過（`ropecheck`、`ship` 水線、甲板連通、梯子 `✗ 0 ⚠ 0`、火藥桶 `400 lb`、廚房 `galley+smoke`、門 `door`、格柵 `grating`、小艇 `boat`、絞盤 `capstan`、羅經櫃 `binnacle`、尾燈 `light`、中式開孔升降舵＋`stock-top`＋`spin`＋舵柄 `tiller` 100% 操舵鏈、四爪鐵錨＋`hawse`、船尾窗 `glass`、三段硬篷 `set=1/2/3`）。歐式砲門蓋板、槳／蒸汽／砲塔／裝甲本船不適用。

# 百夫長號（Centurion, 1650）—— 英國四等艦（兩層砲甲板）建造筆記（0.1 m／格）

委託：Tim 2026-11-01（/scp-task，TASK-1153）：「那把卡拉維爾以及其他都開單吧」（TASK-1146 候選 #6）「/scp-task 1153 go」。
驗收（TASK-1153）：① 造船資料（查得到的附出處、推的標明）② 雕好照造船規格匯入 Blockside（開得動、帆與砲位能用；反向對照：照吃水與全長停不進太小一級的泊位）③ 接進 Blocksail（FLEET.types 一型、war）④ Tim 看過一次；步驟 1–15 照 Ship_Steps（刪 13：木造帆船）。

## 範圍
- 外部完整；內部只做遊戲用得到的大致構造（甲板、艙口、break、梯子、火藥庫）—— 照牛津號（erina）的範圍。
- 產生程式整套照抄牛津號 `erina-oxford-01m/design/`（它又抄自收穫號 calli）：每支檔頭寫來源；改的地方是**兩層砲甲板**（下層 culverin、上層 demi-culverin）、放大的主尺寸。

## 步驟 2 開工前（2026-11-01）
- 座標：0.1 m／格；框 600 × 256 × 512；x 船頭朝 +x、中線格 y 128（格 y ↔ 256 − y）、z 0 ＝ 龍骨底面。
- 作品：組裝件 `ridge-two-centurion-01m-assembly`「百夫長號」（主作品，關聯 `船殼` at 0,0,0）；船殼 `ridge-two-centurion-01m`「百夫長號 船殼」（任務作品、tags sub）；子作品都用整船的框、關聯 at 0,0,0。兩件都記了 meters_per_voxel 0.1。
- 現成元件（`sub=components`）：
  - 下層 culverin ⇒ 遊戲 `18l`：憲法號 `basecamp-frigate-constitution-01m-gun-long18` ×0.5（康塞普西翁號、收穫號、炎羽號同一份）。
  - 上層 demi-culverin ⇒ `8l`：風暴角號 `summit-stormkaap-01m-gun-6l` ×0.55（牛津號同一份）；上層 2 門 6 磅與後甲板 saker ⇒ `6l`：同一件 ×0.5（牛津號同一份）。
  - 方帆桁：風暴角號帆桁元件等比縮放（牛津號的做法）；後桅三角帆桁：牛津號 `erina-oxford-01m-yard-mizzen-lateen` 縮放；火藥桶（憲法號）、錨（憲法號）、艙蓋（莫尼特號）、爐灶（光榮號）、絞盤（餘燼號）。
  - 每艘自己做的：船首像、船尾雕飾、旗。

## 步驟 3 造船資料與新圖紙 01／02（2026-11-01）
- 資料：`references/research_centurion_2026-11-01.md`（〔查〕〔二手〕〔估〕〔設計〕）。
  - 〔查〕百夫長號（Peter Pett I，Ratcliffe，1650）：531 噸 bm、龍骨 104 ft、寬 31 ft；1666 編制 48 門 —— 下層 20 culverin、上甲板 22 demi-culverin＋2 門 6 磅、後甲板 4 saker；1661–63 Myngs 從牙買加皇家港出發打聖地牙哥（古巴）、坎佩切。
  - 〔二手〕艙深 12 ft 6 in（infobox；內文的 15 ft 6 in 是量噸公式的 B/2）；主桅 88.9 ft（Lees 1670 規則，牛津號同一條）。
  - 〔估〕下層砲甲板長 124 ft（同一批 1650 Programme 的炮甲板／龍骨 1.183–1.197）；吃水 14 ft 2 in（牛津號吃水／寬的比）。
- 改程式：`lines.py` 甲板照 plan 的 `on` 疊（gun 下層 → upper → qd／fc，poop 在 qd 上；沒寫 `on` 照牛津號舊規則）；`layout.py` 炮門可以逐門指定砲種（`guns`）；`draft_layout.py` 炮門頂的天花板照「疊在這一層上的每一層」找、版面照 plan 的框。控制組：抄來的 `lines.py`／`draft_lines.py` 拿牛津號的 plan 重跑 ⇒ 船殼清單跟牛津號逐位元組相同（da0c8b04）。
- 圖紙：`sheet01_lines_v1.png`、`sheet02_layout_v1.png`、`sheet03_ports_paint_v1.png`；`verify_lines.json`、`verify_layout.json`、`verify_ports.json`。重跑三支 ⇒ 清單與讀數逐位元組相同。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 下層砲甲板長（z 50，艏柱到艉柱） | 37.71 m（123.73 ft） | 〔估〕124 ft |
| 龍骨 | 31.70 m（104.0 ft） | 〔查〕104 ft |
| 最大寬 | 9.50 m（95 格，31.17 ft） | 〔查〕31 ft |
| 設計水線 | z 43（吃水 4.3 m） | 〔估〕14 ft 2 in |
| 排水量（水線下實心 × 1.025） | 713 t | 531 噸 bm 的 1.34 倍（牛津號 1.30） |
| 炮門下緣離水線 | 下層 1.3–2.1 m、上層 3.3–4.2 m、後甲板 5.2–5.4 m | — |
| 桅頂離水線 | 主 40.8 m、前 36.3 m、後 24.7 m | — |
| 帆面積（攤平 10 面） | 1,018 m² | — |
| 船殼牆 | 289,378 格；1 元件、空腔 0、鏡像差 0 | — |

- 第一版艏樓後緣在 x 372 ⇒ 上甲板 x 360 那個炮門頂離船腰舷頂只 1.7 格 ⇒ 艏樓後緣挪到 352（最前面兩門在艏樓底下）。
- 塗裝：兩排炮門中間多一條 middle wale（下層甲板 ＋17）；channel wale 在上層炮門頂上（＋34）；上部飾帶從 ＋36 起。

## 步驟 4 船殼落格、炮門、塗裝、船尾窗（2026-11-01）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py ridge-two-centurion-01m 0 masks/hull/hull_01.vox.txt hull_02.vox.txt`（2 刀，placed 250,000＋39,378 ＝ 清單）→ `船殼:end`。
- 結果帳（`tools/check_hull.py`，作品從 export 讀）：作品 289,378 ＝ 設計，缺 0、多 0、色差 0；線形對照 1,247 點差 0；**反向對照** `probe_x=250`（那一站 +3）⇒ 報 28 點、最大差 3。
- `炮門:begin` → carvevox `masks/ports/carve.vox.txt`（9,333）→ stampvox overwrite=1 `paint.vox.txt`（26,829）→ `炮門:end`。
  - 炮門：下層每舷 10（x 88…358、0.9 × 0.8 m）、上甲板每舷 12（x 80…388、0.7 m 見方；最後面那一門是 6 磅）、後甲板每舷 2（x 150、186）；外一圈紅框 192。
  - 船尾：wing transom 黑（z 58–59）、以上藍底、兩排各 5 扇窗（上甲板船長室、後甲板 coach）；玻璃 325 格留給步驟 6 的 `-stern-glass` 子作品。
- 讀數（`tools/check_stage3.py`）：結果帳 280,045 缺 0、多 0、色差 0；48 個炮門開口裡實心 0；**正向對照**（同一把尺量 `船殼:end`）48 個全報；**反向對照** `draft_ports.py --probe=skip_port=upper:5` ⇒ 只報那一門兩舷（各 147 格）；stats 1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_ports_{sternq,bowq}.png`。

## 步驟 5 甲板、艙口、break、梯子（2026-11-01）
- `draft_decks.py` ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`。
- 改程式：橫樑可以每層各自對齊（`every_by`／`phase_by`：上甲板的樑吊在下層頂上、對齊下層炮門每 15 格；後甲板、艏樓、艉樓的樑對齊上層炮門每 14 格）；炮門擋路檢查的量測寬度照本船半寬（牛津號寫死 |dy| 10–40）。
- 甲板（第一層空氣 z，`decks.py` 量）：底艙平台 32（x 120–360）、下層砲甲板 51–62、上甲板 71–82、後甲板 90–102（x 到 230）、艏樓 91–98（x 352 起）、艉樓 111–119（x 52–132）。
- 艙口：主艙口 x 268–282、前艙口 312–326，下層與上甲板都開。break 三道（後甲板前緣 x 230、艉樓前緣 132、艏樓後緣 352；門開在中線，艉樓前緣開兩舷）。
- 梯子 8 座：hold（底艙 → 下層，在後甲板底下開井）、up-P／S（下層 → 上甲板，主桅兩舷開井）、qd-P／S、poop（中線）、fc-P／S。每層都有梯子通到。
  - 🩸 v1：後甲板前緣在 x 220 ⇒ 艙壁正好切過上甲板 x 220 的炮門（擋 217 格）⇒ 挪到 230（兩門之間），船殼舷頂跟著變 ⇒ `tools/hull_state.py`＋`tools/delta_apply.py`（標記 `後甲板前緣挪位`：補 1,050、換色 150，再比 0 差）。
  - 🩸 v1：上甲板梯子在 x 300 ⇒ 擋住下層 x 298 的炮門 ⇒ 挪到主桅兩舷（x 246–263，下層 238 與 268 兩門之間）。
- 讀數（`tools/check_decks.py`）：子作品 11 件 136,654 格，缺 0、多 0、色差 0、跟船殼重疊 0、互相重疊 0；梯子點（組裝件 parts）32／32、差 0、空氣／腳下／頭頂 14 格問題 0；炮門往艙裡被擋 0；組裝件 1 元件、空腔 0、鏡像差 0。**反向對照** `--probe=drop_ladder=hold` ⇒ 底艙平台沒有梯子通到。
- 甲板 meta：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（代號 orlop／lower／upper／quarter／forecastle／poop，名字照本船）⇒ `work sub=meta`（6 筆）。
- 過程圖 `overlays/stage5_decks_nohull.png`。

## 步驟 7 桅與帆桁（2026-11-01）
- `draft_masts.py` ⇒ `masks/masts/<桅>.vox.txt`、`masks/bowsprit_hole/`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`。
- 桅（子作品 `-mast-main／fore／mizzen`，關聯 主桅／前桅／後桅）：下桅＋圓桅樓（主 r 17、前 15、後 13）＋上桅（doubling）＋上桅帆桅；桅頂 z：主 451、前 406、後 290（離水線 40.8／36.3／24.7 m）。
- 艏斜桅（`-bowsprit`）：根部 (401, 78) 在上甲板、仰 35°、16.3 m；開孔 236 格（船殼 56、艏樓甲板 157、上甲板 23；牛津號只開到艏樓與炮甲板 ⇒ 開孔清單加上甲板）。
- 方帆桁 9 根：引用風暴角號（summit）帆桁元件等比縮放（主 course 0.885、topsail 0.846、topgallant 0.675；前 0.879／0.820／0.807；crossjack ＝ 主上桅帆桁 0.740；mizzen topsail 0.970；spritsail 0.807）。
- 後桅三角帆桁：**不另做**，引用牛津號 `erina-oxford-01m-yard-mizzen-lateen` ×1.3015（17.7 m；Ship_Setup §2.1）；meta 照牛津號 `yard=gaff rig=lateen`、rotate y 40°。
- 🩸 後桅腳兩側各 1 格封閉空腔（桿與船底內板夾住）⇒ `draft_masts.py` 每根桅腳 ±12 格的框裡被封死的空氣填成桅色（後桅 2 格、主前 0）。
- 讀數：桅與艏斜桅 delta 0；組裝件 472,175 格、1 元件、空腔 0、鏡像差 0；ropecheck link_overlap 0、link_clipped 0；view models_broken 0；艏斜桅開孔後甲板 11 件與船殼重比 0 差、梯子點 32／32 問題 0。
- 過程圖 `overlays/stage7_masts.png`。

## 步驟 6 裝飾（2026-11-01）
- `draft_deco.py`、`tools/build_deco.py`（照抄牛津號）：船首喙 `-beakhead`（平台面 z 88、伸出艏柱到 x 477、半寬 1.7 m 收尖；cutwater 從 z 34 的艏柱斜到平台尖、前緣金；兩舷兩條 head rail＋柱）、船首像 `-figurehead`（鍍金獅子、紅冠，牛津號那一隻 ×1.3 ⇒ 程式加 `scale`；1,056 格）、船尾旗桿 `-ensign-staff`（x 49、5.5 m）、船尾窗玻璃 `-stern-glass`（400 格，關聯 meta material=glass）。
- 🩸 船尾窗玻璃 v1：斜的船尾板一柱一柱放「第二格」⇒ 10 扇裂成 25 塊（相鄰兩柱只在斜角相碰）⇒ `draft_ports.py` 在窗洞裡補一格（Ship_Materials「窗的玻璃」）⇒ 10 扇 10 塊、各自 6 連通；炮門與塗裝清單不變。
- 🩸 v1 欄杆柱在 x 466 ⇒ 插進獅子身體 10 格 ⇒ 挪到 451、457。
- 讀數：件與件重疊 0、跟船組起來 1 元件、空腔 0、艏斜桅線上的裝飾 0；組裝件 478,040 格、1 元件、空腔 0、鏡像差 0、link_overlap 0。**反向對照** `--probe=shift=figurehead:20`（推出平台尖）⇒ 元件 2（浮空）；推 8 格還踩在平台上 ⇒ 1。
- 船名板沒做（1660 年代英國船船尾不寫船名）；quarter gallery 沒做。
- 過程圖 `overlays/stage6_bow.png`。

## 步驟 8 索具、帆、旗（2026-11-01）
- `draft_rigging.py` ⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落地 `tools/rigging_apply.py`（channels → 固定點 → 繩 → 橫繩組 → 帆 → 帆的繩 → 風 → meta）。
- 改程式（牛津號寫死的）：主桅下的後桅支索腳（62 ⇒ 上甲板 ＋21）、船頭綁點上限（300 ⇒ 440）、後桅三角帆 sheet 綁點（42 ⇒ 50）、艏斜桅側索與 bobstay 的高度（52／56／40 ⇒ 84／90／50）、找「那一欄最上面的甲板」加 upper、桅樓邊緣的點照上桅 shroud 根數均分（3 根時同值）、channels 的起點與間距可以每根桅各自。
- channels：兩舷一件 1,454 格；每舷 shrouds 主 8、前 5、後 4，backstay 主、前各 1；上桅 shroud 每舷 4。
  - 🩸 v1 前桅 7 根、間距 8 ⇒ 排到艏樓後面的船腰（x 330）⇒ channels 照整段最低的舷頂 z 86 放 ⇒ 碰上上甲板 x 388 炮門的開口（assert：deadeye 那一欄量不到船殼）⇒ 前桅 5 根、間距 6、從桅後 2 格起，全部在艏樓那一段 x 357–387。
  - 🩸 v1 上桅 shroud 改 4 根 ⇒ 桅樓邊緣只產了 3 點（rim-S-4 解不到）⇒ 照根數均分。
- 繩 118（靜索 95＋帆的繩 23，全帶 meta）、橫繩組 12（下桅 6 組 climb=1）、帆 9＋旗 2（英國紅 ensign 掛船尾旗桿、主桅頂紅長旗）、固定點 136。
- 帆裝三段（照 meta 的 sail／set 算；旗不算）：

| 段 | 張哪幾面 |
|---|---|
| 1 收帆 | fore-topsail、main-topsail、mizzen-topsail |
| 2 戰鬥帆 | ＋ fore-topgallant、main-topgallant、mizzen-lateen |
| 3 滿帆 | ＋ fore-course、main-course、spritsail（set 3） |

- 讀數：ropecheck 繩 356、兩端 712 全 ok、link_overlap 0、link_clipped 0；view ropes_broken 0、sails_broken 0、models_broken 0；組裝件 479,494 格、1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage8_rigging.png`。

## 步驟 9 砲（2026-11-01）
- **新通用部件 `ridge-two-centurion-01m-gun-8l`**「8 磅長砲（gun 8l，demi-culverin 鐵砲管＋兩軸四輪砲架；通用部件，0.05 m）」：產生程式 `design/draft_gun8l.py`（照抄聖羅曼號 `pinnacle-patache-01m/design/draft_gun4l.py`，plan.json `gun8l`）⇒ `masks/gun8l/gun-8l.vox.txt`、`verify_gun8l.json`。15×60×23、3,217 格、1 元件、空腔 0、左右鏡像差 0；砲管 2.9 m、耳軸高 0.83 m；固定點 muzzle（內膛空格）／breech／cascabel／trunnion／train／eye-aft／eye-fwd；作品預設 meta `kind=gun, gun=8l`；pivot ＝ 砲架前緣中間 (7.5, 35, 0)。
  - 為什麼新做：Ship_Guns §2.2（Tim 2026-10-28）「炮只有同型號共用模型」—— 現有元件沒有真正的 8 磅（牛津號是拿 6 磅縮 0.55，文件列為還沒換的舊船）。
- 擺法 `draft_guns.py`（照抄牛津號；plan `guns_build`：三層甲板、三種砲）⇒ `guns_placement.json`、`verify_guns.json`；落地 `tools/build_guns.py`（P 舷 mirror=y）。
  - 下層 20 門 culverin ⇒ `18l`：憲法號 `-gun-long18` ×0.5（pivot 13.5, 38.5, 0）。
  - 上甲板 22 門 demi-culverin ⇒ `8l`（上面那件新部件 ×0.5）＋ 2 門 6 磅（每舷最後一門）⇒ `6l`：風暴角號 `-gun-6l` ×0.5。
  - 後甲板 4 門 saker ⇒ `6l`（同一件）。
- 🩸 v1 下層炮門下緣 0.6 m ⇒ 18 磅砲軸高 1.08 m 貼著炮門頂 ⇒ 兩頭三門退到砲口只伸出 1–2 格 ⇒ 炮門下緣 0.7 m（sill 7）；船殼 `hull_state`＋`delta_apply`（標記 `下層炮門上挪`：刻 540、補 540、換色 1,320，再比 0 差）；甲板、炮門擋路、梯子點重量 0 問題。
- 讀數：48 門全 ok（砲口伸出 18l 5–8、8l 7.75–9.75、6l 6.25–7.25 格；砲口空；腳下支撐 0.5–1.0）、砲與砲不撞、兩舷對稱；models_broken 0。**反向對照** `--probe=push=砲U-S05:4`（往外推 4 格）⇒ 只報那一門 1,908 個碰撞樣本。
- 過程圖 `overlays/stage9_guns.png`。

## 步驟 10 火藥庫、艙蓋、廚房、絞盤（2026-11-01）
- `draft_gear.py`（照抄牛津號）⇒ `masks/gear/magazine.vox.txt`、`gear_placement.json`、`verify_gear.json`；落地 `tools/build_gear.py`（宿主多一件上甲板）。
- 火藥庫（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine pos=aft powder_lb=1200 hoist=甲板-gun/梯子/hold,甲板-upper/梯子/up-P,甲板-qd/梯子/qd-P`）：底艙平台後段 x 121–151、前後兩道牆、前牆中線門 5 寬 1.5 m 高；固定點 blast（138,128,38）、door（152,128,32）。12 個火藥桶（憲法號共用桶 ×0.2）。
  - 三層砲甲板 ⇒ hoist 列三座梯子（Ship_Magazine：每一層只用梯頭落在那一層甲板的那一座）。
  - 🩸 v1 桶第一排 x 126.5 ⇒ 兩桶撞到穿過火藥庫的後桅腳（後桅 x 128）⇒ 三排挪到 x 134.5／141／147.5。
- 艙蓋（莫尼特號 `-hatch` 照開口縮放，kind=door）：上甲板主艙口、前艙口（船腰露天）。
- 爐灶（光榮號 `-galley` ×0.33，kind=galley）：艏樓底下上甲板左舷；絞盤（餘燼號 `-capstan` ×0.16）：後甲板底下上甲板中線 x 180。
- 讀數：16 個模型碰撞 0、問題 0；組裝件 481,763 格、1 元件、空腔 0、鏡像差 0、link_overlap 0。

## 步驟 11 舵與錨（2026-11-01）
- `draft_rudder_anchor.py`、`tools/build_rudder_anchor.py`（照抄牛津號）：舵子作品 `-rudder`（2,398 格，沿艉柱、z 0–72、前緣兩側削 1 格、牛津號的舵葉 ×1.3）掛成模型 `舵`：kind=rudder、hinge (72, 128.5, 0)、axis (−0.191, 0, 0.982)、max 35°、spin=rudder ±35°；stock-top (54,128,72) 離船殼 4 格。
- 不放舵輪（1660 年代 whipstaff；舵令 ⇒ 舵柄在舵上，同牛津號）。
- 錨：憲法號共用錨 ×0.72（531 噸；牛津號 220 噸 0.55、收穫號 0.85）兩舷，rz ±58、離船殼 1.55 m，錨冠落在錨架托板 `-anchor-gear`（1,980 格）上；船殼固定點 hawse-S／P (435, 150／106, 62)（下層砲甲板那一層）。
- 讀數：舵與托板落在實心 0、鏡像差 0；錨碰撞 0；組裝件 483,743 格、1 元件、空腔 0、鏡像差 0、link_overlap 0；models_broken 0。
- 過程圖 `overlays/stage11_rudder_anchor.png`。

## 步驟 12 砲門蓋板（2026-11-01）
- `tools/portlids.py`（照抄牛津號 ← basecamp 的通用工具；船表只有本船、`decks` 兩層 `甲板-gun`、`甲板-upper`；顏色：朝外木色 177、內側紅 192、鉸鏈板黑 36）：下層 20 片＋上甲板 24 片 ＝ 44 片；後甲板 saker 從舷牆上過、§9.12 不做。蓋板子作品 `-portlid` 11×10×2（本船最大的開口每邊 ＋1；牛津號那片 9×9 蓋不住下層 9 寬的炮門 ⇒ 自己一件）。
- `lid_of` 指砲的物件 id（步驟 14 先匯入＋`admin.py ids` 才有）。
- 🩸 v1 開著的蓋板撞船 594 個取樣點：上甲板第 5 門（x 192）兩舷 —— 主桅 channels 從 x 186 排起、在船腰舷頂的高度（z 85），那一帶甲板因舷弧抬高、蓋板開著平伸進 channel ⇒ 主桅 shroud 間距 8 ⇒ 6（channels 收到 x 199 以前；根數、繩名不變）⇒ `draft_rigging.py`、channels `delta_apply`（刻 212、補 84）、`rigging_apply.py anchors ropes ratlines`；ropecheck 繩 354、兩端 708 全 ok、link_overlap 0。
- 讀數（`portlids.py check`）：開著碰船 0、碰砲 0；關上碰縮回的砲 0、落進船殼最多 1.52%、開口全蓋住；house 7–12、close 75.8–94.6°；**反向對照** house 0 ⇒ 44 片碰砲、P 舷改 mirror=y ⇒ 22 片往上關。收砲時砲尾碰到船內 126 個取樣點（只是畫面，同牛津號照實留著）。
- 過程圖 `overlays/stage12_portlids.png`。

## 步驟 14 給遊戲的 meta 與匯入（2026-11-01）
- 船殼關聯 meta `kind=ship, waterline_z=43`；ropecheck 繩 354、兩端 708 全 ok、link_overlap 0。
- Blockside 自己的 worktree（`ridge-two/centurion`，從子模組 `heads/dev` 5fec654 開；`_cache` 先從共用的複製 87 檔）：`admin.py import --work ridge-two-centurion-01m-assembly --id centurion --name 百夫長號` ⇒ 匯入檢查 ✗ 0、⚠ 12。
- 一路修下來（✗ 0 不變，⚠ 12 → 2）：
  - geo、crew（遊戲那側的設定，本小姐照量過的高度填）：`spar` [71, 102]、`marines` [60, 100]、`center` 80、`aim` 64、`aimZ` [10, 450]、`deckAim` [55, 90]、`rigAim` [160, 440]；crew officers 4、marines 12、marineGap 14、navigator 0（沒有舵輪）；gangway 船腰 x 300.5 兩舷 z 89.5 ⇒ 軍官、陸戰隊、航海士站不下的 3 條消掉。
  - `admin.py ids --id centurion`（兩次：蓋板是第一次發號之後才加的）。
  - 🩸 上甲板梯子 up-P／S v1 往船尾爬、梯頂 x 244 正前方是後甲板梯子的梯腳（⚠ 梯頂正前方擋住）⇒ 往船頭爬（xs 246、dir +1、梯頂 x 264）；甲板 96 格、梯子 386 格 `delta_apply`，梯子點重登記；check_decks 0 問題。
  - 🩸 火藥庫 `hoist` 三座梯子用舊的路徑寫法 ⇒ `ids` 不拆逗號清單、換不成 id（✗ 找不到這個部件）⇒ 手寫成 id 寫法 `ladders-1#hold,ladders-2#up-P,ladders-3#qd-P`、`metasync`。
- 照實留著的 ⚠：
  1. 艙底下不去（x 133–417、z 5–21、約 138 m²，最下層是底艙平台）—— 跟牛津號同一套佈置，沒有往艙底的梯子。
  2. 漏水：再多載 988 噸（吃水再深 3.3 m，沉沒線 +4.2 m）從上甲板 x 248 炮門下緣漏，分類「砲門旁（塞住了還漏）」—— 遊戲 `75_leakcheck.js` 塞砲門是從砲口往裡 6 格起算，本船 8 磅砲口伸出船殼 7.75–9.75 格 ⇒ 塞子搆不到牆上的炮門；不是船殼的縫。
- 火藥 48／48 門走得到取用點（最遠 19 m）；廚房 1 座（廚師站得住的面 4 ✓）；操舵：舵令 ⇒ 舵柄在舵上 ⇒ 舵 100%；蓋板 44 片（後甲板 4 門 saker 照規格沒有蓋板）。

## 給遊戲那側填 geo 用的高度（已經照這些填進 Blockside game.json ships[centurion].geo）
- 水線 z 43；底艙平台 z 32；下層砲甲板（第一層空氣）船中 z 51、船尾 62、船頭 59；上甲板 71–82；後甲板 90–102；艏樓 91–98；艉樓 111–119。
- 砲軸：下層 z 62–71、上甲板 79–87、後甲板 98–100；桅樓：主 z 250、前 225、後 201；桅頂：主 451、前 406、後 290（離水線 40.8／36.3／24.7 m）。
- 船殼 x 47（船尾板）～ 447（艏柱）；喙平台尖 x 477、獅子到 x 481；艏斜桅尖到 x 535。全長（含艏斜桅）48.9 m、水線長 37.9 m（船卡）。
- 最後一次（`metasync`）：匯入檢查 ✗ 0、⚠ 2（上面兩條）；樓梯自檢 8 座全 ✓；繩 354 條綁定、照外框猜 0；材質 橡木 483,215 格 338.3 t、玻璃 400 格 1 t。

## 步驟 15 交船（2026-11-01）
- 換一艘船時的檢查表（Ship_Game §10）逐條：ropecheck ✓（bind／snap 0、照外框猜 0）、名稱與 sub ✓、mpv 與模型 scale ✓、現成元件（18 磅、6 磅砲、方帆桁、三角帆桁、火藥桶、錨、艙蓋、爐灶、絞盤）✓／新做的（8 磅砲通用部件、砲門蓋板、舵、火藥庫、裝飾）列在上面 ✓、舵模型＋stock-top＋spin ✓、沒有舵輪（舵柄在舵上）✓、kind=ship waterline_z 43 ✓、梯子＋樓梯自檢 8 座 ✓、橫繩組＋繩梯 ✓、火藥桶＋取用點 48／48 ✓、甲板 meta ✓、三角帆桁 rig=lateen＋fore ✓、玻璃 ✓、砲零碰撞 ✓、砲門蓋板 ✓、繩帆模型斷 0 ✓、帆與帆的繩 meta ✓、帆裝三段表 ✓、1 元件／空腔 0／重疊 0／鏡像 0 ✓、shipcheck ✗ 0 ✓、spin ✓。空艙房沒標（遊戲用不到時可以之後加）。
- checksum：Blockside `_cache/centurion.vxk`（鎖檔 c:f97201517b2a）vs 從作品重新匯出 ⇒ 格子逐位元組相同、檔頭只差 253 條繩的 `bind`（Blockside 匯入時 ropebind 加的，作品匯出本來就沒有）。
  - ⚠ `admin.py cache --all` 那天把 30 艘都報「作品變過」—— 本船量出來只差 bind，別艘多半同一個原因（不是本小姐的船，沒動它們的 _cache）。

## 接進遊戲（2026-11-01）
- Blockside：分支 `ridge-two/centurion` 0534a1d（匯入）＋ d2fb64d（合 dev 349939a：取 dev 的成品再整個重建；dev 新加的 ships/showlod.js 補烘本船 ⇒ showlod --check 31 型 ✓）⇒ ff 進子模組的 dev。共用 `_cache/centurion.vxk` 指紋 ＝ 鎖檔 c:f9720151。⚠ **Blockside dev 還沒推**（推送被權限擋下，等 Tim）。
- Blocksail：737bfd6a ff 進 main（沒推）—— `FLEET.types.fourth`（531 t、war、hull centurion）、`hullLoa` 48.9、`SAILOR.crew` 180、TRADE_SIM 船型表、fleet_check 兩條；子模組 → d2fb64d、battle.html 重套。fleet_check 前後 ✓ 89 → 91、✗ 0，起始檔一年讀數一位不差。
- 遊戲裡（worktree 成品 `?ship=centurion`，對手憲法號）：開局掉落的模型 0；W／S 帆裝 0–3 段跟上面那張表一樣；側順風 12.1 節；一輪舷側排出 23 門。截圖 `overlays/stage14_ingame_sailing.jpg`。

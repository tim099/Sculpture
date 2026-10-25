# 牛津號（Oxford, 1656）—— 英國五等艦（frigate）建造筆記（0.1 m／格）

委託：Tim 2026-10-26（/scp-task，TASK-0964／0972）：「開一下任務吧 目前打算挑3種1666年附近 最常見的加勒比海商船船型 還有一種海盜船 來建造（且最好有圖紙及參考資料 同級艦等 …」「先把這8種都開成task好了」「972 GO」。
驗收（TASK-0972）：① 造船資料（查得到的附出處、推的標明；沒核的原典核過一次）② 雕好照造船規格匯入 Blockside（開得動、帆與砲位能用；反向對照：照吃水與全長停不進太小一級的泊位）③ 接進 Blocksail 船型清單 ④ Tim 看過一次。
造船規格：`senate cmd doc --arg op=show --arg name=Sculpture_Shipbuilding`；大型作品流程：`Sculpture_Blueprint_Build`。

## 範圍
- 外部完整；內部只做遊戲用得到的大致構造（甲板、艙口、break、梯子、火藥庫）—— 照收穫號（calli）的範圍。
- 設計程式的結構多半從收穫號 `calli-cosecha-01m/design/` 抄來改（每支檔頭寫了來源）：線形「船中剖面 × 長度方向收縮」、炮門與塗裝、甲板與梯子、落格與結果帳工具。

## 座標與比例
- 0.1 m／格；框 448 × 192 × 384；x 船頭朝 +x、中線格 y 96（格 y ↔ 192 − y）、z 0 ＝ 龍骨底面。
- 組裝件 `erina-oxford-01m-assembly`「牛津號」（主作品）；船殼 `erina-oxford-01m`「牛津號 船殼」（任務作品、tags sub）；子作品都用整船的框、關聯 at 0,0,0。全部記了 meters_per_voxel 0.1。

## 階段一 造船資料與新圖紙 01／02（2026-10-26）
- 資料：`references/research_oxford_2026-10-26.md`（〔查〕〔二手〕〔設計〕三種標記）。
  - 〔查〕牛津號：220 噸 bm、龍骨 72 ft、寬 24 ft、艙深 10 ft、吃水 11 ft；建造時 16 demi-culverin（炮甲板）＋ 6 saker（後甲板）；船員 100–110。
  - 〔設計〕炮甲板長 84 ft ＝ 72 × 1.17（同時代 Basing、Pearl、1650 Programme 五艘的炮甲板／龍骨 1.144–1.200）。
  - 〔二手〕主桅 64 ft（Lees 轉述的 1670 年規則）；其他桅帆比例〔設計〕。
  - ⚠ 更正：TASK-0964 留言說 Deane《Doctrine》1670 有各等艦圖 —— 書目說明是從頭畫一艘**三等艦**；原書沒拿到，**沒核**。Winfield 2009、Lees 原書也沒讀到（只讀到轉引）。
  - 〔設計〕1660 年代英國船用 whipstaff，不放舵輪（舵柄獨立標 `kind=tiller`，之後的階段）。
- 新圖紙：`design/plan.json`（每個數字的 src）、`lines.py`（線形）、`layout.py`（佈置）；`draft_lines.py` ⇒ `sheet01_lines_v1.png`、`verify_lines.json`；`draft_layout.py` ⇒ `sheet02_layout_v1.png`、`verify_layout.json`。
  - 跟收穫號不同的線形：艏柱 1/4 橢圓（一路倒到艏柱頭）；方艉（square tuck）的過渡帶往前越拉越寬 ⇒ 船尾水線上下是高腳杯形；兩頭各照自己的 deadwood 收成 V；炮甲板照舷弧逐欄。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 炮甲板長（z 40，艏柱到艉柱） | 25.56 m（83.86 ft） | 〔設計〕84 ft |
| 龍骨 | 21.90 m（71.85 ft） | 〔查〕72 ft |
| 最大寬 | 7.30 m（73 格，23.95 ft） | 〔查〕24 ft |
| 設計水線 | z 33（吃水 3.3 m） | 〔查〕11 ft ＝ 3.35 m |
| 排水量（水線下實心 × 1.025） | 287 t | 220 噸 bm 的 1.3 倍（量級） |
| 炮門下緣離水線 | 炮甲板 1.30–2.00 m、後甲板 3.20–3.70 m | 1650 年代 frigate 本來低舷 |
| 桅頂離水線 | 主 29.2 m、前 26.1 m、後 17.7 m | — |
| 帆面積（攤平 10 面） | 584 m² | — |

- 第一版剖面兩頭不對（船尾 x 80 一片水平的板、船頭 x 280 太方）⇒ 兩頭的 e 各照自己的 deadwood、方艉帶照 ua 拉寬（`end_hollow` 3）。
- 第一版舷牆：炮門頂（甲板 ＋13）剛好頂到船腰舷頂（＋13）⇒ 船腰舷牆改 ＋15、後甲板 ＋13。

## 階段二 船殼落格（2026-10-26）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py erina-oxford-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 138,128 ＝ 清單）→ `船殼:end`。
- 結果帳（`tools/check_hull.py`，作品從 export 讀）：作品 138,128 ＝ 設計，缺 0、多 0、色差 0；線形對照 569 點差 0；**反向對照** `probe_x=180`（那一站 +3）⇒ 報 18 點、最大差 3。
- 結構（引擎 stats）：1 元件、空腔 0、鏡像差 0。組裝件關聯 `船殼` meta `kind=ship, waterline_z=33`。
- 過程圖 `overlays/stage2_hull_{bowq,sternq,side}.png`。

## 階段三 炮門、塗裝、船尾窗（2026-10-26）
- `draft_ports.py` ⇒ `masks/ports/carve.vox.txt`（3,368，帶刻之前的顏色守門）、`paint.vox.txt`（14,931，換色）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 炮門：炮甲板每舷 8（x 72…228、248；0.7 m 見方、下緣在甲板上 0.6 m）、後甲板每舷 3（x 74、104、134）；外擴一圈紅框 192。
- 塗裝（〔設計〕1660 年代英國船）：水線上外板木色 177、wale 三條黑 36（主 wale 兩條在炮甲板下、channel wale 在炮門頂上）、channel wale 以上藍 6 底金 248 邊、舷頂黑；船尾 wing transom 黑、以上藍底、兩排各 4 扇窗（金框、玻璃 87）。
  - 🩸 船尾面「每個 (y, z) 最後面那一格」把船尾附近的舷側也算進去（側面斜紋藍）⇒ 只算離艉柱斜面 3 格內的格。
- 階段四之前把第 8 門炮挪到 x 248（讓艏樓梯子）：`tools/hull_state.py`（船殼 − 開口 ＋ 塗裝）＋ `tools/delta_apply.py`（作品對清單：刻 258、補 258、換色 264；標記 `炮門8挪位`），挪完再比 0 差。
- 讀數（`tools/check_stage3.py`）：結果帳 134,760 缺 0、多 0、色差 0；22 個炮門開口裡實心 0；**正向對照**（同一把尺量 `船殼:end`）22 個全報；**反向對照** `--probe=skip_port=gun:3` ⇒ 只報那一門兩舷；stats 1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage3_ports_{a,b,c}.png`。

## 階段四 甲板、艙口、break、梯子（2026-10-26）
- `draft_decks.py` ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`。
- 甲板（第一層空氣 z）：底艙平台 21（x 100–250，火藥庫用）、炮甲板 40（船中；舷弧船尾 +10、船頭 +7）、後甲板 ＝ 炮甲板 ＋19（x 到 158）、艉樓 ＝ 後甲板 ＋17（x 46–96）、艏樓 ＝ 炮甲板 ＋18（x 262 起）。橫樑每 13 格（照炮門相位）。
- 艙口：主艙口 x 190–204、前艙口 232–244；桅孔照桅軸；break 三道（後甲板前緣、艉樓前緣、艏樓後緣：艙壁＋門＋胸牆，梯子頭留口）。
- 梯子 6 座：hold（底艙 → 炮甲板，在兩個艙口之間開井）、qd-P／S（炮甲板 → 後甲板，x 158–172 在兩門炮之間）、poop（後甲板 → 艉樓，中線）、fc-P／S。每層都有梯子。
  - 🩸 break 艙壁從下一層甲板板那一列開始 ⇒ 跟甲板重疊 149 格 ⇒ 從 +1 起；梯腳照起點那一欄的甲板高度 ⇒ 舷弧差 1 格懸空 ⇒ 照梯腳那一欄。
- 讀數：結果帳 9 件 49,577 格缺 0、多 0、色差 0、重疊 0（`tools/check_decks.py`）；梯子點（組裝件 parts）24／24、差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 1 元件、空腔 0、鏡像差 0；炮門往艙裡被擋 0。
- 甲板 meta：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（代號、名字照本船改）⇒ `work sub=meta`（5 筆）。
- 過程圖 `overlays/stage4_decks_{bowq,nohull}.png`。

## 2026-10-26 流程更新：造船步驟表
- Tim 04:14 把造船規格拆成 `Ship_*` 十六份＋步驟表 `Ship_Steps`（gura TASK-0967）⇒ 步驟表已接到 TASK-0972 的驗收標準（刪步驟 13：木造帆船）；之後每一步只讀那一行的文件。
- 已勾：步驟 1–5、7–9（下面的階段六～八）。下一步：6 裝飾、10 彈藥庫與甲板物件、11 舵與錨、12 砲門蓋板、14 匯入、15 交船。

## 階段六 桅與帆桁（步驟 7；2026-10-26）
- `draft_masts.py` ⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen.vox.txt`＋`yard_lateen_anchors.json`、`masks/bowsprit_hole/`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`。
- 桅（子作品 `-mast-main／fore／mizzen`，關聯 主桅／前桅／後桅）：下桅＋圓桅樓（主 r 13、前 11、後 7；2 格厚＋外緣矮欄黑頂）＋上桅（在下桅頭前面 doubling）＋上桅帆桅；每節頂一個黑 cap；上桅頭十字桁。桅頂離水線：主 29.2、前 26.1、後 17.7 m。
- 艏斜桅（`-bowsprit`）：根部 (284, 49)、仰 35°、11.6 m；船頭牆與艏樓甲板開孔、孔由艏斜桅填滿。
  - 🩸 根部 v0 (262, 50) 會穿過前桅 ⇒ 挪到前桅前面；(284, 46) 切到炮甲板 18 格 ⇒ z 49。
  - 🩸 `draft_masts` 第一版算佔用是「匯出整艘、扣掉自己的清單」：第一次跑時桅還沒放、上一輪的清單卻在 ⇒ 扣掉的是船殼 ⇒ 開孔少算 73 格（ropecheck 報 link_overlap 73）⇒ 改成匯出時 `hide_links` 藏掉本階段的關聯（`tools/wio.py` 加 hide_links），補刻 69＋4（標記 `艏斜桅孔補刻`）⇒ link_overlap 0。
  - 🩸 上桅十字桁的半徑是小數 ⇒ y 範圍兩舷不對稱、鏡像差 8 ⇒ 取整數（差分刻 16＋10）。
- 方帆桁 9 根：照造船規格 §2.1 引用風暴角號（summit，17 世紀荷蘭船）的帆桁元件等比縮放（main course 0.681、topsail 0.650、topgallant 0.519、fore 0.676／0.631／0.614、crossjack ＝ 主上桅帆桁 0.569、mizzen topsail 0.746、spritsail 0.619）。帆桁掛在那一節桅的前面（半徑＋2.5）。
  - 🩸 模型名 `yard-main-tg` ⇒ Blockside 匯入檢查拿 `yard-` 後面那段對帆名 ⇒ 改成 `yard-main-topgallant`、`yard-fore-topgallant`。
- 後桅三角帆桁：新元件 `erina-oxford-01m-yard-mizzen-lateen`（136×5×5、中段粗兩頭細；固定點 pivot／sling／fore／peak／earing-F／A／top-NN）—— 風暴角號的沒有 `fore`、持火號的加了會改到持火號在遊戲裡的擺角 ⇒ 新做。擺在後桅左舷側、rotate y 40°（前端低）、meta `yard=gaff rig=lateen`。
- 讀數：組裝件 1 元件、空腔 0、鏡像差 0；models_broken 0。

## 階段七 索具、帆、旗（步驟 8；2026-10-26）
- `draft_rigging.py` ⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落地 `tools/rigging_apply.py`（channels → 固定點 → 繩 → 橫繩組 → 帆 → 帆的繩 → 風 → meta）。
- 帆桁模型的點（earing、pivot、fore、peak）從組裝件 `export format=parts` 讀世界座標（不自己算旋轉）。
- channels：兩舷一件、舷頂下 1 格（船腰炮門頂 ＋13、舷頂 ＋15 ⇒ 不擋炮門；照那一段最低的舷頂 —— 前桅 shrouds 落在艏樓後面的船腰）；shrouds 主 6、前 5、後 3／舷；上桅 backstay 主、前各 1。
- 靜索 77、帆的繩 23（sheet 18、tack 5，全帶 meta）；ratlines 橫繩組 12（下桅 6 組 climb=1：foot 舷牆內側甲板、head 桅樓靠這一舷的邊；上桅 6 組）。
- 帆 9＋旗 2：fore／main course、topsail、topgallant，mizzen topsail（帆腳綁 crossjack），spritsail（`sail=course set=3`），mizzen-lateen（`sail=gaff`）；英國紅 ensign（左上角白底紅聖喬治十字，暫掛三角帆桁後端）、主桅頂紅長旗。
- 讀數：ropecheck 繩 250、兩端 500 全 ok、link_overlap 0；view ropes_broken 0、sails_broken 0、models_broken 0。

## 階段八 砲（步驟 9；2026-10-26）
- `gunsim.py`（照抄收穫號）＋ `draft_guns.py`（照抄改：本船炮門、沒有追擊砲）⇒ `guns_placement.json`、`verify_guns.json`；落地 `tools/build_guns.py`。
- 炮甲板 16 門 demi-culverin ⇒ `8l`（風暴角號 `-gun-6l` ×0.55）；後甲板 6 門 saker ⇒ `6l`（同一件 ×0.5）。P 舷 mirror=y。
- 🩸 碰撞格網外擴 4 格：砲口伸出舷外 ~7 格、出了網格框 ⇒ 框外當實心 ⇒ 船腰 8 門「砲口不空」假警報 ⇒ pad 16。
- 🩸 甲板高度取樣點往舷內 26 格會碰到主艙口圍欄（P 舷多 1 格）⇒ 砲墊高、兩舷不對稱 ⇒ 只取到 20 格。
- 讀數：22 門全 ok（砲口伸出 6.3–9.3 格、砲口空、腳下支撐 0.5–1.0）、砲與砲不撞、兩舷對稱；models_broken 0。

## 步驟 10 火藥庫、艙蓋、廚房、絞盤（2026-10-26）
- `draft_gear.py`（模型取樣點不落在實心格、不進砲的外框、量腳下支撐）⇒ `masks/gear/magazine.vox.txt`、`gear_placement.json`、`verify_gear.json`；落地 `tools/build_gear.py`。
- 火藥庫（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine pos=aft powder_lb=800 hoist=<hold 梯子>`）：底艙平台後段 x 101–126、前後兩道牆、前牆中線門 5 寬 1.5 m 高；固定點 blast（115,96,28）、door（127,96,22）。8 個火藥桶（憲法號共用桶 ×0.2）。
- 艙蓋（莫尼特號 `-hatch` 照開口縮放，kind=door）：主艙口、前艙口（船腰露天；低乾舷 ⇒ Ship_Fittings §9.7 露天出入口都該有門）。
- 爐灶（光榮號 `-galley` ×0.33，kind=galley）：艏樓底下炮甲板左舷（艏樓淨高 15 格 ⇒ 縮小）；匯入檢查：廚師 1 位、站得住的面 4 ✓。
- 絞盤（餘燼號 `-capstan` ×0.16）：後甲板底下炮甲板中線 x 116。
- 讀數：13 個模型碰撞 0、問題 0；組裝件 1 元件、空腔 0、鏡像差 0。

## 步驟 11 舵與錨（2026-10-26）
- `draft_rudder_anchor.py`、`tools/build_rudder_anchor.py`（照抄收穫號改）：舵子作品 `-rudder`（1,371 格，沿艉柱、z 0–56、前緣兩側削 1 格）掛成模型 `舵`：kind=rudder、hinge (58, 96.5, 0)、axis (−0.191, 0, 0.982)、max 35°、spin=rudder ±35°；stock-top (45,96,56) 離船殼 2 格。
- 不放舵輪（1660 年代 whipstaff；匯入檢查「操舵」：舵令 ⇒ 舵柄在舵上 ⇒ 舵 100%）。
- 錨：憲法號共用錨 ×0.55（兩舷，rz ±69.5、離船殼 1.2 m）＋錨架托板 `-anchor-gear`（1,260 格）；船殼固定點 hawse-S／P (298, 116／76, 50)。

## 步驟 12 砲門蓋板（2026-10-26）
- `tools/portlids.py`（照抄 basecamp 的通用工具，船表只有本船、顏色：朝外木色 177、內側紅 192、鉸鏈板黑 36）：炮甲板 16 片（後甲板 saker 從舷牆上過、§9.12 不做）；蓋板子作品 `-portlid` 9×9×2。
- 🩸 第一次 check：開著的蓋板撞船 576 個取樣點 —— 水平伸出去碰到炮門正上方的 channels ⇒ channels 改成舷頂那一列、1 格厚（並且 channel 高度照實際船殼最上一列量，⛔ 照設計的舷頂線：前桅最後一個 deadeye 那一欄量不到船殼、落在中線浮空 2 塊）。
- 讀數：開著碰船 0、碰砲 0；關上碰縮回的砲 0、落進船殼最多 0.55%、開口全蓋住；house 9–10、close 79–86°；反向對照 house 0 ⇒ 16 片碰砲、P 舷改 mirror=y ⇒ 8 片往上關。收砲時砲尾碰到船內 79 個取樣點（只是畫面，照實留著）。

## 步驟 14（前半）匯進 Blockside（2026-10-26）
- Blockside 自己的 worktree（`erina/oxford`，從 heads/dev 開；_cache 先從共用的複製過去）：`admin.py import --work erina-oxford-01m-assembly --id oxford --name 牛津號`；`game.json` 只多一列（沒有整份重排）。
- geo：spar [40, 72]（船腰炮甲板＋後甲板＋艏樓）、marines [112, 50]、center 60、aim 45、aimZ [10, 300]、deckAim [42, 56]、rigAim [120, 300]；crew：officers 2、marines 8、marineGap 12、navigator 0（沒有舵輪）。
- `admin.py ids --id oxford`：64 件（gun-1…22、yard-1…10、powder-1…8、anchor-1／2、ladders-1…4、deck-1…5…）；hoist 換成 id。
- 匯入檢查一路修下來（✗ 0 不變，⚠ 25 → 3）：
  - 🩸 break 艙壁的門開在兩舷（|dy| 18）⇒ 門前是梯子與砲、走出來是死角 ⇒ 門改開中線。
  - 🩸 第 7、8 門只隔 2.0 m ⇒ 砲班 2／3 ⇒ 炮門 200／224（間距 24）。
  - 🩸 單一間火藥庫 ⇒ 遊戲把取用點擺在火藥庫前後 1.6 m、夾在兩門砲中間，桶把取用點圍死（16 門走不到）⇒ 底艙梯挪到後甲板底下、火藥庫 `hoist` ＝ 這座梯子（火藥從艙口吊上來）、拿掉那片艙蓋 ⇒ 22／22。
  - 🩸 後桅樓 r 7 ⇒ 桅頂水手站不下 ⇒ r 10。
  - 試過把後甲板炮門往前挪（102／124／146）⇒ 後甲板前取用點被擠到艏樓梯頂 ⇒ 挪回 74／104／134。
  - 🩸 `build_guns.py` 重掛砲時 meta 整份覆寫 ⇒ 會洗掉 ids 發的 id ⇒ 改成保留原本的 id。
- 剩下的 ⚠ 3（都看過）：
  1. 送藥手 10／11：炮甲板最後一對（x 73、船長室）船尾窄，兩門砲尾只差 1.4 m，中線 ±0.9 m 站不下人 —— 船形本身，照實留著（那一對靠砲旁藥箱）。
  2. 底艙梯腳被取用點的火藥桶擋住、3. 後甲板梯頂前面有取用點的桶 —— 桶是遊戲擺的（23_powder.js），規格寫明雕刻作品不用改。

## 給遊戲那側填 geo 用的高度（到這一階段）
- 水線 z 33；炮甲板（第一層空氣）船中 z 41、船尾 z 50、船頭 z 47；後甲板 z 60–70；艉樓 z 81–87；艏樓 z 62–65；底艙平台 z 22。
- 船殼 x 39（船尾板）～ 309（艏柱）；艏斜桅（之後）尖到 x 377。

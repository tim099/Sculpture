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

## 給遊戲那側填 geo 用的高度（到這一階段）
- 水線 z 33；炮甲板（第一層空氣）船中 z 41、船尾 z 50、船頭 z 47；後甲板 z 60–70；艉樓 z 81–87；艏樓 z 62–65；底艙平台 z 22。
- 船殼 x 39（船尾板）～ 309（艏柱）；艏斜桅（之後）尖到 x 377。

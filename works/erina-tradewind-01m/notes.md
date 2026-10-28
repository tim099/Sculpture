# 信風號（雙桅帆船 brig，150 噸級商船）—— 建造筆記（0.1 m／格）

委託：Tim 2026-10-29（TASK-0964 → TASK-1097）：「那開單 造一台brig吧 交給妳了 GO」。
為什麼：《Blocksail》船隊的「雙桅帆船」`brig`（150 噸、開場發的那一型）一直借炎羽號（kiara-phoenix，624 噸、32 門砲的巡防艦）來畫；造一艘真的 brig 換掉它。
驗收（TASK-1097）：① 造船資料（查得到的附出處、推的標明；brig 在 1666 年偏早照實寫）② 雕好照造船規格匯入 Blockside（開得動、帆與砲位能用；反向對照：照吃水與全長停不進太小一級的泊位）③ 接進 Blocksail：`FLEET.types.brig` 的 hull 換成它（key 不動）④ Tim 看過一次；再加 Ship_Steps 步驟 1–11、14、15（刪 12 砲門蓋板：砲在露天甲板從舷牆砲門打；刪 13：木造帆船）。
造船步驟：`senate cmd doc --arg op=show --arg name=Ship_Steps`。

## 範圍
- 外部完整；內部只做遊戲用得到的大致構造（甲板、艙口、梯子、火藥庫、貨艙）—— 照牛津號（erina-oxford-01m）的範圍。
- 設計程式從牛津號 `erina-oxford-01m/design/` 整套抄來改（每支檔頭寫了出處）；牛津號又是從收穫號（calli-cosecha-01m）抄的。`design/plan_oxford_ref.json` 是牛津號的參數，只拿來對照，⛔ 不被程式讀。

## 座標與比例（步驟 2）
- 0.1 m／格；框暫定 448 × 192 × 384（資料回來再照全長、帆桁長調；調尺寸免費、不縮放內容）。
- x 船長、船頭朝 +x；y 船寬、中線格 y 96（鏡像 y ↔ 192 − y；P 舷 y < 96）；z 0 ＝ 龍骨底面。
- 作品：組裝件 `erina-tradewind-01m-assembly`「信風號」（主作品，關聯 `船殼` at 0,0,0）；船殼 `erina-tradewind-01m`「信風號 船殼」（任務作品、tags sub、委託 ref TASK-1097、領薪 10）。兩件都記了 meters_per_voxel 0.1。子作品之後照牛津號：用整船的框、關聯 at 0,0,0、tags sub、parent_work ＝ 船殼。

## 現有元件（步驟 2；`work sub=components` 2026-10-29 查的，引用前再查一次 meta）
- 砲：`pinnacle-patache-01m-gun-4l`（4 磅、gun:4l）、`summit-stormkaap-01m-gun-6l`（6 磅、gun:6l／4l）—— 等資料定砲種。
- 火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`；錨 `basecamp-frigate-constitution-01m-anchor`；絞盤 `basecamp-ember-01m-capstan`；舵輪 `basecamp-frigate-constitution-01m-wheel`＋`-wheel-stand`（要不要舵輪看年代）；羅經櫃 `summit-night-falcon-01m-binnacle`；小艇 `basecamp-ember-01m-boat`；門 `gura-pinas-01m-door`；燈 `gura-tridente-01m-lantern`；廚房 `gura-pinas-01m-galley`／`kaguya-gloire-01m-galley`；艙蓋 `meadow-monitor-01m-hatch`。
- 帆桁：方帆桁縮放風暴角號／憲法號的元件；主帆的斜桁、帆杆 `gura-tridente-01m-yard-mizzen-gaff`／`-boom`（飛魚號也用）。

## 階段一 造船資料與新圖紙 01／02（步驟 3；2026-10-29）
- 資料：`references/research_brig_2026-10-29.md`（研究代理查的；〔源〕〔二手〕〔推〕三種標記，398 行）。
  - **原型：英國船廠運輸船 Supply（1759，Thomas Slade 設計）**。〔源〕RMG 原圖 ZAZ5427（線圖、尺寸表：甲板 78 ft 6 in、龍骨約 64 ft 4½ in、寬 22 ft 2 in、艙深 11 ft 6 in、168 20/94 噸）、ZAZ5429、ZAZ5430（各層甲板）；〔二手〕Winfield 建成 79 ft 4 in × 22 ft 6 in × 11 ft 6 in、龍骨 64 ft 11 in、174 76/94 噸；原始編制 14 人（＝ 遊戲佔位值）；4 門 3 磅砲＋6 門 ½ 磅旋轉砲。
  - **桅桁：〔源〕Steel 1794 p.52「BRIGS, 150 TONS」商船表**（Supply 沒有桅桁數字）；brig 沒有主橫帆（「no main-yard, but a cross-jack-yard」），主帆是 gaff＋boom 縱帆。
  - **年代**：有原圖的 150 噸級 brig 最早是 1759（Supply）；兩桅都掛橫帆的 snow 約 120 噸 1702、150 噸以上 1732；1666 年的加勒比找不到任何 150 噸雙桅橫帆船（那時兩桅商船是 10–70 噸的 ketch）⇒ 開局就有 brig 是刻意的時代錯置（`from` 要不要加由 Tim 定）。
  - 〔推〕低信心：吃水（取 3.2 m）、舷牆高、砲門位置、艉窗、後甲板與艏樓的長度與高度（在原圖上量）。
- 新圖紙：`design/plan.json`（每個數字的 src）、`lines.py`（照牛津號的線形模組，參數換成 18 世紀中葉英國運貨船：底平、圓舭飽滿、中段長、tumblehome 小、艉柱倒 5°）、`layout.py`（兩桅、帆桁 z 照桅的各節算、gaff＋boom、艏斜桅＋三角帆桿、艏帆兩面）；`draft_lines.py` ⇒ `sheet01_lines_v1.png`、`verify_lines.json`、`masks/hull/hull_01.vox.txt`；`draft_layout.py` ⇒ `sheet02_layout_v1.png`、`verify_layout.json`。
  - 遊戲砲種表沒有 3 磅舷側砲（只有 3 磅追擊砲）⇒ 舷側砲用 4 磅（long4）〔設計〕；旋轉砲用 pierrier。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 甲板長（z 45，艏柱到艉柱） | 24.18 m（79.32 ft） | 〔二手〕建成 79 ft 4 in |
| 龍骨 | 19.80 m（64.96 ft） | 〔二手〕64 ft 11 in |
| 最大寬 | 6.90 m（69 格，22.64 ft） | 〔二手〕22 ft 6 in |
| 設計水線 | z 32（吃水 3.2 m） | 〔推〕平均 10.5 ft |
| 排水量（水線下實心 × 1.025） | 290 t | 174 噸 bm 的 1.7 倍（滿載貨船的量級） |
| 主甲板（第一層空氣） | 船中 z 45；舷弧船尾 +0.8、船頭 +0.6 m | 〔源〕艙深 11 ft 6 in |
| 炮門下緣離水線 | 1.60 m（x 124、206） | 〔設計〕 |
| 桅頂離甲板 | 主 25.2 m、前 24.0 m | 〔推〕研究推 25.0／23.8 m |
| 艏斜桅＋三角帆桿 | 仰 16°；艏斜桅尖 (356, 77)、三角帆桿尖 (405, 91) | 〔源〕32 ft／26 ft 7 in；〔推〕仰角 |
| 主帆杆 | 離舷頂最少 1.0 m、伸出船尾 0.6 m | 〔源〕34 ft |
| 帆面積（攤平 8 面） | 432 m² | — |

- 讀數：線形 1 元件、空腔 0、鏡像差 0；兩支 draft 重跑逐位元組相同；**反向對照**：`--probe=half_beam=+3` ⇒ 全寬 69 → 75、各站 +2～+3；`--probe=port=gun:1:+3` ⇒ 砲門淨距 77 → 80。

## 階段二 船殼落格（步驟 4 前半；2026-10-29）
- 標記 `船殼` begin（upto=start）→ `tools/stamp_lists.py erina-tradewind-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 114,720 ＝ 清單）→ `船殼` end。（另有一個 point 標記 `船殼` 是第一次打錯參數留下的，無害。）
- 結果帳（`tools/check_hull.py`，作品從 export 讀）：114,720 ＝ 設計，缺 0、多 0、色差 0；線形對照 465 點差 0；**反向對照** `probe_x=180` ⇒ 報 18 點、最大差 3。
- 結構（引擎 stats）：1 元件、空腔 0、鏡像差 0。組裝件關聯 `船殼` meta `kind=ship, waterline_z=32`。

## 階段三 炮門、塗裝、船尾窗（步驟 4 後半；2026-10-29）
- `draft_ports.py` ⇒ `masks/ports/carve.vox.txt`（600，帶刻之前的顏色守門）、`paint.vox.txt`（10,301，換色）、`glass.vox.txt`（100，步驟 6 用）、`verify_ports.json`、`sheet03_ports_paint_v1.png`；落格：標記 `炮門塗裝` begin → carvevox 600 → stampvox overwrite=1 10,301 → end。
- 炮門：每舷 2（x 124、206；0.5 m 見方、下緣在甲板上 0.3 m；外擴一圈紅框）；船尾窗 4 扇（後甲板底下船長艙、窗洞整段牆刻穿）。
- 塗裝〔源〕RMG SLR0581：水線上木色 177、兩條黑 wale 36（主甲板下 0.5–0.6、0.1–0.2 m）、舷頂下兩列淡灰藍 146、舷頂黑、舷牆內側（最上面那一層甲板以上的內板）紅 192、水線下灰白 182；船尾 wing transom 黑、以上木色、窗框灰藍。
  - 跟牛津號不同：舷頂照每一欄實際最上一格（牛津號照 top_z 四捨五入，小數那幾欄的黑舷緣會漏）。
- 讀數（`tools/check_stage3.py`）：結果帳 114,120 缺 0、多 0、色差 0；炮門開口裡實心 0；**正向對照**（同一把尺量 `船殼:end`）4 個全報；**反向對照** `--probe=skip_port=gun:2` ⇒ 只報那一門兩舷；stats 1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq}.png`。

## 階段四 甲板、艙口、break、梯子（步驟 5；2026-10-29）
- `draft_decks.py` ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`（子作品 `-deck-<層>`、`-ladders-<層>`，關聯 `甲板-<層>`、`甲板-<層>/梯子` meta kind=ladders）。
- 甲板（板面 z）：底艙平台 22（x 60–135，火藥庫）、**船長艙 ＝ 主甲板 − 8**（x 46–109）、主甲板 45（船中；舷弧船尾 +8、船頭 +6；x 110–294）、後甲板 ＝ 主甲板 ＋11（x 44–109）、艏樓 ＝ 主甲板 ＋11（x 250–296）。橫樑每 12 格。
  - 〔推〕後甲板只比主甲板高 1.1 m ⇒ 底下的船長艙若跟主甲板同高只剩 1 m 淨高 ⇒〔設計〕地板往下沉 0.8 m（sunk cabin），淨高約 1.6 m。
- 艙口：主艙口 x 170–196（半寬 8）、前艙口 222–232；桅孔照桅軸；break 兩道：後甲板前緣 x 109（艙壁從船長艙地板到後甲板，門開在中線、門檻 ＝ 主甲板面 `door_from`）、艏樓後緣 x 250。
- 梯子 7 座：hold（**貨艙梯子**，梯腳踩艙底，在主艙口裡往前爬，Ship_Decks §9.3 ⑥）、orlop（底艙平台 ⇄ 船腰，梯井開在後甲板前緣前面）、cabin（船長艙 ⇄ 船腰，穿過 break 的門，兩階）、qd-P／S、fc-P／S（|dy| 14）。每層都有梯子通到。
  - 牛津號的程式改了三處：梯子 lo 可以是 `hold`（中線那一柱船殼內板的頂）、break 的門可以從另一層的高度開、梯子點的頭頂只量 foot／head 1.2 m（§9.3 ②；牛津號四個點都量 1.4 m ⇒ 船長艙那座的 hi 被誤報）。
- 讀數：結果帳 8 件 31,768 格缺 0、多 0、色差 0、重疊 0（`tools/check_decks.py`）；梯子點（組裝件 parts）28／28、差 0、問題 0；組裝件 1 元件、空腔 0、鏡像差 0；炮門往艙裡被擋 0；draft 時的封閉空腔 0（沒有要填的）。
- 甲板 meta：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（代號 orlop／cabin／main／quarter／forecastle、名字照 plan 的 names 改）⇒ `work sub=meta file=`（5 筆）。
- 預覽 preset `藏船殼`。過程圖 `overlays/stage5_decks_nohull.png`。空艙房沒標（遊戲用不到時可以之後加）。

## 步驟 6 裝飾（2026-10-29）
- `draft_deco.py`（整支改寫：牛津號是 beakhead 平台＋獅子）、`tools/build_deco.py`：船首 `-head`（knee of the head 從水線下 z 26 彎到 z 54、往前 1.3 m，前緣一條黑；**渦卷 scroll** 0.7 m 金底黑螺旋 1.5 圈；兩舷 head rail 黑、6 連通；固定點 bobstay-1）、錨架 `-catheads`（艏樓舷牆頂下、往前斜 25°、伸出舷外 1.2 m；固定點 cat-S／P）、船尾窗玻璃 `-stern-glass`（100 格，4 扇各自 6 連通一整片、後面是船長艙的空氣；關聯 meta material=glass）。
- 〔源〕RMG：Supply 是 scroll head、沒有人像。〔設計〕不立船尾旗桿：主帆杆伸出船尾 0.6 m，旗桿會撞到 ⇒ 船旗掛斜桁尖（步驟 8）。船名板沒做（1786 年以前英國商船船尾不用寫船名）。
- 讀數：落在船上不放的 263／20 格；件與件重疊 0；組起來 1 元件、空腔 0、鏡像差 0；艏斜桅＋三角帆桿那條線（半徑 ＋1）裡的裝飾格 0 —— v1 渦卷頂 z 55 有 3 格貼著 ⇒ knee 頂降 1 格；**反向對照** `--probe=shift=scroll:6` ⇒ 63 格。
- 過程圖 `overlays/stage6_head.png`。

## 步驟 7 桅與帆桁（2026-10-29）
- `draft_masts.py` ⇒ `masks/masts/<桅>.vox.txt`、`masks/bowsprit_hole/`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`（牛津號那支刪掉後桅與三角帆桁）。
- 桅（子作品 `-mast-main／fore`，關聯 主桅／前桅）：下桅＋桅樓（r 11，2 格厚＋外緣矮欄黑頂）＋上桅（在下桅頭前面 doubling）＋頂桅；每節頂一個黑 cap；上桅頭十字桁。桅頂離甲板：主 25.2、前 24.0 m（〔源〕Steel 150 噸 brig 表）。
  - 🩸 v1 桅腳 z 8／10 懸空：船殼只是 3 格厚的殼、中線是一條 V 形槽（沒有 keelson），甲板桅孔 r 3 又比桅（r 2.1）大一圈 ⇒ 整根桅跟船不相連 ⇒ 桅腳往下伸到龍骨頂（主 heel 4、len 187；前 heel 8、len 167），甲板以上高度不變。
- 艏斜桅（`-bowsprit`）：根部 (262, 50)、仰 16°、9.8 m；**三角帆桿**疊在艏斜桅上面（同一件子作品，軸線往上平移兩個半徑）、伸到 (405, 94)；艏斜桅尖一個黑 cap 箍住。開孔：船殼 32 格＋主甲板 4 格（carvevox 帶顏色守門、標記 `艏斜桅孔`，孔由艏斜桅填滿）。
- 帆桁 8 根（外部模型，掛在各自的桅子作品裡）：方帆桁 6 根照 Ship_Setup §2.1 引用風暴角號（summit）元件等比縮放（main crossjack ×0.943〔yard=crossjack、sail=main-topsail：brig 沒有主橫帆〕、main topsail ×0.740、main topgallant ×0.831、fore course ×0.531、fore topsail ×0.820、fore topgallant ×1.123）；**主帆 gaff ×0.367、boom ×0.753 引用三叉戟號（gura）元件**（元件本來就斜：gaff 約 34°、boom 約 3°；pivot 在主桅軸心、jaws 高度 160／78；sail=mainsail，照飛魚號的寫法）。
- 讀數：組裝件 1 元件、空腔 0、鏡像差 0、link_overlap 0；models_broken 0。過程圖 `overlays/stage7_masts.png`。

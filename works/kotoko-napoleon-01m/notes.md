# 拿破崙號（Le Napoléon，1850）—— 螺旋槳蒸汽戰列艦，兩層砲甲板 90 砲（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-15（TASK-0605 傘，子單 TASK-0606～0615）：「然後接著 按照遊戲規格準備造船吧 拿破崙號 請參考圖紙與歷史資料建造 有資訊不足的地方交給妳設計 另外圖紙也是參考歷史圖紙再由妳重畫」。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫、機艙這些遊戲用得到的大致構造。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 座標約定
- 空間 1200×400×800；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 200 格**，鏡像 y ↔ 400 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 200。
- 「在不在船裡」：|y − 200| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱；遊戲取船寬中心 size/2 ＝ 200。
- 0.1 m／格（書卡 meters_per_voxel 已記）。

## 設計方向（開工時的決定）
- 原型 Le Napoléon（Toulon 1850 下水，Dupuy de Lôme）：第一艘一開始就設計成螺旋槳推進的戰列艦。
- 圖紙：參考歷史圖紙與史料「重畫」，不描圖 —— `design/plan.json` 是設計來源，每個數字標出處或設計決定。
- 管線結構照三叉戟號（`gura-tridente-01m/design`：`hull_lines.py`、`layout.py`、`plan_io.py`、`draft_lines.py`、`draft_layout.py`、`tools/wio.py`、`tools/stamp_lists.py` 抄過來改，檔頭註明）—— 尺寸最接近的一艘（三叉戟號 61 m × 16.3 m）。
- 沿用現成零件當模型：砲、舵輪、火藥桶、燈、羅經櫃、絞盤、小艇、帆桁（`work sub=components`）。煙囪、螺旋槳、船首像、船尾裝飾是這艘船自己的。

## 階段一 新圖紙 01／02（2026-10-15，TASK-0606）
查證：兩個獨立研究 agent 並排 ⇒ `references/research_napoleon_2026-10-15.md`（本艦：Shipscribe／Winfield & Roberts、WP、Navypedia、Commons 圖像）、`references/research_french90_2026-10-15.md`（同期：Algésiras 姊妹艦、Suffren／Hercule／Jupiter 級、Fincham 的法國帆桁比例、早期蒸汽艦）。互相不同意的照列（長 71.46 deck／71.23 WL／73／77.8 m；寬 16.22 moulded／16.80 extreme／17 m；帆面積 2,852 vs Algésiras 2,010 m²）。
歷史圖紙：**本艦的原始圖紙不在網上**（NMM Greenwich FORB0004 三張只有目錄；CNAM 4 Sa 29 的 1853 年 Dupuy de Lôme 說明書文字層壞了）。能用的「圖」是 Toulon 兵工廠照 Dupuy de Lôme 圖紙做的 1/50 模型（MnM 23 MG 8）的正側面照片 ⇒ 我在瀏覽器裡逐像素量（`references/model_photo_readings_2026-10-15.md`），再加 c.1860 實船照片、Le Breton 1850 石版畫看塗裝。圖紙照這些**重畫**，不描。

設計 `design/plan.json`（每個數字的 `src`：參考資料附出處／設計決定；`refs` 是縮寫表）；程式（抄三叉戟號、檔頭註明）：
- `hull_lines.py`：線形 ⇒ 每個 (x, z) 的半寬。改了三處：① 艏柱圓弧只走到切線斜率 ＝ 前傾角那一點再接直線（原版走到垂直再接斜線 ⇒ 側面有一個折角，第一版圖上看到的）；② 船尾 deadwood 開螺旋槳 aperture（艉柱往前 5 格起、30 格長、z 14–70）；③ **圓船尾**（`lines.round_stern`：水線以上俯視收成半徑 7.5 m 的圓弧，z 82 → 114 從細的 run 換過去）—— 階段二渲出來才加的，見下。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`verify_lines.json`、`masks/hull/hull_01..05.vox.txt`（船殼清單，at 0,0,0）。船殼 ＝ 線形實心往裡留 4 格牆（外板 1、肋骨 141 ×2、內板 177）；外板水線 z 79 以下銅 168、以上黑 36。
- `layout.py`＋`draft_layout.py` ⇒ `sheet02_layout_v1.png`（側面：白帶、砲門三層、甲板、桅帆外框、煙囪、螺旋槳、舵；正面；俯視）、`verify_layout.json`。

| 項目 | 讀數 | 史料 |
|---|---|---|
| 甲板長（下砲甲板 z 90 量） | 71.50 m（715 格） | 71.46 m on deck（SS） |
| 最大寬（含外板） | 16.9 m（169 格） | 16.80 m extreme（SS；格數只能奇數） |
| 設計水線 | z 79（7.9 m） | mean draught 7.86 m（SS） |
| 排水量（水線下實心 × 1.025） | 5,121 t | 5,120 t（SS） |
| 龍骨 | 63.06 m | 沒查到 |
| 船殼牆（v2，圓船尾） | 1,114,104 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（船中 z，舷弧往船尾 +5、往船頭 +4）：faux-pont 67（x 180–860，**機艙與鍋爐 x 330–650 不鋪**）、下砲甲板 90、上砲甲板 113、上甲板（gaillards 接成一層）137；舷頂船腰 z 155、船尾 168。下砲甲板砲門下緣 z 96 ＝ 離水線 1.7 m（同期 Hercule／Suffren 2.0 m，SS113）。
- 砲門每舷 18／15／12（1852 年配置：36＋30＋14 門 16 cm ＋ 10 門 carronade ＝ 90）；間距 3.5 m（模型量的）、上下兩層錯開；追擊砲沒查到、不開。
- 桅：位置照模型（mizzen 244、main 460、fore 757）；帆桁照 Fincham 的法國比例 × Jupiter 甲板長（SS：拿破崙號用 Jupiter 的帆裝）—— main course 33.8、topsail 24.3、topgallant 17.2 m；fore × 0.9；桅長是設計決定。主桅頂離水線 53.9 m。
- 煙囪兩根（SS：法國戰列艦唯一兩根）：x 406（主桅後）、x 615（主桅與前桅之間），半徑 1.1 m、頂 z 205（離水線 12.6 m，設計決定）、離最低的方帆桁 61 格。
- 螺旋槳：固定式（SS）、3 葉（只有 militaryfactory，低可信度）、直徑 5.2 m（設計決定）、軸心 (x 178, z 42)，在 aperture 裡上下各留 2 格、前後 13 格。
- 外觀（之後的階段）：黑船殼、兩層砲列各一條白帶、黑砲門蓋（c.1860 照片）、水線下銅、黑煙囪、圓船尾。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 最大寬 169 → 175（每舷 +3）；站位 x 200／250／300／350／400 的水線半寬 23／52／71／81／83 → 24／54／73／83／86（+1／+2／+2／+2／+3，兩頭收縮 × 3 再取整；v2 線形重量）。
- `draft_layout.py --probe=port=lower:5:3` ⇒ 下砲甲板砲門間距 25–26 → 23／28。
- 產生程式重跑：9 個輸出檔（5 份船殼清單、兩張圖、兩份 verify）逐位元組相同。
- 過程圖：`overlays/stage1_sheet01_lines.png`、`overlays/stage1_sheet02_layout.png`。

⚠ 已知、之後的階段處理：
- 艏柱 z 87 以上在模型上是 knee of the head（往前凸）—— 船殼只做到艏柱直線，knee、head rails、船首像在階段五。
- 圓船尾的窗、quarter galleries 在階段三／五；舵是之後的模型（階段九，`kind=rudder`）。
- 模型的垂直比例不採（見 references 的讀數檔）：甲板高度是史料推＋遊戲需要。

## 階段二 船殼落格（2026-10-15，TASK-0607）
- 標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py kotoko-napoleon-01m 0 masks/hull/hull_01..05.vox.txt`（5 刀，每刀讀回 placed ＝ 清單格數）→ `船殼:end`。
- 🩸 **渲出來第一眼：船尾收成尖的，像獨木舟**（`overlays` 舊圖已覆寫；v1 只有三叉戟號的 transom_ratio，0.3 的平面收到一點點寬）。史料三份（SS113、模型、Le Breton）都說圓船尾 ⇒ `hull_lines` 加 `round_stern`（見階段一），船頭上半也從 2.2 飽滿到 3.0；排水量重調（2.32 ⇒ 5,219 t、2.21 ⇒ 5,121 t）。
  換船殼：標記 `船殼v2:begin` → `design/tools/delta_apply.py`（抄收穫號，作品對清單：多的帶顏色守門刻、少的貼、顏色不同的換）：刻 397,229、貼 431,333、換色 192,997，每刀讀回對上 → `船殼v2:end`。
- **結果帳**（`design/tools/check_hull.py`，作品那側從 `export format=list links=none mark=船殼v2:end` 讀）：作品 1,114,104 ＝ 設計 1,114,104，缺 0、多 0、色差 0。
- **結構**（引擎 `stats structure=1 mirror=y:200`）：1 元件、封閉空腔 0、鏡像差 0／0／0。
- **線形對照**：右舷外緣（每個 (x, z) 最大的 dy）vs `lines.hb` 取 floor，x 150..875 每 25、z 6..171 每 5，864 點、差 0。**反向對照**：設計那一站（x 400）+3 ⇒ 報 31 點（那一站每個高度）、最大差 3。
- **組裝件** `kotoko-napoleon-01m-assembly`「拿破崙號」：0.1 m、1200×400×800（parent 船殼，沒標 sub ＝ 主作品）；關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=79`。船殼標 `tags=sub`、名稱「拿破崙號 船殼」。
- 產生程式重跑（v2）：9 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage2_hull_{bowq,sternq,side,top}.png`（yaw 30／150／90／90 俯 85）。
- ⚠ 看得到的：船殼一整片黑（白帶、砲門在階段三）；艏柱是直線到舷頂（knee of the head 在階段五）；船尾 aperture 已開、螺旋槳與舵還沒放（階段五／九）；艙裡是空的（甲板在階段四）。

## 階段三 砲門、塗裝、圓船尾的窗（2026-10-15，TASK-0608）
設計 plan.json `paint`（加 `banded`、`band_overrun`、`glass`）、`stern`；產生 `design/draft_ports.py`（抄三叉戟號，檔頭註明）⇒ `masks/ports/carve.vox.txt`（32,291，帶刻之前的顏色守門）、`masks/ports/paint.vox.txt`（43,659，換色）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 砲門 ＝ `layout.ports`（每舷 18／15／12，兩舷同一組 x）：開口 (x, z) 範圍裡、那一舷 |dy| ≥ 6 的牆全刻。
- 塗裝（c.1860 照片：黑船殼、兩層砲列各一條白帶、黑砲門蓋）：下砲甲板與上砲甲板各一條白帶（砲門下緣 −2 到上緣 ＋3，照甲板舷弧；從第一個砲門前 14 格到最後一個後 14 格）；帶裡的砲門框一圈也白（開口看進去是暗的 ⇒ 白帶上一排黑方格）。上甲板的砲門不畫帶（照片那一層是黑的）。舷頂一條金（LEBRETON：欄杆 ochre）。
- 圓船尾的窗：下砲甲板 5 扇、上砲甲板 7 扇（寬 7、刻最外一格、第二格玻璃 87、外一圈金框；沒查到數量 ⇒ 設計決定）。
- 🩸 v1 兩處：① 舷頂金線拿「每一欄 (x, y) 最上面那一格」⇒ tumblehome 的外板每一欄都有自己的頂，側面畫出一圈圈金色等高線（圖紙上看到）⇒ 改成「每一站 x 牆最高那一層」；② 白帶照高度漆 ⇒ 圓船尾轉角那一段外板幾乎是水平的，從船尾斜上方看白帶底下一片白斑（stage3 sternq 第一版）⇒ 帶子只漆**朝舷外**的外板（往外那一格是空的），作品換回黑 442 格（`砲門v2`）。
- 落格：`砲門:begin` → carvevox（顏色守門，32,291）→ stampvox overwrite=1（44,101）→ `砲門:end`；修正 `砲門v2:begin` → `delta_apply.py`（作品對「船殼 − 刻 ＋ 換色」：換色 442）→ `砲門v2:end`。

讀數（`design/tools/check_stage3.py`，抄三叉戟號；作品從 export 讀）：
- **結果帳**：作品 1,081,813 ＝ 設計（船殼 − 刻 ＋ 換色），缺 0、多 0、色差 0。
- 90 個舷側開口（每舷 45）：**從作品的格子量**，開口往舷外看還有實心的 0 個。**正向對照**（同一把尺量刻之前的 `船殼v2:end`）⇒ 90 個全報（例：下砲甲板第 1 個每舷 658 格）。**反向對照**：`draft_ports.py --probe=skip_port=upper:4` ⇒ 只報 upper 第 4 個（兩舷各 360 格）。
- 帶子高度裡朝舷外的外板還是黑的：0；引擎 stats：1 元件、空腔 0、鏡像差 0。
- 換色：白 33,992、金 8,946、玻璃 721；刻掉：外板 8,513、肋骨 15,946、內板 7,832。
- 產生程式重跑：4 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage3_sheet.png`、`overlays/stage3_ports_{bowq,sternq,side,astern}.png`。
- ⚠ 看得到的：船尾四分之一那個角，上層白帶在圓弧上還看得到一點點（帶子繞進轉角），先留著；艙裡沒甲板 ⇒ 從砲門看得到對面的牆。

## 階段四 甲板、艙口、梯子、煙囪孔（2026-10-15，TASK-0609）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（抄三叉戟號；改：沒有 poop、faux-pont 只鋪前後兩段、煙囪孔）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`（抄三叉戟號）。`layout.py` 加 `funnel_hit`（煙囪截面；甲板開孔與之後的煙囪共用）。
- 甲板（甲板面 z，舷弧往船尾 +5、往船頭 +4）：faux-pont 67（x 180–860，**機艙與鍋爐 x 330–650 不鋪**）、下砲甲板 90、上砲甲板 113、上甲板（gaillards 接成一層）137。艙裡的甲板板 177、上甲板 250；橫樑每 16 格、寬 2、深 3（136）；圍欄 2 格（136）。
- 開口：艙口三個在中線（後 296–314、主 505–533、前 680–698，四層都開）＋圍欄；梯子井；桅孔（主 r 5、前 4.5、後 3.5；後桅腳立在 faux-pont 不開）；**煙囪孔**（x 406／615、r 11，下砲甲板、上砲甲板、上甲板三層 —— 鍋爐在下砲甲板以下的艙裡，設計決定）。
- 梯子 6 座（每 3 格一階、每階 2 格、踏板 7 寬）：faux-pont → 下砲甲板 後 x 250／前 x 720（落在前後兩段裡）、下 → 上砲甲板 後 340／前 548、上砲甲板 → 上甲板 後 362／前 640；避開艙口、桅、煙囪。
- 子作品（parent 船殼、tags sub、0.1 m、1200×400×800、at 0,0,0）：`-deck-{orlop,lower,upper,spar}`、`-ladders-{lower,upper,spar}`；梯子掛在它上面那一層甲板裡（關聯 `梯子`，meta `kind=ladders`），固定點 `<梯名>.foot／lo／hi／head`。組裝件關聯 `甲板-<層>`。
- **甲板 meta**（§9.3）：每層甲板子作品 `export format=vxk links=none` ⇒ `Blockside/src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成中文名）⇒ `work sub=meta`：kind=deck、deck、level 0–3、name、floor、thick 4。
- 預覽 preset（組裝件）：`藏船殼`、`只看下砲甲板以下`。
- 封閉空腔（設計那一側組起來找）：3 個共 203 格（舷弧取整在兩頭夾住的）⇒ 填進最近那一層甲板（橫樑色），照三叉戟號的作法。

讀數：
- 設計那一側：甲板／梯子跟船殼重疊 0、彼此重疊 0、每件鏡像差 0、梯子點問題 0。
- **結果帳**（`design/tools/check_decks.py`，每件從匯出讀）：7 件、480,119 格，缺 0、多 0、色差 0。
- **組起來**（引擎 `stats structure=1 mirror=y:200`，組裝件）：1,561,932 格（＝ 船殼 1,081,813 ＋ 甲板與梯子 480,119 ⇒ 重疊 0）、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 `export format=parts`，遊戲讀的那一份）：6 座、24／24 點、跟設計（格心）差 0；每個點那一格是空的、腳下實心、頭頂 14 格空。
  **反向對照**：`draft_decks.py --probe=drop_ladder=fore-spar` ⇒ 5 座、少的正是 fore-spar。
- 產生程式重跑：10 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage4_sheet.png`、`overlays/stage4_decks_{nohull,bowq,sternq}.png`。
- ⚠ faux-pont 的 meta `floor` 是一條折線（194–854），遊戲看不出中間 330–650 是機艙、沒有地板 —— 匯進遊戲時跟 ame 對（TASK-0615）。

## 階段五 船頭、船首像、圓船尾陽台與船名、船尾燈、煙囪、螺旋槳（2026-10-15，TASK-0610）
設計 plan.json `deco`（knee、rails、figurehead、balcony、name、lanterns、funnel、screw；每一項 src）；產生 `design/draft_deco.py`（自己寫的；船的現況 ＝ 階段二～四的清單，那幾份跟作品逐格相同、各階段結果帳證過）⇒ `masks/deco/<部件>.vox.txt`、`deco_placement.json`（船尾燈）、`verify_deco.json`、`sheet05_deco_v1.png`；落格 `design/tools/build_deco.py`。
- **船頭**（`-head`，關聯 `船頭`）：knee of the head 沿中線 5 格寬（水線下 3 格），最多伸出艏柱 2.8 m（z 132–140），水線下銅、以上黑、兩側 trailboard 金（z 116–134）；head rails 每舷兩道（上金、下黑）從船頭舷側彎到船首像後面，中間 3 根 head timber。
- **船首像**（`-figurehead`，關聯 `船首像`）：沒查到 ⇒ 設計決定：**帝國鷹**（第二帝國；船名 1850 年由 24 Février 改成 Napoléon）—— 金色、身體橢圓、鉤喙、黑眼、翅膀往上往後張（span 2.6 m、後緣一根根羽毛），站在 knee 前端頂上；在中線 ⇒ 兩舷對稱。跟 knee 重疊的 284 格讓給 knee。離艏斜桅軸線最近 18.6 格（knee 17.6）。
- **船尾裝飾**（`-stern-deco`，關聯 `船尾裝飾`）：上砲甲板那一排船尾窗外一圈陽台（|dy| ≤ 50、伸出 7 格、地板 136、下緣黑、黑立柱每 3 格、金扶手；相鄰兩欄的扶手 x 不一樣 ⇒ 兩欄一起補中間那一段，鏡像才對稱）；**三盞船尾燈**（外部模型，沿用 `gura-tridente-01m-lantern`，scale 0.5、meta `kind=light`、pivot 8.5,8.5,0），站在 taffrail 上 dy −24／0／24。quarter galleries 不做（圓船尾兩舷是封閉的，設計決定）。
- **船名板**（`-name-board`，關聯 `船名板`）：「NAPOLÉON」3×5 字型＋É 的重音，金字黑底金框，z 148–157、|dy| ≤ 18，每一格貼著那一高度的船尾曲面凸出一格；從船尾看左手 ＝ −y（引擎：左舷 P ＝ −y）⇒ 第一個字在 y 最小那邊。字不對稱 ⇒ **這一件的鏡像差照實報**。
- **煙囪**（`-funnels`，關聯 `煙囪`）：x 406／615、外半徑 11、2 格厚的管子（中間空，下面通到機艙）、從下砲甲板地板一路到 z 205，頂上 2 格灰 73＋1 格 lip；用跟甲板開孔同一支 `funnel_hit` ⇒ 剛好填滿三層甲板的煙囪孔、跟甲板重疊 0。
- **螺旋槳**（`-screw`，關聯 `螺旋槳`）：固定式、3 葉、直徑 52（5.2 m）、軸心 (x 178, z 42)；葉片在 y-z 平面、厚 5 格（葉尖 3）、角寬照半徑表；hub 半徑 4、軸往前接到螺旋槳柱（aperture 前緣）；青銅 176。
- 🩸 設計時改的：① v1 knee 只伸出 2.0 m，船首像只能站在船頭舷牆頂上（sheet05 v1）⇒ knee 加長到 2.8 m、鷹往前 11 格往下 9 格；② 圖紙的「從船頭／船尾看」左右畫反了（引擎是左舷 ＝ −y，船名本身是對的）；③ 陽台扶手只往 dy+1 補 ⇒ 鏡像差 36 ⇒ 兩欄一起補 ⇒ 0；④ head rail 與 knee 夾出 2 格封閉空腔（x 894、z 149、兩舷各 1）⇒ 填進船頭（黑）。

讀數：
- **結果帳**（`design/tools/check_stage5.py`，每件從匯出讀）：6 件、46,760 格（船頭 8,566、船首像 3,238、船尾裝飾 1,813、船名板 370、煙囪 28,900、螺旋槳 3,873），缺 0、多 0、色差 0。
- 設計那一側：落在船上的不放（船頭 1,551、船首像 284 讓給 knee、螺旋槳 52 進螺旋槳柱）；部件之間重疊 0；除了船名板每件鏡像差 0。
- **組起來**（引擎 stats，組裝件）：1,608,692 格（＝ 1,561,932 ＋ 46,760 ⇒ 跟船重疊 0）、1 元件、空腔 0；鏡像差 20 對（全是船名板的字）—— `hide_links=船名板` ⇒ 0。
- 船尾燈：models_broken 0、三盞腳下是 taffrail 的實心、頭頂是空的。
- **反向對照**：`draft_deco.py --probe=shift=name:-3`（船名板往後離開船殼 3 格）⇒ 組起來 1 → 7 個元件；`--probe=shift=funnels:3` ⇒ 煙囪撞甲板 0 → 468 格。（probe 模式不讓位，所以讀數裡另有船首像跟 knee 的 284，那是設計本來就讓掉的。）
- 產生程式重跑：9 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage5_sheet.png`、`overlays/stage5_{full,bow,sternq}.png`。
- ⚠ 看得到的：船尾四分之一那個角，下層白帶在圓弧上還有一點零碎的白（帶子繞進轉角）；艏斜桅還沒放（階段六要穿過船頭舷牆，那時開孔）。

## 階段六 桅與帆桁（2026-10-15，TASK-0611）
設計 plan.json `masts_build`（截面、tops、crosstrees、艏斜桅、帆桁來源與 brace、spanker）；產生 `design/draft_masts.py`（抄三叉戟號；改：船的現況從本船清單組 —— 新增 `design/mio.py`、沒有 poop、帆桁不另做、沒有 spritsail、多一項帆桁掃線讀數）⇒ `masks/masts/{main,fore,mizzen,bowsprit}.vox.txt`、`masts_placement.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`（抄三叉戟號）。
- **桅**（每根一件子作品，關聯 `主桅`／`前桅`／`後桅`）：下桅（甲板那一段照 `layout.mast_hit` ⇒ 剛好填滿甲板桅孔、往上收到 masthead、每 12 格一圈黑箍）＋上桅＋頂桅（各在下一段前面）、top（2 格厚、前緣圓、黑邊）、trestletrees／crosstrees、caps、truck（白）。主桅頂 z 618（離水線 53.9 m）、前桅 571、後桅 499。
  主桅從 z 12 穿過機艙（沒有 faux-pont 的那一段）；前桅立在船頭 deadwood 上；後桅立在 faux-pont 的甲板面上（z 71）。
- **艏斜桅**（`-bowsprit`，關聯 `艏斜桅`）：根部 (845, z 146)、仰角 28°、20 m，jib-boom 15 m 疊在上面（從 70% 起）、caps、根部墊木到上甲板（261 格）。尖 x 1022、jib-boom 尖 x 1098（空間 1200 夠）。從船頭舷牆頂上過去 —— 船殼不用刻（清單 0 格），也不碰 knee、head rails、帝國鷹。
- **帆桁 13 根**（外部模型、放在各自的桅子作品裡）—— **沿用三叉戟號的帆桁元件**（造船規格 §2.1；三叉戟號是一級艦、主帆桁 34.7 m，跟本船 33.8 m 最接近），方帆桁只沿長度（y）縮放，固定點（arm、earing、jackstay、sling、pivot）跟著縮：

| 帆桁 | 長 | 來源（三叉戟號） | scale | brace |
|---|---|---|---|---|
| main course／topsail／topgallant／royal | 33.8／24.3／17.2／11.0 m | main-course 34.7／main-topsail 27.3／main-topgallant 17.1／main-royal 11.1 | y 0.974／0.890／1.006／0.991 | −20／−22／−24／−26 |
| fore course／topsail／topgallant／royal | 30.4／21.9／15.5／9.9 m | fore-course 30.5／fore-topsail 23.9／fore-topgallant 15.1／fore-royal 9.9 | y 0.997／0.916／1.026／1 | −20／−22／−24／−26 |
| mizzen crossjack／topsail／topgallant | 24.3／17.2／11.8 m | mizzen-crossjack 23.9／mizzen-topsail 17.1／mizzen-topgallant 11.1 | y 1.017／1.006／1.063 | −20／−22／−24 |
| spanker gaff／boom | 14.0／15.0 m | mizzen-gaff 15.0／mizzen-boom 13.5 | 等比 0.933／只沿 x 1.111 | 0 |

  meta `kind=yard、mast、yard、sail（帆名，階段七用；crossjack 沒有帆）、length_ft、length_m、diameter_in、pivot_anchor=pivot、turn_axis=z、rotate_z_deg`。spritsail 不掛（1850 年，設計決定）。
  boom jaws 抬到 z 188：過船尾時底在 taffrail 中線那盞船尾燈（頂 z 186）上面。
- 🩸 設計時改的：① 艏斜桅根部 v0 z 140 ⇒ 半徑 5 的底穿過上甲板 2 格 ⇒ z 146；② 後桅腳 v0 z 67 ⇒ faux-pont 在那裡因為舷弧是 z 69–70，桅腳穿過甲板板 39 格（讀數「撞到 mizzen 39」）⇒ z 71、下桅長 −4（桅頂不變）。

讀數：
- 設計那一側：四件跟船（含階段五）重疊 0、彼此重疊 0、甲板桅孔沒填滿 0、鏡像差 0、浮空 0、空腔 0。
- **帆桁掃線**：每根帆桁在 brace 角時 arm-P → arm-S（gaff／boom：pivot → peak／end）半徑 1.5 內碰到船、煙囪或別根桅：13 根全 0。
- **結果帳**（`design/tools/check_stage6.py`，每件從匯出讀）：4 件、91,139 格，缺 0、多 0、色差 0。
- **帆桁模型**（作品裡登記的 at／pivot／rotate／scale／meta vs `masts_placement.json`）：13／13、差 0；models_broken 0。**反向對照**：讀完作品之後把設計的 main-topsail at.z −3 ⇒ 只報那一根（作品 450.5 ≠ 設計 447.5）。
- `draft_masts.py --probe=main-course:-35`（brace 換角度）⇒ arm-S 走了 43.7 格。
- **組起來**（引擎 stats，組裝件，`hide_links=船名板`）：1,699,461 格（＝ 前面 1,608,692 − 船名板 370 ＋ 桅 91,139 ⇒ 重疊 0）、1 元件、空腔 0、鏡像差 0。
- 產生程式重跑：9 個輸出檔逐位元組相同（含 layout 圖重產）。
- 過程圖：`overlays/stage6_{sheet,full,side,sternq}.png`。

## 階段七 索具與帆（2026-10-15，TASK-0612）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（抄三叉戟號；改見下）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/{ensign,pennant}.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（抄三叉戟號）。
- **channels**（`-channels`，關聯 `channels`＋`channels-鏡像`（mirror=y），右舷一件）：每根桅一塊 12 格寬的板（上甲板 ＋ 17）、外緣一排 deadeye；5,310 格、跟船重疊 0。每舷 shrouds 主 8、前 8、後 6（80 砲 Jupiter 的帆裝，design），topmast backstays 2／2／1、topgallant backstay 1。
- **固定點 164**：桅上 hound／stay-head／futtock／tm-hound／tg-hound／top 邊（rim、rim-low）／crosstrees／top-aft；前桅 mainstay-foot、主桅 mizzenstay-foot；艏斜桅 forestay-foot／cap-top／jib-end／side／bob；船殼舷頂 belay（兩舷）與艏斜桅側索腳；**knee（`-head`）上的 bobstay 下端 2 個**。
- **繩 381 條**：shrouds 44、topmast shrouds 28、futtock 28、topgallant shrouds 12、backstays 16、stays 9、艏斜桅 4（bobstay 2＋側索 2）、ratlines 212（下 132、上 80，子繩）、sheets 24、tacks 4。色、粗、slack 照造船規格 §6／三叉戟號。
- **帆 15 面**：前、主桅 course／topsail／topgallant／royal（8）、後桅 topsail／topgallant（2；crossjack 不掛帆）、spanker（gaff＋boom）、fore-topmast-staysail（set 2）、jib、**船尾旗**（法國三色旗，藍白紅直條、旗桿那一邊藍，掛 gaff 頂）、**長旗**（主桅頂、藍白紅）。預設風 4.5,−1.5,0、4 秒。
- **meta**（§9.1）：帆 15（course、topsail、topgallant、royal、gaff、staysail、jib、flag ×2 ＝ ensign／pennant）、帆自己的繩 28（sheet／tack ＋ sail ＝ 帆名）。帆桁 meta 的 sail（階段六）都是某一面帆的名字。
- 改三叉戟號的地方（🩸 讀數抓到的）：
  ① **後桅 stay** 原本綁主桅腳 ⇒ 拉直的繩在後煙囪那裡 z 173，**穿過後煙囪**（頂 z 205）⇒ 改綁主桅 z 228（煙囪頂上 2.3 m）。前桅那邊的 main stay 在前煙囪上面 z 219，不用改。
  ② **bobstay**：v1 從 knee z 100–120 拉到艏斜桅 80–96%：繩貼在 knee 裡 106 格、穿過帝國鷹 25 格 —— knee 前緣比繩斜，從低處起的繩一定在 knee 裡；z 58–74 起也一樣 ⇒ 改從 knee 最往前那一段（z 128／131）拉到 97／100%，從鷹前面過；第三條（z 134）擦過鷹嘴 1 格 ⇒ 只留兩條。
  ③ 艏斜桅側索的船殼端 (880, z 150) 穿過船頭舷牆 10 格 ⇒ (905, z 161)。
  ④ 船尾旗的第 4 角寫在 gaff 模型的局部座標：本船的 gaff 是三叉戟號 gaff 等比縮 0.933 ⇒ 局部座標用來源元件的、旗高除以縮放。
- 新讀數「每條繩拉直的兩端連線碰到船上的格（兩端 3 格內不算）」：剩 fore-topmast-stay 2（艏斜桅 cap，離端點 3–4 格）、bobstay-1 2／bobstay-2 1（離開 knee 那一下，3.5–5 格）—— 都是綁點本身，照實留著。

讀數（`design/tools/check_stage7.py`，抄三叉戟號）：
- ① channels 結果帳 5,310 ＝ 5,310，缺 0、多 0、色差 0。
- ② 組裝件結果帳：設計 1,710,451（階段七之前 1,699,831 ＋ channels 右 5,310 ＋ 左 5,310）＝ 組裝件，缺 0、多 0、色差 0；鏡像 y 兩邊加起來都是 400。
- ③ 固定點 164（船殼 14、channels 30、主桅 38、前桅 40、後桅 33、艏斜桅 7、knee 2）：缺 0、多 0、位置不同 0。
- ④ 繩 381 ↔ 381、帆 15 ↔ 15：缺 0、多 0、欄位不同 0、meta 不同 0；預設風對上。
- ⑤ 帆自己的繩 28：沒有 meta 0、kind 錯 0、sail 錯 0；旗 2；帆沒有 meta 0（引擎 `work sub=meta part=sail`：meta_sail 15、without 0）。
- ⑥ 引擎：ropes 381（子繩 212）**broken 0**、ungrouped 0；sails 15 **broken 0**、帆自己的繩 broken 0。
- ⑦ 反向對照：拿掉 sheet 的 meta ⇒ 1；tack 的 sail 改錯 ⇒ 1；繩鬆緊 +0.01 ⇒ 1；帆一角釘／不釘對調 ⇒ 1（ensign 也 1）；channels 固定點偏 1 ⇒ 1；組裝件一格改色 ⇒ 1；鏡像那件 y 錯 1 ⇒ 缺 285、多 690。另：`draft_rigging.py --probe=nometa=main-topsail.sheet-P` ⇒ 只報那一條。
- 組起來（引擎 stats，`hide_links=船名板`）：1,710,081 格、1 元件、空腔 0、鏡像差 0。
- 產生程式重跑：5 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage7_{full,side,sternq}.png`、`overlays/stage7_ensign_texture.png`。

## 階段八 砲（2026-10-15 下午，TASK-0613）
Tim 2026-10-15：「接著 繼續造船直到完成吧（然後通知 ame 匯入遊戲內）」。設計 plan.json `guns`；產生 `design/draft_guns.py`（抄三叉戟號，檔頭註明；改：沒有追擊砲、每個砲門可以給自己的型、船頭船尾收窄的砲門照角度搜／墊高、落格之後可以重跑）⇒ `verify_guns.json`、`masks/guns/pads_{lower,upper,spar}.vox.txt`；落格 `design/tools/apply_guns.py`（pads／models）；讀數 `design/tools/check_stage8.py`（都抄三叉戟號）。
- **全部沿用現有砲元件**（造船規格 §2.1；一門一個外部模型，掛在所在甲板的子作品 `甲板-<層>/砲-S01`…，P 舷 mirror=y）：

| 層 | 每舷 | 史料（SS，1852 年配置） | 元件（遊戲代碼） | scale |
|---|---|---|---|---|
| 下砲甲板 | 18 | 30 磅 No.1／22 cm 砲 | 餘燼號 `-gun-long32`（32l） | 0.5 |
| 上砲甲板 | 15 | 30 磅 No.2／22 cm 砲 | 憲法號 `-gun-24`（24l） | 1 |
| 上甲板 | 12 | 16 cm 砲 14 ＋ carronade 10 | 風暴角號 `-gun-12l`（12l）× 7、憲法號 `-gun-carronade32`（32c）× 5 | 0.5 |

  - 上甲板哪幾個砲門放 carronade 沒查到 ⇒ 設計決定：兩頭（後甲板 1–2、艏樓 10–12；船頭收窄、carronade 短），16 cm 砲在船腰 3–9。
  - 合計 **90 門**（32l 36、24l 30、12l 14、32c 10）＝ SS 的 90。meta：kind=gun、gun、side、port、deck。
- 擺法（三叉戟號／風暴角號的做法）：對準砲門中線、從牆外往裡每 0.5 格退到零碰撞；排序 輪子全著地 ＞ 砲口伸出 ≥ 0.5 ＞ 置中。
  - 🩸 **本船加的：收窄的砲門照角度搜、還不行就墊高**。下砲甲板第 1 個砲門在圓船尾開始收的地方，砲架碰到砲門底下往裡斜的牆：正橫放砲口縮在牆裡 4–7 格，0°～45° 都出不去（32l、24l、carronade 都試過）⇒ 墊高 3 格（0.3 m 砲座）＋往船尾偏 20° 才出得去（砲口伸出 0.7）。上甲板第 12 門（carronade）往船頭偏 10°。其他 84 門正橫。
  - 🩸 角度條件第一版寫太寬（「不理想」就轉）⇒ 輪子懸空（墊木補得掉）的也被轉了，連船腰都歪 20°；改成只有砲口出不去才轉。
  - 墊木（甲板舷弧取整一階一階的 ⇒ 一側輪子懸空 1 格；照三叉戟號補甲板板色）：下砲甲板 158（含第 1 門的砲座 39×2）、上砲甲板 24、上甲板 52 格。
- 落格：三層甲板子作品標記 `階段八墊木:begin` → stampvox（placed ＝ 清單）→ `:end`；90 個模型（IOException 重試 0）。

讀數（`check_stage8.py`，只讀引擎的匯出）：
- ① 墊木結果帳：三層 begin ＋ 墊木 ↔ 現在，缺 0、多 0、色差 0。
- ② parts：砲 90 門，找不到 0、state 不是 ok 0、meta 不同 0；muzzle／breech 跟 draft 算的最大差 0.0003 格。
- ③ 碰撞（變換從引擎的固定點反推，殘差 0.0000；每格格心＋八角 vs 組裝件 links=all ＋ 其他模型外框 ＋ 別門砲）：0。④ 砲口在船殼外：沒伸出 0。⑤ 輪子著地：懸空 0。
- ⑥ **反向對照**（單子要的）：砲-S08@甲板-lower 往外推 3 格 ⇒ 碰撞 4,041 個取樣點；往船頭推 2 ⇒ 0；抬高 1 ⇒ 懸空 192／192；meta 改 gun=xx ⇒ meta 不同 1。
- 產生程式重跑（不用快取、從引擎重讀；藏後面階段的關聯、扣掉本階段的墊木、跳過已上船的模型）：verify_guns.json 與三份墊木清單逐位元組相同。
- 遊戲（Blockside 暫存副本的匯入檢查，見階段十）：**90 門站滿、缺 0 人**。
- 過程圖：`overlays/stage8_spar_guns.png`、`overlays/stage8_lower_guns.png`。
- ⚠ 砲具與砲索（環首螺栓、breeching、tackle）、rammer／sponge、shot garland 沒做（三叉戟號是後來另外幾個階段做的）。

## 階段九 彈藥庫、舵、甲板零件、艙房、錨、煙囪 meta（2026-10-15 下午，TASK-0614）
設計 plan.json `magazines`、`rudder`、`fittings`、`rooms`、`anchors`；產生 `design/draft_{magazines,fittings,rooms}.py`（抄三叉戟號）、`design/draft_rudder.py`（改自三叉戟號）、`design/draft_anchors.py`（自己寫的）；落格 `design/tools/apply_stage9.py magazines|fittings|rudder`、`apply_rooms.py`、`split_funnels.py`；讀數 `design/tools/check_stage9.py`。
- **彈藥庫兩間**（`-magazine-aft`／`-fore`，0.1 m、parent 船殼、sub；組裝件 `彈藥庫-後` @252,139,49、`彈藥庫-前` @716,140,30，meta kind=magazine、pos、powder_lb 11,500）：faux-pont 底下的貨艙，避開機艙與鍋爐（x 330–650）。
  - 後 x 252–294（後梯子之後、後艙口之前）：螺旋槳軸（z 42，hub 半徑 4）在底下 ⇒ 地板抬到 z 49、天花板就是 faux-pont（樑從天花板凸下來）；12,153 格。前 x 716–750（前艙口之後、前桅之前）：照三叉戟號地板 z 30、天花板 z 49；12,206 格。
  - 桶：照砲數換算（憲法號 54 門 138 桶 ⇒ 90 門 ≈ 230 桶，⚠ 不是史料），兩間各 115；後間全在地板層，前間地板 84 ＋ 上架 31（架 1,145 格）。火藥桶引用憲法號 -powder-barrel（scale 0.2、kind=powder、powder_lb 100）。固定點 blast、door。
- **舵**（`-rudder`，外部模型 `舵`，0.1 m、整船的框、世界座標，同收穫號）：掛在螺旋槳 aperture 後面的艉柱上；寬 2.0 → 1.7（水線）→ 0.7 m、厚 0.5／0.3 m；水線下銅、以上黑；pintle 帶。meta kind=rudder、hinge 160,200.5,1、axis（艉柱後傾 3°）−0.0523,0,0.9986、max_deg 35、turn_axis hinge；固定點 **stock-top** 153,200,103（旁邊 8 格內船尾格 672）。6,476 格。
  - 🩸 新加的尺「鉸鏈軸轉 ±15°、±35°，舵每一格的格心落在船裡幾格」第一版報 240：① 舵前緣是方的 ⇒ 一轉前角吃進艉柱；② 舵頂那一段掛在 counter 後面（前緣跟著 counter 往後挑）⇒ 一轉掃進 counter 兩側。改：前緣削斜角（離前緣第 k 欄只留 |dy| ≤ k）、舵頂停在 counter 開始往後挑的地方、pintle 帶離前緣 3 格起 ⇒ 0／0／0／0（draft 與 check 兩把尺都是 0）。子作品用 delta_apply 刻掉 794 格。
- **甲板零件**（掛 `甲板-spar`，沿用三叉戟號用的那幾件）：`舵輪`（憲法號 -wheel，kind=wheel）at 152,200.5,143（後桅後面；本船沒有 poop ⇒ taffrail 內面 x 134 前面留 0.9 m 給舵手站）、`羅經櫃`（餘燼號，kind=binnacle）at 168、`主絞盤`（餘燼號，kind=capstan）at 335（後艙口與後煙囪之間）、`小艇-S`／`-P`（餘燼號 cutter 9 m，kind=boat、boat=cutter、length_m 9）at 560,200.5±30。舵索 2 條（steering）。
  - 🩸 小艇 dy 17（三叉戟號）只放得進 x 470–477、騎在主桅兩邊壓到主艙口 ⇒ dy 30（坐在艙口圍欄外側），x 560。
- **faux-pont 艙房**（造船規格 §9.2；`-rooms-orlop` S 舷一件 12,162 格，`甲板-orlop/艙房` @229,221,69、`艙房-鏡像` @229,123,69 mirror=y，meta kind=rooms）：中線 |dy| ≤ 20 留走道；faux-pont 中間是機艙 ⇒ 前後兩段（切點 229／251／276／301／329、651／683／715／751／787／820，落在舷弧台階 ⇒ 地板平），每舷 9 間（2.1×1.1 m 到 3.5×4.6 m，高 1.9 m）。固定點 27（.min／.max／.door）。
- **錨**（造船規格 §9 anchor）：共用錨元件（憲法號 -anchor）縮 0.9 ⇒ 5.2 m，`錨-S`／`錨-P` 掛在組裝件（meta kind=anchor、anchor=bower），at 875,251／150,105.75、轉 ±120°（錨爪順著船頭弧面），錨環 z 130 貼著船頭；船殼登記 **hawse-S／P** 878,241／159,126（船頭外表面、上砲甲板那一層）。
  - 🩸 第一版錨環在舷頂外 > 8 格 ⇒ 遊戲（`10_ship.js`：錨的掛點 ＝ ring 旁 8 格內的實心）判「開場就掉」×2 ⇒ 搜尋加「ring 離實心 ≤ 5 格」。
- **煙囪拆成兩件**（`split_funnels.py`）：遊戲（`78_funnel.js`）一條 `kind=funnel` 關聯冒一股煙 ⇒ 階段五的 `-funnels` 拆成 `-funnel-aft`（14,512）／`-funnel-fore`（14,388），各登記 **smoke**（煙囪口中心 406／615,200,205），關聯 `煙囪-後`／`煙囪-前` meta kind=funnel、**material=iron**、render=smooth（照維吉尼亞號 ame-virginia-01m-funnel）；舊關聯 `煙囪` 拿掉（-funnels 那件留著、改名註明不再使用）。組裝件拆之前／之後缺 0、多 0、色差 0。

讀數（`check_stage9.py`）：
- ① 彈藥庫結果帳 兩間 0 差；② 組裝件 藏彈藥庫 1,735,009 ＋ 12,153 ＋ 12,206 ＝ 1,759,368，0 差、重疊 0。
- ③ parts：兩條彈藥庫關聯 meta（pos、powder_lb 11,500 ＝ 115 × 100）、blast 對；火藥桶 230／230 state ok；甲板零件 5 件 meta 不同 0。④b 零件格子級碰撞（位置從引擎外框反推）0（④ 外框這把尺對舵輪報 38 格 ＝ 舷弧台階那一階甲板板，格子級 0）。
- ⑤ 引擎：1,759,368 格、1 元件、空腔 0、link_overlap 0；模型 344 broken 0；繩 383 broken 0。
- ⑥ 反向對照：拿掉 `彈藥庫-前` 的 pos ⇒ 少 1 欄；加回 ⇒ 相同。⑧ **反向對照（單子要的）：拿掉羅經櫃的 kind ⇒ 報 ['羅經櫃']；加回 ⇒ []**。
- ⑦ 舵：結果帳 0 差、meta 相同、stock-top 對；轉 ±15°／±35° 落在船裡 0。⑨ 錨：state ok、meta 相同、固定點差 0.0001；hawse 對；碰撞 0、往船裡推 3 格 ⇒ 322。
- 產生程式重跑：彈藥庫、零件、舵、艙房、煙囪清單逐位元組相同（艙房的 verify 第一次跑時砲還沒上船 ⇒ note 的模型外框數不同、牆與框相同；現在這份重跑相同）。
- 過程圖：`overlays/stage9_{magazine_aft_open,magazine_fore_open,rudder_sternq,deck_fittings_aft,orlop_rooms,anchors_bow}.png`。

## 階段十 匯進遊戲的準備（2026-10-15 下午，TASK-0615）
- 匯出 `kotoko-napoleon-01m-assembly/exports/napoleon.vxk`（不進版控）：1,759,368 格、header checksum **2227734757**、sha256 ccc71331…；繩 383、帆 15、模型 344、meshes 61、parts 25、帶 meta 358、固定點 1,192、rig_skipped 空、材質 iron 28,900（兩根煙囪）、render smooth 28,900。
  - 當時發布版 `publish/senate.exe` 是 09:02 的（早於 646eb3a 材質匯出）⇒ 匯出的檔頭沒有 `materials`／`render`（格子與 checksum 相同）；這份是用 `src/Senate.Cli/bin/Debug/net10.0/senate.exe`（16:52）匯的。之後 ame 部署了 senate 988bf02（酒館 seq 24919：雕刻匯出會帶 material／render）⇒ 這條已經不是問題。
- **甲板 meta**（`decks.py` 重量四層甲板子作品）：跟階段四標的逐欄相同（墊木沒動到 floor）。
- **艙房**（遊戲那側 `rooms.py`，讀這份 vxk）：check 18 間全過（框裡實心 0、地板全實心、不重疊、都有門）；scan 獨立找到 18 間。反向對照：框往下 1 ⇒ 撞地板 19,488。
- **匯入檢查**（Blockside 複製到暫存、`admin.py import --work kotoko-napoleon-01m-assembly --id napoleon --name 拿破崙號`，⛔ 沒動 ame 的工作區）：**✗ 0、⚠ 1**（geo 沒填 ⇒ 遊戲那側填）。砲 90、站不滿 0 門缺 0 人、船員 567、模型 362（含陣營旗）、繩 383、帆 15（＋陣營旗 3）、桅 3、彈藥庫 2、甲板 4、梯子 6、艙房 18、錨兩舷 模型＋ring＋hawse、水線 79；材質 橡木 1,730,468 格 1,211 t、鐵 28,900 格 225 t。建置「還原驗算 9 艘逐個相同」、格子鏡射 diff 57 格（船名板）。
  - 第一次跑 ⚠ 5（geo、兩舷沒錨、沒 hawse）⇒ 補了錨（階段九）⇒ 錨第一版 ✗ 2 開場就掉 ⇒ 改 ⇒ ✗ 0。
- **反向對照**（單子要的）：甲板-spar 一格改色重匯 ⇒ checksum 2227734757 → 2562792970；改回 ⇒ 2227734757。
- 給遊戲那側填 geo 的高度（格，z 0 ＝ 龍骨底）：水線 79；甲板地板（第一層空氣）faux-pont 69–72、下砲甲板 91–96、上砲甲板 114–120、上甲板 138–144；砲口 下 102–107、上 125–129、上甲板 145–152；桅頂平台 主 304、前 288、後 278；帆頂（royal 帆桁）主 590、前 545；船殼 x 126–911（艏斜桅尖 1,022、jib-boom 1,098）、寬 y 116–284。
- 蒸汽：史料航速 12.14 kn 連續（1852-08-30 Toulon→Ajaccio）、13.86 kn（1852-09-25）、機器 900 nhp ⇒ 遊戲 `cfg.base`（額外動力）參考；螺旋槳在遊戲裡沒有對應（只是外觀）。
- ⚠ 還沒做（由遊戲那側）：正式匯入（`admin.py import`）、`ships[].geo`／`cfg`（航速、額外動力）／`crew`／`names`；faux-pont 的 floor meta 是一條折線（中間機艙沒有地板，遊戲照折線看不出來）。
- **正式匯入**（ame，Blockside d1815aa，酒館 seq 24949）：1,759,368 格、checksum 2227734757 對上；shipcheck ✗ 0 ⚠ 0、火藥取用點 6、90／90 門拿得到火藥；`cfg` 額外動力 12 節、靈活 1.2、硬度 4；geo 照本節的高度。ame 回的兩件：螺旋槳先當外觀（之後要轉再標 kind 與軸）；faux-pont 的 floor 折線不用拆（遊戲照格子切走路格，機艙那段自然站不了，前後兩塊 2,992／6,156 點各有梯子通上去）。兩根煙囪口下面各 996 格，會冒煙。
- 🩸 **遊戲的 bug（殉爆後 jib-boom 浮在空中，Tim 2026-10-15 截圖）**：Blockside 把格座標壓成一個整數 `x | y << 10 | z << 20`（`VK.pack`、`VK.detached`、10_ship／22_pieces／32_hull／75_shipcheck／90_main 共 13 處）—— x 只有 10 位元（0–1023）。本船 jib-boom 伸到 x 1,098，是第一艘超過 1023 的船（其他九艘的外框都在 1024 以內）。重現（暫存副本 `__game.ignite(0, 1, 'mag')`）：前彈藥庫殉爆、船在 x 733.5 斷成兩截，船頭那半截變成碎塊（227,292 格，x 739–1023）漂走下沉；x 1024–1098 那 725 格壓不進去、從打掉的格往外找走不到 ⇒ 留在船上、掛在空中。Tim 選修遊戲那側 ⇒ x 加寬到 11 位元（`x | y << 11 | z << 21`，13 處；先在酒館 seq 24979 跟 ame 說）⇒ Blockside **16a5507**、成品照 HEAD 重建 20ca300。讀數：殉爆重現 ⇒ 船頭碎塊 x 739–1098（含那 725 格）、船上剩 0；`?demo=60&dump=1&seed=3` 改前改後 50bfa34008d3、加 `&ship=napoleon,constitution` 改前改後 b89382ea0141（舊船、一般戰局一位元不差）。

## 階段十一 蒸汽機：主機、螺旋槳軸、鍋爐與煙道（2026-10-15 傍晚，TASK-0625）
Tim 2026-10-15：「是否可以建造 拿破崙號 的蒸汽引擎」「同時可能要標記 meta」「遊戲中如果引擎被破壞 引擎提供的額外動力要消失（且煙會停掉）因此需要標記」。
設計 plan.json `engine`；產生 `design/draft_engine.py`（自己寫的）⇒ `masks/engine/{engine,shaft,boilers_aft,boilers_fore}.vox.txt`、`engine_placement.json`、`verify_engine.json`、`sheet07_engine_v1.png`；落格 `design/tools/apply_engine.py`；讀數 `design/tools/check_engine.py`。
- 史料：1850 原裝 Indret 齒輪傳動雙缸、960 nhp、574 ihp（SS／WP）；1852 試航 12.14 kn 連續、13.86 kn 最高。鍋爐座數沒查到 ⇒ 照姊妹艦 Algésiras 8 座；機艙位置沒查到 ⇒ 研究 A 的推論：兩根煙囪夾著主桅 ⇒ 鍋爐在主桅前後、主機在後鍋爐後面。尺寸都是設計決定。
- 位置：faux-pont 中間沒鋪的那一段（x 330–650，從船底到下砲甲板底下 z 86）；只放在船殼裡面的空氣（每個 (x, z) 從中線往兩舷走到第一格實心），落在船外的不放（照實數：軸 387、後鍋爐 1,198、前鍋爐 2,380 格 —— 鍋爐底的外角照船殼內面切掉）。
- **主機**（`-engine`，關聯 `機艙-主機` @334,179,7，28,976 格）：底座（從船底到 z 16）、兩缸立在中線兩側（y ±13、半徑 0.8 m、頂蓋黃銅）、連桿斜接到沿 x 的曲軸（z 64）、兩座軸承座、曲軸上的大齒輪（半徑 1.8 m、六根輻條）咬螺旋槳軸上的小齒輪（半徑 0.4 m ⇒ 增速約 4.5 倍，geared）。meta `kind=engine, engine=geared, cylinders=2, nhp=960, ihp=574, kn=12.14, kn_max=13.86, maker=Indret, material=iron`；固定點 `core`（曲軸中點）、`cyl-1／2`、`gear`。
- **螺旋槳軸**（`-shaft`，關聯 `螺旋槳軸` @220,197,14，2,532 格）：軸心 z 42、半徑 0.2 m，從螺旋槳柱往前接到小齒輪；穿 deadwood 那一段是船殼（不畫）；每 30 格一座軸承座落到船底；從後彈藥庫地板（z 49）底下過。meta `kind=shaft, material=iron`；固定點 `aft`（露出 deadwood 的第一格）、`fwd`。
- **鍋爐兩組**（`-boilers-aft` @384,162,9 171,951 格、`-boilers-fore` @578,162,9 170,428 格）：每組 4 座（x 兩排 × 兩舷，3.6 × 2.9 × 3.8 m 箱形、頂收圓），爐門（火色＋鐵框，每座兩個）朝兩排之間的燒火通道；鍋爐座（磚）到船底；頂上煙道從整組外框（smoke box 一整片）收成煙囪的圓、接到下砲甲板底下。meta `kind=boiler, boilers=4, funnel=煙囪-後／煙囪-前`；固定點 `boiler-1…4`、`uptake`。
  - **鍋爐不標 iron**：實心的鍋爐格代表「鐵殼＋滿水」，平均密度接近水；標 iron 兩組 34 萬格 ≈ 2,600 t（全船排水量 5,121 t）⇒ 照全船預設（橡木 0.7）。主機與軸標 iron（≈ 246 t）。
- 遊戲怎麼用（⚠ 遊戲還沒讀，造船規格 §9 kind 表補了 engine／boiler／shaft 三列）：建議同 `funnel` 的判法 —— 固定點旁 8 格內剩不到一半 ⇒ 壞了；主機壞了 ⇒ 額外動力歸零、煙囪停煙；某組鍋爐壞了 ⇒ 動力打折、它 `funnel` 那條煙囪停煙。各固定點旁 8 格內的格數（基準）：core 477、cyl 2,109、gear 606、boiler-* 2,109、uptake 225／197、軸 aft 82／fwd 52。
- 🩸 設計時改的：① 連桿是斜線、煙道每一層的殼一圈一圈往裡收 ⇒ 只靠斜角相接、面相連斷開 ⇒ 判成浮空（5,000 多格）⇒ 連桿畫十字截面、煙道殼「上一層的殼正下方那格也算殼」⇒ 0；② 煙道的對稱軸寫成 200.5 ⇒ 鏡像差 3,121 ⇒ 200（格 y ↔ 400 − y）⇒ 0；③ 煙道頂跟煙囪壁之間夾出兩個 1 格的封閉空腔 ⇒ 照三叉戟號的封腔填進鍋爐件；④ 軸的 `aft` 原本在 deadwood 裡（框外）、`uptake` 在空心中間（旁邊 0 格）⇒ 改到第一格軸、smoke box 那一片。

讀數（`check_engine.py`，只讀引擎的匯出）：
- ① 四件結果帳 清單 ↔ 子作品 缺 0、多 0、色差 0。② 組裝件 藏機艙 1,759,368 ＋ 171,951 ＋ 170,428 ＋ 28,976 ＋ 2,532 ＝ 2,133,255，缺 0、多 0、色差 0、重疊 0。
- ③ parts：四條關聯 meta 相同、固定點跟 draft 差 0.0000。④ 引擎（藏船名板）：2,132,885 格、1 元件、空腔 0、link_overlap 0；鏡像差 0／37 —— 37 格是階段九前彈藥庫上層木架的立柱（741,204,31–35 色 104，只立在一側；階段九的讀數沒量鏡像差，這裡才看到），不是機艙。
- ⑤ **反向對照**：真的拿掉 `機艙-主機` 的 kind ⇒ meta 不同（kind=None）；加回 ⇒ 相同；kind=engine 的關聯只有 `機艙-主機`。
- 設計那一側：四件跟船重疊 0、彼此重疊 0、浮空 0、鏡像差 0、新空腔 0（封了 2 格）。
- vxk 重匯：2,133,255 格、header checksum 1066745730、材質 iron 60,408（煙囪 28,900 ＋ 主機 28,976 ＋ 軸 2,532）、render smooth 28,900；暫存副本 reimport ＋ 匯入檢查 ✗ 0、⚠ 1（geo）；全船 橡木 2,072,847 格 1,451 t ＋ 鐵 471 t（排水量 5,121 t ⇒ 照樣浮在設計水線，壓艙物補）。
- 過程圖：`design/sheet07_engine_v1.png`（中線側面＋俯視）、`overlays/stage11_engine_room_half.png`（剖半：軸、主機、後鍋爐、主桅、前鍋爐）。
- ⚠ 沒做：煤艙（570 t 煤，research_french90）、機艙的走道與梯子（遊戲裡沒人進機艙）、冷凝器與泵。

## 階段十二 螺旋槳拆成外部模型（2026-10-16 凌晨，TASK-0625 續）
ame 2026-10-16（酒館 seq 25026，Tim：「可以通知kotoko拆出螺旋槳」）：Blockside 的動力串上了（主機 → 軸 → 螺旋槳，鍋爐供汽；TASK-0630／0628），階段十一的 meta 遊戲讀得到 —— 完好 12.25 節、打掉主機 ⇒ 額外動力 0%、兩根煙囪停煙、打掉 1／8 座鍋爐 ⇒ 87.5%。螺旋槳原本是關聯（格子）⇒ 轉不了 ⇒ 拆成外部模型（造船規格 §9 propeller，同光榮號 kaguya-gloire-01m-screw）。工具 `design/tools/split_screw.py plan|apply|check`。
- 同一件 `-screw`（整船的框、世界座標）改當外部模型「螺旋槳」：at ＝ pivot ＝ hub 格心 (178.5, 200.5, 42.5)、scale 1；原本的關聯「螺旋槳」拿掉。固定點 `hub` (178, 200, 42)、`shaft-fwd` (193, 200, 42)（軸線上最前面那格的下一格 ＝ 螺旋槳柱）。
- meta `kind=propeller, axis=(1,0,0), blades=3, diameter_m=5.2`。轉向沒查到 ⇒ 取最常見的右旋槳（從船尾往前看、前進時順時針 ⇒ 右手定則繞 +x）；`rpm_max` 沒查到不寫（遊戲預設 80）。
- **軸的 aft 改到螺旋槳柱**：遊戲照「軸的 aft 離 hub／shaft-fwd 24 格以內」找螺旋槳接哪根軸；階段十一的 aft 在軸露出 deadwood 的第一格 x 224（離 shaft-fwd 31 格）⇒ 照構造改成軸穿過 stern tube 碰到螺旋槳柱那一格 x 193（plan `engine.shaft.x` 193、軸承座起點寫死 220 ⇒ 軸的格一格不動）；軸子作品的框往後撐到 x 193（框 127 → 154、關聯 at 220 → 193，delta_apply 搬局部座標）。組裝件前後逐格相同；主機、鍋爐的清單逐位元組相同。
讀數：
- 組裝件 2,133,255 → 2,129,382：少掉的 ＝ 螺旋槳的 3,873 格（逐格）；1 元件、空腔 0、link_overlap 0；`check_engine.py` 四件結果帳 0 差、固定點差 0、反向對照照報。
- parts：模型「螺旋槳」state ok、meta 相同、hub／shaft-fwd 對；關聯「螺旋槳」沒了。轉一圈（每 15°）螺旋槳每一格的格心落在船殼裡最多 0 格（葉片在 aperture 裡轉得開）。軸的 aft 離 hub 15.0、離 shaft-fwd 0.0 格。models_broken 0（模型 345）。
- vxk：2,129,382 格、header checksum **95738965**、sha256 5675265b…；模型 345、meshes 62、parts 28、iron 60,408。Blockside HEAD 乾淨副本 `admin.py reimport --id napoleon` ⇒ 匯入檢查 **✗ 0、⚠ 0**（90／90 門拿得到火藥、取用點 6；橡木 1,448 t ＋ 鐵 471 t）。
- ⚠ 沒做：遊戲裡的正式 reimport（ame）；螺旋槳的平滑金屬（ame 跟 meadow 在對做法）。
- `design/tools/check_stage5.py`（2026-10-16 01 時）：它讀的是子作品不是關聯，本來就沒壞；改成讀現在掛著的 `-funnel-aft`／`-funnel-fore`（不再讀已不關聯的 `-funnels`）⇒ 7 件、46,760 格、缺 0、多 0、色差 0（兩根 14,512 ＋ 14,388 ＝ 舊的 28,900）。

## 階段十三 機艙的出口：主艙口兩座鐵梯、鍋爐頂四座（2026-10-16 晚上）
Tim 2026-10-16：「拿破崙號目前有一些小細節希望能優化 因為加了第一人稱模式 目前掉到引擎倉沒有樓梯上不去」。產生 `design/draft_engine_access.py`（自己寫的）⇒ `masks/engine_access/{ladders,coaming_carve}.vox.txt`、`engine_access_points.json`、`verify_engine_access.json`；落格 `design/tools/apply_engine_access.py`；讀數 `design/tools/check_engine_access.py`。
- 🩸 **為什麼會上不來**：第一人稱（Blockside `81_fps.js`）往下踩得下 0.8 m、往上只跨得上 0.6 m ⇒ 船底內側的弧面是一段**只能往下的台階**。機艙（x 330–650 不鋪 faux-pont）從船底（z 8）到下砲甲板（z 90）8 m 沒有任何東西接。讀數（照遊戲的走法重算）：**放梯子之前，從甲板走得進機艙 47,861 格、走得回甲板 0 格**。
  - 🩸 我的第一把尺量錯兩次：① 量「從甲板走得到」⇒ 57,553 格，看起來像沒問題 —— 要量的是「走得**回**甲板」（同一張有向圖反著走）；② 旁邊那一柱「窗裡任何一個高度都能去」⇒ 從煙箱斜殼外面掉進殼底下 9,692 格 —— 遊戲挑的是**離腳最近**的那個高度（`fpStand`），改成一樣之後 0。
- **主艙口梯子 2 座**（`engine-S` y 207／`engine-P` y 193，鏡像）：主艙口（x 505–533）底下直通機艙地板、中間全空 ⇒ 梯子掛在艙口裡，往船頭爬、從艙口前緣出到下砲甲板（head x 537, z 91）。機艙的鐵梯（陡）：每 3 格一階、往前 1 格（約 72°，史料 60–70° —— 研究 agent，英國做法推的、信心中低）、踏板 2 格深 7 格寬、兩側 stringer，鐵灰 73；27 階。出口那一段艙口圍欄（2 格高、|y − yc| ≤ 4）刻開 36 格 ⇒ 最上面一階跟甲板只差 1 格。
- **鍋爐頂梯子 4 座**（`boiler-aft-S／P` 在後組的前面 x 447 往船尾爬、`boiler-fore-S／P` 在前組的後面 x 577 往船頭爬，離中線 ±25 避開主桅與燒火通道）：上到鍋爐頂外緣（看安全閥用；13 階）。反向對照：拿掉這四座，回不來的照樣 0 —— 它們只是多開放 3,425 格鍋爐頂，不是救命用的。
- 子作品 `-ladders-engine`（parent 船殼、sub、0.1 m、整船的框），掛在 `甲板-lower/梯子-機艙`（meta kind=ladders），固定點 24（`<梯名>.foot／lo／hi／head`；lo／hi 取踏板外側那一格 ⇒ 頭上是空的）。⚠ foot 不在任何一層甲板上 ⇒ 遊戲的船員不用這幾座（§9.3 自動判接不上），第一人稱照固定點爬。

讀數：
- 設計那一側：2,528 格、跟現有的格重疊 0、鏡像差 0、梯子點問題 0；**連通：從甲板走得到的 51,520 ＝ 走得回甲板的 51,520，掉得進去回不來 0**（另外 7,369 格是煙箱裡面，走路進不去）。
- 反向對照：拿掉 `engine-S` ⇒ 另一座照樣全部救得回來（51,403 ＝ 51,403）；拿掉鍋爐頂四座 ⇒ 48,095 ＝ 48,095。
- **結果帳**（`check_engine_access.py`，只讀引擎匯出）：組裝件 2,131,874 ＝ 之前 2,129,382 ＋ 梯子 2,528 − 圍欄 36，缺 0、多 0、色差 0；parts 關聯 `甲板-lower/梯子-機艙` meta kind=ladders、固定點 24／24 差 0；照作品重算連通，回不來 0。
- 引擎 stats（藏船名板）：2,131,504 格、1 元件、空腔 0、link_overlap 0；鏡像差 0／37（37 ＝ 階段九前彈藥庫木架立柱，舊的）。
- 產生程式重跑：兩份清單逐位元組相同。
- 過程圖：`overlays/stage13_engine_ladders_cut.png`（藏船殼、上兩層甲板，剖到中線 +12）。
- ⚠ 沒做：遊戲裡的 reimport（vxk 格數與 checksum 會變）。

## 階段十四 司爐艙：燒火通道、機艙鐵地板（level −1）、站位、會轉的齒輪（2026-10-16 晚上）
Tim 2026-10-16：「動力部件可以設定需要船員工作(鍋爐) 沒有會影響輸出」「動力部件相關參數其實我希望都在遊戲端設定(後台預設 遊戲內可調參數) 模型只提供meta標記」「照計畫先做司爐艙：鍋爐縮短拉寬燒火通道、機艙鋪地板標 level -1、梯子重算、鍋爐和主機標站位。遊戲那側的規則交給 ame」；截圖（主機大齒輪）「另外這個能旋轉嗎」「可以參考螺旋槳做法」「動力算法其實要大改 這部分不影響(就先拆件吧 之後只要改META)」。
- **燒火通道**（plan.json `engine.boilers.rows[].x`，外框不動）：原本後組 0.5 m（x 413–417）、前組 1.1 m（607–617）站不進人 ⇒ 每排縮短：後組 [384–404]＋[426–446]、通道 2.1 m（405–425）；前組 [578–600]＋[624–646]、通道 2.3 m（601–623）。史料（研究 agent，推）爐口前 2.4–3 m；本船外框夾在主機與主桅之間只到這裡。delta_apply：後組刻 43,808、前組刻 32,376、換色各 336（爐門搬到新的那一面）⇒ 128,143／138,052 格。`boiler-1…4` 跟著新的鍋爐中心。
- **機艙鐵地板**（`design/draft_engine_floor.py` ⇒ `masks/engine_floor/floor.vox.txt`；子作品 `-deck-engine`，組裝件關聯 `甲板-engine`）：板面 z 12（站 z 13 ＝ 鍋爐底），x 348–650、船殼裡面、船底比板面低的地方；排水孔 (x, y) 都是 10 的倍數那一格不鋪（108 個）⇒ 板底下的艙底跟機艙通著、封死的空腔 0；12,385 格、鐵灰 73。甲板 meta：`kind=deck, deck=engine, level=-1, name=機艙, floor=348:13,650:13, thick=1`（Blockside `35_decks.js` 照 level 排序，−1 排在 faux-pont 底下）。
- **梯子照新地板重算**（`draft_engine_access.py`，匯出時藏 `甲板-lower/梯子-機艙`）：梯腳都踩在板上（z 13）；主艙口兩座 25 階、加 meta `engine-S／P.decks ＝ engine,lower`（§9.3 直接指定 ⇒ 船員也走這兩座）；鍋爐頂四座 12 階。delta_apply 刻 1,832、貼 1,656 ⇒ 2,352 格。圍欄清單沿用階段十三那一份（🩸 中途一次錯跑把它蓋成空的，從作品歷史 `diff 機艙梯子出口:begin → :end` 撈回 36 格，sha256 跟階段十三記的一樣）。
- **站位**（固定點，只是 meta 標記 —— 要幾個人、人不夠怎麼扣出力都在遊戲端）：鍋爐子作品 `stoke-1…4`（每座爐門前往燒火通道 4 格、這座鍋爐的中線 y 179／221、z 13）；主機 `tend-1／2`（兩缸外側 y 176／224、x 356、z 13）。全部站得住（船員頭上 1.2 m 空）、兩舷鏡像。主機的框裝不下 tend ⇒ 框往兩舷各撐 3 格（y 179 → 176、寬 43 → 49；`work sub=update size`、delta_apply 搬局部座標 5,500 格、關聯 at 跟著挪 ⇒ 組裝件位置不變，check_engine ② 0 差）。
- **大齒輪、小齒輪拆成會轉的外部模型**（`design/tools/split_gears.py`，照 split_screw.py）：子作品 `-engine-gear`（1,253 格：齒輪三片＋曲軸在那三片與後面那一段）、`-engine-pinion`（207 格），整船的框、世界座標；組裝件模型 `大齒輪`／`小齒輪` at ＝ pivot ＝ 轉軸格心、scale 1。meta `kind=gear, gear=crank｜pinion, spin=rpm, spin_mode=rate, spin_k ＝ −1.3333｜6`（小齒輪在螺旋槳軸上 ⇒ 同轉速同方向；大齒輪外咬合 ⇒ 反轉、÷ 4.5）；固定點 `spin-a`→`spin-b`（+x）、**`bail`**（掛點：大齒輪掛曲軸 x 340、小齒輪掛螺旋槳軸 x 340）。
  - 🩸 拆完量到主機件浮空 29 格（曲軸在齒輪後面那一小段，兩頭都不接）⇒ 併進大齒輪（`split_gears.py extend`）。
  - 🩸 產生程式先拿掉齒輪、才畫軸 ⇒ 軸補進小齒輪那 39 格 ⇒ 改成畫完軸再拿。
  - 🩸 遊戲的匯入檢查第一次 ⚠ 2「掛著擺的小艇已經自己在轉 ⇒ spin 不收」：遊戲（`10_ship.js`）替模型找掛點，從外框底往下 12 格內沒有船的格 ⇒ 當成吊著的小艇；大齒輪底下 30 格才到主機底座 ⇒ 登記 `bail`（遊戲不看種類，同燈的提環）⇒ ⚠ 0。
- draft_engine.py：現況多藏 `甲板-engine`、`甲板-lower/梯子-機艙`（在本件之後；不藏 ⇒ 鍋爐座跟地板夾出 425 格空腔，讀數擋下來的）；齒輪的格照 `masks/engine/gears_from_engine.json` 不放進主機件。

讀數：
- `check_engine.py`：四件結果帳 0 差（主機 27,516、軸 2,532、鍋爐 128,143／138,052）；組裝件 0 差；固定點鍋爐各 9、主機 6，跟設計差 0；反向對照照報。
- `check_engine_access.py`：梯子關聯 meta 帶 `.decks`、固定點 24／24 差 0；照作品重算第一人稱連通：**掉得進去回不來 0**。
- `split_gears.py check`：兩個模型 state ok、meta 相同、子作品格 ＝ 拆的那一刻記下的格；主機件那三片裡剩 0 格。
- 引擎 stats（藏船名板）：2,066,069 格、1 元件、空腔 0、link_overlap 0；鏡像差 0／37（舊的）。
- **遊戲的匯入檢查**（Blockside HEAD 6a7424d 的 git archive 副本＋工作區 _cache 的複本，`admin.py reimport --id napoleon`，⛔ 沒動工作區）：**✗ 0、⚠ 0**；甲板 5、梯子 8（主艙口兩座船員也能用）、模型 366；會轉的：舵、大齒輪（rpm × −1.3333°/s）、小齒輪（rpm × 6°/s）、舵輪。
- 過程圖：`overlays/stage14_stokehold_cut.png`（藏船殼與各層甲板、剖到中線）。
- ⚠ 沒做：遊戲裡的正式 reimport（ame）；連桿是往復運動，spin 只會轉 ⇒ 不動；煤艙、汽缸走台、內部陳設（todo）。
- **階段十四補一刀：軸線不斷**（ame 2026-10-16 酒館 seq 25400，TASK-0653 動力件的新檢查）：齒輪拆成模型之後，軸的格子在小齒輪那三片（x 337–339）與軸承座（340–342）斷開 ⇒ 遊戲判軸「開局 0 條路」、打斷也不停。修法（ame 給的兩個選①）：小齒輪挖軸孔 39 格（`split_gears.py bore`，207 → 168），draft_engine 的軸線上一律歸軸（軸承座讓出 39 格）⇒ 軸 2,610 格、軸線 x 224–346 不斷（224 以前穿 deadwood，是船殼）；主機 27,477、`core` 旁照舊 477。讀數：check_engine 四件與組裝件（2,066,478）0 差、1 元件、空腔 0；split_gears check 兩個模型 ok；Blockside main 34dbb65（含 c649381）乾淨副本 reimport：✗ 0、⚠ 0，「螺旋槳軸 2,610 格＋穿過船殼借 724 格，開局 ≥ 7 條路、傳得滿」。
  - 🩸 我自己的盲點：拆齒輪那一刀只量了「主機件浮空」「組裝件少掉的 ＝ 齒輪」，沒量「拆走之後，剩下的件還是不是一根完整的東西」。軸看起來還在，其實斷成兩截 —— 跟階段十三「掉得進去 ≠ 爬得出來」同一族：在場不等於接得上。
- **2026-10-17 拿掉兩個齒輪的 `bail`**：遊戲 c0eec07 起，照參數轉的模型沒有 `bail` ⇒ 掛在 `spin-a` 旁那一格（ame 酒館 seq 25415）。`work sub=unanchor name=bail` × 2（`-engine-gear`、`-engine-pinion`），兩件剩 `spin-a`／`spin-b`，沒有繩或帆綁在 bail 上。只換 meta ⇒ 等 ame metasync，不用整份重匯。
  - 遊戲現況回讀（Blockside main 1dd93e5 的 git archive 副本，`admin.py shipcheck --id napoleon`）：✗ 0、⚠ 0；橡木 2,007,491＋鐵甲 58,987 ＝ **2,066,478 格**（跟組裝件一樣）；大齒輪 −1.3333°/s、小齒輪 6°/s；軸 2,610＋借 724、開局 ≥ 7 條路；螺旋槳 3,873 格體素件。這份還帶著 bail；拿掉之後在同一份副本（＋工作區 _cache 複本）跑 `admin.py metasync --id napoleon --no-build`：只換了「大齒輪、小齒輪」兩個模型的 meta／固定點、關聯 0 條；shipcheck **✗ 0、⚠ 0**，兩個齒輪照樣在「照參數轉」那一行（沒被當成吊著的小艇）。⛔ 沒動 Blockside 工作區；正式 metasync 是 ame 那邊。
- **2026-10-17 機艙的金屬質感**（Tim：「鍋爐以及其他金屬部件 是否可以參考煙囪改成金屬質感」）：
  - 鍋爐 ⛔ 不能照煙囪標 iron（實心格 ＝ 鐵殼＋滿水，iron 7.8 會多好幾千噸）⇒ 照 copper_sheath 的先例（外觀金屬、密度另算）開新材質 ID **`boiler`**：關聯 `機艙-鍋爐-後／前` meta `material=boiler, render=smooth`；`Sculpture/materials.json` 加 `boiler`（metal 0.85、rough 0.45）。
  - 主機、軸本來就 iron ⇒ 只加 `render=smooth`（`機艙-主機`、`螺旋槳軸`）。
  - 預覽讀數：平滑 325,182 格｜材質 boiler 266,195、iron 58,987。過程圖 `overlays/metal_engine_before.png`、`metal_engine_after.png`、`metal_engine_close.png`。主機的斜連桿（十字截面）平滑後扭成麻花狀，跟主機同一件、蓋不回方塊 ⇒ 留著；鍋爐頂的煙道殼是逐層內收的格 ⇒ 平滑後看得到一圈一圈的稜。
  - 遊戲對拍（Blockside HEAD 乾淨副本＋_cache 複本：reimport → build → shipcheck，⛔ 沒動工作區）：🩸 **metasync 不夠**，材質與平滑是匯出時烤進 .vxk 檔頭的（metasync 後讀數一格沒變）⇒ 要整份 reimport。reimport 後：平滑 6 條關聯 325,182 格；**⚠ 1「材質表沒有 boiler ⇒ 照全船預設 oak」**（boiler 266,195 格算橡木 186.3 噸，重量跟改之前一樣，但遊戲裡不反光）。⇒ 遊戲材質表要加 `boiler`（kind metal、metal／rough 同上、density 由遊戲端定）才會反光、⚠ 消失。Tim 2026-10-17：「boiler 的數值…妳自己加」⇒ 遊戲材質表加 `boiler`：kind metal、density 0.9（一座 39.7 m³ 估鐵約 18 t＋水約 20 t ≈ 0.95，格裡另含空心煙道殼與磚座 ⇒ 0.9）、hard 1.5、flammable 0、metal 0.85、rough 0.45；⛔ 不寫 pen（鍋爐不是裝甲）。
  - 遊戲：Blockside 56f8535（材質表＋整份 reimport）合進 dev f4ac89c、推上測試站（`git push dev heads/dev:dev`）；shipcheck **✗ 0、⚠ 0**，boiler 266,195 格 **239.6 噸**（之前照 oak 186.3 噸，+53.3 噸）；平滑 6 條關聯 325,182 格。還沒發版到 main／origin（等 Tim 在測試站看過）。

## 階段十五 內部陳設第一批（2026-10-17，TASK-0682 裝飾 meta）

Tim：「試著繼續裝修拿破崙號吧(裝飾可以額外標meta 之後遊戲會有性能選項隱藏裝飾)」→ 開了 TASK-0682（遊戲畫質「裝飾」；Blockside e27d835、合進 dev 5012386）。
設計 `design/draft_furnish.py`（擺放照階段九 draft_fittings：取樣點不撞「組裝件 links=all ＋ 模型外框」、梯子端點保留區、腳下要有甲板）；落格 `design/tools/apply_furnish.py`。
全部是外部模型、meta `deco=1`（造船規格 §9.9：畫質「裝飾」關著載入時就不載入；開著只畫，不算重量、不被打）。0.05 m 子作品、scale 0.5、pivot ＝ 底面中心。
- `-galley` 爐灶（32,684 格）：`甲板-upper/爐灶` @726,200.5,116 —— 前艙口與前桅之間的中線（候選 726–735；715 起擋到東西）。磚座、鑄鐵身（色 36；37 畫出來是藏青，改掉了）、朝船尾兩扇烤爐門＋火門、兩只銅鍋、煙管照頭上第一個實心接到上甲板底面（世界 z 139）。
- `-bitts` 錨鏈繫纜柱（5,610）：`甲板-upper/繫纜柱` @838 —— 錨鏈孔（hawse x 878）後面。
- `-fiferail` 繫索栓圍欄（1,980）：`甲板-spar/繫索栓圍欄-main` @460、`-fore` @757（中心 ＝ 桅軸；柱腳 72／72 著地）。
- `-shotrack` 砲彈架（1,543）：`甲板-lower`／`甲板-upper` 的 `砲彈架-S`／`-P`，主艙口兩舷圍欄外側（y 214／187，P mirror=y）。
- ⛔ 沒放：主桅旁的水泵 —— 遊戲有抽水機功能（45_pumps.js pumpModels），不能標裝飾；要做就照功能件做。

讀數：
- 產生程式重跑：擺放與四份清單逐位元組相同；四件子作品匯出 ＝ 清單（缺 0、多 0，含色）。
- 遊戲（Blockside worktree，之後合進 dev）：拿破崙號匯入檢查表格那一列（模型 366、水線 79…）跟加陳設之前逐字相同 ⇒ 裝飾不算重量；「裝飾：8 個模型」。
  瀏覽器 g_deco=1 ⇒ 畫 8、模型網格 70、111,152 三角形；g_deco=0 ⇒ 0、65、107,628。同種子 90 秒對戰（seed 7、合併後 seed 11）開／關 dump 逐字相同。
- 過程圖 `overlays/furnish_{galley_piece,fiferail_piece,bow_upper,spar_main,lower_main_hatch}.png`。
- ⚠ 另外看到的（不是本階段）：dev 新的梯子檢查對鍋爐頂四座梯子報 ⚠ 4（上端落在鍋爐頂、不是 kind=deck 的甲板）—— 見 todo。

## 階段十六 砲門蓋板 62 片（2026-10-20 凌晨，造船規格 §9.12、TASK-0719）

Tim：「參考光榮號 把妳的船都加上炮門吧 GO」—— 我的船只有拿破崙號。
工具 `design/tools/portlids.py`：gura 三叉戟號那一支（basecamp 通用版改三處）複製，改開頭的表＋兩處：
① 凸出物照平面殘差判（ame 維吉尼亞號那一條）—— 圓船尾收進來那一段（下砲甲板 2、3 號）外表面 10 格高差 11 格，照中位數整片被當成凸出物；
② 開口沿斜面量比蓋板長 ⇒ 不做；鉸鏈上面外張 ⇒ 開著的蓋板插進船殼 ⇒ 鉸鏈往外挪一格再量（最多 3 格；summit 那一條）。
- 子作品 `kotoko-napoleon-01m-portlid` 12 × 11 × 2（264 格；兩層的開口全是 10 × 9 ⇒ 兩層共用一件）：朝外黑 36 ＋ 鉸鏈板 73、貼船殼內板 177（PHOTO c.1860：白帶上黑砲門蓋，黑白棋盤）；hinge-a 0,0,0 → hinge-b 11,0,0。
- 下砲甲板 32 片（掛 `甲板-lower`）、上砲甲板 30 片（`甲板-upper`）；meta kind=portlid、lid_of（砲的 id）、close_deg、house。P 舷 rotate 180 − rz。
- 沒做：下砲甲板 1 號兩舷（斜放、砲口那一欄沒有封閉的開口）、2 號兩舷（外表面斜 45.3°，開口沿斜面 12.8 格 > 蓋板 11 ⇒ 關不滿，開著也插進外張的船殼）；`甲板-spar` 24 門（露天，§9.12 不做）。
- 下砲甲板 3、4 號兩舷鉸鏈往外挪 1 格（不挪 ⇒ 開著插進船殼 17／12 個取樣點）；close 102.5–116.9°（圓船尾往上外張）。

讀數（`design/verify_portlids_{lower,upper}.json`）：
- 開著撞船 0、撞推出去的砲 0；關上撞收回 house 格的砲 0；關上落進船殼最多 0.51%（下）／0.34%（上）；開口全蓋滿；反向對照 house 0 ⇒ 30／32、30／30 片碰砲（下層沒碰的 2 片是 3 號：砲口本來就縮在牆裡），P 舷改 mirror=y ⇒ 31 片全部往上關。
- 掛上去之後對作品：蓋板 264 格缺 0、多 0、色差 0，固定點對，62 片擺法與 meta 跟 placement 一樣，parts 的 hinge-a 差 ≤ 0.0005。
- house：下 4–8、上 8–10（上砲甲板砲口伸出去 7–9 格）。下砲甲板 12 號兩舷收砲 8 格時砲尾碰到後面的東西 27 個取樣點 —— 只是畫面，照實留著。
- 遊戲（Blockside HEAD d8a0a86 的 git archive 暫存副本，`admin.py reimport --id napoleon`）：匯入檢查 **✗ 0、⚠ 4** —— 砲門蓋板 62 片（P 31、S 31）、house 4–10、close 82–117° 沒有任何一條；⚠ 4 是鍋爐頂四座梯子（Tim 10-17 看過、照現狀）。蓋板的物件 id 等正式 reimport 時 `admin.py ids` 發。
- 預覽圖 `overlays/portlids_side.png`（右舷、開著）。

## 階段十七 船尾窗改成玻璃（2026-10-21，造船規格 §9.5「窗的玻璃」）

Tim：「拿破崙號的窗戶 參考 憲法號 改成玻璃吧」。階段三開窗是「刻最外一格、第二格塗玻璃色 87」⇒ 玻璃是船殼的格、後面還有肋骨與內板，遊戲裡不透明、看不到艙裡。
產生 `design/draft_window_glass.py`（自己寫的）⇒ `masks/glass/{glass,behind_carve}.vox.txt`、`verify_window_glass.json`。
- 船殼裡色 87 一共 721 格、全在船尾窗（下排 5 扇 × 7 × 8、上排 7 扇 × 7 × 9；別的地方沒用這個色）⇒ `work sub=split colors=87` 原位拆成子作品 **`-stern-glass`**「拿破崙號 船尾窗玻璃」（外觀不變、驗過），雙生關聯 **`船殼-窗玻璃` meta `material=glass`**（⛔ 不寫 render）；顏色換成憲法號的 **155**（淡藍灰，stampvox overwrite）。
- 玻璃後面刻穿：朝船裡 ＝ 玻璃旁邊空的那一側（開窗刻掉的外板）的反方向、只取水平（圓船尾每扇窗朝向不同），每 0.5 格走、碰到空氣停；窗洞轉角（兩面朝外）再補刻正後方。⛔ 不刻碰到窗外空氣的格（＝ 每一格玻璃朝外那一側的空格；刻了就繞過玻璃成洞）。
- 🩸 第一刀（1,631 格）落格之後引擎量到 **元件 1 → 93、封閉空腔 0 → 10 個 24 格**：斜著走在刻掉的格之間漏下單格殘牆；窗緣 30 格玻璃靠旁邊的窗框撐著，轉角補刻把窗框刻掉 ⇒ 浮空；玻璃跟殘牆之間夾出封死的空間。我只量了「每一格玻璃後面空不空」，沒量「刻完剩下的還接不接得上」—— 跟階段十四拆齒輪斷軸同一族。
  ⇒ 產生程式反覆到穩定：浮空的殘牆也刻（136 格）、浮空玻璃旁被刻掉的格放回（58）、封死的空腔放回（34）；`窗玻璃v2`：stampvox 放回 92 格、carvevox 多刻 136 格。

讀數：
- 刻掉 1,675 格（肋骨 141 964、內板 177 711），全部帶色守門；碰到窗外 0；兩舷鏡像差 0（玻璃、刻掉的都是）。
- 玻璃 721 格裡 **677 格正後方是空的**（看得到艙裡）；44 格後面留著牆：4 格是最外側兩扇下排窗的轉角（刻了會漏到窗外）、其餘是撐住窗緣玻璃的窗框。
- **結果帳**（組裝件船尾那一塊 export，110..220,130..270,85..145）：改之前 − 刻 ＋ 換色 ⇒ 缺 0、多 0、色差 0。
- 引擎 stats（藏船名板）：2,064,433 格（＝ 2,066,478 − 1,675 − 船名板 370）、**1 元件、空腔 0、link_overlap 0**；鏡像差 0／37（舊的前彈藥庫木架）。
- **反向對照**：`--probe=keep_behind:30`（故意少刻 30 格）⇒ 後面是空的玻璃 691 → 報少 26 格。產生程式重跑：兩份清單逐位元組相同。
- 過程圖：`overlays/glass_stern.png`（船尾、透視；CLI 照不透明畫，透明只在遊戲裡）。

### 階段十七之二 從艙裡看窗被擋（2026-10-21 傍晚，標記 `窗玻璃v3`）
Tim 第一人稱截圖：「船內部窗戶有些遮擋」—— 窗洞前面一階一階的木牆擋住玻璃。
- 🩸 為什麼：每格玻璃各自沿一條線往船裡刻，圓船尾的斜牆在線與線之間留下鋸齒狀的殘牆；而且玻璃順著斜的船尾面一階一階排（一欄多半 1～2 格高），只靠斜角相接 ⇒ 每一小塊靠背後的牆撐，牆不能整片刻。我量的「每格玻璃正後方那一格空不空」（717／721）量不到從艙裡看的樣子。
- 新的尺 **glass_sightline_blocked**：沿**整扇窗**的朝向從玻璃往船裡看 7 格，碰到刻完還在的船殼格 ⇒ 被擋。同一把尺量遊戲裡那一版（`--probe=no_prism:1` 重現的就是它）：**190 格被擋**。
- 改：① 一扇窗（玻璃 26 連通 ⇒ 12 扇；6 連通會切成 132 塊）當一個整體，玻璃後面、窗寬窗高範圍裡、深 7 格以內的船殼格全刻 ⇒ 方形窗洞；② 照造船規格 §9.5「斜的船尾面上下兩排差 1 格的地方補 1 格」：同一扇窗裡斜角相接的兩格玻璃之間補一格玻璃（取窗框層的牆格），補到那一扇面相連 ⇒ 整片玻璃靠窗框撐，不用再放回撐玻璃的牆；補一格就把鏡像格也補（第一次跑沒有：補的玻璃 64 格對不上鏡像）。
- 落格：船殼 carvevox 462 格（方形窗洞＋變成玻璃的牆格，帶色守門）、`-stern-glass` stampvox 補 114 格玻璃（共 835 格）；放回 0 格。
- 讀數：被擋 **190 → 20 格**（剩下的都在窗洞側壁：下排最外側幾扇的轉角刻了會漏到窗外、照規則留著，其餘是從窗緣那格正看看到的窗框厚度）；玻璃正後方空的 717／721；碰到窗外 0；撐玻璃放回 0、封死的空腔 0。結果帳（船尾那一塊，對產生程式模擬的最終樣子）缺 0、多 0、色差 0；引擎 2,064,085 格（＝ 2,064,433 − 462 ＋ 114）、1 元件、空腔 0、link_overlap 0；兩舷：刻掉的、玻璃都鏡像差 0。產生程式重跑逐位元組相同。
- 過程圖：`overlays/glass_stern_inside.png`（上砲甲板往船尾窗看；CLI 照不透明畫）。

### 階段十七之三 玻璃上的雜點（2026-10-25，標記 `窗玻璃v4`、`窗玻璃v4b`）
Tim 第一人稱：「有兩個窗戶上面還有一些雜點，應該是船殼溢出的部分」。
- 新的尺 `design/tools/check_glass_specks.py`：一扇窗（玻璃 26 連通）沿朝外方向（從船裡 (260,200) 指向窗中心 —— 玻璃後面已刻穿、兩側都是空氣，用「不在組裝件那一側」判不出內外）投影成 (u,z)，找落在玻璃投影裡、玻璃內外 2～3 格以內的非玻璃實心格。讀數：**4 格**，全在下排最外側那一對鏡像窗（中心 y 169／231）：肋骨色 141，夾在同一層玻璃中間（三面玻璃、艙內那面與上下是空氣）。
- 🩸 為什麼 v3 沒抓到：v3 的「1 元件」量的是**連著玻璃**的樣子；船殼單獨量（`stats structure=1`，`mark=窗玻璃v4:begin`）是 **11 塊**——10 格 1 格大小的船殼殘格只靠玻璃撐著。除了那 4 格，同兩扇窗還有 6 格在窗緣（尺的「四周都有玻璃欄」條件把它們當窗框排除了），是從「船殼單獨的元件」找到的。
- 改：10 格都刻掉（帶色守門 141）、`-stern-glass` 原位補成玻璃 155 —— 它們本來就在玻璃那一層，往外是玻璃、不會漏到窗外。
- 讀數：雜點 4 → 0；船殼單獨 11 塊 → **1 塊**、空腔 0、兩舷鏡像差 0；玻璃 835 → **845**、12 扇、鏡像差 0；組裝件船尾那一塊格數 85,016 不變（只換了 10 格的歸屬與顏色）。
- 已重匯：這一版在 Blockside dev 7471d18（vxk_compare 只差這 10 格）。
- ✓ Tim 在遊戲裡看過：「拿破崙號窗玻璃 ok」（2026-10-25）。

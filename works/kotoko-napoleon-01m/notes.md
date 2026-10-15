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

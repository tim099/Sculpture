# 收穫號（La Cosecha）—— 西班牙大帆船，參考 1618 年 Ordenanza（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-15（TASK-0589 傘，子單 TASK-0590～0599）：「接著開task造一艘新船吧 可以嘗試用西班牙大帆船的船型做參考(可以找真實圖紙&參數等資訊) 由妳重新設計圖紙打造一艘專屬於妳的船吧(自由發揮) 另外要是遊戲用的規格」。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫這些遊戲用得到的大致構造。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 座標約定
- 空間 800×320×640；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 160 格**，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（書卡 meters_per_voxel 已記）。1 codo de ribera ＝ 0.57468 m ＝ 5.7468 格。

## 設計方向（開工時的決定）
- 船名「收穫號」：死神的鐮刀原本是農具 —— Memento Mori → Vivere → Harvest。船首像、船尾雕飾、船名板是本船自己的（TASK-0594）。
- 船型：**1618 年 Ordenanza 的 manga 21 codos（946½ toneladas）**，兩層砲甲板（主甲板＋puente）＋三座船樓（toldilla、alcázar、castillo）＋espolón。不描任何一張圖：每個尺寸照法令的比例表與條文算，算不到的才是設計決定。
- 線形的程式結構參考 gura 的三叉戟號（`gura-tridente-01m/design/hull_lines.py`：船中剖面 × 長度方向收縮）；剖面、兩端、舷頂換成 galleon 的（平底＋astilla、大圓弧艏柱、平的 espejo、法令的 tumblehome 規則）。`design/tools/wio.py`、`stamp_lists.py` 照抄三叉戟號（檔頭註明）。
- 沿用現成零件當模型：砲（18l／12l／6l）、舵輪、火藥桶、燈、羅經櫃、絞盤、小艇（`work sub=components`）。

## 階段一 新圖紙 01／02（2026-10-15，TASK-0590）
查證：兩個獨立研究 agent 並排 ⇒ `references/research_ordenanzas_2026-10-15.md`（法令比例表、Palacio、Cano）、`references/research_galleons_2026-10-15.md`（實船與複製船：Andalucía、San José、Atocha、Manila galleons、Red Bay）。互相不同意的照列（codo 0.57468／0.57864／0.557；San José 的 codo 0.418 vs 0.5747；Andalucía 長 48／49／50／51 m）。主要出處兩份都逐頁讀過的是 Fernández-González 2009（UPM）。

設計 `design/plan.json`（每個數字的 `src`：參考資料附出處／設計決定）；程式：
- `lines.py`：線形 ⇒ 每個 (x, z) 的半寬。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`verify_lines.json`、`masks/hull/hull_01..02.vox.txt`（船殼清單，at 0,0,0）。船殼 ＝ 線形實心往裡留 4 格牆（外板 1、肋骨 141 ×2、內板 177）；外板水線 z 52 以下灰白 182、以上黑 36（塗裝在階段三）。舷頂以上多算 EXTRA ＝ 60 層再切（階段二的坑，見下）。
- `layout.py`＋`draft_layout.py` ⇒ `sheet02_layout_v1.png`（甲板、砲門、桅、帆桁、帆、俯視）、`verify_layout.json`。

| 項目 | 讀數 | 1618 年 Ordenanza（21 codos） |
|---|---|---|
| 甲板長（主甲板 z 65，艏柱到艉柱） | 37.92 m（379.2 格） | eslora 66 codos ＝ 37.93 m |
| 龍骨 | 29.30 m | quilla 51 codos ＝ 29.31 m |
| 最大寬（含外板） | 12.10 m（121 格） | manga 21 codos ＝ 12.07 m |
| 比例 甲板長／寬、龍骨／寬 | 3.13、2.42 | 3.14、2.43（研究者照表算的） |
| mura（艏柱往後 L/4＋1 codo）的寬 | 115 格 | manga − 1 codo ＝ 115.3（art.21） |
| cuadra（艉柱往前 L/4＋2 codos）的寬 | 111 格 | manga − 2 codos ＝ 109.5（art.21）—— 寬只能是奇數格，111 是最近的 |
| hold beams（z 45）／puente（z 85）那一層的寬 | 119／119 | 兩者相等（art.22 的 tumblehome 規則） |
| 設計水線 | z 52（5.2 m） | 法令沒給（設計決定；Atocha 4.3 m） |
| 排水量（水線下實心 × 1.025） | 1,130 t | 946½ toneladas 是容積噸，不是排水量（只當量級） |
| 船殼牆 | 426,821 格；1 元件、空腔 0、鏡像差 0（第一版 428,046，階段二修掉船樓前後緣 1,225 格） | — |

- 甲板（甲板面 z）：底艙 orlop 45（只 x 190–430）、主甲板 65、puente 85、alcázar 102（到 x 268）、toldilla 119（到 x 196）、castillo 102（從 x 422）。主甲板與 puente 有舷弧（aft 6、fwd 3 格，FG）；船樓平的（art.16）。
  ⚠ 甲板間距 20 格（1589 年 galleon 3½ codos）而不是 1618 年的 3 codos（17 格）—— 遊戲裡站人要頭頂 14 格空，17 扣掉甲板板和橫樑不夠。船樓照 1618 的 17 格。
- 砲門（art.42：下緣在甲板上 1 codo、1¼ codos 見方）：主甲板每舷 9（18l）、puente 8（12l）、alcázar 2、castillo 2（6l）＋船尾追擊 2（18l）＝ **44 門**。間距 27–28 格；puente 的砲門頂到船腰舷頂留 2 格（船腰舷牆拉到 z 100）。
- 桅（art.66–68：主桅腳在龍骨中點 x 296、前桅腳在艏柱 rake 中點 x 472）：fore 29.6＋14.8 m、main 30.2＋15.1 m（Cano 2½ manga、上桅 ½）、mizzen 18.4 m＋lateen 24.5 m、bonaventure 13.8 m＋lateen 17 m、bowsprit 23.7 m @ 32°（Palacio）。主桅頂離水線 38.6 m（Andalucía 複製船 air draft 37 m，只當量級對照）。⚠ 桅帆比例只讀到 MP 部落格的轉述（二手，沒對過 Cano／Palacio 原文）；1618 年 art.72–91 的桅帆條文兩個 agent 都沒拿到。
- espolón：art.45 manga 的 3/5 ＝ 7.24 m 伸出艏柱（圖上只畫外框，TASK-0594 做）。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 最大寬 121 → 127（每舷 +3）；站位表 33 格中 19 格 +3、12 格 +2、各 1 格 +1／0（＋2 以下的都在兩頭：長度方向收縮 × 3 再取整）。
- `draft_layout.py --probe=port=main:5:+3` ⇒ 主甲板間距 [28, 27, 28, 27, 28, 28, 27, 28] → [28, 27, 28, **30, 25**, 28, 27, 28]。
- 產生程式重跑：6 個輸出檔（兩份清單、兩張圖、兩份 verify）逐位元組相同。

⚠ 已知、之後的階段處理：
- 艏柱 z 57.5 以上是直的，船頭面是一整片平的到舷頂（x 500）—— espolón、船首像、castillo 前緣的裝飾在 TASK-0594。
- 船尾是一整片平的 espejo（照艉柱的 23.8° 往後倒）—— 船尾窗、galleries（art.69：最多伸出 ⅔ codo）在 TASK-0592／0594。
- bonaventure 的 lateen 帆桁照「吊點在 40%」畫，後端伸出船尾約 8 m —— 桅與帆桁階段（TASK-0595）要調（吊點改到中間，或船尾加 outrigger）。
- 三角帆（lateen）在遊戲裡怎麼轉、`sail=` 用哪一種，TASK-0595 先跟 ame 對。

## 階段二 船殼落格（2026-10-15，TASK-0591）
- 標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py calli-cosecha-01m 0 masks/hull/hull_01..02.vox.txt`（2 刀：250,000 ＋ 178,046，每刀讀回 placed ＝ 清單格數）→ `船殼:end`。
- 🩸 渲出來第一眼：**船樓前後緣（toldilla／alcázar、alcázar／船腰、船腰／castillo）的舷頂各多一條橫跨船寬的橫桿**。成因：`draft_lines` 算牆用「離船外的距離 ≤ 4」，舷頂以上只多算 12 層 ⇒ 船腰上方 z 112 起就是「船外」，船樓內側離它不到 4 格的那一條被當成牆。各自的讀數（元件 1、空腔 0、鏡像 0）全綠 —— 橫桿兩頭接在舷牆上，是一塊合法的實心。
  修法：舷頂以上多算 EXTRA ＝ 60 層（> 船樓與船腰最大落差 33）⇒ 新清單是舊清單的子集（新有舊沒有 0 行；舊有新沒有 1,225 行，全在 x 195／196、267／268、421／422）。刻：`masks/hull_fix/carve_breaks.vox.txt`（carvevox 帶刻之前的顏色守門，carved 1,225）→ 標記 `船殼修正`。
- **結果帳**（`design/tools/check_hull.py`：作品那側從 `export format=list links=none mark=船殼修正` 讀）：作品 426,821 ＝ 設計 426,821，缺 0、多 0、色差 0。
- **結構**（引擎 `stats structure=1 mirror=y:160`）：1 元件、封閉空腔 0、鏡像差 0／0／0。
- **線形對照**：右舷外緣（每個 (x, z) 最大的 dy）vs `lines.hb` 取 floor，x 100..480 每 20、z 4..129 每 5，412 點、差 0。**反向對照**：設計那一站（x 300）+3 ⇒ 報 20 點（那一站每個高度）、最大差 3。
- **組裝件** `calli-cosecha-01m-assembly`「收穫號」：0.1 m、800×320×640（parent 船殼，沒標 sub ＝ 主作品）；關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=52`。船殼標 `tags=sub`、名稱「收穫號 船殼」。
- 產生程式重跑（EXTRA 60 之後）：清單、verify、圖逐位元組相同。
- 過程圖：`overlays/stage2_hull_{bowq,sternq,side}.png`（yaw 30／150／90）。
- ⚠ 看得到的：船殼一整片黑（帶子、砲門在階段三）；船頭是平的圓頭到舷頂（espolón 在階段五）；艙裡是空的（甲板在階段四）。

## 階段三 砲門、塗裝、船尾窗（2026-10-15，TASK-0592）
設計 plan.json `paint`、`stern`；產生 `design/draft_ports.py`（船殼照 draft_lines.hull_volume ＝ 作品，階段二證過；結構照三叉戟號的 draft_ports）⇒ `masks/ports/carve.vox.txt`（8,633，帶刻之前的顏色守門）、`masks/ports/paint.vox.txt`（19,278，換色）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 砲門 ＝ `layout.ports`（每舷 9／8／2／2，兩舷同一組 x）：開口 (x, z) 範圍裡、那一舷 |dy| ≥ 6 的牆全刻；外擴 1 格那一圈牆漆玫瑰粉 242（reveal）。
- 塗裝（只換外板那一層的黑 36；水線下灰白不動）：
  - **wale 三條**（art.52：主甲板下 1 codo、主甲板上 2½ codos；puente 上 14 格比照）：玫瑰粉 2 列＋上下各一列金 248，照甲板舷弧走。
  - **船樓菱格**：toldilla（z 121–131）、alcázar 與 castillo（z 107–114／115）舷牆外面玫瑰粉菱形配黑底（週期 10、半徑 3，只照 x、z 算 ⇒ 兩舷對稱），上下金邊。
  - 舷頂最上一格金。
- 船尾 espejo（每個 (y, z) 從最後面往前那一段牆）：puente 5 扇、alcázar 5 扇、toldilla 3 扇窗（寬 5、刻最外一格、第二格玻璃 87、外一圈金框）；主甲板兩個追擊砲門（寬 7，整段牆刻穿）。窗寬一律奇數、對稱取整。
- 🩸 v1 每層砲列一整條 11 格的帶子（三叉戟號的作法）⇒ 舷側一半是粉的，不像 galleon；改成 wale 細帶＋砲門框。
- 🩸 wale 漏漆讀數（wale 高度裡外板還是黑的）兩次不是 0：① puente 的 wale 照舷弧在兩頭抬到 z 105，被從 z 104 起的船樓菱格蓋黑（184 格）⇒ 菱格改從 z 107 起；② 舷弧拋物線過了 x 120 還外推，最船尾 x 105–112 的 wale 抬到 z 107（16 格）⇒ `layout.deck_z` 的舷弧在 x 120／500 夾住（甲板範圍都在 x ≥ 113，主甲板與 puente 那一段 deck_z 變了；砲門 x ≥ 168 不受影響，verify_layout 重產）。
- 落格：`砲門:begin` → carvevox（顏色守門，carved 8,633）→ stampvox overwrite=1（placed 19,278）→ `砲門:end`。

讀數（`design/tools/check_stage3.py`，作品從 export 讀）：
- **結果帳**：作品 418,188 ＝ 設計（船殼 − 刻 ＋ 換色），缺 0、多 0、色差 0。
- 42 個舷側砲門開口（兩舷）：**從作品的格子量**，開口裡還有實心的 0 個；船尾兩個追擊砲門：船尾面那一段牆 0 格。
  **正向對照**（同一把尺量刻之前的 `船殼修正`）⇒ 42 個全報（每個 196 格）、追擊砲門各 49 —— 尺會說話。
  **反向對照**：`draft_ports.py --probe=skip_port=puente:4` ⇒ 只報 puente 第 4 個（兩舷各 196 格）。
- wale 漏漆 0；引擎 stats：1 元件、空腔 0、鏡像差 0。
- 換色：玫瑰粉 11,741、金 7,122、玻璃 415；刻掉：外板 2,467、肋骨 4,114、內板 2,052。
- 產生程式重跑：8 個輸出檔（船殼清單、砲門清單、verify、圖）逐位元組相同。
- 過程圖：`overlays/stage3_sheet.png`、`overlays/stage3_ports_{bowq,sternq,side,astern}.png`。
- ⚠ 看得到的：船尾四分之三那個角上，wale 與菱格在圓弧的船尾肩膀上從船尾看成一條一條直的粉色細線（像滴下來的漆）—— 先放著，船尾 galleries（TASK-0594）會蓋住那一段；艙裡沒甲板 ⇒ 從砲門看得到對面的牆。

## 階段四 甲板、船樓、艙口、梯子（2026-10-15，TASK-0593）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（結構照三叉戟號：甲板板＋橫樑＋圍欄、梯子踏板與 stringer、組起來找封閉空腔）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z；主甲板與 puente 有舷弧）：底艙 orlop 45（只 x 190–430）、主甲板 65、puente 85、alcázar 102（x ≤ 268）、toldilla 119（x ≤ 196）、castillo 102（x ≥ 422）。艙裡的甲板板 177、露天的（puente、三座船樓）209；橫樑每 16 格、寬 2、深 3（船樓 2）136；圍欄與 break 141。
- 開口：艙口三個疊在中線（後 214–226、主 312–332、前 395–409，orlop／主甲板／puente 都開）＋圍欄 2 格；梯子井；桅孔照桅的傾斜軸線（r：前、主 4、後 3、bonaventure 2.5；桅腳立在那一層 ⇒ 不開）。
- **break**（1618 art.5）：alcázar 前緣 x 268、toldilla 前緣 x 196、castillo 後緣 x 422 —— 一道艙壁（從下一層甲板到船樓甲板，兩扇門 寬 5 高 15）＋船樓甲板邊上一道 7 格高的胸牆（梯子頭留口）；放在船樓那一層的子作品裡。
- 梯子 9 座（每 3 格一階、每階 2 格、踏板 7 寬）：艙裡 3 座（orlop→主甲板 x 270、主甲板→puente 後 x 262／前 x 372，在上一層開井）；船樓 6 座（puente→alcázar、alcázar→toldilla、puente→castillo 各兩舷），靠在 break 外面、頭踩上船樓甲板。每一層要讓人走得到的甲板都有梯子（reach：orlop 1、主甲板 3、puente 6、alcázar 4、toldilla 2、castillo 2）。
- 子作品（parent 船殼、tags sub、0.1 m、800×320×640、at 0,0,0）：`-deck-{orlop,main,puente,alcazar,toldilla,castillo}`、`-ladders-{main,puente,alcazar,toldilla,castillo}`；梯子掛在它上面那一層甲板裡（關聯 `梯子`，meta `kind=ladders`），固定點 `<梯名>.foot／lo／hi／head`。組裝件關聯 `甲板-<層>`。
- **甲板 meta**（§9.3）：每層甲板子作品 `export format=vxk links=none` ⇒ `Blockside/src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的中文名）⇒ `work sub=meta`：kind=deck、deck、level 0–5、name、floor、thick（艙裡 4、船樓 3）。
  🩸 第一次匯出沒帶 `links=none` ⇒ 甲板子作品把關聯的梯子一起匯出，三座船樓的 floor 多了往下走的尾巴（alcázar 271–279 從 z 103 降到 92 ＝ 梯子踏板）。遊戲照 floor 判斷梯子接哪一層 —— 這條尾巴會讓 puente 的梯子腳被判到 alcázar。
- 預覽 preset（組裝件）：`藏船殼`、`只看主甲板以下`。
- 🩸 設計時抓到的兩個：① orlop 梯子的 lo 點頭頂 14 格碰到主甲板的橫樑（梯子井從第 4 格才開）⇒ 井從第 2 格開；② 主甲板多開了後桅的孔 —— 拿「整層甲板最高的 z」跟桅腳比，主甲板船尾舷弧抬到 71 > 後桅腳 67 ⇒ 改拿桅那一格的甲板高度。

讀數：
- 設計那一側：重疊（船殼／彼此）0、砲門往艙裡 20 格內被甲板／樑／艙壁擋到的 0、梯子點問題 0、封閉空腔 0、每件鏡像差 0。
- **結果帳**（`design/tools/check_decks.py`，每件從匯出讀）：11 件、168,839 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0。
- **組起來**（引擎 `stats structure=1 mirror=y:160`，組裝件）：587,027 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 `export format=parts`，遊戲讀的那一份）：9 座、36／36 點、跟設計差 0；每個點那一格是空的、腳下實心、頭頂 14 格空。
  **尺的反向對照**：把設計的 main-fwd.head 偏 3 格 ⇒ 報「跟設計差 1」、腳下不是實心（設計檔已還原，雜湊對過）。
  **反向對照**：`draft_decks.py --probe=drop_ladder=castillo-S` ⇒ 8 座、castillo 只剩 castillo-P。
- 產生程式重跑：14 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage4_sheet.png`、`overlays/stage4_decks_{nohull,bowq,sternq}.png`。
- ⚠ 還沒做：船樓的艙房（遊戲空艙房 §9.2，之後要配功能艙可以加）；彈藥庫（TASK-0598，orlop 上）。

## 階段五 船首喙、船首像、船尾裝飾與燈（2026-10-15，TASK-0594）
設計 plan.json `espolon`、`figurehead`、`stern_deco`；產生 `design/draft_deco.py`（讀組裝件現在的格子 ⇒ 船殼＋甲板＋梯子，佔用與貼面都照它算）⇒ `masks/deco/<部件>.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`；落格 `design/tools/build_deco.py`，之後的修正 `design/tools/delta_apply.py`（作品對清單：多的帶顏色守門刻、少的貼、顏色不同的換）。
- **船首喙**（`-espolon`，關聯 `船首喙`）：1618 art.45 manga 3/5 ＝ 72 格伸出艏柱（x 501–572）；甲板頂 z 73、3 格厚、半寬 24 收到 2；兩舷 head rail（4 格高、每 6 格一根柱、金頂條，停在船首像前面）；下面一片 cutwater（5 格寬、沿前緣 10 格的帶子，從 z 20 的艏柱掃到喙尖，前緣內側一條玫瑰粉線）。
  喙放在 z 73 是因為**艏斜桅**：它從主甲板（x 486, z 69）以 32° 往前上，x 500 中心 z 77.7、x 510 到 z 84 —— 喙放更高會被它穿過。讀數：艏斜桅那條線半徑 3 內的裝飾格 0。
- **船首像**（`-figurehead`，關聯 `船首像`）：死神見習生 —— 黑斗篷（下襬玫瑰粉）、兜帽裡蒼白的臉、兜帽兩側垂下粉髮、袖子握著立在中線的鐮刀（柄 132、刀刃 219 往前往下彎、柄頂一點金）；站在喙尖。鐮刀在中線 ⇒ 兩舷對稱。
- **船尾裝飾**（`-stern-deco`，關聯 `船尾裝飾`）：船尾陽台（puente 船長室那排窗下、伸出 espejo 5 格、半寬 26、玫瑰粉欄杆金扶手、每 8 格一個托架）＋兩舷 quarter galleries（x 102–140、z 86–118、伸出 4 格 ＝ art.69 的 ⅔ codo；兩排窗、玫瑰粉腰帶、上面一個收進去的頂）＋**三盞船尾燈**（外部模型，沿用 `gura-tridente-01m-lantern`，scale 0.5、meta `kind=light`，站在 toldilla 船尾舷頂 z 134、y 142.5／160.5／178.5）。
  ⚠ galleries 兩舷是一件裡一起產的（照 |dy| 算 ⇒ 對稱），不是造船規格 §2「一舷＋mirror=y 關聯」的做法 —— 它是貼著船殼曲面長的，一舷＋鏡像要另外處理 at 的換算，這件不值得；鏡像差照樣量（0）。
- **船名板**（`-name-board`，關聯 `船名板`）：espejo、alcázar 那排窗上面（z 113–119）、比 espejo 往外一格；3×5 字型「LA COSECHA」金字黑底玫瑰粉框；從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊。字不對稱 ⇒ **這一件的鏡像差 29 對照實報**。
- 裝飾不蓋船的格：落在船殼／甲板／梯子上的不放、照實數（stern-deco 10 格：gallery 的頂在船尾肩膀上用 z 118 那一層的外緣，碰到更上面的船殼）。

🩸 這一階段的坑：
- 設計一開始讀到的組裝件是**空的**：抄來的 `wio.export_list` 固定帶 `links=none`，組裝件自己沒有格子 ⇒ 加 `links` 參數（預設照舊 none）。
- 落過一次之後重產，設計讀的組裝件**已經含舊裝飾** ⇒ 把舊裝飾當成船、新的被大量跳過（喙 5,526 格被跳過）、galleries 往外長 ⇒ 設計那一側扣掉本階段自己的四件。
- 組起來 **28 個元件**（27 小塊共 109 格浮空）：head rail 頂條沿著越收越窄的寬度只在斜角相接、柱子之間一段段浮空；船首像的手、柄、刀刃也只在斜角相接 ⇒ 頂條在寬度變的地方補台階、袖子一塊、柄從甲板面起、刀刃逐段往上補。（第一次補台階的 range 差一格是空的，又多跑一輪。）
- `delta_apply.py` 用 heredoc 寫 ⇒ 反斜線被吃掉、語法錯（我記過的坑，又踩一次）⇒ 用 Edit 工具修。

讀數：
- **結果帳**（`design/tools/check_stage5.py`，每件從匯出讀）：船首喙 7,961、船首像 734、船尾裝飾 9,754、船名板 287，缺 0、多 0、色差 0。
- **組起來**（引擎 stats，組裝件）：605,763 格、**1 元件**、空腔 0；鏡像差 29 對（全是船名板的字）—— `hide_links=船名板` ⇒ 0。
- 跟船（船殼＋甲板＋梯子）重疊 0、部件之間重疊 0；艏斜桅那條線被擋 0；三盞燈腳下實心、models_broken 0。
- **反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 船首像鏡像差 0 → 668。
- 產生程式重跑：6 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage5_{sheet,full,bow,stern}.png`（bow 那張用 region 框，模型不跟著 region 裁 ⇒ 左上角的三盞燈是船尾的，不是浮在那裡）。
- 階段三的「船尾肩膀滴漆」：galleries 蓋住了那一段（stage5_stern.png）。

## 階段六 桅與帆桁（2026-10-15，TASK-0595）
設計 plan.json `rig_build`（桅帆尺寸與位置在 `masts`）；產生 `design/draft_masts.py`（讀組裝件現在的格子、扣掉本階段自己的件）⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen-<桅>.vox.txt`＋`yards_lateen.json`、`masks/bowsprit_hole/carve.vox.txt`、`yards_placement.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`。
- **桅**（每根一件子作品，關聯 `前桅`／`主桅`／`後桅`／`bonaventure`）：下桅（半徑 3.5→2.5；後桅 2.5→1.8；bonaventure 2→1.4，都比甲板桅孔小、用同一個圓的判斷式）＋**cofa**（圓的桅樓籃子：主 r 19（Palacio：上緣周長 ＝ manga，⚠ 二手）、前 r 15、後 r 9；地板 2 格、籃子 6 格高、玫瑰粉腰帶、金頂）＋上桅（前、主；半徑 2.5→1.5、頂一格金）。桅照 plan 的傾斜軸線（前 −3°、主 1°、後 3°、bonaventure 4°）。
  前桅腳插進船頭 deadwood 的那 112 格是船殼 ⇒ 不放（桅坐在船殼上）。
- **bonaventure 往前挪到 x 140**（v0 x 120）：桅腳往上 z 72–79 那一段落在船尾 espejo 的牆裡（被船殼擋 74 格）。甲板的桅孔照差量重開（puente／alcázar／toldilla 各刻補約 20 格，`delta_apply.py`）；lateen 後端伸出船尾從 4.55 m 降到 2.55 m。
- **艏斜桅**（`-bowsprit`，關聯 `艏斜桅`）：主甲板 (486, 69) 起 32°、23.7 m、半徑 3→2；**船頭牆開孔** 180 格（船殼 carvevox 帶顏色守門，標記 `艏斜桅孔`），孔整個由艏斜桅填滿。
  🩸 v1 牆裡那段當成船殼跳過 ⇒ 艏斜桅在牆裡斷開、牆外那段 4,273 格浮空（組起來 2 個元件）；v2 孔比桿大半格 ⇒ 牆裡 10 個小空腔（16 格）；v3 孔整個填滿 ⇒ 1 元件、空腔 0。設計那一側讀開孔之前的船殼（`砲門:end`），重產時孔的清單才不會變空。
- **方帆桁 5 根**（外部模型、放在各自的桅子作品裡）—— 沿用憲法號的帆桁元件，只沿長度（y）縮放到本船的長度（造船規格 §2.1）：

| 帆桁 | 長 | 來源（憲法號） | scale y | brace |
|---|---|---|---|---|
| fore course | 21.7 m | yard-fore-course（24.9） | 0.8715 | −15° |
| fore topsail | 9.7 m | yard-main-royal（9.3） | 1.043 | −17° |
| main course | 27.2 m | yard-main-course（29.1） | 0.9347 | −15° |
| main topsail | 12.1 m | yard-main-topgallant（14.3） | 0.8462 | −17° |
| spritsail | 14.5 m | yard-spritsail（18.5） | 0.7838 | 0 |

  meta `kind=yard、mast、yard、sail（帆名，階段七用）、length_m、pivot_anchor=pivot、turn_axis=z、rotate_z_deg`。吊點在桅軸前面（桅半徑 ＋3.5）；spritsail 在艏斜桅 85% 處、往下 5 格。
- **lateen 帆桁 2 根**（新做的子作品 `-yard-mizzen-lateen`、`-yard-bonaventure-lateen`；沒有現成的）：斜桿，前端低、後端高；後桅 24.5 m／40°／吊點在前端往後 40%；bonaventure 17 m／45°／45%。固定點 pivot、sling、fore、peak、jackstay-NN（每 8 格）。模型 rotate 0（水平投影沿船長），放在桅的左舷側（y − (桅半徑＋2.5)），不穿過桅。meta `yard=gaff`、`rig=lateen`。
  **遊戲怎麼轉**：讀 `Blockside/src/js/30_rig_physics.js` 的 braceYards —— `yard` 是 gaff／boom 的照縱帆往下風擺（8°–80°），其他當方帆桁；所以 lateen 標 `yard=gaff`。已在酒館問 ame（seq 24767），**她還沒回**。⚠ 擺動時前端會掃向主桅那一側（後桅帆桁前端 x 271、主桅 x 296）。

讀數：
- **結果帳**（`design/tools/check_stage6.py`，每件從匯出讀）：前桅 11,932、主桅 13,264、後桅 3,597、bonaventure 1,229、艏斜桅 4,766、lateen 1,620／1,096，缺 0、多 0、色差 0；船殼 ＝ 砲門:end − 艏斜桅孔 180 ＝ 418,008，缺 0、多 0、色差 0；四層甲板（桅孔搬位）缺 0、多 0、色差 0。
- 帆桁模型 7 根：meta 齊全、來源固定點齊全；models_broken 0（五件桅子作品）。
- **組起來**（引擎 stats，`hide_links=船名板`）：640,084 格、1 元件、空腔 0、鏡像差 0。
- **帆桁穿船**：沿線每 0.5 格取樣、半徑約 1 內有實心（離自己吊點 7 格內不算）⇒ 7 根全 0。**反向對照**：`--probe=pivot=yard-main-course:-200`（往下放到船殼的高度）⇒ 只有那一根報 34 格。
- 作品裡每根帆桁模型的 at／pivot／rotate／scale ＝ 設計（yards_placement.json）：7 根 0 差。**反向對照**：暫時把設計的 yard-main-course at.z −3 ⇒ 只報那一根（作品 274.84 ≠ 設計 271.84）；設計檔已還原、雜湊對過。
- lateen 後端伸出船尾：後桅 0.65 m、bonaventure 2.55 m。
- 梯子點（組裝件 parts）照樣 36／36、0 問題（甲板桅孔搬位之後重量）。
- 產生程式重跑：18 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage6_{sheet,full,side,sternq}.png`。

## 階段七 索具與帆（2026-10-15，TASK-0596）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（結構參考三叉戟號 draft_rigging）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/{ensign,cross_course}.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件、照 |dy| 算 ⇒ 對稱）：每根桅一塊 4 格寬的板、舷頂下 3 格，外緣一排 deadeye（3 格高）；2,164 格、跟船重疊 0。每舷 shrouds 前 5、主 6、後 3、bonaventure 2，前／主各加 1 條 topmast backstay。
- **固定點 113**：桅上 hound／stay-head／futtock／tm-hound／tm-stay-head／cofa 邊（rim、rim-low）／top-aft；stay 下端（前桅 castillo 上、主桅 puente 上、後桅 alcázar 上）；艏斜桅 forestay-foot／cap-top／side／bob；船首喙 cutwater 上的 bobstay 腳；船殼舷頂的 belay；puente／toldilla 甲板上的 lateen tack。cofa 邊那 26 個點落在籃子的實心上 —— 就是要綁在那裡。
- **繩 368 條**：shrouds 32、topmast shrouds 12、futtock 12、backstays 4、stays 6、艏斜桅 4、ratlines 278（下 190、上 88，子繩）、sheets 14、tacks 6。色、粗、slack 照造船規格 §6。
- **帆 9 面**：fore／main course（很深、帆腳在舷頂上 5 格；**畫勃艮第十字**）＋ topsail（sheet 綁下一根帆桁同舷 earing）、spritsail（sheet 往後綁船首樓舷頂）、mizzen／bonaventure lateen（前緣沿帆桁 fore → peak、clew 自由、兩舷 sheet 綁船尾舷頂、tack 從帆桁前端綁甲板）、ensign（**勃艮第十字**，掛在 bonaventure 帆桁後端）、pennant（主桅頂、玫瑰粉）。預設風 4.5,−1.5,0、3 秒。
- **meta**（§9.1）：帆 9（course、topsail、spritsail、gaff ×2、flag ×2）、帆自己的繩 20（sheet／tack ＋ sail ＝ 帆名）。lateen 標 `sail=gaff`（遊戲預設戰鬥帆才開）；spritsail 標 `sail=spritsail`（遊戲不認得的帆種照滿帆，31_sailing.js）。

讀數（`design/tools/check_stage7.py`，從作品／CLI 讀）：
- channels 結果帳 2,164 ＝ 2,164，缺 0、多 0、色差 0。
- CLI：繩 368、**ropes_broken 0**；帆 9、**sails_broken 0**。
- meta（從作品讀回）：帆 9／9、帆自己的繩 20／20、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字（7／7）。
- **反向對照**：check 讀完作品之後當作 `main-course.sheet-S` 沒標 ⇒ 只報那一條；`draft_rigging.py --probe=nometa=fore-topsail.sheet-P` ⇒ 只報那一條。
- 組起來（hide_links=船名板）：642,240 格、1 元件、空腔 0、鏡像差 0。
- 產生程式重跑：5 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage7_{full,side,sternq}.png`、`overlays/stage7_ensign_texture.png`。
- ⚠ lateen 的標法 ame 還沒回（酒館 seq 24767）；她要別的就改帆桁與帆的 meta（不動格子）。
  ⇒ ame 2026-10-15 17:59（酒館 seq 24919）：後桅、bonaventure 的三角帆照我標的 `yard=gaff、rig=lateen` 照 gaff 畫（遊戲 30_rig_physics.js braceYards：往下風擺 8°–80°），截圖看得到，**不用改 meta**。

## 階段八 砲（2026-10-15，TASK-0597）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（幾何共用 `design/gunsim.py`；讀組裝件現在的格子 —— 模型不在匯出裡 ⇒ 重產時不會撞到自己上一輪的砲）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`。
- **44 門，全部是外部模型、沿用現有的砲**（造船規格 §2.1；`work sub=components kind=gun`），掛在所在甲板的子作品上（藏甲板就一起藏）；P 舷 mirror=y，meta `kind=gun、gun、deck、side、port`：

| 甲板 | 砲 | 來源 | 門數 | 退 | 砲口伸出（設計）|
|---|---|---|---|---|---|
| 主甲板 | 18 磅長砲 `gun=18l` | 憲法號 -gun-long18（0.05 m、scale 0.5、pivot 13.5,38.5,0） | 9／舷 | 5.5–7.5 | 4.0–6.0 |
| 主甲板船尾 | 18 磅追擊砲 `gun=18chase` | 同一件；φ ±90、往中線偏 1.5 | 2 | 8 | 3.5 |
| 上甲板（puente） | 12 磅長砲 `gun=12l` | 風暴角號 -gun-12l（pivot 9.5,38,0） | 8／舷 | 3.5–5.0 | 6.25–7.75 |
| 後甲板（alcázar） | 6 磅砲 `gun=6l` | 風暴角號 -gun-6l（pivot 8.5,33,0） | 2／舷 | 4 | 6.25 |
| 船首樓（castillo） | 6 磅砲 `gun=6l` | 同上 | 2／舷 | 5–8 | 2.25–5.25 |

- 擺法（造船規格 §4.2，同餘燼號 place_guns.py）：從船殼外面沿砲身往裡退（每步 0.5），退到模型每一格的格心＋八個角（inset 0.2）都不在組裝件實心裡；ok ＝ 砲口超過船殼面、砲口那一點空、砲最底層格子正下方有實心 ≥ 0.5；先 ok、再低、再退得少。
- 🩸 **主甲板砲門加高一格（船殼改了）**：v1 主甲板 18 門砲口全在牆裡 4.5–5.5 格，碰到的全是門楣那一層 —— 沿用的 18 磅砲管頂在站立面上 12.5 格，art.42 的砲門（門檻 1 codo、1¼ codos 見方 ＝ 7 格）門楣在站立面上 12 格。門檻照 art.42 不動，主甲板舷側＋船尾追擊砲門 h 7 → 8（⚠ 偏離 art.42）。
- 🩸 **舷弧是台階**：v2 第 7 門還是頂到門楣、第 2 門腳下只有一半是甲板 —— 甲板舷弧一格一格地抬，18 磅砲架 13.5 格寬會跨在台階上、站在高的那一階，比「砲門中心那一點」量的甲板高 1 格。⇒ `layout.ports` 加 `ref_pad`：門檻改從砲門左右各多 4 格那一段甲板的最高處量（主甲板第 7 門 71 → 72）；船尾追擊砲門加 `ref_x` 118–141（船尾最後一階比 x 130 高 1 格，76 → 77）。support 門檻 0.6 → 0.5：遊戲判斷掉不掉是從外框中心往下 12 格內找甲板（Blockside/src/js/10_ship.js:47），跨台階的砲架有一半懸 0.1 m（照實記：主甲板第 2、7 門與兩門追擊砲 support 0.5）。
- 船殼差量：`tools/hull_expected.py` 照清單組船殼（hull − 砲門刻 ＋ 塗裝 − 艏斜桅孔）；**先拿舊的砲門清單組 ⇒ 跟作品 0／0／0**（帳組得對），再拿新的 ⇒ `delta_apply` 刻 560＋換色 490（v1）、刻 112＋補 112＋換色 162（v2）；套完 0 差；標記 `主甲板砲門加高:begin／end`。
  ⚠ 落紙那一步我寫「多刻 1,022」是算錯（主甲板 18 門再 × 2 舷，重複算了一次）；實際舷側 504 ＋ 追擊 56 ＝ 560，每門正好多一列。

讀數（`design/tools/check_stage8.py`，從作品讀：models.json、CLI `work sub=models`、組裝件匯出）：
- 砲模型 44 ＝ 設計 44，CLI 狀態 ok 44（models_broken 0）；at／pivot／rotate／scale／mirror ≠ 設計 0。
- 外框：gunsim 的變換 vs CLI 印的外框，44 門最大差 0.05（CLI 印到 0.1）—— 變換公式對。
- **碰撞 0 門**；**砲口不在船殼外 0 門**（砲口實心、或沒超過砲門兩側的船殼面；作品量的伸出 1.0–7.0，最少是船首樓 P02 —— 船頭收窄、兩側的面比較外面）。
- meta：kind=gun、gun 都在遊戲砲種表（18l 18、18chase 2、12l 16、6l 8）、來源都有 muzzle／breech。
- 砲撞砲 0、兩舷不對稱 0（P 的 at.y ＝ 321 − S；v1 我寫成 320 − y，22 對全報 —— 尺錯：格 y ↔ 320 − y 換成連續座標是 321 − y）。
- **反向對照**：`check_stage8.py --push=砲U-P05:3` ⇒ 碰撞只報那一門（3,897 樣本）；`draft_guns.py --probe=push=M-chase-stern-S:3` ⇒ 只報那一門（3,170）。**正向對照**：`--push=砲M-S04:-8`（往裡拉）⇒ 砲口只報那一門、伸出 −2.5（＝ 5.5 − 8）。
  🩸 砲口那一格 v1 量「砲口往外 20 格內有沒有船殼」，失明兩次：① 船殼格網框外當實心 ⇒ 40 門假警報（`gunsim.Grid` 加 outside）；② 修好讀 0，可是往裡拉 8 格**照樣 0** —— 砲門是洞，砲口縮在洞裡往外看一路都空。改量砲門兩側的船殼面。
- 組起來（hide_links=船名板）：641,680 格、1 元件、空腔 0、鏡像差 0。階段三的砲門檢查換到 `主甲板砲門加高:end` 量：42 個舷側砲門、2 個追擊砲門開口裡實心 0（結果帳缺 180 ＝ 艏斜桅孔，階段三的設計不知道它）。
- 產生程式重跑（draft_layout／draft_ports／draft_guns）：8 個輸出檔逐位元組相同（verify_layout 因砲門高度改了一行）。
- 過程圖：`overlays/stage8_{full,side,sternq,decks}.png`（decks：只看四層有砲的甲板＋砲）。
- ⚠ 還沒量的：砲班站不站得滿（遊戲 shipcheck，交船 TASK-0599 時跑）；砲索與砲具（§4.4）不在這張單。

## 階段九 彈藥庫與甲板物件（2026-10-15，TASK-0598）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（讀組裝件現在的格子、扣掉本階段自己的兩件子作品）⇒ `masks/gear/{magazine,skids}.vox.txt`、`gear_placement.json`、`verify_gear.json`；落格 `design/tools/build_gear.py`。
- **彈藥庫**（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine、pos=aft、powder_lb=11200`）：底艙船尾那一段 x 194–244（orlop 只鋪 x 190–430 就是留給它的），門開在船頭那道艙壁、對著底艙梯子（foot x 269）。做法照夜燈號 draft_magazine.py：兩道橫艙壁銅皮 168＋橡木框 136、門洞 5 格寬、靠船殼那一側包銅、松木地板 177（每 6 格橡木壓條）；9,807 格。固定點 `blast` (220,160,54)、`door` (244,160,47)。
  火藥桶 **112 桶**（憲法號 -powder-barrel，0.02 m、scale 0.2）：底層 74、第二層 38（木架、立柱 104）。⚠ 112 是照砲數換算（憲法號 54 門 138 桶 × 44／54），不是史料。⚠ galleon 的 pañol de la pólvora 在船尾下層只讀到一般說法，未查證。
- **小艇架**（`-boat-skids`，關聯 `小艇架`）：船腰三座橫架（x 305、344、372；橫樑 z 96–97、2×2 立柱落到甲板），612 格 —— 船腰沒有連續 90 格的空甲板（主桅、主艙口、前梯子井），小艇擱在架上跨過主艙口。中間那座在小艇外框中心正下方：遊戲的「腳」是外框中心往下第一格實心 ⇒ 腳是架子，不是 1.2 m 下面的甲板。
- **模型**（沿用現有元件，§2.1）：

| 名 | 掛在 | 來源 | at | meta |
|---|---|---|---|---|
| 舵輪 | deck-alcazar | 憲法號雙舵輪（6 艘在用） | 224, 160.5, 103 | kind=wheel |
| 羅經櫃 | deck-alcazar | 夜隼號羅經櫃（4 艘） | 243, 160.5, 103 | kind=binnacle |
| 主絞盤 | deck-puente | 餘燼號主絞盤（7 艘） | 280.5, 160.5, 86 | kind=capstan |
| 小艇 | deck-puente | 餘燼號 cutter 9 m | 345, 160.5, 98 | kind=boat、boat=cutter、length_m 9 |
| 桶-001…112 | -magazine | 憲法號火藥桶 | — | kind=powder、powder_lb 100 |

  z 由產生程式量（從所在甲板子作品的頂往上、第一個不撞而且腳下有東西的高度）。⚠ 1618 年的 galleon 用 whipstaff，舵輪要到 18 世紀 —— 遊戲的舵手要 kind=wheel，照遊戲；toldilla 底下淨高 1.4 m 站不下 2.1 m 的舵輪 ⇒ 放在後甲板、後桅前面。
- 🩸 火藥桶擺法照抄夜燈號，夜燈號只有一層、四個坑都沒被踩過：① 第二層木架的立柱往下長只看格子空不空 —— 桶是模型、不在格子裡 ⇒ 立柱長進底層的桶身（10 個桶報碰撞）；② 「格子空」的半徑 R＋0.3 太樂觀（一格碰得到半徑 R 的圓，格心最遠到 R＋0.71）⇒ 改 R＋0.75；③ 改完立柱被底層的桶擋住長不下去 ⇒ 6 塊架板浮空（造船規格 §8 早就寫了）⇒ 立柱改在架板底下找一路通到地板的兩欄、找不到就不放那一對；④ 兩舷各挑立柱、排到 112 停在第二層一半 ⇒ 鏡像差 74／300 ⇒ 一次放一對、P 舷照 S 舷鏡過去。
  還有一格是尺：桶與桶相距 0.2 格，v1 用世界格取整量「重疊」⇒ 全報；改成把 a 的格心換回 b 自己的格子座標去比 ⇒ 0。
- 🩸 z 自動量 v1 從 z 40 往上掃 ⇒ 13 格高的絞盤會先落進底艙（寫完就看到，沒跑出來）⇒ 從所在甲板子作品的頂開始。

讀數（`design/tools/check_stage9.py`，從作品讀）：
- 結果帳：彈藥庫 9,807、小艇架 612，缺 0、多 0、色差 0。
- 模型 116 ＝ 設計，CLI 狀態 ok 116；參數 ≠ 設計 0、撞實心 0、腳下 12 格內沒有實心 0；模型彼此重疊 0（設計那一側）。
- 彈藥庫：powder_lb 11,200 ＝ 作品裡的火藥桶 112 × 100；blast 是空氣；door 是空氣、腳下實心。
- 遊戲要的 kind：magazine、powder、wheel、binnacle、capstan、boat 一種都不缺、沒有 kind 的 0。
- **反向對照**：`--drop=主絞盤` ⇒ 缺 capstan、只報 主絞盤；`--drop=link:彈藥庫` ⇒ 缺 magazine、只報那條關聯；`--drop=桶-057` ⇒ 只報那一桶；`draft_gear.py --probe=nokind=小艇` ⇒ 只報 小艇。
- 新格：落在實心上 0、封閉空腔 0、浮空 0；鏡像差 彈藥庫 0、小艇架 0。
- 組起來（hide_links=船名板）：652,099 格（＝ 641,680 ＋ 9,807 ＋ 612）、1 元件、空腔 0、鏡像差 0。梯子點 9 座 36／36、問題 0（小艇架沒擋到前梯子井）。
- 產生程式重跑：4 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage9_{magazine,waist,full}.png`（magazine：只看彈藥庫＋底艙；waist 用 region 框 —— 模型不跟著 region 裁，浮在空中的帆桁與三盞燈是框外的）。
- ⚠ 這艘船**還沒有舵、也沒有錨**（船殼裡沒有，也沒有模型）—— 不在 TASK-0598 的範圍，照實記；交船前要不要補看 Tim（舵沒有 ⇒ 外觀缺一塊；錨可以用共用元件 `-anchor`）。⇒ Tim：「開一張單先補舵與錨」＝ TASK-0619（階段九半）。

## 階段九半 舵與錨（2026-10-15，TASK-0619）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（讀組裝件現在的格子、扣掉本階段的錨架；船首樓的砲取樣成格一起算）⇒ `masks/rudder/{rudder,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`；落格 `design/tools/build_rudder_anchor.py`。
- **舵**（新子作品 `-rudder`，0.1 m；舵是這艘船自己的形狀 ⇒ 不沿用）：沿艉柱後緣（`lines.x_post`，斜 23.8°）從龍骨底到 z 76，3 格厚（y 159–161）；舵葉 1.4 m 往上收到 1 m、水線以上 0.5 m 的舵頭；水線下白 182、上黑 36、每 12 格一道鐵箍 73；2,243 格。
  組裝件的外部模型 `舵`：at ＝ pivot ＝ 鉸鏈下端 (150, 160.5, 0)（子作品的世界座標原樣），meta `kind=rudder、hinge_x／y／z、axis (−0.4035, 0, 0.915)、max_deg 35、turn_axis=hinge`；固定點 `stock-top` (113,160,76)，3 格內就是船殼（遊戲找 8 格內）。
  🩸 前緣兩側削 1 格（bearding）：v1 沒削 ⇒ 轉 ±35° 時兩側前緣掃進艉柱 39 格（寫程式前就推得出來：鉸鏈在艉柱面上、舵 3 格厚）；削 1 ⇒ 0（試過 1／2／3）。
  ⚠ galleon 的舵頭從 espejo 下面的 limera 穿進船裡、接舵柄與 whipstaff —— 本船舵頭貼在 espejo 外面、沒有開孔、沒有舵柄。
- **錨**（共用元件 `basecamp-frigate-constitution-01m-anchor`，scale 0.85 同夜燈號 ⇒ 遊戲裡同一份網格；meta `kind=anchor、anchor=bower`）：兩舷各一，掛在新子作品 `-anchor-gear`（關聯 `錨架`）裡。吊在船頭舷外 x 490：錨臂順著船殼切線（rz ±45°，P 舷不鏡像、只轉 −45° ⇒ 取樣格兩舷對稱差 0）、橫桿越過船首樓欄杆、ring 在 z 131.5、離船殼 2.5 格。
  **錨架**：錨冠底下一塊 billboard 托板（3 格厚、橡木 136），兩舷 872 格 —— 遊戲判斷掉不掉是外框中心往下找實心 ⇒ 錨的腳是托板（間距 0）。⚠ 沒有吊錨桿（cathead）、沒有 fish tackle。
  🩸 搜尋 v1 每個 x 一找到可行的高度就停 ⇒ 橫桿下緣擦到欄杆頂（z 116），整隻錨被推出去 18 格（＝ 半根橫桿）；改成每個高度都試完、取最貼船的 ⇒ 2.5 格。
- **錨鏈孔**：船殼固定點 `hawse-S` (494,181,88)、`hawse-P` (494,139,88)（上甲板那一層的船殼外緣格；⚠ 只登記固定點，沒有開孔）。

讀數（`design/tools/check_stage95.py`，從作品讀）：
- 結果帳：舵 2,243、錨架 872，缺 0、多 0、色差 0（舵削斜走 `delta_apply` 刻 154）。
- 舵：模型 1、CLI ok；meta 齊；stock-top 8 格內有船格（曼哈頓 3）；舵的格跟組裝件重疊 0；轉 ±35° 掃進實心 0（資訊：遊戲轉舵不做格子碰撞）。
- 錨：2 隻、CLI ok、撞實心 0、腳是錨架、來源有 ring；hawse-S／P 在船殼格上、各在那一舷。問題 0。
- **反向對照**：`--drop=stock-top` ⇒ 只報舵沒有 stock-top；`--drop=錨-S` ⇒ 只報 S 舷沒有錨；`--drop=hawse-P` ⇒ 只報 hawse-P；`draft_rudder_anchor.py --probe=shift=錨-S:-3` ⇒ 只報 錨-S（1,195 樣本）。
- 組起來（hide_links=船名板）：652,971 格（＋錨架 872）、1 元件、空腔 0、鏡像差 0（舵是模型、不在格子裡）。
- 產生程式重跑：4 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage95_{stern,bow,full}.png`（stern、bow 用 region 框 —— 模型不跟著裁）。

## 階段十 匯進 Blockside（2026-10-15，TASK-0599）—— 在暫存副本驗
- ⚠ **沒有動真的 Blockside**：Blockside 工作樹裡有一批還沒提交的改動（TASK-0616 材質那一批，`src/config/game.json` 也在裡面），`admin.py import` 會改寫 game.json、template、成品 ⇒ 匯進去等於把我的船混進別人做到一半的檔案。照造船規格 §9.4「自己在 Blockside 的暫存副本跑」：`git archive HEAD`（Blockside 7884463）＋ `VoxelKit/_cache` 複製到 scratchpad，在那裡 `admin.py import --work calli-cosecha-01m-assembly --id cosecha --name 收穫號`。真的匯入交給遊戲那側（ame）／Tim。
- 匯入：成品多一艘 `ship-cosecha`（設定檔船隻清單、`index.html` 標籤都有），壓縮還原驗算 8 艘逐位元組相同；`admin.py verify` ✓。.vxk：653,268 格、checksum 1150694525、繩 368、帆 9、模型 173（砲 44＋甲板物件與桶 116＋錨 2＋舵 1＋帆桁 7＋燈 3）、關聯外框 25；格子鏡射差 29 格（＝ 船名板的字）。
- **shipcheck**（遊戲開一場跑 2 秒）：v1 ✗ 0 ⚠ 6 —— 其中「砲班站不滿」2 門（船首樓前面那對 6 磅砲 2／3）。
  🩸 原因是階段九半剛掛上去的錨：錨轉 45°，遊戲拿模型的**軸對齊外框**（外擴 1 格、往下 3 格）當佔位（Blockside 40_crew.js `blocked`）⇒ 錨外框 x 478–506 蓋到那門砲第二個砲手的站位 (483,183) 四格內。寫了 `design/tools/crew_sim.py` 照遊戲的 standNear／standZ／blocked 模擬 ⇒ 同樣兩門、同樣 2／3、指出擋路的是 `錨架/錨-S`（第二把尺：模擬 vs 遊戲，同一個結果）。
  ⇒ 船首樓第二對砲門往後挪：plan `ports.tiers.castillo.x_to` 480 → 461（第二門 474–479 → 455–460，在前桅 channels x 431–472 底下，跟第一門一樣）。船殼走 hull_expected＋delta_apply：刻 288、補 298、換色 438，標記 `船首樓砲門後移`；套完 0 差；階段三的砲門檢查換到 `船首樓砲門後移:end`：開口裡實心 0。砲重擺（check_stage8：碰撞 0、砲口在船殼外 0 門不合、meta 0 不合）；錨位置不變（錨架、舵 0 差）。
  v2：crew_sim 站不滿 0；**shipcheck ✗ 0 ⚠ 4、砲班 0 門缺 0 人**。剩下 4 個都是遊戲那側的設定：geo 沒填、送藥手 21／22、陸戰隊 6／12、桅頂水手 8／16。
- **反向對照**（checksum）：組裝件開草稿貼 1 格、匯出 ⇒ 653,269 格、checksum 3969875597（≠ 1150694525）；丟掉草稿再匯 ⇒ 653,268、1150694525。
  🩸 第一次匯出沒帶 `draft=1` ⇒ 草稿那一格沒進匯出、checksum 照舊 —— 量的是「草稿進不進匯出」，不是 checksum 會不會變；帶上 `draft=1` 才量到。
- **rooms.py**：候選艙房 0 間（這艘船沒有隔艙房）。**decks.py**：六層甲板子作品各匯出（`links=none`）⇒ floor、thick 跟作品上的 meta（decks_meta.tsv）完全相同。
  🩸 第一次又沒帶 `links=none`（階段四踩過、寫在本檔上面）⇒ 三座船樓的 floor 多了往下的尾巴；照規矩重量才相同。
- **給遊戲那側填 geo 的高度**（格、z 0 ＝ 龍骨底）：設計水線 52；甲板地板（站的那一格）底艙 46、主甲板 66–72（舷弧）、上甲板 86–92、後甲板 103、船首樓 103、船尾樓 120；砲口（砲軸）主甲板 76.75–79.75、船尾追擊 82.75、上甲板 93.25–95.25、船樓 109.75；桅頂平台（cofa 底）前 289、主 287、後桅頂 251、bonaventure 頂 208；帆桁 course 前 277／主 275、topsail 前 410／主 411；船殼 x 91–500（船尾面到船頭）、組裝件 x 91–687（含艏斜桅）、y 99–221、z 0–437。
- **開得了戰**：暫存副本的成品用無頭 Chrome 開 `index.html?ship=cosecha,constitution&demo=8&still=1`（照 admin.py shipcheck 的 Chrome 參數加 `--screenshot`）⇒ `overlays/stage10_battle.png`：收穫號張帆、course 的勃艮第十字、砲班站在甲板上、船腰的小艇、船尾三盞燈亮著，憲法號在後面（旗是遊戲換的陣營旗）。
- 交船時跟 ame 問了新砲種與三角帆（酒館 seq 24898）。
- **ame 匯進 Blockside main**（4863f9b，酒館 seq 24919）：geo 照上面的高度填（露天甲板 86–121、砲甲板瞄 74–97、帆具瞄 140–330）、陸戰隊 6、桅頂水手每根 1；三角帆照 gaff 畫、不用改 meta；錨轉 45° 外框蓋到甲板那件她記下了，之後遊戲改成照模型實際形狀判斷佔位。
  回讀（我這側）：Blockside 有 4863f9b；`game.json` 有 cosecha 與 geo；`vxk_lock.json` 指紋 `c:bab7db…` ＝ 暫存副本那一份；`_cache/cosecha.vxk` 653,268 格、checksum 1150694525、work calli-cosecha-01m-assembly。
  自己在真的 Blockside 跑 `admin.py shipcheck --id cosecha`（只寫 reports/）：✗ 0、⚠ 2 —— 送藥手 21／22、**桅頂水手 2／4**（ame 報 ⚠ 1；我跑的時候 Blockside 工作樹另有 11 個未提交的改動，不一定是她跑的那一份程式；2／4 可能是後桅、bonaventure 沒有能站的平台 —— bonaventure 本來就沒做 cofa）。砲班 0 門缺人。

## 階段十一 後桅與 bonaventure 的桅頂平台（2026-10-15，TASK-0623）
Tim：「cofa 補吧」「補完 GO」。改 plan `rig_build.tops`（mizzen 9 → 12、bonaventure 新加 13、`tops_z.bonaventure` 206）＋ `draft_masts.py` 吃平台高度覆寫；兩件桅子作品走 `delta_apply`。
- 遊戲怎麼找桅頂站位（Blockside 10_ship.js findMasts ＋ 40_crew.js topSpot）：桅的 x ＝ 最低橫帆桁（沒有 ⇒ 最低的非 boom 帆桁）吊點附近、吊點下 10–40 格中線格子最多的那一欄；從吊點高度往上，第一層「半徑 9／12／15／18、16 個角度」有 6 個以上站得住（腳下實心、頭頂 14 格空）的就是平台。後桅 cofa r 9 的牆正好落在 r 9 那一圈、bonaventure 沒有 cofa ⇒ 兩根都找不到。
- `tools/crew_sim.py` 加桅頂那一段（照上面的規則）：改之前模擬 ⇒ 前、主找得到、後桅與 bonaventure ✗ ＝ shipcheck 的 2／4（第二把尺對得上）。
- **後桅** cofa r 9 → 12（plan 先試 13 ⇒ 三角帆桁往船尾斜上去擦到地板邊 2 格 ⇒ 12 ⇒ 帆桁穿船 0）：刻 438、補 986。**bonaventure** 新加 cofa r 13、平台 z 206（照平台公式是 197，在 hound z 204 下面 ⇒ shrouds 會穿過平台 ⇒ 放到 hound 上面）：補 1,702、換色 12。兩件 0 差、鏡像差 0。
  ⚠ 後桅 r 12、bonaventure r 13 比照前桅 15 是設計決定（遊戲要站人），沒有史料。
讀數：
- 模擬：bonaventure 平台 z 207（22 點）、前 289（32）、主 287（53）、後桅 237（16）；砲班照樣 0 門站不滿。**反向對照**：`crew_sim.py --nocofa=mizzen`（拿掉後桅 cofa 的 1,486 格）⇒ 只報後桅找不到。
- 繩（直線近似、兩端 2 格不算）：後桅、bonaventure 的繩穿過 cofa 0 條。⚠ 另外量到 8 條前／主桅 topmast shrouds 穿過自己 cofa 的籃子牆 6–9 個取樣 —— 階段七就有（綁在 cofa 邊上、尾段擦過牆），這次沒動。
- 帆桁穿船 7 根全 0；組起來（hide_links=船名板）655,231 格、1 元件、空腔 0、鏡像差 0；draft_masts 重跑逐位元組相同（其他 8 個輸出跟改之前一樣）。
- Blockside 暫存副本 `reimport`：.vxk 655,518 格、checksum 2993321142（模型 173、繩 368、帆 9）；**shipcheck「桅頂水手」那一條沒了**（暫存那份設定是預設員額 4／根：船員 265 → 273）；✗ 0、⚠ 3（geo —— 暫存那份沒有 ame 填的 geo、送藥手 21／22、陸戰隊 6／12）。真的 Blockside 要請 ame reimport（checksum 變了）。
- 過程圖：`overlays/stage11_tops.png`（region 框船尾上空；模型不跟著裁）。

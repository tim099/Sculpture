# 康塞普西翁號（Nuestra Señora de la Concepción y las Ánimas）—— 西班牙 Capitana Real，三層甲板的大帆船 galeón，1687 年下水（0.1 m／格）—— 建造筆記

委託：TASK-0969（Tim 2026-10-27「969 GO」；母單 TASK-0964 的 8 種候選之一）：《Blocksail》1666 加勒比船型 —— 西班牙大帆船 nao／galeón，印度群島船隊的大型商船、運寶船。照造船規格雕刻、匯入 Blockside、接進 Blocksail 船型清單。
流程：照 `Ship_Steps` 步驟表走（步驟表貼在 TASK-0969 的驗收標準，每一步只讀那一行寫的文件）。帆船、舷側砲、封閉砲甲板、全船木頭 ⇒ 刪步驟 13。

## 方向（Tim 2026-10-27 拍板）
- 收穫號 `calli-cosecha-01m` 已經是 1618 年條例 21 codos 的 galeón（946½ t、44 門），Maravillas 891 t 同級 ⇒ Tim：「參考現代模型以及資料另外造噸位更大 火力更強的呢」「如果找不到圖紙的話」⇒ **比收穫號大一級、砲更多**；資料先找圖紙，找不到再照現代模型與文字資料推。
- Tim 給的參考圖（模型照片）：四根桅（前、主、後桅三角帆、船尾小後桅 contramesana）、船身三排砲門＋船樓砲門、高船尾樓兩舷側廊、船首喙、前主桅有上桅帆、斜桅帆＋斜桅頂帆。
- 研究（`references/research_concepcion_2026-10-27.md`）：有當年圖紙的大型 galeón 只有 Capitana Real **Nuestra Señora de la Concepción y las Ánimas**（Gaztañeta 1681 設計、Colindres 1687 下水、1,550 t、三層甲板＋船尾樓、94 門）⇒ Tim 選「就是 Concepción 本人」＋「四根，照參考圖」⇒ 船名 **康塞普西翁號**。
- 年代：比 1666 晚 21 年 —— Tim「雖然遊戲起始於1666 但世界時間會推進 有些船可以在時間到後才出現」⇒ Blocksail 那側照下水年 1687 才出現。

## 座標約定（照藍鯊號／收穫號，產生程式也從它抄來）
- 空間 900×320×700；X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 160 格，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- ⚠ 一開始建成 Y 360，改回 320：抄來的工具全部把中線寫死成 160。改尺寸時組裝件的關聯擋著 ⇒ 先拆關聯、改、再接（記憶 sculpture-resize-and-stamp-limit）。
- 0.1 m／格（船殼、組裝件書卡都記了）。西班牙尺寸用 codo de ribera（換算等步驟 3 研究結果回來再核）。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。

## 作品
- 船殼 `apex-two-galeon-01m`「康塞普西翁號 船殼」：任務作品（委託 TASK-0969、10 token 已發），`tags=sub`。
- 組裝件 `apex-two-galeon-01m-assembly`「康塞普西翁號」：主作品（沒標 sub），parent 船殼；關聯 `船殼` at 0,0,0。
- 子作品照藍鯊號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`，建立時就記 0.1 m。

## 產生程式
- `design/` 整套從藍鯊號 `gura-pinas-01m/design/` 抄來（43 個 .py；它又出自收穫號 `calli-cosecha-01m/design/`）：作品 id、persona、尺寸 800,320,640 → 900,320,700、單號、船名已換；每個檔第一行寫直接出處。`plan.json` 照 galeón 重寫（藍鯊號那份留成 `plan_pinas_ref.json` 對照）。

## 沿用的現有元件（`work sub=components`，2026-10-27 查；跟藍鯊號同一套）
- 砲：風暴角號 12 磅 `summit-stormkaap-01m-gun-12l`、6 磅 `-gun-6l`（可縮放當 8／4 磅）；憲法號 18 磅 `basecamp-frigate-constitution-01m-gun-long18`、24 磅 `-gun-24`；餘燼號 32 磅 `basecamp-ember-01m-gun-long32`（大口徑的 cañón 照它縮）。
- 舵輪＋座 `basecamp-frigate-constitution-01m-wheel`／`-wheel-stand`、羅經櫃 `summit-night-falcon-01m-binnacle`、絞盤 `basecamp-ember-01m-capstan`、小艇 `basecamp-ember-01m-boat`、錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、船尾燈 `gura-tridente-01m-lantern`、砲門蓋板 `basecamp-frigate-constitution-01m-portlid`、方帆桁 `basecamp-frigate-constitution-01m-yard-*`、艙壁門與廚房看藍鯊號的 `-door`／`-galley` 能不能直接引用。
- 自己做：船首像、船尾鏡板（西班牙船慣例：聖像或王室紋章）、船名。

## 步驟 3 找資料與新圖紙（2026-10-27）
查證：研究代理 ⇒ `references/research_concepcion_2026-10-27.md`（每個數字標〔查／二手／推〕）。主要出處 Palacio Ramos 2009（RHN 107，Concepción 主尺寸 p.14、砲與人員 p.18）、Fernández-González 2009（1618 Ordenanza 表 4 與條文）；桅桁比例照 Cano 1611／Palacio 1587 的二手轉述（MP）。
設計 `design/plan.json`（每個數字的 src：參考資料／研究的推／設計決定）。⚠ 這份是**新寫的**，底子是收穫號 `calli-cosecha-01m` 的 plan（同一套 1618 年的西班牙線形；留成 `plan_cosecha_ref.json` 對照），藍鯊號的 plan 留成 `plan_pinas_ref.json`。
程式：`lines.py`（照抄，沒改）、`layout.py`（改：三層連續甲板 tercera 也有舷弧；桅腳可以照 plan 的 heel_deck 立在哪一層）、`draft_lines.py`（讀數換成 Concepción 對照 `ordenanza_check`）、`draft_layout.py`（三層甲板、畫的範圍、標題）。藍鯊號的 `tools/tune_lines.py`（掃線形對 Witsen 體積）刪掉 —— 本船用不到。

| 項目 | 本船（格 ＝ 0.1 m） | Concepción（1 codo ＝ 5.7468 格） |
|---|---|---|
| 甲板長（第一層甲板 z 74，艏柱到艉柱） | 467.7 | eslora 81.33 codos ＝ 467.4 |
| 龍骨 | 398.8 | quilla 69.39 ＝ 398.8 |
| 最大寬（含外板） | 129 | manga 22½ ＝ 129.3 |
| puntal（龍骨頂到最寬處） | 66.0 | 11½ ＝ 66.1 |
| plan（平底寬） | 60（參數；格子量到 z 11 → 57、z 12 → 71 夾住） | 10½ ＝ 60.3 |
| 艏／艉 rake（到第一層甲板） | 51.7／17.2 | 9／3 codos（研究〔推〕）＝ 51.7／17.2 |
| mura／cuadra 的寬（art.21） | 123／119 | 123.3／117.5（寬只能是奇數格） |
| hold beams z 54 ＝ 第二層甲板 z 94 的寬（art.22） | 127 ＝ 127 | 相等 |
| 設計水線 | z 60（吃水 6.0 m） | 查不到；研究〔推〕0.9 × puntal |
| 排水量（水線下實心 × 1.025） | 1,820 t | 1,550 toneladas 是 arqueo（容積噸），只當量級 |
| 船殼牆 | 632,763 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（甲板面 z）：底艙 54（x 230–520）、第一層 main 74、第二層 puente 94、第三層 tercera 114（三層都有舷弧 aft 6、fwd 3）、alcázar 134（到 x 330）、toldilla 152（到 x 240）、castillo 134（從 x 560）。砲甲板之間 20 格、船樓 18（遊戲頭頂 14 格；1618 是 17）。
  🩸 v0 船樓 132／150：第三層甲板的舷弧往船尾抬 4 格 ⇒ 最船尾的砲門頂到 alcázar 橫樑 clear 0 ⇒ 船樓整個抬 2（clear 2）。
- 砲 **94 門 ＝ PR**：第一層 18 磅每舷 13 ＋ 船尾追擊 2、第二層 12 磅每舷 13、第三層 8 磅每舷 12、alcázar 6 磅每舷 4、castillo 6 磅每舷 2、toldilla 4 磅每舷 2（各層分配原文沒寫 ⇒ 研究〔推〕重的在下）。砲門 art.42（下緣甲板上 1 codo、1¼ codos 見方；18 磅 h 8 同收穫號）。間距 23–26 格。
- 桅（四根）：前 x 605（艏 rake 中點，art.67）、主 x 379（龍骨中點，art.66）、後 x 265、船尾小後桅 x 195（立在第三層甲板）、艏斜桅腳 (612, z 78) 仰 30°。主桅頂離水線 43.0 m。
  🩸 v0 船尾小後桅立在第一層甲板 ⇒ 只比船尾樓高 4.7 m ⇒ plan 加 heel_deck、改立第三層甲板（頂 z 237）。
- 讀數：產生程式重跑 6 個輸出檔逐位元組相同。**反向對照**：`draft_lines.py --probe=half_beam=+3` ⇒ 寬 129 → 135、mura／cuadra／hold beams 各 +6；`--probe=forefoot_x=+3` ⇒ 只有甲板長、龍骨 +3；`draft_layout.py --probe=port=puente:5:+3` ⇒ 只有第二層第 4–5、5–6 段間距變（24 → 27、23 → 20）。
- 圖紙：`design/sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`sheet02_layout_v1.png`（甲板、砲門、桅帆、俯視、砲位表）。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-27）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py apex-two-galeon-01m 0 masks/hull/hull_01..03.vox.txt`（250,000 ＋ 250,000 ＋ 137,591，每刀 placed ＝ 清單）→ `船殼:end` → `砲門:begin` → carvevox `masks/ports/carve.vox.txt`（帶刻之前的顏色守門，19,326）→ stampvox overwrite=1 `masks/ports/paint.vox.txt`（31,022）→ `砲門:end`。
  ⚠ 第一次標 `船殼` 沒帶 phase ⇒ 記成 point（預設）；補標 begin／end，那一筆 point 留著（不影響 `船殼:begin／end` 的查法）。
- `draft_ports.py` 沒改程式（藍鯊號那版已經吃 plan.stern 的 face_x_max／z_ref_x、腰板 edge、舷牆 bg 色）；窗照藍鯊號步驟 6 的做法：最外一格刻掉、第二格是玻璃（從船殼拿出來，`masks/glass/stern_glass.vox.txt` 590 格，步驟 6 做成子作品）、玻璃後面的牆刻穿。
- 塗裝：舷側橡木焦油褐 136、wale 黑 36 四道（第一層甲板下 1 codo、上 2½ codos ＝ art.52；第二層、第三層砲門上各一道）、砲門外一圈紅 224、船樓舷牆赭黃 213 底紅菱格、舷頂金 248、水線 z 60 以下白 182（sebo）。船尾：第一層甲板兩個追擊砲門、第二／三層與 alcázar 各 5 扇窗、toldilla 3 扇（金框、玻璃 87）。
- 讀數（作品一律從 CLI 匯出讀）：
  - `tools/check_hull.py`：結果帳 作品 637,591 ＝ 設計，缺 0、多 0、色差 0；線形對照 426 點差 0；**反向對照** probe_x=400（那一站 +3）⇒ 只報那一站 26 點、最大差 3。
  - `tools/check_stage3.py`：結果帳（船殼 − 刻 ＋ 換色）618,265，缺 0、多 0、色差 0；92 個舷側砲門開口裡實心 0、船尾 2 個追擊砲門刻穿；**正向對照**（同一把尺量 `船殼:end`）⇒ 92 個全報、船尾各 56。
  - 引擎 `stats structure=1 mirror=y:160`：1 元件、封閉空腔 0、鏡像差 0。
- 過程圖：`overlays/step4_hull_{bowq,sternq,side}.png`、`design/sheet03_ports_paint_v1.png`。

## 步驟 5 甲板、梯子、艙房（2026-10-27）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（照抄，沒改程式）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板 7 層（子作品 `-deck-{orlop,main,puente,tercera,alcazar,toldilla,castillo}`、組裝件關聯 `甲板-<層>`）；艙口三個（後 285–295、主 395–413、前 505–515，閃開主桅 379；後艙口開到底艙）；break 三道（alcázar 前緣 x 330、toldilla 前緣 240、castillo 後緣 560：艙壁兩扇門＋7 格胸牆，梯子頭留口）；桅孔照傾斜軸線（bonaventure 立在第三層甲板 ⇒ 下面三層不開孔）。
- 梯子 11 座（子作品 `-ladders-<上面那層>`，關聯 `梯子` meta `kind=ladders`，固定點 `<梯名>.foot／lo／hi／head`）：底艙→第一層（左舷 dy −16）、第一→二層 前後、第二→三層 前後、第三層→alcázar 兩舷、alcázar→toldilla 兩舷、第三層→castillo 兩舷。每一層都有梯子通到。
- 🩸 castillo 那兩座 v0 在 dy ±24 ⇒ 擋在第三層第 12 門砲的艙內那一側（ports_blocked_inside 48 格）⇒ 收到 dy ±14、船首樓艙壁的門改開 dy ±26（改梯子不動船殼；改砲門的話已落格的船殼要重刻）。
- 甲板 meta：每層子作品 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的名字）⇒ `work sub=meta`（7 條）：level 0 底艙、1 第一層、2 第二層、3 第三層、4 alcázar、5 castillo、6 toldilla；floor 照舷弧（例：第一層 165:81 → 314:75 → 625:78）、thick 砲甲板 4、船樓 3。
- 艙房：沒隔（同藍鯊號）；之後要配功能艙再加。
- 讀數：設計那一側：重疊 0、砲門往艙裡被擋 0、梯子點問題 0、封閉空腔 0、鏡像差 0（第一層 634 ＝ 底艙梯子靠左舷的井、梯子 424 ＝ 那座梯子本身，照實）；`tools/check_decks.py`（每件從匯出讀）：13 件 272,339 格，缺 0、多 0、色差 0、跟船殼／彼此重疊 0；梯子點（組裝件 parts）44／44、跟設計差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 1 元件、空腔 0。產生程式重跑 16 個輸出檔逐位元組相同。**反向對照**：`draft_decks.py --probe=drop_ladder=castillo-S` ⇒ 10 座、castillo 只剩 castillo-P。
- 預覽 preset：`藏船殼`。過程圖 `overlays/step5_decks.png`。

## 步驟 6 裝飾、窗的玻璃（2026-10-27）
`draft_deco.py` 框架照藍鯊號，部件換成西班牙 Capitana Real 的（plan.json `espolon`、`figurehead`、`stern_deco`）；改：部件 galjoen → espolon、FONT 補 C／O／N／P、圖案多一個膚色、船尾面的 x 門檻、圖的範圍。`tools/build_deco.py`（三盞燈各一個模型名）、`tools/check_stage5.py`（部件名）、`tools/hull_expected.py`（船殼清單讀全部 hull_*：本船有三份）跟著改。
- `-espolon`「船首喙」8,103：甲板頂 z 81、長 78（1618 art.45：manga 的 3/5）、head rail、cutwater 從艏柱 z 22 掃到喙尖；艏斜桅那條線（半徑 3）被擋 0。
- `-figurehead`「船首像」1,044：**鍍金的戴冠獅子**（西班牙 galeón 的 león；赭金身 213、金鬃、金冠），長 30、前端翹 8，站在喙甲板上。
- `-stern-deco`「船尾裝飾」4,196：alcázar 那排窗下面的船尾走廊（伸出 5、藍欄杆金頂）＋兩舷側廊（art.69：外伸 ⅔ codo ⇒ 4 格；x 156–179、z 116–134、三個開間、紅頂到 z 138 —— 再高會蓋住 alcázar 第 1 門 6 磅砲 x 176–181、z 139）。側廊窗做成玻璃、後面刻穿到第三層甲板的艙裡（藍鯊號的側廊 v2 做法）。
- `-hackebort`「船尾拱形板」2,272：船尾頂上的拱形板（z 165–190、半寬 22），奶油底金框、**無原罪聖母**（白袍藍斗篷、合掌、金冠、腳下新月 —— 船名的聖像）、紅帶金字 **CONCEPCION**（從船尾看從左讀）⇒ 這一件的鏡像差 60 照實報；板頂三盞船尾燈（三叉戟號 `lantern` scale 0.75、kind=light；三盞 ＝ 旗艦燈號〔推〕），腳下實心、頭上空。
- **窗的玻璃**（Ship_Materials）：子作品 `-stern-glass`（船尾 espejo 的窗 590 ＋ 側廊的窗 108 ＝ 698 格），組裝件關聯 `船尾窗玻璃` meta `material=glass`。船尾窗的玻璃格在步驟 4 的砲門刻裡已經從船殼拿掉；側廊窗洞：標記 `側廊窗洞:begin／end` 之間 carvevox `masks/deco/gallery_carve.vox.txt` 432（帶顏色守門）。落之前量過：玻璃要放的 698 格現在都是空的、要刻的 432 格顏色全對。
- 讀數：`tools/check_stage5.py` 四件結果帳缺 0／多 0／色差 0；跟船重疊 0、部件之間重疊 0、跳過 0；側廊窗 108 扇都刻通到艙裡、被擋 0、鏡像差 0；船殼設計帳（`tools/hull_expected.py`：船殼 − 砲門刻 ＋ 塗裝 − 側廊窗洞）617,833 ＝ 作品，缺 0、多 0、色差 0；組裝件 1 元件、空腔 0、link_overlap 0、models_broken 0。**反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 獅子鏡像差 0 → 1,044、其他件不變。產生程式重跑逐位元組相同（`verify_deco.json` 與清單的 sha256 在 verify 裡）。
- 過程圖：`overlays/step6_{bow,stern}.png`、`design/sheet05_deco_v1.png`。⚠ 船頭只有喙 —— Tim 參考圖那種往上彎進船首樓的 head rail 沒做（先放著，之後要細修再加）。
- 🩸 重跑檢查第一次沒過：`sheet05_deco_v1.png` 變了（清單與 verify 沒變）—— 玻璃子作品落了之後，畫圖從組裝件讀到鏡板窗的玻璃色。藍鯊號的程式只扣側廊的玻璃 ⇒ 改成兩份玻璃清單都扣 ⇒ 9 個輸出檔跟落格之前那一次逐位元組相同。

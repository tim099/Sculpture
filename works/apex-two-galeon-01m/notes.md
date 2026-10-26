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

## 步驟 7 桅與帆桁（2026-10-27）
設計 plan.json `rig_build`（長度與位置在 `masts`）；產生 `design/draft_masts.py`（照抄藍鯊號；改：自己這一步的件多 `mast-bonaventure`、量 lateen 伸出船尾的高度 133 → 164、圖的範圍、艏斜桅讓開前桅）；落格 `design/tools/build_masts.py`（四根桅）；讀數 `tools/check_stage6.py`（四根桅、兩根 lateen）。
- 桅（每根一件子作品）：前桅 10,401（下桅＋桅樓＋中桅＋十字架＋上桅）、主桅 12,169（同）、後桅 4,294（下桅＋桅樓＋後中桅）、船尾小後桅 884（只有下桅）、艏斜桅 5,244（含斜桅頂桅 5.0 m）。桅樓半徑 前 13、主 14、後 11（紅腰帶金頂）。
- 帆桁 11 根（外部模型，掛在各自的桅子作品）：方帆桁 9 根沿用憲法號的帆桁元件、只沿長度縮放 —— 前 course 21.7 m（main-topsail ×1.0）、前 topsail 11.9、前 topgallant 6.0、主 course 27.2（main-course ×0.935）、主 topsail 14.9、主 topgallant 7.5、後 sobremesana 8.0、cebadera 14.5、sobrecebadera 6.0；三角帆桁 2 根新做 `-yard-mizzen-lateen`（21.7 m、35°）、`-yard-bonaventure-lateen`（14.5 m、40°；吊點前端往後 40%、meta yard=gaff、rig=lateen）。
- 艏斜桅孔：船頭牆刻 212 格（標記 `艏斜桅孔`），孔由艏斜桅填滿。
- 🩸 後桅三角帆桁 v0 照收穫號 40° ⇒ 往船尾上揚、在 x 246 擦到後桅桅樓底 1 格（yard_clash_cells 1）⇒ 35°。
- 🩸 組裝件 link_overlap 0 → 6：艏斜桅的腳（x 612）跟前桅（往前傾 3°）擠在 x 611 那一欄 ⇒ draft_masts 讓艏斜桅讓開前桅已佔的格、作品刻掉那 6 格（`masks/masts/bowsprit_fix_carve.vox.txt`）⇒ link_overlap 0。
- 讀數：`tools/check_stage6.py` 桅 5 件＋三角帆桁 2 件結果帳缺 0／多 0／色差 0；船殼（側廊窗洞:end − 艏斜桅孔 212）617,621 ＝ 作品；帆桁模型 11 根 meta 與來源固定點問題 0；帆桁穿船 11 根全 0；船尾小後桅三角帆桁後端伸出船尾 2.0 m；models_broken 0；組裝件 1 元件、空腔 0、link_overlap 0。跳過的格：前桅腳插進船頭 deadwood 118（桅坐在船殼上，同藍鯊號）、艏斜桅腳壓到甲板 21。主桅頂離水線 43.0 m。**反向對照**：`--probe=pivot=yard-main-course:-150`（放到船殼的高度）⇒ 只有那一根報 72 格。產生程式重跑 12 個輸出檔逐位元組相同。
- 過程圖：`overlays/step7_masts.png`、`design/sheet06_masts_v1.png`。

## 步驟 8 索具、帆、旗（2026-10-27）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（以藍鯊號那支為主：中桅、上桅、斜桅頂桅、橫繩組、繩梯；從收穫號那支併進 bonaventure 的 shrouds 2／支索／第二面三角帆、勃艮第十字 `cross_png`；改：channels 的間距／起點／舷頂下幾格每根桅可以不同、主桅繩梯落腳第三層甲板、船頭 x 上限 620、喙 galjoen → espolon）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/{ensign,cross_course}.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（沒改）。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件）2,476 格：每舷 shrouds 前 6、主 8、後 4、bonaventure 2（＋中桅 backstay 前、主各 1）。前桅那一排壓到舷頂下 9 格（z 136–137）、間距 5、從桅後 2 格起 ⇒ deadeye 落在 x 573–603，閃開船首樓兩個 6 磅砲門（x 566–571、605–610、z 139–144）；主桅照藍鯊號從桅前 12 格起往後排、z 126–127（第三層砲門頂 z 125 之上）。
- 固定點 156、繩 129（shrouds 40、中桅 shrouds 18、futtock 18、上桅 shrouds 8、backstays 4、stays 9 —— 前上桅支索拉到斜桅頂桅頂、主上桅支索到前桅十字架後端、後中桅支索到主桅桅樓、bonaventure 支索到後桅、艏斜桅 4、帆自己的繩 28）。
- **ratlines 用橫繩組**：12 組（前、主、後 × lower／topmast × 兩舷），下桅 6 組 `climb=1` 繩梯（foot：前 castillo、主 tercera、後 alcázar 的舷牆內側往裡 3 格；head：桅樓靠這一舷的邊），站不站得住先量過 —— 問題 0。bonaventure 沒有桅樓 ⇒ 不做 ratlines。
- 帆 13：前／主 course（勃艮第十字）、topsail、topgallant、後中桅帆 sobremesana（sheet 綁後桅桅樓邊）、後桅三角帆（clew 205,172、sheet 綁船尾樓兩舷 x 215、tack 綁 alcázar x 318）、bonaventure 三角帆（clew 165,185、sheet 綁船尾舷頂 y ±24 避開三盞燈、tack 綁 toldilla x 228）、cebadera、sobrecebadera、船尾旗（勃艮第十字，掛在 bonaventure 三角帆桁後端）、主桅頂紅長旗。
- **帆裝三段**（Ship_Rigging §9.1）：
  | 帆裝 | 張哪幾面 |
  |---|---|
  | 收帆（1） | fore-topsail、main-topsail、mizzen-topsail（3 面） |
  | 戰鬥帆（2） | 收帆的 3 面 ＋ fore-topgallant、main-topgallant、mizzen-lateen、bonaventure-lateen（7 面） |
  | 滿帆（3） | 戰鬥帆的 7 面 ＋ fore-course、main-course、spritsail（set 3）、sprit-topsail（set 3）（11 面） |
- 讀數：channels 結果帳 0 差；CLI 繩 359（含展開的橫繩）、ropes_broken 0、帆 13、sails_broken 0；meta 帆 13／13、帆自己的繩 28／28、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字；橫繩組 12 組全 ok、繩梯 6 組都有 🪜。固定點落在實心上 47 個 ＝ 桅樓邊、十字架、艏斜桅頂（固定點本來就釘在那幾格上；藍鯊號同樣 47）。**反向對照**：`draft_rigging.py --probe=nometa=main-topgallant.sheet-S` ⇒ 只報那一條。產生程式重跑 5 個輸出檔逐位元組相同。
- 過程圖：`overlays/step8_{full,sternq}.png`。

## 步驟 9 砲（2026-10-27）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（照抄藍鯊號；改：個別砲門放寬搜尋 `override`（dx 乘 side 才兩舷對稱）、放不下的照實列出來停、`GUNS_ONLY=<層>:<序號>` 只算一個砲門的測試模式）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`（砲名表換成本船五種砲）。全部算一次約 8.5 分鐘。
- **94 門 ＝ PR**（全部外部模型、沿用現有的砲、掛在所在甲板的子作品上；P 舷 mirror=y；meta kind=gun、gun、deck、side、port）：
  - 第一層 18 磅 ×26（憲法號 `-gun-long18` scale 0.5）＋ 船尾追擊 ×2（同一件，φ ±85°：照角度搜，90° 正後方撞到 espejo 的牆）。
  - 第二層 12 磅 ×26（風暴角號 `-gun-12l` scale 0.5）；第三層 8 磅 ×24（同一件縮 0.45）。
  - alcázar 6 磅 ×8、castillo 6 磅 ×4（風暴角號 `-gun-6l` scale 0.5）；toldilla 4 磅 ×4（同一件縮 0.42）。砲種代碼 18l／12l／8l／6l／4l 都在遊戲砲種表。
- 🩸 第一次全跑：第三層第 5 個砲門（x 324–329）兩舷放不下 —— 緊貼 alcázar 前緣艙壁（x 330），照一般搜尋（dx ±1、φ 0）退到 40 格都撞 ⇒ 程式在下游 KeyError 'phi'。改成放不下照實列出來停，這一門放寬（dx 到 −3、φ ±3／±6）⇒ 往船尾挪 1.5 格、φ 0 就放得下。
  🩸 放寬的第一版左舷選了 φ −6：側向 d_side 在 P 舷是反的，同一個 −1.5 在左舷是往船頭（推向艙壁）⇒ 放寬的 dx 乘 side ⇒ 兩舷 x 都是 325.5、y 106 ＝ 321 − 215。
- 讀數（`tools/check_stage8.py`，從作品讀）：模型 94 ＝ 設計、CLI ok 94；參數 ≠ 設計 0；碰撞 0 門；砲口不在船殼外 0 門（伸出 1.0–7.0）；meta 不合 0；兩舷不對稱 0、砲撞砲 0。
  ⚠ 外框（gunsim vs CLI）最大差 1.14 只在兩門追擊砲（轉 ±85°）：gunsim 是把來源外框的八個角轉過去再取外框，CLI 照網格頂點算 ⇒ 斜放的會差一圈；不轉的 92 門最大 0.05（在容差 0.06 內）。檢查程式多印一行分開報。
  **反向對照**：`--push=砲M-S05:3`（往外推）⇒ 碰撞只報那一門 5,591 樣本；`--push=M-chase-stern-P:-6`（往裡拉）⇒ 只報那一門、伸出 −3.5。
- ⚠ 沒做砲具與砲索（環、breeching、tackle；94 門 × 5 條）—— 記在 todo。

## 步驟 10 彈藥庫與甲板物件（2026-10-27）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（照抄，沒改程式）；落格 `design/tools/build_gear.py`。
- **彈藥庫**（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine、pos=aft、powder_lb=12000`）7,727 格：底艙 x 236–280（水線 z 60 以下）、門開在船頭那道艙壁、沿底艙走到底艙梯子；銅皮 168、橡木框 136、松木地板 177。固定點 `blast` (259,160,63)、`door` (280,160,56)。火藥桶 **120 桶**（憲法號 `-powder-barrel` scale 0.2；Concepción 的火藥量查不到 ⇒〔推〕照藍鯊號每門 1.33 桶 × 94）：底層 108、上層 12。
- **小艇架**（`-boat-skids`，關聯 `小艇架`）604 格：第三層甲板船腰三座橫架 x 425、460、495（主艙口與前艙口之間；中間那座跨過第二→三層前梯的井）、橫樑 z 125。
- 模型（沿用現有元件）：主絞盤（餘燼號）第三層甲板 x 363、羅經櫃（夜隼號）後甲板 x 300、小艇（餘燼號 cutter 9 m）擱在小艇架上 x 460、z 127。
- **艙壁門**（Ship_Fittings §9.7）：門板**直接引用藍鯊號的 `gura-pinas-01m-door`**（同一支 build()，我們算的清單跟那件逐格相同 896 格；Ship_Setup §2.1）；`draft_doors.py` 門洞的高度範圍 z 40–120 → 40–200、`tools/build_doors.py` 引用別人的元件時不建、不動它的固定點。6 扇：alcázar 前緣 x 331.5、toldilla 前緣 241.5（rotate 0）、castillo 後緣 559.5（rotate 180），meta kind=door open=side；撞實心 0、背後都是艙壁、腳下都有地板。
- **廚房爐灶**（Ship_Fittings §9.13）：**直接引用藍鯊號的 `gura-pinas-01m-galley`**（清單逐格相同 17,548）；第三層甲板 x 584.5、船首樓底下中線（西班牙船的 fogón 也在船首樓底下），煙囪從船首樓甲板 x 576／592 兩根橫樑之間穿出 ⇒ 甲板-castillo 刻 9 格；撞實心 0、懸空 0、廚師站的船尾那一面站得住。
  🩸 第一版洞只刻 8 格：煙囪中空（煙道），照模型格刻會在洞中間留 1 格甲板 ⇒ 組裝件 2 個元件 ⇒ 洞外框以內全刻、補刻那 1 格 ⇒ 1 元件。
  🩸 改 `draft_galley.py` 時把「康塞普西翁號」註解接在 `json.dump({…,` 那一行中間 ⇒ 同一行後面的 `'name'`、`'at'`… 全變成註解、build_galley KeyError（記憶 inline-comment-swallows-code 又一次）⇒ 註解移到上一行。
- 艙蓋不做：艙口都在第一層甲板（z 74，水線上 1.4 m）以上（同藍鯊號）。
- 讀數（`tools/check_stage9.py`，從作品讀）：彈藥庫、小艇架結果帳缺 0／多 0／色差 0；模型 123 ＝ 設計、CLI ok 123；powder_lb 12,000 ＝ 120 × 100；blast 空氣、door 空氣且腳下實心；參數 ≠ 設計 0、撞實心 0、腳下 12 格內沒有實心 0；新格落在實心上 0、封閉空腔 0、浮空 0、鏡像差 0（缺的種類 wheel 在步驟 11）。甲板帳（扣掉煙囪洞）13 件 0 差；組裝件 1 元件、空腔 0、link_overlap 0、models_broken 0（模型 238）。**反向對照**：`draft_gear.py --probe=nokind=小艇` ⇒ 只報小艇。產生程式重跑逐位元組相同（verify_gear 讀到的組裝件格數照實少了煙囪洞 9 格）。

## 步驟 11 舵、舵輪、錨（2026-10-27）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（照抄藍鯊號，沒改程式）；落格 `design/tools/build_rudder_anchor.py`。
- **舵**（`-rudder` 2,444 格，組裝件的外部模型 `舵`）：沿艉柱後緣（斜 13.1°）從龍骨底到 z 70（yugo z 71 底下）；3 格厚、前緣兩側削 1 格；水線下白、上橡木褐、每 12 格一道鐵箍。meta `kind=rudder`、鉸鏈 (180, 160.5, 0)、軸 (−0.2265, 0, 0.974)、max_deg 35、turn_axis=hinge、**spin**（rudder、±35、lag 0.3）。固定點 `stock-top` (160,160,70) 離船殼 4 格。
- **舵輪＋座**：沿用憲法號雙舵輪 `-wheel`（spin rudder 540）＋木頭雙柱座 `-wheel-stand`，後甲板中線 x 285（後桅前、羅經櫃後）。⚠ 1680 年代西班牙船用舵桿（pinzote），遊戲要舵輪（同收穫號、藍鯊號）。
- **錨**：共用錨元件 ×2（scale 1.0、kind=anchor、anchor=bower）吊在船頭舷外 x 620（前桅支索板、船首樓第 2 門砲之前）、ring z 144、錨臂順著船殼切線（rz ±45）、離船殼 21 格（試了 x 614–624 × z 136–148）；錨架 `-anchor-gear`（billboard 托板，關聯 `錨架`）3,944 格；錨鏈孔固定點 hawse-S／P (626, ±18, 88)（只登記、沒有開孔）。
- 讀數（`tools/check_stage95.py`，從作品讀）：舵、錨架結果帳 0 差；舵模型 CLI ok、stock-top 8 格內有船殼、舵跟組裝件重疊 0、轉 ±35° 掃進實心 0；錨 2 隻 CLI ok、撞實心 0、腳是錨架、來源有 ring；hawse 在船殼上、在那一舷；問題 0。舵輪與座撞實心 0。遊戲讀的那一份（組裝件 `export format=parts`）：舵、舵輪都有 spin。**反向對照**：`--drop=錨-P` ⇒ 只報 P 舷沒有錨。

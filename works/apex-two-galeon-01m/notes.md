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

## 步驟 12 砲門蓋板（2026-10-27）
工具 `design/tools/portlids.py`（照抄藍鯊號的通用工具；改開頭的表成康塞普西翁號、兩層（第一、二層 ＝ 封閉砲甲板）、一件蓋板；第三層多在船腰露天 ⇒ 不做，同 §9.12）⇒ `portlids_placement.json`、`verify_portlids.json`、蓋板子作品 `-portlid`（9×10×2：外面船殼褐 136、裡面紅 224、鉸鏈板 73）。
- 54 片：第一層 26 ＋ 第二層 26 ＋ 第一層船尾追擊砲 2（P 舷 27、rotate 180 − rz，⛔ 不用 mirror=y）；meta kind=portlid、lid_of ＝ 砲的物件 id（先做步驟 14 的匯入＋`admin.py ids`）。
- 讀數（`portlids.py check`）：開著撞砲 0、收砲後關著撞砲 0；關著撞船最多 2.04%（> 5% 的 0 片）；砲門 54／54 蓋滿；掛上去 180 格 0 差、models_bad 0、鉸鏈最大差 0.0005。**反向對照**：house 0（砲不收）⇒ 54 片全撞砲；mirror=y ⇒ 26 片往上開。
  ⚠ 開著撞船 32 樣本：第一層第 4 門兩舷（船尾開始收窄、外表面沿 x 斜一格 ⇒ 鉸鏈那一邊壓進外表面一層）；追擊砲收砲（house）時砲身擦船 45 樣本 ×2 —— 都只是畫面，照實留著。
- 🩸 遊戲匯入檢查第一次 ✗ 2：第一層第 13 門兩片「關上時穿過縮回去的砲（house 6）」⇒ `HOUSE_ADJ` 這兩片至少 8（檢查建議）；⚠ 第 4 門兩片 close 86.3° 關上 5% 落進船殼 ⇒ `CLOSE_ADJ` −2°（84.3°）。重匯 ⇒ ✗ 0。重套模型時 `ids` 發的 id 保留（meta 合併）。

## 步驟 14 給遊戲的 meta 與匯入（2026-10-27）
- 組裝件的關聯 `船殼` meta kind=ship、waterline_z 60（第一次標在組裝件 part=work，遊戲讀不到 ⇒ 照藍鯊號標在關聯上；part=work 那一筆留著沒害）；ropecheck 718 端 ok（沒有 bind／snap）。
- Blockside 自己的 worktree（分支 apex-two/0969-galeon，從 refs/heads/dev —— `dev` 同時是遠端名，要寫全名）：`admin.py import --work apex-two-galeon-01m-assembly --id concepcion --name 康塞普西翁號` ⇒ `metasync` ⇒ `ids`（271 個，加蓋板之後再 54 個）⇒ reimport。
- 給遊戲那側填的 geo（z 從龍骨底，格 ＝ 0.1 m）：水線 60；甲板地板 orlop 55、main 75–81（舷弧）、puente 95–101、tercera 115–121、alcázar 135、castillo 135、toldilla 153 ⇒ `spar [115,155]`、`marines [35,170]`（外框含後桅帆桁與艏斜桅：x 136–787）、`center 110`、`aim 90`、`aimZ [30,460]`、`deckAim [76,130]`、`rigAim [175,450]`；船員照預設。
  🩸 import／ids 會把整份 game.json 照 json.dump 重排（別人那幾段的單行物件被展開）⇒ 照 HEAD 原樣、只插回新船那一段（先斷言其他船與其他鍵逐字相同）。
- 讀數：reimport checksum **420549008**、格 954,007、模型 278（網格去重 113 份）、繩 359；shipcheck ✗ 0 ⚠ 10（門 6 扇正下方沒有空格 —— 門洞在水線上 5 m 以上；第一層最後一門兩舷砲班 4／5 —— 離追擊砲 2.5 m；桅頂水手 12／16 —— bonaventure 沒有桅樓；第一層左舷追擊砲的送藥路線不連通、93／94 門走得到取用點）；ladcheck 11 座全部 ✓；廚房 1 座、廚師 1、站得住的面 4。
- 船卡：1,822 t、水線長 50.7 m、94 門、齊射 503、帆 13、船員 482；外框全長 **65.1 m**（vxk 檔頭 bbox × 0.1；藍鯊號、收穫號同法量出 49.8／59.6 ＝ Blocksail hullLoa）。
- 對打（Blockside `report.py`，concepcion vs cosecha、seed 1／2、120 秒、jobs 1）：開火 699、命中 56%；砲可開 81%／裝填 16%；砲被打掉平均 1.5／94；航速最高 5.8／8.5 節（平均 4.4／5.9）⇒ 開得動、砲打得出去。
- **泊位反向對照**（gura 的 `berth_fit.cjs`，照 Blocksail 地球儀 docksFit：泊位 loa ≥ 全長、泊位與航道水深 ≥ 吃水 ＋ 1.5）：吃水 6.0、全長 65.1 ⇒ 7 城 66 個泊位：large 24／24、huge 2／2、titan 7／7 停得進；**small 0／21**（21 座太短 36 < 65.1、8 座也太淺）、boat 0／12。對照組 30 m、吃水 2 m ⇒ small 21／21。
- Blockside：b720625（ff 合進 dev、已推；`_cache/concepcion.vxk` 先複製進共用 _cache）。

## 步驟 15 交船（2026-10-27）
照 Ship_Game §10 換一艘船時的檢查表逐條看過（遊戲那一份：`admin.py shipcheck --id concepcion` ✗ 0 ⚠ 10）：
- ✓ ropecheck 718 端 ok、沒有 bind／snap；組裝件名 ＝ 康塞普西翁號、船殼帶 sub；mpv 0.1 每件都記（門板、爐灶、砲、火藥桶、帆桁等元件照它們自己的 0.05／0.02 m，模型明寫 scale）；開工前查過現有元件（新做的只有：船首喙、鍍金獅子、船尾裝飾與拱形板、兩根三角帆桁、蓋板 —— 個性裝飾與本船尺寸的部件）。
- ✓ 砲 94、帆桁 11、舵輪、火藥桶 120、絞盤、羅經櫃、小艇、門 6、爐灶都是外部模型帶 kind；舵 kind=rudder＋stock-top（開局就掉的模型 ＝ 匯入檢查 ✗ 那一類，0）；spin：舵 ±35°、舵輪 540°；操舵鏈「舵令 ⇒ 甲板-alcazar/舵輪 ⇒ 舵 100%」。
- ✓ 關聯 `船殼` kind=ship waterline_z 60（高度在步驟 14 那一段）；甲板 7 層 kind=deck、梯子 11 座 kind=ladders 四個固定點；ladcheck 11 座全部 ✓；ratlines 橫繩組、下桅 6 組繩梯；三角帆桁 2 根 rig=lateen＋fore；彈藥庫有桶、93／94 門送藥走得到；窗的玻璃獨立關聯 material=glass（698 格）；廚房 kind=galley（不標 deco）、站得住的面 4。
- ✓ 繩與帆的端點綁 model:、ropes_broken／sails_broken／models_broken 0；帆 meta 13／13、帆自己的繩 28／28、帆桁 sail ＝ 帆名；帆裝三段表在步驟 8；組裝件 1 元件、空腔 0、link_overlap 0；vxk checksum 420549008（reimport 跟作品現在這份一樣）。
- ✓ 舷側砲門蓋板 54 片（第一、二層＋船尾追擊砲）；匯入檢查「砲門」✗ 0。
- 不適用：槳、撞角、蒸汽、鐵甲與金屬部件、迴旋砲／砲塔、砲身與砲座拆兩件、空艙房（沒隔艙，艙房 0）。
- ✓ 遊戲裡看過（Blocksail worktree 的 battle.html?ship=concepcion,cosecha，Blockside b720625）：載得進來（94 門、帆 13＋陣營旗 4）、滿帆 6.0 節；按 S 一段一段 ⇒ 滿帆 11 面張、戰鬥帆 7 面（三面 topsail、兩面 topgallant、兩面三角帆）、收帆 3 面 topsail、全收 0 面 —— 跟步驟 8 那張表一樣；全收那一刻帆布收成一捲掛在帆桁上。截圖 `overlays/step15_ingame_{full,furled}.jpg`。
- ⚠ 沒特別看的：窗玻璃的透明與反光（遠景截圖看不出來）—— 等 Tim 看那一格一起看。
- ⚠ 照實留著的匯入檢查 ⚠ 10：見步驟 14。

## 步驟 16 Tim 看過之後：船樓梯子接上甲板、裝飾與曲線（2026-10-27）
Tim 在遊戲裡看了兩件事：「樓梯沒有接上甲板（目前樓梯自檢應該要發現 是否自檢有Bug）」＋「希望可以參考模型 圖紙 船身做出一些裝飾 曲線」（附三張：遊戲裡的側面、OcCre 式模型的船尾側廊、San Felipe 式整船模型）。
- **船樓的 6 座梯子沒接上甲板**：船樓的梯子靠在 break 外面，梯頂（最後一段只有扶手）停在 x 336／248／555，break 艙壁在 x 330／240／560 ⇒ 中間空 5／7／4 柱（往下 16–19 格才有甲板）；hi → head 那一段人得跨過去。藍鯊號同一支 draft_decks 六座都是空 0 格 —— 是本小姐把船樓抬高、break 挪過之後 xs 沒有跟著重算（梯頂 ＝ xs ＋ dir × (run × (階 ＋ 1) ＋ run − 1)）。
  - 修：plan `decks_build.ladders` 船樓那 6 座的 xs 351／261／540 ⇒ 346／254／544（梯頂貼著艙壁、階數不變）⇒ `draft_decks.py` 重產；`tools/delta_apply.py` 套三件梯子子作品（各刻 416／372／400、貼回同數）、`work sub=anchor overwrite=1` 搬 18 個點（head 不動）；`tools/check_decks.py`：13 件 272,330 格問題 0、梯子點 44／44 跟設計差 0、空氣／腳下／頭頂問題 0。重疊 0、砲門往艙裡被擋 0。
  - **自檢為什麼沒抓到**（Blockside `js/75_ladcheck.js`）：① 梯口連到外面（船樓的梯子靠在甲板邊上）就不量洞、② 只看 head 那一格（head 在甲板上 ✓）、③ 從 head 走得出去 ✓ ⇒ hi 到 head 那一段沒人量。補 ④「梯頂接不上甲板」：hi 到 head 沿走向逐柱看梯子寬度裡、腳下那一層（內插）上下 NAV_DZ 格內有沒有踩得到的面（實心而且上面空 ⇒ 貼著梯子的舷牆不算），連續空 2 柱以上 ✗；反向對照 `ladcheck --selftest` 多一組 matsushima break-P `cut:4`（拿掉梯頂 4 柱）。改之前的成品：康塞普西翁號正好報這 6 座（5／7／4 柱）。
- **wale 的曲線**（船殼的漆，`draft_ports.py`）：研究筆記 §6 的 1618 Table 4 —— wale 的舷弧船艏 1¾–2、船艉 2¼–2½ codos，比甲板（艏 ½、艉 1）多翹 ⇒ plan `paint.wales.sheer`：船中 x 380 往兩頭照平方再加 艉 8（x 165）／艏 8（x 620）；第三層那條細的只加一半、頂超過 z 133 的那幾柱不畫（收進船樓菱格帶的金邊底下）。砲門照舊跟甲板走，碰到的格照樣被紅框蓋掉。
- **砲門金框**（`paint.wreath`）：第三層甲板與船樓（alcázar、castillo、toldilla）的砲門，紅框外再一圈金（參考圖的上層砲門花框）；下兩層重砲不描。
  - 船殼：`tools/hull_expected.py` 先用舊的漆組帳 ⇒ 跟作品逐格相同（多 0／少 0／換色 0，證明帳組得對），再用新的組 ⇒ 只差換色 14,432 ⇒ `delta_apply` 套上、讀回 0。刻 19,326 不變、砲門看得穿 92／92、追擊 2／2、鏡像差 0。
- **裝飾子作品 `-ornament`**（新寫 `design/draft_ornament.py`、落格 `tools/build_ornament.py`，組裝件關聯 `裝飾-2`）2,748 格，只放空格：
  - 側廊第二層（參考圖二：上下兩層、上層窄一點）：疊在第一層的紅頂上 z 139–149、2 個開間 x 156–171（讓開 alcázar 第 1 門砲的金框）、伸出 3 格、紅頂收成拱到 z 153（讓開 toldilla 第 1 門砲）、拱窗。
  - 第一層側廊底下的金托架（每個開間兩端，高 7、往下收）、船尾走廊底下的金托架（木斜撐之間 dy 4／12／20）。
  - 鏡板每排窗之間與兩頭的金壁柱（凸出 1 格）、每扇窗頂的金窗楣。
  - 船頭的 head rail（參考圖三；todo 那一條）：每舷兩條，船頭側面 x 598（z 112／101）往前往下彎再往上接到獅子的頸背 x 646（z 96／90）、上面那格金；喙上兩根 head timber（x 634、640）。v1 終點 z 85／82 ⇒ 兩條在喙上壓平、貼著原本的欄杆頂 ⇒ 抬高成笑臉形。
  - 讀數：撞到的格 ＝ 托架 144（側廊底下往外收那一節本來就是側廊的格，照設計讓開）＋ head timber 6（喙的欄杆）；擋砲門 0；鏡像差 0；重跑逐位元組相同（第一次產的圖紙用的是船殼換漆以前的顏色，清單本身相同）。
  - 組裝件：956,755 格（954,007 ＋ 2,748）、1 元件、空腔 0、link_overlap 0。圖紙 `design/sheet07_ornament_v1.png`、`sheet03_ports_paint_v1.png`（wale 與金框）。
- `draft_deco.py` 扣掉的件多一個 ornament（步驟 6 重產時不把步驟 16 的裝飾當成船）：清單 `masks/deco/*` 逐位元組相同；`verify_deco.json` 的「喙碰到船的格」90 ⇒ 106 是步驟 11 的錨架、步驟 7 的艏斜桅後來貼上去的 ⇒ 步驟 6 的紀錄照原樣留著。
- **匯入**（Blockside worktree，分支 apex-two/0969-ornament，從 dev 75d4e31）：reimport ⇒ ⚠「物件 id」1（新關聯 裝飾-2）⇒ `ids` ⇒ part-15；game.json 照 HEAD 原樣只改 idNext.part 14 ⇒ 15。checksum 420549008 ⇒ 248864085、繩 359（端點跟著格子重算 206 條、猜 0 端）、shipcheck ✗ 0 ⚠ 10（同交船那 10 條）、srccheck 對得回來 ⇒ 4be399e。
- **遊戲裡**（Blocksail worktree 套 4be399e 的 battle.html?ship=concepcion,cosecha）：載得進來；`__game.ladders(0)` 船樓 6 座讀到的是新的點（alcázar lo 344 ⇒ hi 334、toldilla 252 ⇒ 244、castillo 546 ⇒ 556）、broken 0。過程圖 `overlays/step16_{ingame.jpg,sternq,stern_galleries,head_rails,ladder_castillo}.png`。

## 步驟 17 Tim 再看過：船頭船尾重畫、真的門（2026-10-27）
Tim：「是否可以嘗試優化一下船的曲線(會需要動船殼)」「特別是船尾部分」「船頭 船尾 可以參考西班牙大帆船的模型 & 圖紙」「重新繪製船頭船尾曲線&裝飾」；參考 San Felipe 整船與船尾四分之一、OcCre 船頭特寫、Galeón Andalucía 複製船；途中圈了船頭「希望船頭能做出這個造型(有層次感)」「是否有辦法讓船頭變成一整個平台(雕像往上移)」，再加「開真的可以打開的門(第一人稱模式可以走出去) 船尾有陽台的地方也可以開門出去」。做法整理成 Senate 文件 `Ship_Ends`、收穫號照做開了 TASK-1027。
- **線形**（`lines.py`，plan `lines`）：
  - `top_curve`：舷頂照節點走 smoothstep（船樓前後緣的落差 4 格直角 ⇒ 12 格 S 形，落在矮的那一邊）＋船尾樓往船尾翹 6、船首樓往船頭翹 5。
  - `counter`：wing transom z 71 以上往後外伸，smoothstep 到 z 118 伸出 20 格，俯視兩角收 30%；長度比例 s 改照艉柱線量 ⇒ 船身其他地方的寬一格不變。
  - `stern_tumble`：船尾那一段 z 100 以上每 10 格每舷再收 1 格 × ua²（船尾樓頂那一圈收 7 格）。
  - `beakhead`：z 96 以上、x 620 以前切掉 ⇒ 船首樓前面一道平的艙壁（牆 616–619，前桅在船首樓甲板那一層到 x 613.9）、底下的船頭頂面成了平台（z 95；艏斜桅頂 92.5 在平台的牆底下）。
  - 控制組：改程式、plan 不動 ⇒ 6 個輸出檔逐位元組相同；新舊船殼照 x 分段 ⇒ 只有船尾 x < 350、三個船樓前後緣、船首樓 x ≥ 540 有差。`draft_lines`：1 元件、空腔 0、鏡像差 0；船殼 637,591 ⇒ 648,711 格（牆）。
- **船殼的漆與開口**（`draft_ports.py`）：counter 扇形（以中線 z 66 為心每 12° 一條金線、136／177 輪流、頂上金邊）；第二層那排船尾窗拿掉（落在 counter 上）；stern walk 後面兩舷的窗（第三層 4 扇、alcázar 3 扇，真玻璃、後面刻穿）；beakhead 艙壁那一面（金邊框、z 116 金線、船首樓菱格照 y 排、圓窗、兩扇門的金框與拱）；平台頂甲板色。門洞見下。讀數：砲門看得穿 92／92、追擊 2／2、帶子裡還是黑的 0（扣扇形與艙壁那一面）、鏡像差 0。
- **船尾裝飾**（`draft_deco.py` `stern_deco.walks`，子作品 -stern-deco）：兩層開放的 stern walk —— 下層地板 z 121、伸出 6、沿兩舷到 x 186；上層 z 136、伸出 5、到 x 170；欄杆 4 格（底欄、隔一格一根藍柱、金扶手）、地板 2 格厚外緣金、托架每 6 格一組往下收（上層錯開 2 格讓門）。取代步驟 6 的船尾走廊、兩舷側廊、步驟 16 的側廊第二層與兩組托架（側廊的窗洞清單清空）。拱形板 z 165–190 半寬 22 ⇒ z 170–196 半寬 20（船尾往裡收之後頂上變窄；CONCEPCION 10 個字要 39 格寬）、三盞燈 dy ±14 ⇒ ±11、搬到 z 197。
  - 🩸 v1 結構：11 個元件、空腔 548 格 —— 托架頂端跟地板之間空一格（地板只有 1 格厚）、扶手只有斜角相接、地板外緣金邊把船殼往外鼓的那段圍成空腔 ⇒ 地板 2 格厚、外緣取 dep − 1.5；v2 剩 4 小塊在兩舷窗凹進去的那幾格裡 ⇒ 船殼外形改照線形算（窗、門的凹口不算外面）⇒ 空腔 0。
- **船頭**：
  - 喙（-espolon）改成跟 beakhead 平台同高的一整片平台：甲板頂 81 ⇒ 95、從艙壁前 x 620 起鋪（半寬 26 收到艏柱 22、再收到喙尖）、甲板邊往下包側板到 z 82（上下金線、最前面那一欄整片封、底下不封）；knee 頂到 z 82、前緣在 x 656 接上平台底（`cutwater_pow` 2）、水線以下 182、兩條 trailboard 金線；側板貼著船殼圍出的 1 格縫（14 格）照填滿內部補進喙。
  - 獅子跟著抬 14 格 ⇒ 在 x 650 正好擋在艏斜桅的路上（擋掉 216 格）⇒ 挪到 x 676（喙尖 708）。
  - `draft_ornament.py`：head rail v1 三條細的 U 形＋直立格柵 ⇒ v2 照 OcCre 特寫改成一條寬帶（深色 36 底、上下金邊、卷草：波浪＋波峰波谷金點，艙壁上角 x 616 z 136 ⇒ 最低 x 648 z 107 ⇒ 獅子後面 x 670 z 112）；兩條 cheek 金線（下面那條沿 knee 再往前 18）；鏡板的壁柱照舊（門的兩旁也放、門頂不放窗楣）。
  - 🩸 `link_overlap` 卡在 4：ornament 重產時扣掉「自己現在的格」⇒ 跟喙重疊的那 4 格被當成空的、永遠重疊 ⇒ 自己的格也屬於別的裝飾件就不扣。
- **真的門**（Tim「第一人稱模式可以走出去」）：門洞是船殼刻的（`draft_ports.py` plan `stern.doors`、`paint.beakhead.doors`），門板沿用藍鯊號 `gura-pinas-01m-door` 只縮放高度（`draft_doors.py`＋`tools/build_doors.py`；10 扇 ＝ 原本 break 6 扇＋4）：
  - 船尾第三層、alcázar 那兩排船尾窗正中間那扇換成門：門洞 5 × 11（z 122–132）、5 × 13（z 137–149），底邊 ＝ stern walk 站的那一格；船尾的牆往後倒 ⇒ 門板直立擺在門洞最底下那格牆外面、前面的牆刻掉成門廊。門板 12／14 格高、掛在甲板-tercera／alcazar。
  - 船頭 beakhead 兩扇（dy ±10）：門洞 5 × 15（z 98–112），牆留 z 96–97 當門檻（＝ 艙裡第二層甲板面）、到平台往下一階 2；門板 18 格高從平台面 z 96 立起、掛在甲板-puente。🩸 v1 從 z 96 刻 ⇒ 門口正下方 x 616 是底下船頭的艙、腳下一路空到第一層甲板 ⇒ 走不出去。
  - 讀數 `tools/walk_doors.py`（照 81_fps.js：頭上 7 格、上 ≤ 6、下 ≤ 8）：4 扇都走得出去也走得回來；**反向對照** `--nocarve`（門洞當實心）⇒ 4 扇都走不出去。
- **連帶重產**：甲板 5 層往船尾延伸、船首樓／第三層／第二層收到艙壁（梯子不變）；甲板 meta（Blockside `decks.py`）6 層的 floor 範圍；玻璃 698 ⇒ 810（船尾窗＋兩舷窗）；索具：綁點（船頭那一欄 `bow_belay_max_x` 620 ⇒ 617、船尾舷頂的帆腳）、支索板（bonaventure 那段貼回往裡收的船殼）、bobstay、後桅兩組繩梯的落腳點、前帆一角 ⇒ 繩 359、broken 0、兩端 718 ok；錨 `x_try` 614–624 ⇒ 606–614（切線在 x 612、錨 (623.6, ±48.8, 144)、撞 0、腳下是錨架）。
- **砲**（`draft_guns.py` 全部重算兩次、各 9 分鐘）：舷側 92 門都放得下、船尾那幾門挪 0.5–2 格（船尾往裡收）。🩸 第一次兩門追擊砲放不下（退到 37.5 格、砲口在船殼裡 26 格）：counter 是斜面，砲管頂擦到砲門頂 z 93 ⇒ 追擊砲門 sill 6 ⇒ 7（z 86–93，大小不變）⇒ x 162.5、φ ±90、砲口伸出 1.0。`check_stage8`：碰撞 0、參數差 0、meta 0；④ 兩門追擊砲 −0.5 ⚠ —— 那把尺量砲口左右各偏 6–8 格的船殼最外面，圓的船尾在靠中線那一側比砲門往後凸；砲口本身在砲門的洞裡、是空的，照實留著。
- **砲門蓋板**（`tools/portlids.py`）：🩸 追擊砲那兩片第一次被跳過（找開口拿砲口上下 ±14 格的最外面當外表面，counter 上面那段往後凸 12 格 ⇒ 開口灌水漏出去）⇒ 船尾的只看 ±6 ⇒ 54 片；關上撞砲 0、關上落進船殼最多 2.04%（> 5% 0 片）、開著撞砲 0、開著撞船 186 樣本（追擊砲兩片往上掀插進上面那段 counter 各 81 —— 只是畫面，照實留著）、收砲撞船 108；重跑逐位元組相同、鉸鏈差 0.0005。第二層靠船尾那 5 對 close 85.9° ⇒ 82.5°（船尾往裡收）。
- **欄杆加高**：🩸 遊戲裡第一人稱從 alcázar 的門走出去（x 140.5 ⇒ 128.7）接著一腳踩上扶手頂（z 141）—— 4 格的欄杆跨得過去（FP_UP 6）⇒ stern walk 與喙平台邊的欄杆 rail_h 4 ⇒ 7。`tools/walk_doors.py` 多一項「從門外走得到、站在扶手頂上的格」0；**反向對照** `--lowrail=3` ⇒ 234。
- **組裝件**：1 元件、空腔 0、link_overlap 0（🩸 途中三次：stern walk 的托架浮空與地板圍出的空腔、ornament 跟喙重疊 4 格（自己的格一扣就永遠重疊）、cheek 照組裝件最外面貼到錨架外面浮空 8 小塊 ⇒ 改照船殼量；錨架托板只留最大的那一塊連通的）；ropecheck 718 端 ok、繩 359、broken 0。
- **匯入**（Blockside worktree，從 dev a1cd834）：reimport 兩次（第二次是欄杆加高）⇒ 格 956,755 ⇒ 971,981、checksum 248864085 ⇒ 890116286、繩 359（端點照格子重綁 208 條、猜 0）、玻璃 698 ⇒ 810；`ids` ⇒ 新門 door-7..10（idNext.door 7 ⇒ 11）。外框 x 136–787 ⇒ 115–787 ⇒ 陸戰隊照 hx0 整排往船尾挪、站不滿 10／12 ⇒ geo.marines[0] 35 ⇒ 56。game.json 照 HEAD 原樣只改那兩格。匯入檢查 ✗ 0 ⚠ 11（直立的門 10 扇「被打掉不會進水」、桅頂水手 12／16；交船時那兩條「第一層末門砲班 4／5」「左舷追擊砲送藥路線」沒了）；樓梯自檢 11 座 ✗ 0 ⚠ 0。船卡：1,821 t、水線 47.5 m（knee 在水線那一層不再伸到 x 673；只是顯示）、船員 484。Blockside d689b6d（ff 合進 dev、已推；_cache/concepcion.vxk 已複製進共用 _cache）。
- **遊戲裡**（worktree 的成品 `?mode=observe&ship=concepcion,cosecha`；窗格藏著 ⇒ 畫布 POST 給本機收圖）：船頭平台、寬帶、獅子都在；第一人稱 `__game.fp`＋按住 W：alcázar 的門 135 ⇒ 走廊 137、到欄杆停住；第三層的門 121 ⇒ 122、到欄杆停住；船頭 beakhead 的門 98 ⇒ 平台 96、一路走到喙上 x 665。過程圖 `overlays/step17_{sternq,bowq,side}.png`（雕刻引擎）、`step17_ingame_bow.jpg`、`step17_ingame_fp_doors.jpg`（第一人稱走出三組門）。
- **Blocksail**：world/fleet.js `FLEET.hullLoa.concepcion` 65.1 ⇒ 67.2（泊位照等級給長度：還是停進大船 80 m 以上、停不進小船 36 m）＋ Blockside → d689b6d ＋重套 battle.html（開過 concepcion 對 cosecha 一場、主控台沒有錯）⇒ 本地 main 8237f43（Tim：先不推）。
- 工具：`tools/render_preview.py`（還沒落格的清單直接出預覽圖）、`tools/walk_doors.py`；`draft_deco.py`／`draft_ornament.py` 帶 `--occ=` 可以拿本機清單當船跑。

### todo（沒做的，照實留著）
- 砲具與砲索（94 門 × 5 條；Ship_Guns §4.4）。
- 第一層左舷追擊砲的送藥路線（走路格不連通，遊戲照直線送）。
- 錨鏈孔只登記固定點、沒開孔；bonaventure 沒有桅樓（桅頂水手 12／16）。
- ~~側廊第二層的窗是畫上去的~~（步驟 17 側廊整個換成 stern walk，窗改成船殼上的真窗）。

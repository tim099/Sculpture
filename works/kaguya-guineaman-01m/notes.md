# 幾內亞船（Guineaman，約 120 噸英國三桅商船，1660 年代的奴隸船）—— 建造筆記（0.1 m／格）

委託：Tim 2026-11-01「/scp-task 1149 go」（TASK-1149，summit 開單；傘 TASK-1146 缺口 #3）；查完史料問「新造還是福祿特船改型」，Tim 選「新造英國船」。
驗收（TASK-1149）：造船資料（查得到的附出處、推的標明）→ 雕好照造船規格匯入 Blockside（開得動、帆與砲位能用）→ Blocksail 有一型畫它（玩家不能造、不能買；AI 商人照載重挑船型時不挑它；fleet_check 沒動的船型讀數不變）→ Tim 看過；加 Ship_Steps 步驟 2–11、14、15（刪 12 砲門蓋板：砲在露天甲板從舷牆砲門打；刪 13：木造帆船、沒有槳）；步驟 3、6 加讀 Ship_Ends（方艉、船首喙）。
⚠ 立場（WORLD_LORE §5.1）：它是被攔截、被解放的目標；⛔ 不做成玩家可以經營的貨船。

## 方向（步驟 1；2026-11-01）
- 同級船：**Henrietta Marie** —— 倫敦登記，1700 年沉在佛州外海；唯一找到船骸、身分確定的奴隸船。120 噸（Builder's Old Measurement）、全長約 18–24 m、船員約 18 人、最後一航 191 人；船骸找到龍骨與部分艉柱、80 多副鐐銬、1 門砲、2 隻錨（Wikipedia "Henrietta Marie"，引 Malcom、Cottman、Sullivan）。可能是法國造（未確認）。
- 1666 年的英國奴隸船（皇家冒險者公司 1662–1672，自有船 104 航次）單船尺寸網上查不到：要英國國家檔案館的通行證登記冊（ship、tonnage、guns、crew）—— 照實寫「同級船」，不假裝有原船數字。
- 大的例外：Hannibal（1693，450 噸、36 門砲，皇家非洲公司）—— 不是這一級。
- 船名：不借真船的名字，作品叫「幾內亞船」（Guineaman 是那一型的通稱）。

## 座標與比例（步驟 2；2026-11-01）
- 0.1 m／格；框 448 × 192 × 384（同好旅號；調尺寸免費、不縮放內容）。x 船長、船頭 +x；y 中線格 96（鏡像 y ↔ 192 − y；P 舷 y < 96）；z 0 ＝ 龍骨底面。
- 作品：組裝件 `kaguya-guineaman-01m-assembly`「幾內亞船」（主作品，關聯 `船殼` at 0,0,0）；船殼 `kaguya-guineaman-01m`「幾內亞船 船殼」（任務作品、tags sub、委託 ref TASK-1149、領薪 10）。兩件都記 meters_per_voxel 0.1（create 之後用 update 補、回讀 work.json 確認 —— 好旅號踩過 create 不存 tags／比例）。
- 現有元件（`work sub=components` 2026-11-01）：4 磅砲 `pinnacle-patache-01m-gun-4l`、6 磅砲 `summit-stormkaap-01m-gun-6l`、迴旋砲 `apex-one-reale-01m-gun-pierrier`＋座、火藥桶、錨 `basecamp-frigate-constitution-01m-anchor`、絞盤 `basecamp-ember-01m-capstan`、羅經櫃、小艇 `basecamp-ember-01m-boat`（縮放）、門 `gura-pinas-01m-door`、艙蓋 `meadow-monitor-01m-hatch`、爐灶 `kaguya-gloire-01m-galley`、燈 `gura-tridente-01m-lantern`；帆桁縮放風暴角號／憲法號的。
- ⚠ 步驟 11 先記著：1666 年的英國小商船是用舵柄 whipstaff 操舵，舵輪要到 1700 年代才普及 —— 遊戲要 kind=wheel，到時候查 Ship_Helm 怎麼處理（照實寫成時代錯置，或問 Tim）。

## 階段一 造船資料與新圖紙 01／02（步驟 3；2026-11-01）
- 資料：`references/research_guineaman_2026-11-01.md`（〔查〕〔二手〕〔推〕〔設計〕）。Henrietta Marie 只有噸位、全長範圍、船員、人數；1666 年英國奴隸船的單船數字查不到 ⇒ 主尺寸〔設計〕，每個數字在 plan.json 的 src。
- 產生程式：牛津號 `design/` 整套複製（每支檔頭「出處：erina-oxford-01m/design/…」；作品 id、persona、船名、單號換掉，grep 舊 id 只剩註解裡的出處）。牛津號的產物（masks、verify、placement、圖紙）全清掉；`plan_oxford_ref.json` 只拿來對照、⛔ 不被程式讀。砲門蓋板的 `tools/portlids.py` 拿掉（步驟 12 刪了）。
  - **控制組**：還沒改一行時拿牛津號的 plan 重跑 ⇒ `verify_lines.json`、`verify_layout.json`、兩張圖紙跟牛津號存的逐位元組相同。
  - 改的程式：`draft_lines.py` 主尺寸對照的目標（60／20／70 ft）；`draft_layout.py` 圖說與 `--probe` 只列 plan 有的那幾排砲門（牛津號寫死炮甲板＋後甲板兩排、寬 73 格）、圖例「炮甲板」⇒「主甲板」。`lines.py`、`layout.py` 沒改。
- `plan.json`：lines、waterline、readings_at、decks_preview、decks、ports、masts、hull_build.bottom_top_z 換成本船；其餘段落照抄牛津號、列在 `_todo`（到那一步再改）。decks 的鍵照牛津號（orlop ＝ 下層甲板、gun ＝ 主甲板），步驟 5 的標題再換。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 主甲板長（z 37，艏柱到艉柱） | 21.49 m（70.5 ft） | 〔設計〕70 ft；〔查〕Henrietta Marie 60–80 ft |
| 龍骨 | 18.30 m（60.0 ft） | 〔設計〕60 ft |
| 最大寬 | 6.10 m（61 格，20.0 ft） | 〔設計〕20 ft |
| 設計水線 | z 29（吃水 2.9 m） | 〔推〕9.5 ft |
| 排水量（水線下實心 × 1.025） | 191 t | 120 噸 burthen 的 1.6 倍（滿載商船） |
| 甲板 | 下層 z 20（到主甲板樑底 1.4 m）；主甲板船中 z 37；後甲板 ＋18、艉樓再 ＋16、艏樓 ＋16 | 〔設計〕 |
| 砲門 | 每舷 5（x 118、146、172、198、222）、4 磅；下緣離水線 1.30–1.40 m、淨距 19–23 格 | 〔設計〕 |
| 桅頂離水線 | 主 24.4、前 21.6、後 14.7 m | 〔二手〕主桅 53.6 ft（Lees 1670 規則） |
| 帆面積（攤平 10 面） | 389 m²（主帆桁 13.4 m ＝ 2.20 × 寬） | 〔設計〕 |

- 讀數：線形 1 元件、空腔 0、鏡像差 0、問題 0；兩支 draft 重跑兩次 5 個輸出逐位元組相同；**反向對照** `--probe=half_beam=+3` ⇒ 全寬 61 → 67；`--probe=port=gun:1:+3` ⇒ 淨距 [23, 21] → [26, 18]（探針不寫檔）。
- 輸出：`sheet01_lines_v1.png`、`sheet02_layout_v1.png`、`verify_lines.json`、`verify_layout.json`、`masks/hull/hull_01.vox.txt`（102,185 格，sha256 becf0ee8…）。
- ⚠ 留給步驟 8：主桅 x 159 的 channels 跟兩邊的砲門（146、172）很近，鏈板會從砲門之間下來 —— 牛津號也是這樣排，draft_rigging 擺的時候再量。

## 階段二 船殼落格（步驟 4 前半；2026-11-01）
- 標記 `船殼` begin（upto=start）→ `tools/stamp_lists.py kaguya-guineaman-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 102,185 ＝ 清單）→ `船殼` end。
- 結果帳（`tools/check_hull.py`，作品從 export 讀）：102,185 ＝ 設計，缺 0、多 0、色差 0；線形對照 438 點差 0；**反向對照** `probe_x=180`（那一站 +3）⇒ 報 16 點、最大差 3。
- 結構（引擎 stats）：1 元件、空腔 0、鏡像差 0（y:96）。組裝件關聯 `船殼` meta `kind=ship, waterline_z=29`（`part=link`，回讀 links.json 有）。

## 階段三 砲門、塗裝、船尾窗（步驟 4 後半；2026-11-01）
- 程式改兩處：`draft_ports.py` 船尾窗的參考欄照 `plan.stern.x_ref`（牛津號寫死 x 46；好旅號同樣改法）；`tools/check_stage3.py` 讀的標記換成本作品的 `炮門塗裝:end`（牛津號是 `炮門8挪位:end`）。
- plan 的 `paint`、`stern` 換成本船（〔設計〕，從 `_todo` 拿掉）：木色 177、兩條黑主 wale（甲板下 −6、−2）＋ channel wale（＋11）、船腰舷頂黑、**只有船樓的舷牆**藍底金邊（frieze 從 ＋14 起；13 會在船腰前段舷頂下留一串金點 ⇒ 改 14）、砲門紅框 192、水線下灰白 182；方艉 wing transom 黑（z 40–41）、以上藍底；船尾窗 6 扇：後甲板底下大艙 4 扇、艉樓底下船長艙 2 扇（金框、玻璃 155）。
- ⇒ `masks/ports/carve.vox.txt`（1,200，帶顏色守門）、`paint.vox.txt`（11,226）、`glass.vox.txt`（150，步驟 6 用）、`sheet03_ports_paint_v1.png`；重跑逐位元組相同。
- 落格：標記 `炮門塗裝` begin → carvevox 1,200（placed 1,200）→ stampvox overwrite=1 11,226（placed 11,226）→ end。
- 讀數（`tools/check_stage3.py`）：結果帳 100,985 缺 0、多 0、色差 0；10 個砲門開口裡實心 0；正向對照（同一把尺量 `船殼:end`）10 個全報；**反向對照** `draft_ports.py --probe=skip_port=gun:3` ⇒ 只報那一門兩舷（各 75 格）、清單不動；stats 1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq}.png`（還沒有甲板，船殼是空的）。

## 階段四 甲板、艙口、break、梯子（步驟 5；2026-11-01）
- plan 的 `decks_build` 換成本船（從 `_todo` 拿掉）；`draft_decks.py` 改兩處：梯子井的長度照 `well_a`／`well_b`（牛津號固定 2..16 ＝ 6 階的井）、從井口上去的梯子不在 break 的胸牆留口。
- ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`（子作品 `-deck-<層>`、`-ladders-<層>`，關聯 `甲板-<層>`、`甲板-<層>/梯子` meta kind=ladders；tags sub、0.1 m 回讀 work.json 都有）。
- 甲板（地板上第一層空氣，decks.py 量）：**下層甲板** 21（x 79–228；奴隸船艙裡整層 —— 到主甲板樑之間淨高 1.6 m、樑底下 1.3 m，底下約 1 m 的艙放水桶，人站不進去）、主甲板 38（船中；船尾 45、船頭 43）、後甲板 56–63、艏樓 56–59、艉樓 75–80。橫樑每 13 格（相位照第 1 門砲門 x 118）。
- 艙口：主艙口 x 176–188（半寬 7）、前艙口 200–208（半寬 6），只開主甲板；桅孔照三根桅軸（主、前 r 3.8、後 3.0）。break 三道（後甲板前緣 x 141、艉樓前緣 x 90、艏樓後緣 x 228），門：後甲板、艏樓開中線，艉樓開 |dy| 14（中線是梯子）。
- 梯子 6 座：lower（下層 ⇄ 主甲板，後甲板底下大艙裡開井，之後火藥庫放旁邊）、qd-P／S（大艙裡從井口上後甲板，|dy| 9）、poop（中線）、fc-P／S（艏樓底下從井口上艏樓，|dy| 9）。每層都有梯子通到。
  - 🩸 v1 的 qd、fc 梯子照牛津號放在船腰（梯頂靠 break）⇒ 外側 stringer（|dy| 13）擋在第 2 門（x 146）、第 5 門（x 222）砲後面、砲班站的地方（`ports_blocked_inside` 2＋16 格）；船腰 21 m 擠不出 18 格長、不碰砲的空檔 ⇒ 改成船樓底下從井口上去。
  - 艏樓只高 1.6 m ⇒ 5 階：井開到最上一階（`well_b` 13）、head 在井口外 2 格（照 Ship_Decks ④「梯頂接不上甲板」的算法，不留一段空的）；lower 同樣 5 階、同樣改法。
- 讀數：draft 時件與件重疊 0、梯子點問題 0、砲門往艙裡被擋 0、封閉空腔 0；**反向對照** `--probe=drop_ladder=lower` ⇒ 下層甲板沒有梯子通到、`drop_ladder=poop` ⇒ 艉樓沒有（探針不寫檔）；重跑逐位元組相同。結果帳 9 件 36,699 格缺 0、多 0、色差 0、重疊 0（`tools/check_decks.py`）；梯子點（組裝件 parts）24／24、差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 137,684 格 1 元件、空腔 0、鏡像差 0、link_overlap 0。
- 甲板 meta：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（代號照商船的寫法 orlop／main／quarter／forecastle／poop —— 信風號、好旅號的主甲板也是 main；名字照 plan 的 names；level 照 decks.py 的高度順序 0–4）⇒ `work sub=meta file=`（5 筆，回讀 links.json 5 條 kind=deck）。
- 預覽 preset `藏船殼`。過程圖 `overlays/stage5_decks_nohull.png`。空艙房沒標（下層甲板要不要隔出艙房、標 rooms，等玩法那張單）。

## 步驟 6 裝飾（2026-11-01）
- plan 的 `deco` 換成本船（從 `_todo` 拿掉）。程式改：`draft_deco.py` 王冠照 `figurehead.crown`（商船不戴）、獅子尾巴畫成 6 連通；`tools/build_deco.py` 船首像掛成外部模型 `deco=1`（同澤漢號、拉貝爾號）；`draft_ports.py` 船尾窗玻璃補接縫（見下）。
- 船首喙 `-beakhead`（平台面 z 49、從艏柱 x 268 伸到 x 288、半寬 1.1 m 收尖；cutwater 從水線下 z 22 斜到平台尖、前緣金；兩舷兩條 head rail（金、藍）＋柱，6 連通；固定點 bobstay-1 (277, 96, 34)）、船首像 `-figurehead`（金色獅子、不戴冠，489 格；組裝件外部模型 at 0,0,0、pivot 0、scale 1、meta deco=1）、船尾旗桿 `-ensign-staff`（x 43、3.8 m；固定點 flag-head／flag-foot）、船尾窗玻璃 `-stern-glass`（180 格、6 扇；關聯 meta material=glass）。
  - 🩸 v1：平台 z 51、獅子 x 280 ⇒ 尾巴一格一格往上捲、x 與 z 同時變的那幾步只在斜角相碰 ⇒ 上半截浮空 6 格（組起來 2 元件），而且那一截伸進艏斜桅的路（4 格）⇒ 尾巴改 6 連通、平台降到 49、獅子往前 2 格（平台尖延到 x 288 讓前腳站得到）。
  - 🩸 船尾窗玻璃：艉柱倒 10° ⇒ 每扇窗上下兩排玻璃差 1 格、只在斜角相碰（6 扇窗 12 塊）⇒ `draft_ports.py` 上排每格底下補 1 格（30 格；Ship_Materials「窗的玻璃」、澤漢號同樣補法）⇒ 6 塊。carve／paint 清單不變（步驟 4 的帳照樣成立）。
- 〔設計〕船名板不做（1660 年代英國船船尾不寫船名，同牛津號）；quarter gallery、船尾陽台不做（120 噸商船沒有）；船尾燈不做（舷頂窄、會撞到旗桿）。
- 讀數：落在船上不放的 241／3 格；件與件重疊 0；組起來 1 元件、空腔 0、鏡像差 0；艏斜桅那條線裡的裝飾格 0；**反向對照** `--probe=shift=figurehead:9` ⇒ 元件 2（後腳離開平台尖；推 6 格還站在延長的平台上、照樣 1）；重跑逐位元組相同。組裝件 139,626 格 1 元件、空腔 0、鏡像差 0、link_overlap 0（獅子是模型、不算在格子裡）。回讀：models.json 船首像 deco=1、links.json 玻璃 material=glass、子作品 tags sub、0.1 m。
- ⚠ 旗桿的 flag-foot 照 `plan.rigging.flags.ensign`（還是牛津號的旗高）⇒ 步驟 8 改 rigging 時重產 deco（anchor overwrite）。
- 過程圖 `overlays/stage6_{bow,stern}.png`。

## 階段六 桅與帆桁（步驟 7；2026-11-01）
- plan 的 `rig_build` 換成本船（從 `_todo` 拿掉）；程式只改 `draft_masts.py` 艏斜桅開孔多量船首喙（量到 0）。`draft_masts.py` ⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen.vox.txt`＋`yard_lateen_anchors.json`、`masks/bowsprit_hole/`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`。
- 桅（子作品 `-mast-main／fore／mizzen`，關聯 主桅／前桅／後桅）：下桅＋圓桅樓（主 r 12、前 11、後 10 —— ⛔ 不照船的比例縮：遊戲桅頂水手站位半徑 9–18 格，牛津號 r 7 站不下）＋上桅（在下桅頭前面 doubling）＋上桅帆桅（主、前）；每節頂黑 cap、上桅頭十字桁。格數 主 6,651、前 5,350、後 2,628；桅腳落在船底的格不放（前 47、後 42：deadwood 抬高的那一段，桅腳插在船底裡）。桅頂離水線：主 24.4、前 21.6、後 14.7 m。
- 艏斜桅（`-bowsprit`，1,861 格）：根部 (246, 46)、仰 35°、9.8 m；開孔 133 格（船殼 84、艏樓甲板 49、船首喙 0；carvevox 帶顏色守門、標記 `艏斜桅孔`），孔由艏斜桅填滿。
- 方帆桁 9 根：引用風暴角號的帆桁元件等比縮放（main course 0.570、topsail 0.545、topgallant 0.442、fore 0.565／0.532／0.509、crossjack ＝ 主上桅帆桁 0.480、mizzen topsail 0.627、spritsail 0.516），掛在那一節桅的前面（半徑＋2.5）、meta `kind=yard`＋`yard`（course／topsail／topgallant／crossjack／spritsail）＋`sail`。
- 後桅三角帆桁：新元件 `kaguya-guineaman-01m-yard-mizzen-lateen`（114×5×5、中段粗兩頭細，866 格；固定點 pivot／sling／fore／peak／earing-F／A／top-NN 共 20）；擺在後桅左舷側、rotate y 40°、meta `yard=gaff rig=lateen`。
- 讀數：組裝件 155,983 格 1 元件、空腔 0、鏡像差 0、link_overlap 0、link_clipped 0；觀測 models_drawn 11（帆桁 10＋船首像）、models_broken 0；重跑：桅、帆桁、擺法逐位元組相同（艏斜桅孔清單 ＝「還沒刻的」⇒ 刻完之後是 0，照設計）；**反向對照**：同一把尺量刻之前的船殼（`炮門塗裝:end`）∩ 艏斜桅 ＝ 84、現在 ＝ 0。子作品 tags sub、0.1 m。
- 過程圖 `overlays/stage7_masts.png`。

## 階段七 索具、帆、旗（步驟 8；2026-11-01）
- plan 的 `rigging` 換成本船（從 `_todo` 拿掉）。`draft_rigging.py` 改：牛津號寫死的 5 個數改成 plan 給（預設值照牛津號 ⇒ 拿牛津號的 plan 跑結果不變）—— 主支索下端照前桅的 x（牛津號 274）、後桅支索綁主桅的高度 `mizzenstay_foot_z`（62 ⇒ 60）、船頭／船尾能綁的那一欄 `bow_belay_x`／`stern_belay_x`（300／42 ⇒ 262／45；這艘的船殼到 x 268 就沒了，照 300 會當掉）、ensign 貼圖照旗的大小（36 × 24 ⇒ 30 × 20）；繩梯落腳點（見下）。
- ⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落地 `tools/rigging_apply.py`（channels 948 格 → 固定點 114 → 繩 73 → 橫繩組 12 → 帆 11 → 帆的繩 23 → 風 → meta 34）。
- channels：舷頂那一列、1 格厚（在砲門頂上，不擋砲門）；shrouds 每舷主 5、前 4、後 3、間距 0.6 m；上桅 backstay 主、前各 1；上桅 shrouds、futtock 各 3（〔設計〕沒查到 120 噸商船的索具表）。支索 6、bobstay（綁 cutwater 前緣）、艏斜桅 shrouds 2。
- 橫繩組 12：下桅 6 組 climb=1（foot 舷牆內側的甲板、head 桅樓靠這一舷的邊）、上桅 6 組。
  - 🩸 v1 落腳點照牛津號用 shrouds 中間那一欄：前桅 x 224 ＝ 第 5 門砲門正後面（那一欄還剛好是砲門開口、量舷牆寬時 KeyError）、主桅 x 145 ＝ 第 2 門 —— 步驟 9 的砲與砲班就站那裡 ⇒ 改成在 shrouds 範圍裡找：避開砲門 ±（半寬＋5）那一條、要站得住（腳下實心、頭上 7 格空），同一層甲板的先、近的先 ⇒ 主桅 x 154（船腰，第 2 門與主桅之間）、前桅 x 229（船腰那一段全是砲門的範圍 ⇒ 站上艏樓）；後桅 x 77（艉樓）不變。6 個落腳點、6 個 head 都量過：腳下實心、頭上 7 格空。
- 帆 9＋旗 2：前／主 course、topsail、topgallant，後上桅帆（帆腳綁 crossjack），spritsail（`sail=course set=3`），後桅三角帆（`sail=gaff`）；英國紅 ensign（左上角白底紅聖喬治十字）掛船尾旗桿、主桅頂紅長旗。旗桿的 flag-foot 照新的旗高重產（deco 清單不變、只動這個固定點：99 ⇒ 103）。

| 帆裝 | 張的帆 |
|---|---|
| 收帆（1） | fore-topsail、main-topsail、mizzen-topsail |
| 戰鬥帆（2） | ＋ fore-topgallant、main-topgallant、mizzen-lateen |
| 滿帆（3） | ＋ fore-course、main-course、spritsail |

- 讀數：ropecheck 繩 206 條（含橫繩組展開）、兩端 412 全 ok、link_overlap 0；view ropes_broken 0、sails_broken 0、models_broken 0；帆的繩沒 meta 0、meta 的帆名對不上 0、重名 0；固定點落在實心 0；組裝件 156,931 格 1 元件、空腔 0、鏡像差 0；**反向對照** `--probe=nometa=mizzen-lateen-tack` ⇒ 只報那一條；draft 重跑 4 個輸出逐位元組相同。回讀 sails.json 11 筆 meta、channels 子作品 tags sub、0.1 m。
- 過程圖 `overlays/stage8_rigging.png`。

## 步驟 9 砲（2026-11-01）
- 程式：`draft_guns.py`、`gunsim.py`、`tools/build_guns.py` 換成好旅號那一版（出處鏈：牛津號 ⇒ 信風號 ⇒ 好旅號 ⇒ 本船；好旅號那一版多了舷頂迴旋砲、物件 id 先發、迴旋砲座的雙生）；只換 plan 的 `guns_build`（從 `_todo` 拿掉）。⇒ `guns_placement.json`、`verify_guns.json`；落地 `tools/build_guns.py`。
- 主甲板 10 門 4 磅砲（每舷 5，x 118、146、172、198、222）⇒ `pinnacle-patache-01m-gun-4l` ×0.5；P 舷 mirror=y。
- 迴旋砲 6 門 ⇒ `apex-one-reale-01m-gun-pierrier` ×0.5（meta mount=turret、arc −80,80）：艉樓 x 58、後甲板 x 105、艏樓 x 250 每舷各 1 —— 都避開三段 channels（後 68–86、主 123–159、前 206–236）；每門一個「座」雙生（`apex-one-reale-01m-gun-pierrier-mount`、kind=gunmount、mount_of ＝ 那門的 id）。
- 物件 id 自己先發：gun-1..16、gunmount-11..16（步驟 14 的 admin.py ids 照這個留）。
- 讀數：16 門全 ok —— 4 磅砲退 2.0–4.5 格、砲口伸出 2.75–5.25 格、腳下支撐 0.5–1.0（第 5 門 x 222 舷弧往船頭抬、砲架跨兩個甲板高度 ⇒ 支撐 0.5 ＝ 下限、退 4.5、伸出 2.75）；迴旋砲砲口伸出 7.5 格；模型 ok 22／bad 0（砲 16＋座 6）；觀測 models_drawn 33（帆桁 10、船首像 1、砲 16、座 6）、models_broken 0；組裝件 1 元件、空腔 0、鏡像差 0、link_overlap 0。**反向對照** `--probe=push=砲M-S01:4` ⇒ 只報那一門 1,389 個碰撞樣本；draft 重跑逐位元組相同。
- 砲具與砲索沒做（Ship_Steps「要的話」；10 門小砲，同好旅號）。
- 過程圖 `overlays/stage9_guns.png`（藏船殼）。

## 步驟 10 火藥庫、格柵、甲板物件（2026-11-01）
- plan 的 `gear` 換成本船（從 `_todo` 拿掉；`_todo` 只剩 `rudder_anchor_build`）。程式改：`draft_gear.py` 火藥庫可以不砌後牆（`magazine.aft_wall`，照好旅號）、艙口格柵（`gear.gratings`：產生格子、量碰撞與圍板、寫清單，做法照風暴角號 draft_capstan_grating.py）、模型的碰撞與支撐也算格柵的格；`tools/build_gear.py` 建格柵子作品（0.05 m）並掛成模型、後甲板也能掛模型。⇒ `masks/gear/{magazine,grating-main,grating-fore}.vox.txt`、`gear_placement.json`、`verify_gear.json`。
- **火藥庫**（`-magazine`，807 格，關聯 `彈藥庫`）：下層甲板船尾，只砌前牆 x 116（後牆會把船尾那一段封成空腔 —— 好旅號），往後到船殼、後桅（x 86）在裡面；門在前牆中線 0.5 × 1.4 m、朝 lower 梯腳 x 135；固定點 blast (105, 96, 27)、door (116, 96, 21)。桶 4 個（憲法號共用桶 ×0.2、各 100 lb，x 96.5／102.5 × y 88.5／104.5）⇒ meta `kind=magazine pos=aft powder_lb=400 hoist=甲板-gun/梯子/lower,甲板-qd/梯子/qd-P,甲板-poop/梯子/poop,甲板-fc/梯子/fc-P`（後甲板 z 56–63 跟艏樓 56–59 高度重疊 ⇒ 每一層列一座梯子，Ship_Magazine §8）。
- **格柵艙口**（奴隸船的構造，出處見 research §6）：子作品 `-grating-main`（26 × 30 × 4、996 格）、`-grating-fore`（18 × 26 × 4、636 格），0.05 m、1 格條 1 格空（5 cm 的洞）、縱條 177、橫條 136、hatch bar 同圍板色 141；掛在 `甲板-gun` 成模型（scale 0.5、kind=grating），格柵頂齊圍板頂（世界 z 40.0）。不蓋艙蓋（格柵不是門 ⇒ 遊戲不把它當進水口，§9.7）。
- **甲板物件**（擺法照好旅號）：爐灶（光榮號 ×0.22、kind=galley；船腰主桅與主艙口之間 x 164–174 —— 露天 ⇒ 共用件的 smoke 照樣對；廚師站 ±y 兩面）、小艇（餘燼號 cutter ×0.13 ≈ 2.3 m、kind=boat；擱在前艙口前面那道照舷弧升到 z 40 的圍板上，主艙口的格柵留著不蓋）、絞盤（餘燼號 ×0.09、kind=capstan；後甲板中線 x 110–117，艉樓梯腳 x 105 與後甲板梯頂 x 120 之間）、羅經櫃（夜隼號 ×0.2、kind=binnacle；艉樓底下的後甲板中線 x 75–79，步驟 11 的 whipstaff 舵手站這裡）。
  - 🩸 v1：小艇 z 40 ⇒ 撞前艙口前面那道圍板 5 格（舷弧讓它比後面那道高 1 格）⇒ z 41；羅經櫃 x 79.5 ⇒ 撞後桅 4,134 個取樣點（後桅往後倒 4°，z 60 以上已經退到 x 80）⇒ x 77。
- **barricado 不做、通風口不做**（research §6）：barricado 查到的是 1734（Snelgrave）、1788（Falconbridge）、Rediker 的 1700–1808，1660 年代查不到；一道 2.4 m 的牆橫過船腰會改掉船員的走法與接舷戰 ⇒ 留給玩法單（要加 ＝ 一件新的子作品關聯，不動別的件）。通風口是 1788 年 Dolben 法案之後到 19 世紀初的事。
  - 步驟 3 那一行「17 世紀末的文獻有（Phillips 1693–94）」：這次查不到 Phillips 原文裡有 barricado ⇒ 改成「未確認」（research §6 留著原句、劃掉）。
- 讀數：draft 碰撞 0、不進砲的外框 0、問題 0（桶、爐灶、絞盤、羅經櫃支撐 1.0；小艇擱在圍板上不要求、0.05）；格柵世界格碰撞 0、圍板頂一圈 60／60、48／48 實心；**反向對照** `--probe=shift=羅經櫃:3` ⇒ 撞後桅 17,613、`--probe=shift=格柵-主艙口:1` ⇒ 撞圍板 16 格、`shift=小艇:0` ⇒ 0（探針不寫檔）；重跑 5 個輸出逐位元組相同。結果帳（作品從 export 讀）火藥庫 807、主艙口格柵 996、前艙口格柵 636，缺 0、多 0、色差 0。組裝件 157,738 格（＝ 156,931 ＋ 807）1 元件、空腔 0、鏡像差 0、link_overlap 0、link_clipped 0；觀測 models_drawn 43（＋10）、models_broken 0、ropes_broken 0、sails_broken 0。回讀：links.json `彈藥庫` meta 如上；三件子作品 tags sub、parent 船殼、火藥庫 0.1 m、格柵 0.05 m。
- 過程圖 `overlays/stage10_deck.png`（不畫帆與繩）、`stage10_magazine.png`（只留下層甲板與後桅）。

## 步驟 11 舵、舵柄、錨（2026-11-01）
- 程式：`draft_rudder_anchor.py`、`tools/build_rudder_anchor.py` 換成好旅號那一版（出處鏈：牛津號 ⇒ 信風號 ⇒ 好旅號 ⇒ 本船；本船原本那份是牛津號的、沒有舵柄），只換 id、船名、單號；多加一樣：艏樓有迴旋砲 ⇒ 錨的候選位置外框碰到砲模型（kind=gun／gunmount）的外框就不選、每隻錨的讀數多一欄 `gun_box_overlap`。plan 的 `rudder_anchor_build` 換成本船（`_todo` 空了）。⇒ `masks/rudder/{rudder,tiller,helm_port_hull,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`。
- **舵**（`-rudder`，1,277 格）：沿艉柱後緣倒 10°、z 0–70（艉樓底下那一層）、3 格厚、舵葉 1.2 m 往上收到 0.3 m；水線下白、上黑、每 10 格鐵箍；前緣兩側削 1 格。組裝件模型 `舵`：kind=rudder、hinge (58, 96.5, 0)、axis (−0.1736, 0, 0.9848)、max 35°、turn_axis=hinge、spin=rudder ±35°；固定點 stock-top (43, 96, 70)。舵在 y 95–97、船尾窗玻璃最靠中線的是 y 94／98 ⇒ 擋到的玻璃 0 格。
- **舵柄**（`-tiller`，166 格，z 69–70）：從舵軸 x 44 穿過船尾板（helm port 刻 18 格，由舵柄填滿、標記 `helm port`）伸進艉樓底下到 x 71（羅經櫃從 x 75 起）；掛在後甲板子作品成模型 `舵柄`：kind=tiller、spin=rudder ±35°、固定點 spin-a／b (44, 96, 69／70)。不放舵輪。
  - 〔查〕1660 年代英國船是舵柄＋whipstaff（舵柄在下一層、whipstaff 穿上來給艉樓底下的舵手）——〔設計〕這一版把舵柄直接放在舵手那一層（好旅號的寫法），whipstaff 不做：遊戲的操舵鏈只認舵柄，一根跟著舵柄擺的 whipstaff 做不出槓桿的動作。
- **錨**：共用錨元件 ×0.42（好旅號 0.45 是 150 噸級；照噸位的立方根）、meta anchor=bower；兩舷各一（錨環 (253.8, 126.9／66.1, 60)、錨臂順著船殼切線 rz ±69.5°），錨冠落在錨床 `-anchor-gear`（672 格，關聯 `錨床`，ztop 36、foot_gap 0）上。船殼固定點 hawse-S／P (260, 113／79, 47)（主甲板那一層、艏樓底下；只登記固定點、沒有開孔）。〔查〕Henrietta Marie 船骸找到 2 隻錨。
  - 🩸 v1：錨環從 z 54 試起，好旅號的規則是「一樣貼船就取最低的」⇒ 選到 z 54，錨冠垂到 z 31，只比水線（z 29）高 0.2 m ⇒ 只試 z 60–63（艏樓舷頂 z 64 底下）。
- 讀數：舵 on_solid 0、舵柄 on_solid（helm port 以外）0、錨床 on_solid 0、錨碰撞 0、碰到迴旋砲外框 0、舵／舵柄／錨床／錨 鏡像差全 0；**反向對照** `--probe=shift=錨-S:-3` ⇒ 錨-S 撞錨床 1,981、錨-P 0；`shift=錨-S:6` ⇒ 碰到 `甲板-fc/迴旋砲F-S01座` 的外框；`shift=錨-P:0` ⇒ 0；重跑 6 個輸出逐位元組相同。結果帳 舵 1,277、錨床 672、舵柄 166 缺 0／多 0／色差 0；船殼 100,883 格（＝ 100,985 − 艏斜桅孔 84 − helm port 18），helm port 18 格船殼裡剩 0、舵柄填滿 18／18。組裝件 158,392 格（＝ 157,738 − 18 ＋ 672）1 元件、空腔 0、鏡像差 0、link_overlap 0、link_clipped 0；ropecheck 繩 206、兩端 412 全 ok；觀測 models_drawn 47（＋舵、舵柄、錨 ×2）、models_broken 0、ropes_broken 0、sails_broken 0。回讀（export parts）：舵、舵柄的 spin 都在、錨 anchor=bower；子作品 tags sub、0.1 m、parent 船殼。
- 過程圖 `overlays/stage11_stern.png`、`stage11_bow.png`（不畫帆與繩；region 只裁格子、框外的模型照畫 ⇒ 浮在空中的是別處的模型）。

## 步驟 3 的起點（2026-11-01 定的方向，留著對照）
- **產生程式從牛津號抄**（`erina-oxford-01m/design`）：1656 年英國五等艦，同時代、同國 ⇒ 方艉（wing transom＋船尾板兩排窗）、tumblehome、17 世紀英國船頭都對；同一個框 448 × 192 × 384、yc 96。信風號、好旅號都是從它抄的（好旅號修過的坑先看它 notes 再抄）。
  - ⚠ 三套的 `lines.py` 都沒有 Ship_Ends 的 counter／beakhead／stern_tumble —— 120 噸商船不需要兩層 stern walk、整片 beakhead 平台；要的只有小的船首喙與方艉，照牛津號原本的寫法縮。
- **主尺寸（推，待步驟 3 定案、逐項標出處）**：Builder's Old Measurement 噸 ＝ (龍骨長 × 寬 × 寬/2) ÷ 94。120 噸、寬 20 ft（6.1 m）⇒ 龍骨約 56 ft（17.1 m）⇒ 甲板長約 68 ft（20.7 m），落在 Henrietta Marie 的 60–80 ft 之內。寬 19 ft ⇒ 龍骨 62 ft。〔設計〕先取寬 20 ft。
  - 牛津號是 24 ft 寬、220 噸 bm ⇒ 線形參數大致 × 0.83 縮。
  - 吃水〔推〕約 9–10 ft（2.9 m），艙深約 9 ft。
- 砲：〔推〕8～10 門 4 磅（`pinnacle-patache-01m-gun-4l`），露天甲板從舷牆砲門打；後甲板加迴旋砲。Henrietta Marie 船骸只找到 1 門砲，沒有砲數 ⇒ 照實寫推的。
- 奴隸船才有的構造（步驟 5、10 再定、都要標出處）：下層甲板（slave deck，大概 1.5 m 淨高）、主甲板上的格柵艙口與通風口、主桅前橫過甲板的 barricado（17 世紀末的文獻有：Thomas Phillips 1693–94 Hannibal 的航海日誌；1666 年有沒有要查）。⇒ 步驟 10 再查：Phillips 那一條沒查到原文，見步驟 10。

## 下一步
- 步驟 12、13 單上刪了（砲在露天甲板、沒有槳）⇒ 下一步是步驟 14：給遊戲的 meta 與匯入 Blockside（Ship_Game §9、§9.4、§12）。照好旅號的步驟 14：Blockside 自己的 worktree（`_cache` 先從共用的複製）⇒ `admin.py import --work kaguya-guineaman-01m-assembly --id <id> --name 幾內亞船` ⇒ `ids`（砲的 id 是 draft_guns 先發的：gun-1..16、gunmount-11..16）⇒ 修 ⚠ ⇒ `reimport`；import／reimport 會重 dump 整份 game.json ⇒ 拿 HEAD 只插本船那一筆、斷言別的船逐項相同。⚠ 立場：ships[] 那一筆不能讓玩家造或買（Blocksail 那一型是單上 #3，另外做）。
- 還沒提交：作品資料夾（含 design/）全部還沒提交到 Sculpture。

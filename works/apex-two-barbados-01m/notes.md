# 巴貝多商人號（Barbados Merchant, 1666）—— 英國三桅商船建造筆記（0.1 m／格）

委託：Tim 2026-11-01（/scp-task）「1147 go」—— TASK-1147《Blocksail》1666 加勒比船型：英國三桅商船（約 100–300 噸），船隊裡英國沒有中型商船。主單 TASK-1146（summit 盤點的缺口 #1）。
驗收：TASK-1147 的驗收標準（原本 4 格 ＋ Ship_Steps 步驟 1–15，刪步驟 13）。

## 為什麼是她
- 〔查〕Kent HER 海事紀錄 TQ 87 SW 1246：BARBADOS MERCHANT（亦作 Barbadoes Merchant）
  - 1666 年海軍買下當火船，223 噸、長 76 ft × 寬 23 ft 6 in、8 門砲。
  - 1667-06-11 Medway 之役鑿沉在 Long Reach 擋荷蘭艦隊；1669 年殘骸賣給 Richard Boys，1670 年拆掉。
  - 出處：Kent HER 引 Lists of Men of War 1650-1700、British Warship Losses in the Age of Sail、Larn 1995。
- 〔推〕「76 ft」是計噸龍骨長：builder's old measure 76 × 23.5 × 11.75 ÷ 94 ＝ 223.25 ⇒ 正好 223 噸。
- 名字就是她跑的航線（倫敦—巴貝多的糖），開局 1666 年正好在海上。
  - ⚠ Kent HER 推測同名的船 1665 年跑過一趟販奴航線（只是推測，紀錄自己說沒證實）；奴隸船船型是 kaguya 的 TASK-1149，這艘照一般的西印度商船造。

## 座標與比例（步驟 2）
- 0.1 m／格。框 480 × 192 × 384：x 船長、船頭朝 +x；y 船寬、中線格 y 96（格 y ↔ 192 − y）；z 0 ＝ 龍骨底面。照牛津號（erina，同國、同年代、同級）的約定。
- P（左舷）＝ y < 96、S ＝ y > 96。
- 作品怎麼拆：
  - 船殼 `apex-two-barbados-01m`「巴貝多商人號 船殼」：任務作品、tags sub。
  - 組裝件 `apex-two-barbados-01m-assembly`「巴貝多商人號」：主作品，關聯 `船殼` at 0,0,0。
  - 子作品都用整船的框、關聯 at 0,0,0、parent_work 指船殼、tags sub。
  - 三件都記 meters_per_voxel 0.1。
- 可以直接引用的現有元件（`work sub=components`，2026-11-01）：
  - 砲：`summit-stormkaap-01m-gun-6l`（縮放當 4l／6l，牛津號就是這樣用）、`pinnacle-patache-01m-gun-4l`。
  - 帆桁：風暴角號的方帆桁（等比縮放）、牛津號的三角帆桁 `erina-oxford-01m-yard-mizzen-lateen`。
  - 其他：火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`；絞盤 `basecamp-ember-01m-capstan`；小艇 `basecamp-ember-01m-boat`；錨 `basecamp-frigate-constitution-01m-anchor`；艙蓋 `meadow-monitor-01m-hatch`；門 `gura-pinas-01m-door`；爐灶 `kaguya-gloire-01m-galley`；船尾燈 `gura-tridente-01m-lantern`。
- 產生程式：從牛津號 `erina-oxford-01m/design/` 抄來改（每支檔頭寫來源）。

## 步驟 3 造船資料與新圖紙 01／02（2026-11-01）
- 資料：`design/references/research_barbados_2026-11-01.md`（〔查〕〔推〕〔二手〕〔設計〕〔估〕）。
- `plan.json` 第一版由 scratchpad 的 make_plan.py 從牛津號的 plan 改出來；之後手改只用文字插入（⛔ json.dump 整份）。
  - 後面步驟才用的段落（deco、paint、stern、gear、rudder_anchor、rig、rigging）還是牛津號的數字，到那一步再改（`_todo`）。
- 跟牛津號不同的地方：
  - 線形肥：平底半寬 15（12）、舭 2.6（2.0）、收縮 0.34／0.70（0.42／0.64）、deadwood 24（30）。
  - 甲板多一層：下甲板 z 42 通長（`orlop` 這個 key，名字「下甲板」）＋ 上甲板 z 59（`gun`，名字「上甲板」）。艙口兩層都開。
  - 8 門砲全在上甲板船腰（x 170／198／226／254），不做砲門蓋板 ⇒ 刪步驟 12。
- 改了的工具：`draft_lines.py` 主尺寸對照換成 76／23.5／90 ft；`draft_layout.py` 的表照有砲門的那幾層列（牛津號寫死後甲板也有）、圖框放寬到 x 440、z 360。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 上甲板長（z 59，艏柱到艉柱） | 27.38 m（89.82 ft） | 〔設計〕90 ft |
| 龍骨 | 23.20 m（76.12 ft） | 〔推〕76 ft |
| 最大寬 | 7.10 m（71 格，23.29 ft） | 〔查〕23 ft 6 in（奇數格最接近的是 71） |
| 設計水線 | z 35（吃水 3.5 m） | 〔設計〕11 ft 6 in |
| 排水量（水線下實心 × 1.025） | 394 t | 223 噸 bm 的 1.77 倍（商船滿載） |
| 砲門下緣離水線 | 2.90–3.00 m | — |
| 桅頂離水線 | 主 30.1、前 27.0、後 19.6 m | — |
| 帆面積（攤平 10 面） | 553 m² | — |

- 驗：1 元件、空腔 0、鏡像差 0；兩支 draft 重跑兩次雜湊相同（d24b3c99）；反向對照 `--probe=half_beam=+3` ⇒ 寬 71 → 77、每站水線半寬 +3。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-11-01）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py apex-two-barbados-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 177,545 ＝ 清單）→ `船殼:end`。
  - 結果帳（`tools/check_hull.py`）：作品 177,545 ＝ 設計，缺 0、多 0、色差 0；線形對照 714 點差 0；**反向對照** `probe_x=200`（那一站 +3）⇒ 報 23 點、最大差 3。
- `draft_ports.py`（plan 的 `paint`、`stern` 改成本船：wale 三道 ——下甲板那層 dz −19、主 wale −5、channel ＋12；frieze ＋14；wing transom z 56–57）⇒ 刻 1,788（砲門＋船尾窗開口，帶刻之前的顏色守門）、換色 13,958、玻璃清單 260（步驟 6 做成 `-stern-glass`）。
  - 標記 `砲門塗裝:begin` → carvevox 1,788 → stampvox overwrite=1 13,958 → `砲門塗裝:end`。
  - 讀數（`tools/check_stage3.py`，標記名改 `砲門塗裝:end`）：結果帳 175,757 缺 0、多 0、色差 0；8 個砲門開口裡實心 0；**正向對照**（量 `船殼:end`）8 個全報；**反向對照** `--probe=skip_port=gun:3` ⇒ 只報那一門兩舷。
- 結構（引擎 stats）：1 元件、空腔 0、鏡像差 0。圖 `design/sheet03_ports_paint_v1.png`、`overlays/step4_hull_q.png`。
- 組裝件關聯 `船殼` 的 meta `kind=ship waterline_z=35` 留到步驟 14 一起標。

## 步驟 5 甲板、艙口、break、梯子（2026-11-01）
- `draft_decks.py` ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`。
- 甲板（第一層空氣 z）：
  - 下甲板 42（x 60–316，平的）、上甲板 59（船中；舷弧船尾 +9、船頭 +7）。
  - 後甲板 ＝ 上甲板 ＋18（x 到 150）、艉樓 ＝ 後甲板 ＋16（x 46–96）、艏樓 ＝ 上甲板 ＋17（x 276 起）。
  - 橫樑每 14 格（照砲門相位 170）。
- 艙口：主艙口 x 196–210、前艙口 236–248，上下兩層都開；桅孔照桅軸。break 三道（後甲板前緣 x 150、艉樓前緣 96、艏樓後緣 276），門開中線（艉樓前緣 dy 14）。
- 梯子 7 座，每層都有梯子到：
  - cargo：艙底 → 下甲板，12 階，x 252 起往船頭。
  - hold：下甲板 → 上甲板，在後甲板底下。
  - qd-P／S、poop、fc-P／S。
  - 貨艙梯子是從康塞普西翁號搬來的（`"lo": "hold"`：梯腳踩艙底；`well_a`／`well_b`：梯井只開第 7 階以後頭頂碰得到下甲板樑的那段 x 264–278）。⇒ Ship_Decks §9.3 ⑥「艙底下不下得去」。
- `tools/plan_set.py`（新）：先驗 plan 原樣讀寫逐位元組相同，再套改動 ⇒ 只動改到的那幾行。
- 讀數：
  - 結果帳（`tools/check_decks.py`）：10 件 59,035 格，缺 0、多 0、色差 0、重疊 0。
  - 梯子點（組裝件 parts）：28／28、差 0；空氣／腳下／頭頂 14 格的問題 0。
  - 組裝件：1 元件、空腔 0、鏡像差 0；砲門往艙裡被擋 0。
- 甲板 meta：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv` ⇒ `work sub=meta`（5 筆）。
  - 代號：lower、upper、quarter、forecastle、poop；名字：下甲板、上甲板、後甲板、艏樓、艉樓。
- 空艙房沒做（照牛津號）。

## 步驟 6 裝飾、船尾窗玻璃（2026-11-01）
- `draft_deco.py` ⇒ `masks/deco/<件>.vox.txt`、`deco_anchors.json`、`verify_deco.json`；落地 `tools/build_deco.py`。
  - 船首喙 `-beakhead`：平台面 z 73、伸出艏柱到 x 345、半寬 1.3 m 收尖；cutwater 從 z 28 的艏柱斜到平台尖、前緣金；兩舷兩條 head rail（金、藍）＋柱。2,504 格。
  - 船首像 `-figurehead`：鍍金獅子，不戴冠（`crown` false：冠是王室的船），488 格。
  - 船尾旗桿 `-ensign-staff`：x 40、4.5 m，241 格。
  - 船尾窗玻璃 `-stern-glass`：300 格，關聯 meta `material=glass`。
- 改了的程式：
  - `draft_ports.py`：玻璃上下兩排換列的地方只有斜角相碰 ⇒ 下面那一排往外補 1 格（Ship_Materials「窗的玻璃」）。260 ⇒ 300 格，8 扇每扇 6 連通 1 片；刻、換色的清單雜湊不變。
  - `draft_deco.py`：王冠可關；獅子尾巴畫成 6 連通（牛津號那版第 2 格起只有斜角相碰 ⇒ 浮空 6 格），`tail_up` 4（6 會戳進艏斜桅的路 2 格）。
- 讀數：落在船上的格不放（喙 375 格）、件與件重疊 0、鏡像差 0；組起來 1 元件、空腔 0；艏斜桅線上的裝飾格 0。
  - **反向對照** `--probe=shift=figurehead:12` ⇒ 2 個元件。
- 組裝件：238,325 格、1 元件、空腔 0、鏡像差 0。圖 `overlays/step6_bow.png`。

## 步驟 7 桅與帆桁（2026-11-01）
- `draft_masts.py` ⇒ `masks/masts/<桅>.vox.txt`、`masks/bowsprit_hole/`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`。
- 桅（子作品 `-mast-main／fore／mizzen`，關聯 主桅／前桅／後桅）：下桅＋圓桅樓（主 r 13、前 11、後 10）＋上桅（doubling）＋上桅帆桅（主、前）。
  - 桅頂離水線：主 30.1、前 27.0、後 19.6 m。
  - 前桅腳 z 10–11 邊上 12 格碰到船頭 V 形底的內板 ⇒ 不放（桅腳順著船底收）。
- 艏斜桅 `-bowsprit`：根部 (302, 68)、仰 35°、12.1 m；船殼開孔 138 格、艏樓甲板 9 格，孔由艏斜桅填滿（標記 `艏斜桅孔`）。
- 方帆桁 9 根：照牛津號引用風暴角號（summit）的帆桁元件等比縮放 —— main course 0.672、topsail 0.642、topgallant 0.520、fore 0.667／0.622／0.614、crossjack 0.561、mizzen topsail 0.746、spritsail 0.613。
- 後桅三角帆桁：**引用牛津號的元件** `erina-oxford-01m-yard-mizzen-lateen`（136 格、有 fore 固定點）× 0.9853 ⇒ 134 格，meta `yard=gaff rig=lateen`。
  - 改了 `draft_masts.py`：擺法讀 `rig_build.lateen_src`；`build_masts.py`：擺法用別船的元件就不建本船那一根。
- 讀數：組裝件 265,719 格、1 元件、空腔 0、鏡像差 0；link_overlap 0；models_drawn 10、models_broken 0。圖 `overlays/step7_masts.png`。

## 步驟 8 索具、帆、旗（2026-11-01）
- `draft_rigging.py` ⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落地 `tools/rigging_apply.py`（channels → 固定點 → 繩 → 橫繩組 → 帆 → 帆的繩 → 風 → meta）。
- 改了的程式：
  - 牛津號寫死的綁點與高度搬進 `plan.rigging.belay_at`：船頭綁點 x 316、船尾三角帆 sheet x 44、艏斜桅側支索 z 75、bobstay z 42。
  - 支索下端改照桅位算（主支索在前桅腳的艏樓上 4 格、後桅支索在主桅上甲板以上 2.2 m）。
  - 長旗可關（`flags.pennant` null）。
- channels 兩舷一件 1,184 格（鏡像差 0）；shrouds 主 6、前 5、後 3／舷；固定點 118。
- 繩：靜索 77、帆的繩 23（全帶 meta）；橫繩組 12（下桅 6 組 climb=1）。
- 帆 9＋旗 1：fore／main course、topsail、topgallant，mizzen topsail，spritsail（set 3），mizzen-lateen（gaff）；船尾紅 ensign。
  - ⛔ 不掛主桅頂長旗：pennant 是國王的船才掛。
- 帆裝三段：

  | 帆裝 | 張哪幾面 |
  |---|---|
  | 收帆（1） | fore-topsail、main-topsail、mizzen-topsail |
  | 戰鬥帆（2） | ＋ fore-topgallant、main-topgallant、mizzen-lateen |
  | 滿帆（3） | ＋ fore-course、main-course、spritsail |

- 讀數：ropecheck 繩 254 條、兩端 508 全綁好、link_overlap 0、link_clipped 0；view ropes_broken 0、sails_broken 0、models_broken 0；固定點落在實心 0。圖 `overlays/step8_rig.png`。

## 步驟 9 砲（2026-11-01）
- `gunsim.py`、`draft_guns.py`（照牛津號）⇒ `guns_placement.json`、`verify_guns.json`；落地 `tools/build_guns.py`（砲名表改成 4l）。
- 上甲板船腰 8 門 minion ⇒ `4l`：4 磅砲通用部件 `pinnacle-patache-01m-gun-4l` ×0.5、pivot [6.5, 28, 0]（照康塞普西翁號、信風號；Ship_Guns §2.2：砲只跟同一種砲共用模型）。P 舷 mirror=y，模型掛在 `甲板-gun`。
- 讀數：8 門全 ok；從舷外往裡退 2–3 格到零碰撞；砲口伸出舷外 5.25–6.25 格；腳下支撐 1.0；砲與砲不撞；兩舷對稱。
  - view：models_drawn 18（帆桁 10＋砲 8）、models_broken 0、link_overlap 0。圖 `overlays/step9_guns.png`。
- 砲具與砲索沒做（照牛津號）。

## 步驟 10 火藥庫、艙蓋、廚房、絞盤（2026-11-01）
- `draft_gear.py`（模型取樣點不落在實心格、不進別的模型外框、量腳下支撐）⇒ `masks/gear/magazine.vox.txt`、`gear_placement.json`、`verify_gear.json`；落地 `tools/build_gear.py`。
  - plan 的 `gear` 每個模型座標照本船甲板重算：牛津號的寫死在它的甲板高度，本船上甲板高 19 格。
- 火藥庫 `-magazine`：下甲板後段 x 105–129、前後兩道牆、前牆中線門 5 寬 1.5 m 高，2,053 格。
  - 關聯 `彈藥庫` meta：`kind=magazine pos=aft powder_lb=800 hoist=甲板-gun/梯子/hold`（火藥從下甲板 → 上甲板那座梯子吊上去）。
  - 固定點 blast (117,96,49)、door (130,96,43)。
  - 8 個火藥桶（憲法號共用桶 ×0.2）。
- 艙蓋：莫尼特號 `-hatch` 照開口縮放（kind=door），主艙口 z 62、前艙口 z 63（上甲板露天）。下甲板的艙口在艙裡、不加。
- 爐灶：光榮號 `-galley` ×0.3（kind=galley），艏樓底下上甲板左舷 x 301.5。
  - v1 x 303.5 最前一排撞到往船頭翹的甲板板（346 個取樣點）⇒ 往船尾 2 格。
  - 煙管出口照共用件的 smoke 點（在艏樓底下）⇒ 匯入檢查可能報 ⚠ 灶（Ship_Fittings §9.13），步驟 14 看。
- 絞盤：餘燼號 `-capstan` ×0.16，後甲板底下上甲板中線 x 118.5。
- 小艇、羅經櫃不放：1660 年代商船的小艇多半拖在船尾，船腰在主桅與兩個艙口之間放不下；whipstaff 操舵、沒有舵輪（照牛津號）。
- 讀數：
  - 12 個模型碰撞 0、問題 0。
  - **反向對照** `--probe=shift=絞盤:20`（推到梯井上）⇒ 報腳下沒有甲板。
  - 組裝件 268,956 格、1 元件、空腔 0、鏡像差 0；models_drawn 30、models_broken 0、link_overlap 0。

## 步驟 11 舵與錨（2026-11-01）
- `draft_rudder_anchor.py`、`tools/build_rudder_anchor.py`（照牛津號）。
- 舵子作品 `-rudder`：1,785 格，沿艉柱、z 0–74、前緣兩側削 1 格。
  - 掛成模型 `舵`：kind=rudder、hinge (58, 96.5, 0)、axis (−0.174, 0, 0.985)、max 35°、spin=rudder ±35°。
  - stock-top (42, 96, 74) 離船殼 3 格。
- 不放舵輪：1660 年代 whipstaff，舵柄在舵上。
- 錨：憲法號共用錨 ×0.55，兩舷，rz ±69.5、x 304、z 81、離船殼 1.2 m，撞 0、腳下踩在錨架托板 `-anchor-gear`（1,056 格）上。
- 船殼固定點 hawse-S／P (314, 117／75, 69)。
- 讀數：組裝件 270,012 格、1 元件、空腔 0、鏡像差 0；models_drawn 33、models_broken 0、link_overlap 0。圖 `overlays/step11_stern.png`。

## 步驟 14 給遊戲的 meta 與匯入 Blockside（2026-11-01）
- 組裝件關聯 `船殼` meta `kind=ship waterline_z=35`；ropecheck 繩 254 條、兩端 508 全綁好。
- Blockside 自己的 worktree：`D:/Unity/Blockside-wt/apex-two-barbados`，分支 `apex-two/barbados`，從本機 `refs/heads/dev` 39095b5 開，`_cache` 先從共用的複製過去。
  - `admin.py import --work apex-two-barbados-01m-assembly --id barbados --name 巴貝多商人號`；`admin.py ids --id barbados`：55 件，寫回 12 件作品的 meta。
- 匯入檢查一路修下來（✗ 3 ⇒ 0、⚠ 25 ⇒ 2）：
  - ✗ 後甲板、艏樓、艉樓走不到：hold 梯子在中線，梯井 x 134–148 緊貼後甲板前緣的門（x 150、中線）⇒ 船腰走不進後甲板底下。
    - 修法：挪到左舷 dy −12、梯井只開到最上一階（well_b 10 ⇒ x 140–148）、梯頭 x 138。
    - 這一條也連帶讓送藥手 8／8、爐灶、抽水機都走得到。
  - ⚠ 樓梯自檢 ④ 梯頂沒貼到甲板邊：後甲板兩座、艉樓那座各往船尾 2 格；艉樓那座挪到左舷（v1 梯頭正對後桅）。
  - ⚠ 火藥庫後面那塊下甲板走不到（x 60–102、約 17 m²）⇒ 火藥庫後牆也開一扇門（`magazine.door_aft`）。
  - ⚠ geo 沒填、軍官／陸戰隊站不下 ⇒ game.json 本船那一列：
    - geo：spar [59, 90]、marines [112, 76]、qx 60（沒有舵輪 ⇒ 軍官站位照外框起點往前 qx 格，預設 160 會落在船腰兩個艙口之間）、center 80、aim 64、aimZ [10, 330]、deckAim [61, 74]、rigAim [130, 330]。
    - crew：照澤漢號的商船配置；cfg pump 3。
  - 剩的 ⚠ 2：貨艙梯子「尋路沒收」—— Ship_Decks §9.3 ⑥：梯腳踩艙底的梯子本來就不進尋路，第一人稱爬得到。
- 甲板與梯子改了 ⇒ 每件 `delta_apply`、梯子點 overwrite。
  - 🩸 `masks/decks/` 有 `<層>.state.vox.txt`（扣掉艏斜桅孔）：迴圈兩份都套 ⇒ deck-fc 被補回 9 格孔 ⇒ 再照 state 刻掉。之後重套只用 `.state`。
  - 鏡像差 0 ⇒ 430／210：hold 和艉樓那兩座梯子只在左舷（刻意的）。
- 匯入檢查讀數：砲 8 門、0 門缺人；船員 45；帆 10、桅 3；彈藥庫 1（取用點 1）；甲板 5；梯子 6（＋貨艙梯子）；錨兩舷 ring＋hawse；水線 z 35。
  - 材質：橡木 269,675 格 188.8 t、玻璃 300 格；超載極限再 656 噸。
  - 樓梯自檢 7 座 ✗ 0；甲板連通 5 層＋艙底都接得到；廚房 1 座站得住 4 面。
- game.json：import／reimport／ids 會重排整份 ⇒ 照 HEAD 原樣、只插本船那一列（64 行）；JSON 內容跟重排版逐項相同；重建成品、`srccheck` 對得回來。
- 對打（`report.py --match barbados,oxford --seeds 1,2 --secs 120 --jobs 1`）：
  - 本船：開火 82、命中 60%；砲可開 80%、裝填 17%；帆從全張收到戰鬥帆（1 ⇒ 0.52）。
  - 航速：本船平均 4.8／6.6 節、最高 5.5／12.2；牛津號平均 6.4／7.5。
  - ⇒ 開得動、砲打得出去。
- 外框 x 38–402 ⇒ 全長 36.5 m（含艏斜桅；帆桁是模型不算）⇒ 超過小船泊位 36 m。
- Blockside 提交 1f91158（分支 `apex-two/barbados`，還沒合進 dev）。
- 合併（2026-11-01）：
  - Blockside dev ff 到 fba8de6，已推 dev。之前先把 dev f63471f 合進分支：表演船遠近分級；本船補烘 showlod：123×51×99 塊、留 9,326、5 KB。
  - 共用 `_cache/barbados.vxk` 指紋 = lock（c:d14e5274aa9f）。
  - Blocksail main ff 到 eb758b04（`FLEET.types.merchant`、fleet_check、TRADE_SIM 表；子模組 → fba8de6、battle.html 重套），**沒推**。

## 步驟 15 交船（2026-11-01）
- vxk：barbados.vxk 格數 269,975、checksum 2538202501、繩 254、帆 10、模型 33、零件 22（admin.py reimport 讀數）。
- 給遊戲那側的高度（geo 照這些填了）：
  - 水線 z 35。
  - 甲板地板：下甲板 43、上甲板（船腰）59–60、後甲板 78–87、艏樓 80–85、艉樓 98–103。
  - 砲門下緣 z 65–66、砲軸 67–68；船腰舷頂 72–75。
  - 桅頂：主 336、前 305、後 231；course 帆桁 主 182、前 164。
  - 外框 x 38–402（船尾旗桿到艏斜桅尖）。
- Ship_Game §10 檢查表逐條：
  - ropecheck ✓（綁定猜 0、不靠 0）。
  - 名稱與 sub ✓；mpv 與模型 scale ✓。
  - 現成元件 ✓：砲、方帆桁、三角帆桁、火藥桶、錨、艙蓋、爐灶、絞盤；新做的元件 0。
  - 爐灶 = 廚房（kind=galley、沒標 deco、4 面站得住）✓。
  - 舵模型＋stock-top＋spin ✓；沒有舵輪、舵柄畫在舵上（whipstaff）✓。
  - kind=ship waterline_z 35 ✓；梯子＋樓梯自檢 ✗ 0 ✓；橫繩組＋繩梯 ✓。
  - 火藥桶＋送藥手 8／8 ✓；甲板 meta ✓；三角帆桁 gaff＋lateen＋fore ✓；玻璃 material=glass、6 連通 ✓。
  - 艙蓋 kind=door ✓；砲門蓋板不適用（露天船腰）。
  - 繩帆模型斷 0 ✓；帆與帆的繩 meta ✓；帆裝三段表 ✓。
  - 1 元件／空腔 0／link_overlap 0 ✓（鏡像差：只在左舷的兩座梯子）。
  - 重跑逐位元組相同 ✓；shipcheck ✗ 0 ✓、⚠ 2 看過（貨艙梯子）。
- 沒做／沒驗：
  - 空艙房沒標。
  - 遊戲裡沒截圖看玻璃透明、沒在遊戲裡按 W／S 一段一段看帆（對打報表看得到帆從 1 收到 0.52）。
  - 等 Tim 看船。

## 步驟 16 空艙房（2026-11-02；Tim「Build cabins」）
- Ship_Decks §9.2：`draft_cabins.py`（出處 abigail-fluyt-01m draft_fit.py 的艙房那一段）⇒ `masks/cabins/cabins.vox.txt`、`cabins_placement.json`、`verify_cabins.json`；落地 `tools/build_cabins.py`。
  - 子作品 `-cabins`（世界座標 at 0,0,0）：艙壁、門框、平地板 4,922 格；固定點 `<房名>.min／.max／.door` 12 個。
  - 關聯掛在上甲板子作品裡：`甲板-gun/艙房`，meta `kind=rooms`（admin.py ids 補了 id `rooms-1`）。
- 四間（全在上甲板）：

  | 房 | 框（組裝件座標） | 大小 | 門 |
  |---|---|---|---|
  | 大艙 | x 58–84、y 74–118、z 67–80 | 2.7 × 4.5 × 1.4 m | x 85 橫艙壁、右舷 y 100–105（後桅在門外） |
  | 左舷艙 | x 98–122、y 69–85、z 63–76 | 2.5 × 1.7 × 1.4 m | y 86 縱艙壁 x 100–105（絞盤那一側） |
  | 右舷艙 | x 126–148、y 102–125、z 61–74 | 2.3 × 2.4 × 1.4 m | y 101 縱艙壁 x 132–137 |
  | 水手長艙 | x 288–308、y 102–117、z 65–77 | 2.1 × 1.6 × 1.3 m | y 101 縱艙壁 x 297–302 |

- 坑：
  - 甲板有舷弧（後甲板底下 x 每 1 m 降 1 格）⇒ 框要平的地板 ⇒ 每間鋪平到最高那一柱；門口台階 ≤ 3 格（42_hands.js NAV_DZ）。大艙門外甲板 64、艙裡 67 ⇒ 門外補兩階（65、66）。
  - 地板比門外高 ⇒ rooms.py 量不到門洞 ⇒ 每間都標 `.door`。
  - 艏樓、艉樓的樑底下淨高不到 1.4 m ⇒ 框的頂照最低的樑底；船殼往內收那幾排頭上不到 1.2 m ⇒ 不框（不然整間的頂被壓低：左舷艙 v1 只有 1.0 m 高）。
  - 艉樓底下太矮（後甲板上 1.6 m，鋪平就不到 1.4 m）⇒ 不隔；艏樓左舷是廚房（廚師的面要留）⇒ 不隔；hold 梯子上來的地方（左舷 x 124–148）⇒ 不隔。
  - 水手長艙 v1 x 278–296 ⇒ 遊戲能擺的只有 1.5 × 2.0 m、病床與木工台都放不下 ⇒ v2 往前挪到 x 288–308；門 v2 開在後面那道艙壁 ⇒ 格子只有 3 排、門口那排兩旁留走道 ⇒ v3 改開在內側縱艙壁。
- 讀數：
  - 組裝件 274,897 格（＋4,922）、link_overlap 0、link_clipped 0；check_decks 問題 0、梯子點 28／28。
  - Blockside `rooms.py check`：4 間全 ✓（框裡實心 0、地板 100%、重疊 0）。
  - 遊戲 `__game.roomPlans('barbados', type)`：醫療艙 大艙 3 床＋手術台＋藥箱、其他三間各 1 床＋藥箱；木工間 四間都擺得下木工台。
  - 匯入檢查 ✗ 0、⚠ 3：貨艙梯子 2 條（同交船）＋「kind=mast 規格表沒有」（summit TASK-1169 在本船四根桅標的 meta，Sculpture 還沒提交、Blockside 那一半在她的分支）。

# 好旅號（方帆卡拉維爾 caravela redonda，約 150 tonéis 葡萄牙商船）—— 建造筆記（0.1 m／格）

委託：Tim 2026-11-01（TASK-1146 → TASK-1151）：「1151 go」，查完年代選「2」⇒ 造方帆卡拉維爾，當往巴西、往大西洋群島的商船（1660 年代退場中）。
驗收（TASK-1151）：造船資料 → 雕好匯入 Blockside → 接進 Blocksail FLEET.types → Tim 看過；加 Ship_Steps 步驟 1–11、14、15（刪 12 砲門蓋板：砲在露天甲板從舷牆砲門打；刪 13：木造帆船、沒有槳）。

## 範圍
- 外部完整；內部只做遊戲用得到的大致構造（甲板、艙口、梯子、火藥庫、貨艙）—— 照信風號（erina-tradewind-01m）。
- 設計程式從信風號 `design/` 整套抄來改（每支檔頭寫了出處）；`design/plan_tradewind_ref.json` 是信風號的參數，只拿來對照，⛔ 不被程式讀；`design/ref/` 是牛津號有三角帆桁的那幾支（步驟 7、8 參考）。

## 座標與比例（步驟 2；2026-11-01）
- 0.1 m／格；框 448 × 192 × 384（調尺寸免費、不縮放內容）。x 船長、船頭 +x；y 中線格 96（鏡像 y ↔ 192 − y；P 舷 y < 96）；z 0 ＝ 龍骨底面。
- 作品：組裝件 `summit-boaviagem-01m-assembly`「好旅號」（主作品，關聯 `船殼` at 0,0,0）；船殼 `summit-boaviagem-01m`「好旅號 船殼」（任務作品、tags sub、委託 ref TASK-1151、領薪 10）。兩件都記 meters_per_voxel 0.1。
  - 🩸 `work sub=create` 帶的 `tags=sub`、`meters_per_voxel=0.1` 兩件都沒存上（work.json 是 0 與 []），之後用 `sub=update` 補上才有 ⇒ 建完一律回讀 work.json。
- 現有元件（`work sub=components` 2026-11-01）：4 磅砲 `pinnacle-patache-01m-gun-4l`、迴旋砲 `apex-one-reale-01m-gun-pierrier`＋座、火藥桶、錨、絞盤、羅經櫃、小艇、門、艙蓋、爐灶（同信風號）；方帆桁縮放風暴角號元件；三角帆桁照牛津號的做法自己產生（三根長度差太多：24／17／12 m）。

## 階段一 造船資料與新圖紙 01／02（步驟 3；2026-11-01）
- 資料：`references/research_caravela_2026-11-01.md`。主尺寸只有二手（Livro Náutico 龍骨約 18 m、長寬比 3:1–4:1、海軍博物館模型約 30 × 9 × 4.5 m）⇒ 其餘〔設計〕，每個數字在 plan.json 的 src。
- `lines.py` 沒改（參數換成卡拉維爾：底比較尖、tumblehome 強、艉柱倒 9°、方艉、彎的艏柱）；`layout.py` 改寫成四根桅（前桅方帆兩面；主、後、最後桅各一根三角帆桁：吊點、斜角、前段比例）；`draft_layout.py` 的帆杆讀數換成三角帆桁讀數（前端離舷頂、尾端伸出船尾、經過別的桅頂的高度）。

| 項目 | 讀數 | 史料／設計 |
|---|---|---|
| 甲板長（z 44） | 22.97 m | 〔設計〕 |
| 龍骨 | 18.00 m | 〔二手〕約 18 m |
| 最大寬 | 7.30 m（長寬比 3.15） | 〔二手〕3:1–4:1 |
| 設計水線 | z 30（吃水 3.0 m） | 〔推〕 |
| 排水量（水線下實心 × 1.025） | 225 t | — |
| 主甲板 | 船中 z 44；後甲板 ＋20、艉樓再 ＋18、艏樓 ＋17 | 〔設計〕 |
| 桅頂離甲板 | 主 16.0、前 15.7、後 12.2、最後 11.4 m | 〔設計〕 |
| 三角帆桁 | 主 24 m／55°、後 17 m／52°、最後 12 m／50°（尾端伸出船尾 2.3 m） | 〔設計〕 |
| 帆面積（攤平 5 面） | 322 m² | — |
| 炮門 | 每舷 2（x 228、258）、下緣離水線 1.9–2.0 m | 〔設計〕 |

- 讀數：線形 1 元件、空腔 0、鏡像差 0；兩支 draft 重跑逐位元組相同；**反向對照** `--probe=half_beam=+3` ⇒ 全寬 73 → 79；`--probe=port=gun:1:+3` ⇒ 砲門淨距 25 → 28。
- 改過的：v1 艏斜桅腳 x 304 壓在前桅上 ⇒ 312；v1 前桅比主桅高（18.7 對 14.2 m）⇒ 前桅降、主桅加高；主三角帆桁斜 52° ⇒ 55°、前段 0.42 ⇒ 0.48（前端離舷頂 5.4 ⇒ 3.8 m）。

## 階段二 船殼落格（步驟 4 前半；2026-11-01）
- 標記 `船殼` begin（upto=start）→ `tools/stamp_lists.py summit-boaviagem-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 125,198 ＝ 清單）→ `船殼` end。
- 結果帳（`tools/check_hull.py`，作品從 export 讀）：125,198 ＝ 設計，缺 0、多 0、色差 0；線形對照 513 點差 0；**反向對照** `probe_x=180` ⇒ 報 19 點、最大差 3。
- 結構（引擎 stats）：1 元件、空腔 0、鏡像差 0。組裝件關聯 `船殼` meta `kind=ship, waterline_z=30`（`part=link`，回讀 links 有）。

## 階段三 炮門、塗裝、船尾窗（步驟 4 後半；2026-11-01）
- `draft_ports.py` 改兩處：船尾窗的參考欄照 `plan.stern.x_ref`（信風號寫死 x 46）；舷牆內側紅色的「最上面那一層甲板」多算艉樓。
- ⇒ `masks/ports/carve.vox.txt`（840，帶顏色守門）、`paint.vox.txt`（12,200）、`glass.vox.txt`（150，步驟 6 用）、`sheet03_ports_paint_v1.png`；落格：標記 `炮門塗裝` begin → carvevox 840 → stampvox overwrite=1 12,200 → end。
- 炮門每舷 2（x 228、258）；船尾窗 6 扇：後甲板底下艙房 4 扇、艉樓底下船長艙 2 扇。
- 塗裝〔設計〕（查不到 17 世紀葡萄牙商船的塗裝）：木色 177、兩條黑 wale、舷頂下兩列紅 192、舷頂黑、舷牆內側紅、水線下灰白 182、wing transom 黑（z 40–41）。
- 讀數（`tools/check_stage3.py`）：結果帳 124,358 缺 0、多 0、色差 0；炮門開口裡實心 0；正向對照（量 `船殼:end`）4 個全報；**反向對照** `draft_ports.py --probe=skip_port=gun:2` ⇒ 只報那一門兩舷（各 90 格）、清單不動；stats 1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq}.png`。

## 階段四 甲板、艙口、break、梯子（步驟 5；2026-11-01）
- `draft_decks.py` 沒改程式，只換 plan.decks_build ⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `tools/build_decks.py`（子作品 `-deck-<層>`、`-ladders-<層>`，關聯 `甲板-<層>`、`甲板-<層>/梯子` meta kind=ladders）。
- 甲板（第一層空氣）：底艙平台 22（x 100–170，火藥庫）、主甲板 44（船中；船尾 +9、船頭 +7；x 80–324，**後甲板底下的艙房就是主甲板這一層** —— 後甲板高出 2.0 m，不像信風號要下沉）、後甲板 ＝ 主甲板 ＋20（x 80–175）、艉樓 ＝ 後甲板 ＋18（x 80–130）、艏樓 ＝ 主甲板 ＋17（x 280–324）。橫樑每 12 格。
- 艙口：主艙口 x 212–236（半寬 8；貨艙梯子在裡面）、前艙口 242–252；桅孔照四根桅軸（主 r 3.5、最後桅 2.5、其他 3）；break 三道（後甲板前緣 x 175、艉樓前緣 x 130、艏樓後緣 x 280），門都開在中線。
- 梯子 8 座：hold（貨艙，梯腳踩艙底）、orlop（底艙平台 ⇄ 主甲板，梯井在後甲板底下的艙房裡，避開最後桅與後桅）、qd-P／S、poop-P／S（|dy| 10）、fc-P／S（|dy| 12）。每層都有梯子通到。
- 讀數：draft 時件與件重疊 0、梯子點問題 0、砲門往艙裡被擋 0、封閉空腔 0；結果帳 9 件 39,069 格缺 0、多 0、色差 0（`tools/check_decks.py`）；梯子點（組裝件 parts）32／32、差 0；組裝件 1 元件、空腔 0、鏡像差 0。
- `build_decks.py` 用 `work=` 建子作品 ⇒ tags sub、meters_per_voxel 0.1 都有存上（回讀 work.json）。
- 甲板 meta：每層 `export format=vxk links=none`（🩸 第一次沒帶 links=none ⇒ 艏樓、後甲板的 floor 把梯子踏板也量進去）⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（代號 orlop／main／forecastle／quarter／poop、名字照 plan 的 names；level 照 decks.py 的高度順序 0–4）⇒ `work sub=meta file=`（5 筆）。
- 預覽 preset `藏船殼`。過程圖 `overlays/stage5_decks_nohull.png`。空艙房沒標。

## 步驟 6 裝飾（2026-11-01）
- `draft_deco.py` 改兩處：head rail 改成 plan 有給才做（卡拉維爾沒有）；艏斜桅那條線量到艏斜桅尖（沒有三角帆桿）。`tools/build_deco.py` 只改標題。
- 船首 `-head`（小 cutwater：水線下 z 26 從艏柱長出來、頂 z 66 往前 0.6 m，前緣黑；柱頭金色圓頭 r 2、黑螺旋 1 圈；固定點 bobstay-1 (319, 96, 40)）、錨架 `-catheads`（x 312、艏樓舷牆頂下、往前斜 25°、伸出舷外 1.0 m；固定點 cat-S／P (316, ±30, 71)）、船尾窗玻璃 `-stern-glass`（150 格、6 扇；關聯 meta material=glass）。
- 〔設計〕卡拉維爾的艏柱彎、往前倒，沒有 beakhead 平台與船首像（查不到同型船的裝飾資料）；船名板沒做。
- 讀數：落在船上不放的 312／24 格；件與件重疊 0；組起來 1 元件、空腔 0、鏡像差 0；艏斜桅那條線裡的裝飾格 0；**反向對照** `--probe=shift=scroll:6` ⇒ 5 格、元件 2。
- 過程圖 `overlays/stage6_bow.png`。

## 步驟 7 桅與帆桁（2026-11-01）
- `draft_masts.py` 改寫（信風號的兩桅＋三角帆桿 ⇒ 四根桅；三角帆桁照牛津號的做法）⇒ `masks/masts/<桅>.vox.txt`、`masks/bowsprit_hole/`、`masks/yards/yard-<桅>-lateen.vox.txt`、`yard_lateen_anchors.json`、`yards_placement.json`、`verify_masts.json`；落格 `tools/build_masts.py`（四根桅、艏斜桅、三角帆桁元件、帆桁模型、關聯 前桅／主桅／後桅／最後桅／艏斜桅）。
- 桅：前桅（下桅 z 10–160＋上桅 146–206、桅樓 r 9、cap）、主桅（單根 z 4–204、桅頂黑 cap，**不放桅樓**：三角帆桁吊點就在桅頂下、桅樓會擋帆桁）、後桅（z 8–168）、最後桅（z 14–164）。
- 艏斜桅（`-bowsprit`）：根部 (312, 70)、仰 22°、8.8 m、尖一個黑 cap；開孔：船殼 30 格（carvevox 帶顏色守門、標記 `艏斜桅孔`，孔由艏斜桅填滿）。
- 帆桁 5 根（外部模型，掛在各自的桅子作品裡）：前桅方帆桁 2 根縮放風暴角號元件（fore course ×0.5314、fore topsail ×0.6306）；**三角帆桁 3 根是自己產生的元件**（`-yard-main-lateen` 240 × 9 × 9、`-yard-mizzen-lateen` 170 × 9 × 9、`-yard-bonav-lateen` 120 × 7 × 7；沿 x、前端 +x、中段粗兩頭細；固定點 pivot（吊點）、sling、fore、peak、earing-F／A、top-NN 每 8 格）；模型 pivot ＝ 吊點、at ＝ 桅在吊點高度的左舷外側、rotate y ＝ 斜角（55°／52°／50°，前端往下）；meta yard=gaff、rig=lateen、sail=main／mizzen／bonav-lateen（Ship_Masts §5）。
  - 🩸 v1 三角帆桁的框照格子的最大 y 算（7）⇒ 吊點 sling (125, 4, 8) 在框外被擋（零寫入）⇒ 框改照軸心 h 算 2h＋1（9），已建的那件 `sub=update size=240,9,9` 再補固定點。
- 讀數：組裝件 1 元件、空腔 0、鏡像差 0；models_broken 0；三角帆桁外框跟圖紙 02 對得上（主 x 126.5–265、z 98–296；左舷 y 86–92）。過程圖 `overlays/stage7_masts_side.png`。
- 🩸 最後桅那根帆桁的 meta 先是 `mast=bonav`：遊戲的 mast 值只認 fore／main／mizzen／bowsprit，收穫號（calli-cosecha-01m）的第四根桅標 `bonaventure` ⇒ 照它改（draft_masts 的 MAST_META、`work sub=meta part=model` 補一筆）。

## 步驟 8 索具、帆、旗（2026-11-01）
- `draft_rigging.py` 改寫（信風號的 brig 索具 ⇒ 卡拉維爾；三角帆照牛津號的掛法）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落地 `tools/rigging_apply.py`（channels 888 格 → 固定點 71 → 繩 38 → 橫繩組 6 → 帆 6 → 帆的繩 15 → 風 → meta 21）。
- channels：四根桅各一段（舷頂那一列、1 格厚）；shrouds 每舷前 3、主 4、後 2、最後 2；前上桅 backstay 1、上桅 shrouds 2、futtock 2（〔設計〕查不到卡拉維爾的索具表）。三角帆桅的 hounds 在吊點下 4 格。
- 支索：fore-stay（→ 艏斜桅 55%）、fore-topmast-stay（→ 艏斜桅尖）、main-stay（→ 前桅腳）；bobstay＋艏斜桅 shrouds 2。三角帆桅不拉前支索（帆桁要能換舷）。
- 橫繩組 6：前桅 lower 2 組 climb=1（foot 舷牆內側甲板、head 桅樓邊）、前上桅 2 組、主桅 lower 2 組（沒有桅樓 ⇒ 不標 climb）。
- 帆 5＋旗：fore-course（sheet 往後 4 m、tack 往前 2 m 綁舷頂）、fore-topsail（clew 綁前帆桁 earing 旁）、**main／mizzen／bonav-lateen**（tack ＝ 帆桁 fore、head ＝ 帆桁 peak、clew 在尾端往前 0.6 m 的舷頂上 1.0 m；帆緣綁帆桁；sheet 兩舷綁舷頂、tack 拉到帆桁前端正下方的甲板；meta sail=gaff，最後桅 mast=bonaventure）；國旗 ensign（〔設計〕葡萄牙：白底、王徽紅框＋五個藍盾，冠省略；掛最後桅三角帆桁尾端；kind=flag flag=ensign、有貼圖）。
  - 最後桅帆桁尾端伸出船尾 ⇒ clew 最多到船尾板前 3 格（sheet 綁船尾欄杆）。

| 帆裝 | 張的帆 |
|---|---|
| 收帆（1） | fore-topsail |
| 戰鬥帆（2） | ＋ main-lateen、mizzen-lateen、bonav-lateen |
| 滿帆（3） | ＋ fore-course |

- 讀數：ropecheck 繩 129 條、兩端 258 全 ok、link_overlap 0；view ropes_broken 0、sails_broken 0、models_broken 0；帆的繩沒 meta 0、meta 的帆名對不上 0、重名 0；固定點落在實心 0；組裝件 1 元件、空腔 0、鏡像差 0；draft 重跑 rigging_plan.json 逐位元組相同。**反向對照** `--probe=nometa=main-lateen-tack` ⇒ 報那一條。
- 過程圖 `overlays/stage8_rigging.png`。

## 步驟 9 砲（2026-11-01）
- `draft_guns.py`、`tools/build_guns.py` 沒改程式，只換 plan.guns_build（四層甲板子作品、前綴 M／Q／P／F、迴旋砲位置）⇒ `guns_placement.json`、`verify_guns.json`。
- 主甲板 4 門 4 磅砲（〔設計〕商船每舷 2 門；查不到卡拉維爾的具體配砲）⇒ `pinnacle-patache-01m-gun-4l` ×0.5；P 舷 mirror=y。
- 迴旋砲 8 門（〔設計〕berço ⇒ 遊戲的 pierrier）⇒ `apex-one-reale-01m-gun-pierrier` ×0.5：艉樓舷頂每舷 2（x 88、120）、後甲板 1（x 165）、艏樓 1（x 310）—— 都避開 channels；每門一個「座」雙生（kind=gunmount、mount_of）。
- 讀數：12 門全 ok —— 4 磅砲退 1–2 格、砲口伸出 5.25–6.25 格、腳下支撐 1.0；迴旋砲砲口伸出 7.5 格；砲跟砲不撞 0、兩舷不對稱 0；模型 ok 20／bad 0（砲 12＋座 8）。**反向對照** `--probe=push=砲M-S01:4` ⇒ 報那一門 1,215 個碰撞樣本。
- 砲具與砲索沒做（Ship_Steps「要的話」；4 門小砲）。

## 步驟 10 火藥庫與甲板物件（2026-11-01）
- `draft_gear.py` 改一處：火藥庫的門可以開在後牆（`magazine.door_at = aft`）；`tools/build_gear.py` 只改標題。⇒ `masks/gear/magazine.vox.txt`、`gear_placement.json`、`verify_gear.json`。
- 火藥庫（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine pos=aft powder_lb=400 hoist=甲板-gun/梯子/orlop`）：底艙平台**前段** x 140–170、兩道牆、門開在後牆（0.5 × 1.4 m），朝底艙梯子的梯腳 x 121；固定點 blast (155, 96, 29)、door (140, 96, 23)。4 個火藥桶（憲法號共用桶 ×0.2，各 100 lb）。
  - 🩸 v1 放平台後段 x 100–117（照信風號的位置）⇒ 四個桶各撞 3.6–4.6 萬個取樣點：那一段船底 V 形太窄、最後桅又穿過中線 ⇒ 挪到前段。
- 主甲板：艙蓋-主（莫尼特號艙蓋 ×1.58／1.46，蓋在主艙口圍欄頂）、艙蓋-梯井（×1）、小艇（餘燼號 cutter ×0.2，擱在前艙口上）、爐灶（光榮號 ×0.22，kind=galley；主桅後面的船腰 x 193）。後甲板：絞盤（餘燼號 ×0.09，x 163）。艉樓底下（後甲板那一層）：羅經櫃（夜隼號 ×0.2，x 119，舵柄旁邊）。
- 讀數：10 個模型碰撞 0、不進砲的外框 0；火藥桶、爐灶支撐 1.0、絞盤 0.6、羅經櫃 0.78（艙蓋與小艇擱在圍欄上，不要求）；問題 0；組裝件 1 元件、空腔 0、鏡像差 0。

## 步驟 11 舵、舵柄、錨（2026-11-01）
- `draft_rudder_anchor.py`、`tools/build_rudder_anchor.py` 沒改程式，只換 plan.rudder_anchor_build（🩸 hawse 這一格住在 rudder_anchor_build 底下：第一次寫在頂層 ⇒ 錨鏈孔照信風號的 (288, ±30, 54)）。
- 舵子作品 `-rudder`（1,344 格，沿艉柱倒 9°、z 0–77、前緣兩側削 1 格；水線下白、上黑、每 10 格鐵箍）掛成模型 `舵`：kind=rudder、hinge (96, 96.5, 0)、axis (−0.156, 0, 0.988)、max 35°、spin=rudder ±35°；stock-top (81, 96, 77)。
- **舵柄** `-tiller`（112 格，z 76–77）掛在後甲板子作品（艉樓底下那一層）成模型 `舵柄`：kind=tiller、spin=rudder ±35°、固定點 spin-a／b (82, 96, 76／77)；往前伸到 x 100（最後桅在 x 110）。船尾 helm port 刻 18 格（由舵柄填滿）。不放舵輪（17 世紀用舵柄）。
- 錨：共用錨元件 ×0.45、meta anchor=bower；兩舷各一（x 303.8、z 64.5，錨臂順著船殼切線 rz ±69.5°）＋錨床 `-anchor-gear`（744 格，錨冠落在 billboard 上，foot_gap 0）；船殼固定點 hawse-S／P (316, ±17, 57)。
- 讀數：舵 on_solid 0、舵柄 on_solid 0、錨碰撞 0、錨床 on_solid 0、全部鏡像差 0；組裝件 1 元件、空腔 0、鏡像差 0；ropecheck 129 條兩端全 ok；繩／帆／模型斷 0。**反向對照** `--probe=shift=錨-S:-6` ⇒ 錨-S 碰撞 1,438、錨-P 0。
- 過程圖 `overlays/stage11_stern.png`。

## 步驟 14 匯進 Blockside（2026-11-01）
- Blockside 自己的 worktree（`D:/Unity/Blockside-wt/summit-boaviagem`、分支 `summit/boaviagem`，從 heads/dev 349939a 開；`_cache` 先從共用的複製過去）：`admin.py import --work summit-boaviagem-01m-assembly --id boaviagem --name 好旅號` → `ids` → 修 ⚠ → `reimport`。
- 第一次匯入檢查 ✗ 0、⚠ 10 ⇒ 逐條：
  - geo、船員站不下 ×5 ⇒ 遊戲那側填 `ships[boaviagem]`（見下）。
  - 🩸 **小艇擋路**：×0.2（約 3.6 m）擱在前艙口上、從 x 235 擋到 270 ⇒ 艏樓底下那一塊主甲板（x 274–316、16.9 m²）走不到、貨艙梯頂出口堵住 ⇒ ×0.13（約 2.3 m）、挪到 x 257.5（draft_gear 重跑 → build_gear → reimport）。
- **最後一次匯入檢查 ✗ 0、⚠ 4**：貨艙梯子尋路沒收 ×2（Ship_Decks §9.3 ⑥ 的預期）；艉樓右舷梯頂前面是遊戲擺的取用點火藥桶（23_powder.js，報告寫明雕刻作品不用改）；桅頂水手 1／4（遊戲照「每根桅 × crew.top」要人，三根三角帆桅沒有桅樓；40_crew.js 找不到站位就不加人 ⇒ 不會有浮空的水手）。火藥 12／12 門走得到（最遠 12.2 m）、廚房站得住 4 面、操舵「舵令 ⇒ 舵柄 ⇒ 舵 100%」、樓梯自檢 8 座 ✗ 0、甲板 5 層都接得到、超載再多載 429 噸／吃水再深 2.90 m；材質 橡木 178,192 格 124.7 t、玻璃 150 格。
- `ships[boaviagem]`：role merchant；gangway (215.5, 143.5／49.5, 61.5)；geo spar [45,74]、marines [90,172]、center 60、aim 40、aimZ [5,300]、deckAim [45,74]、rigAim [110,295]；cfg pump 2；crew 照信風號（officers 1、helm 1、top 1、marines 0、monkeys 1、handsK 0.25、navigator 0）；idNext 補 gun 13、gunmount 13（砲的 id 是 draft_guns 先發的）。
  - 🩸 import／reimport 會把整份 game.json 重 dump ⇒ 拿 HEAD 只插好旅號那一筆（+79 行），斷言別的 37 艘逐項相同（scratchpad insert_game.py）；reimport 之後再插一次 ⇒ `admin.py build` 重建、srccheck ✓、verify 1,536 份網格一致。
- Blockside `0254ca0`（worktree 提交）。提交時共用 dev 已經走到 d79eee8（ridge-two 的百夫長號 TASK-1153＋townbld）⇒ 把 dev 合進分支（`6018649`）：衝突都是兩邊在同一個位置各加一艘船 ⇒ 兩艘都留（game.json 那一段是從物件中間切開的，補 `}` `},` `{`；斷言 ＝ dev 的 38 艘＋好旅號）；index.html 取 dev 的再 build；worktree `_cache` 補 centurion.vxk；dev 帶進來的表演船遠近分級 ⇒ `admin.py showlod --id boaviagem`（--check 全 ✓）。
- 共用 dev 快轉 349939a…d79eee8 → 6018649（施工場 `coding-20261101T072323Z-summit`）；共用樹上別人沒提交的 ship_cards.json（幾艘船的船員數）先存成 patch、ff 之後原樣套回；共用 `_cache` 補 boaviagem.vxk、verify 1,595 份網格一致。**推上 dev**（d79eee8..6018649，推之前列過 dev/dev..heads/dev 只有這兩筆）。worktree 已拆。
- 新做的元件不標 render：舵、舵柄、三角帆桁是子作品格子。

## 步驟 15 交船（2026-11-01）
- 交船檢查表（Ship_Game §10）逐條：ropecheck 258 端全 ok（沒有 bind／snap）✓、名稱與 sub ✓、mpv 與每個模型的 scale 明寫 ✓、components 先查過（現成：4 磅砲、pierrier＋座、方帆桁、火藥桶、錨、艙蓋、小艇、爐灶、絞盤、羅經櫃；新做：三角帆桁 ×3、舵、舵柄、火藥庫牆、船首、錨架、錨床、船尾窗玻璃）✓、爐灶 kind=galley ✓、舵模型＋stock-top＋spin ✓、舵柄 kind=tiller、操舵鏈 100% ✓、kind=ship waterline_z 30 ✓、梯子 kind=ladders 四點 ✓、樓梯自檢 ✗ 0 ✓、橫繩組＋前桅繩梯 ✓、火藥桶 ✓、甲板 meta ✓、三角帆桁 gaff＋lateen＋fore ✓、玻璃 material=glass ✓、砲零碰撞＋砲口出船殼 ✓、pierrier 座雙生 ✓、露天艙口有門（主艙口、梯井；前艙口被小艇蓋住）✓、砲門蓋板不適用（露天甲板的舷牆砲門）、繩帆模型斷 0 ✓、帆與帆的繩 meta ✓、帆裝三段表 ✓（遊戲裡 W／S 每段看一次 ⇒ 還沒看）、1 元件／空腔 0／link_overlap 0 ✓、匯入檢查 ✗ 0 ⚠ 都看過 ✓。
- 產生程式重跑逐位元組相同：只對 draft_lines、draft_layout、draft_rigging 量過；其他幾支沒有逐一量。
- 空艙房沒標；迴旋砲 arc 照飛魚號、擺角沒逐角量。
- checksum：遊戲那側 `_cache/boaviagem.vxk` 就是 reimport 當下匯出的那份，`admin.py verify` 成品跟它一致。

## 給遊戲那側填 geo 用的高度（已照這些填進 Blockside game.json ships[boaviagem].geo）
- 水線 z 30；主甲板（第一層空氣）船中 z 45、船尾 54、船頭 52；後甲板 z 65–74；艉樓 z 86–92；艏樓 z 65–68；底艙平台 z 23。
- 4 磅砲軸 z 52–53、迴旋砲軸 z 79–105；前桅樓 z 144–147；桅頂：前 206、主 204、後 168、最後 164；三角帆桁尾端最高 z 294（主）。
- 船殼 x 約 80（船尾板）～ 322（艏柱）、艏斜桅尖 x 394；最後桅三角帆桁尾端伸到 x 57（模型，不算進 vxk 外框）。

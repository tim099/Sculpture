# 突尼斯湖淺水轉運划艇 Sandal — 建造筆記（0.1 m／格）

TASK-1301（母單 TASK-1211，為 Tim 與 TASK-1288 北非城鎮建造）。
定位：1666 年期突尼斯（拉古萊特 ⇄ 突尼斯城 *Bâb al-Bahr*）淺水湖內／港灣轉運平底划艇 *Sandal*，並兼作加貝斯（*Gabès*）淺水沿岸運補候選船。

## 一、座標、比例與作品拆法（步驟 2）

- **比例尺**：`meters_per_voxel = 0.1`（1 格 = 0.1 m；船殼 `kiara-tunis-sandal-01m` 與組裝件 `kiara-tunis-sandal-01m-assembly` 及全部子作品一律顯式設定 `0.1`）。
- **軸向**：X 船長（`+X` 朝船首）；Y 船寬（中線 `y = 50`，`P` 左舷 `< 50`、`S` 右舷 `> 50`）；Z 高度（`z = 0` ＝ 平底船底外表面）。
- **作品清單與框**：
  - `kiara-tunis-sandal-01m`（任務作品／船殼，`tags=sub`，框 `136 × 101 × 30`）：平底折角寬腹船殼、舯段開放貨艙壁、艏尖柱與艉平鏡/艉柱、護舷與繫纜柱。
  - `kiara-tunis-sandal-01m-assembly`（主作品，`parent_work=kiara-tunis-sandal-01m`，無 `sub`，框 `136 × 101 × 110`）：只放關聯（船殼 `at=0,0,0`、甲板、桅）、外部模型（帆桁、舵、錨、槳、貨箱酒桶、燈具）、繩、帆與旗。
  - 預定子作品（全部 `tags=sub, meters_per_voxel=0.1, parent_work=kiara-tunis-sandal-01m`）：
    - `kiara-tunis-sandal-01m-deck-main`（艙底鋪板、貨艙平台、前後踏台與坐板，`kind=deck`）
    - `kiara-tunis-sandal-01m-mast`（可卸單主桅，`kind=mast`）
    - `kiara-tunis-sandal-01m-yard`（拉丁帆桁外部模型來源，`kind=yard rig=lateen`）
    - `kiara-tunis-sandal-01m-rudder`（艉柱舵葉與舵柄外部模型來源，`kind=rudder`）

## 二、既有 `sub=components` 盤點與複用決策（步驟 1–2）

- **既有小艇船殼（經 `stats` ＋ `view` 目視確認不沿用）**：
  - `basecamp-piragua-01m`（11.0 × 1.7 m，0.1 m/格）：加勒比雪松獨木舟，寬僅 1.7 m，無平底寬腹貨艙空間。
  - `basecamp-ember-01m-boat`（9.0 × 2.6 × 1.1 m，0.05 m/格）：圓舭較深英式艦載艇、船艙縱塞備用圓材且塗英國海軍漆色。
  - `basecamp-frigate-constitution-01m-whaleboat`（8.55 × 1.85 m，0.05 m/格）：窄深雙尖捕鯨艇。
  - `apex-one-venice-gondola-01m-assembly`（10.5 × 1.4 m，0.1 m/格）：威尼斯不對稱單人站姿貢多拉。
- **複用外部模型元件清單**：
  - 錨：`kotoko-fusta-01m-anchor-grapnel`（0.05 m/格，地中海四爪錨，於 0.1 m 組裝件以 `scale=0.3` 擺於船首）。
  - 貨位實測／陳設：`summit-rocher-01m-crate`（0.6 m 貨箱，0.05 m/格，`scale=0.5`）與 `summit-rocher-01m-barrel`（0.6×0.9 m 酒桶，0.05 m/格，`scale=0.5`）。
  - 槳（步驟 13 實測擇定）：先比對 `basecamp-piragua-01m-oar`（3.4 m，0.05 m/格，`scale=0.5`，`seat` 離支點 0.8 m），若支點、坐板幾何與乾舷入水角契合就直接複用；若需調整長度或入水角再造北非平底艇專用通用槳。
  - 燈具（視步驟 10）：`basecamp-ember-01m-lantern`（0.02 m/格，若夜間懸掛提燈以 `scale=0.2`）。

## 三、新圖紙與線型驗證（步驟 3）

- **設計規格檔**：`design/plan.json`、`design/lines.py`、`design/draft_lines.py`。
- **主尺度（0.1 m／格）**：
  - `LOA = 96` 格（`9.6 m`，`x = 18..113`，艉平鏡有小幅後傾、艏柱有明確前傾與凸出艏柱頭 `x=113, z=12`）。
  - `Beam = 27` 格（`2.7 m`，`y = 37..63`，中線 `y = 50`）；`BWL = 25` 格（`2.5 m`）；`LWL = 90` 格（`9.0 m`）。
  - `DWL = z=4`（滿載吃水 `0.40 m`）；舯貨艙口舷緣 `sheer_z = 9.0`（乾舷 `0.50 m`），前後甲板段舷緣漸升。
  - 平底寬腹斷面（艉平鏡寬 `9` 格 ＝ `0.9 m`；舯貨艙底可用平面 `583` 格，`x=46..78` 保持開放貨艙口）。
- **水靜力與對帳指標**：
  - `cells = 3728`（調色盤分佈：`68`: 1021, `136`: 733, `177`: 1776, `208`: 198；主體橄欖褐、棕木與赭紅飾帶／暗帽欄）。
  - `components = 1`、`cavities = 0`（閉氣空腔 `0`）、`mirror_diff = 0`（左／右舷完美對稱）。
  - `displacement_t = 5.72 t`（船殼 `hull_mass_t = 2.05 t`，含餘裕載貨＋艇員淨載 `free_payload_t = 3.67 t`，足夠覆蓋目標貨載 `3.5 t`＋艇員）。
- **可重現與負控制檢查**：
  - 連跑兩次 `draft_lines.py` 之 `design/masks/hull/hull.vox.txt` SHA-256 完全一致：`AE1D61C0A3A2C3F3312D09006D05AC5BA348E8E586137C797D67AA79F45B4642`。
  - 負控制 `--probe=half_beam=+3 --probe=x_fwd=-10` 驗證：`beam_cells` 由 `27` 增至 `33`（`half_beam_at_sheer` `13.6 → 16.6`）、`loa_cells` 由 `96` 減至 `86`（`bow_tip_x` `113 → 103`）、`lwl_cells` `90 → 80`、`cells` `3728 → 3776`。
  - 目視檢查 `design/sheet01_lines_v1.png`：三視圖與艉鏡／舯貨艙／前段斷面清晰，無偶數步進跳行與多餘破格。

## 四、船殼落格、塗裝與雙帳驗收（步驟 4）

- **落格執行**：`design/tools/stamp_lists.py kiara-tunis-sandal-01m 0 design/masks/hull/hull.vox.txt` → `cells=3728 exit=0 placed=3728`（實落 `work` 一次命中，`draft=0`），已打標記 `hull`（`2026-11-17/131121_260_aaad23.json`）。
- **獨立結果帳 (`design/tools/check_hull.py`)**：
  - `shift=0`: `list=3728, work=3728, missing=0, extra=0, color_diff=0, components=1, cavities=0, mirror_diff=0, mirror_color_diff=0`。
  - 負控制 `--shift=3`：`missing=2863, extra=2863, color_diff=763`；`--shift=15`（完全移出船高）：`missing=3728, extra=3728, color_diff=0`。
- **CLI `stats` 獨立複核 (`structure=1 mirror=y:50`)**：
  - `total_voxels=3728, components=1, largest_component=3728, cavities=0, cavity_cells=0, mirror_missing_low=0, mirror_missing_high=0, mirror_color_diff=0`。
- **目視檢查（`design/overlays/stage1_hull_{3quarter,side,section}.png`）**：
  - 三視角無破洞、無雜散體素，艉平鏡與前傾艏柱、水下深瀝青防污層、舷側赭黃飾帶與帽欄層次清晰，舯底平寬適宜載貨。

## 五、主甲板、艙底鋪板與坐板（步驟 5）

- **子作品與關聯**：`kiara-tunis-sandal-01m-deck-main`（`136×101×30`, `tags=sub`, `meters_per_voxel=0.1`），掛入 `kiara-tunis-sandal-01m-assembly` 之 `甲板-main` `@0,0,0`；meta 寫入 `decks_meta.tsv`：`kind=deck, deck=main, level=0, name=主甲板／艙底鋪板與坐板, thick=1, floor="21:5,29:5,30:2,86:2,87:5,105:5"`。
- **佈局設計 (`design/draft_deck.py`)**：
  - `duckboards`：舯貨艙底鋪板 `x=30..86, z=1`（站面 `z=2`），木條深淺配色並在 `(80..82, 49..51)` 設深木桅座底墊（*carlingue*）。
  - 3 對划手坐板 `thwart-1` (`x=34..36`)、`thwart-2` (`x=42..44`)、`thwart-3` (`x=80..82`，中央留 `3×3` 桅孔 *étambrai*) 設於 `z=4`（頂面 `z=5`），中段 `x=46..78` 留為 `3.3 m × 1.5–1.9 m` 開放平底貨艙（`583` 格淨貨位）。
  - `stern-platform` (`x=21..29, z=4`) 與 `bow-platform` (`x=87..105, z=4`) 均保留艙下朝向貨艙開口以防閉氣空腔。
- **對帳與驗證**：
  - `cells = 1289` (`stamp_lists.py` `placed = 1289`)；`overlap_hull = 0`、`mast_hole_blocked = 0`、`all_parts_touch_both_walls = true`。
  - 組裝件 `stats structure=1 mirror=y:50`：`total_voxels = 5017`、`link_overlap = 0`、`components = 1`、`cavities = 0`、`mirror_missing_low = 0`、`mirror_missing_high = 0`、`mirror_color_diff = 0`。
  - `walk_grid` 連通性：`walk_groups = 1`（`walk_main_cells = 1369`，`13.69 m²`，無孤立碎片）；負控制 `--probe=seat_z=+1`（坐板與前後台抬高 1 格至 `z=5`、步高 `4 > 3`）立即裂解為 `walk_groups = 3`（`walk_other_cells = [151, 83]`）。
  - 本艇屬露天無跨層甲板／無隔間小型轉運划艇，不需樓梯或空艙房，依 `Ship_Steps` 步驟篩減表無額外樓梯／艙房子作品。
- **目視檢查（`design/sheet02_deck_v1.png` 與 `design/overlays/stage2_deck_3quarter.png`）**：鋪板、三坐板、貨艙開口、桅座與艏艉平台層次分明，無干涉破穿。

## 六、裝飾與可隱藏模型（步驟 6）

- **裝飾設計 (`design/draft_deco.py`)**：共 4 件裝飾子作品（`0.1 m/格`、`tags=sub`），以外部模型 (`work sub=model`) 共 9 個實例掛入 `kiara-tunis-sandal-01m-assembly` 且**全數標註 `deco=1`**（滿足遊戲低畫質設定隱藏裝飾與不計重量／命中）：
  - `kiara-tunis-sandal-01m-bitt`：艏主繫纜柱 `繫纜柱-艏` (`at=97.5,50.5,5`)、艉兩側繫纜柱 `繫纜柱-艉P/S` (`at=23.5,47.5,5` 與 `23.5,53.5,5`)。
  - `kiara-tunis-sandal-01m-fender`：中段兩舷麻木護舷靠墊 `護舷-P1/S1` (`x=52.5, y=37.5/63.5`)、`護舷-P2/S2` (`x=68.5, y=36.5/64.5`)，貼齊外殼表面懸於帽欄下方。
  - `kiara-tunis-sandal-01m-stem-orn`：艏柱頂突尼斯朱紅／鎏金彎角飾（`艏飾` `at=113.5,50.5,14`）。
  - `kiara-tunis-sandal-01m-stern-orn`：艉鏡兩側朱紅金點裝飾徽（`艉飾` `at=18.5,50.5,5`），中央 `y=49..51` 保持淨空供步驟 11 舵葉掛設。
- **對帳與負控制檢查**：
  - `total_deco_cells = 81`、`overlap_ship = 0`、`overlap_self = 0`、`rudder_zone_blocked = 0`、`all_attached = true`、`mirror_diff = 0`、`mirror_color_diff = 0`。
  - 負控制 `--probe=shift_y=-1`：護舷內推 1 格後 `overlap_ship` 由 `0` 跳為 `16`。
  - CLI `work sub=models`：`models_drawn = 9, models_broken = 0`；目視 `design/overlays/stage3_deco_3quarter.png` 與 `stage3_deco_aftbow.png` 四種裝飾皆貼合且對稱。

## 七、主桅與拉丁帆桁（步驟 7）

- **子作品與關聯**：
  - `kiara-tunis-sandal-01m-mast`（`136×101×110`, `tags=sub`, `meters_per_voxel=0.1`）：於 `(x=81, y=50)` 踩 `carlingue` 上 `z=2` 起立至 `z=56`，穿過前坐板 `thwart-3` 之 `3×3` 桅孔（`z=4` 深木圍襯），頂設地中海拉丁滑輪桅首塊 `calcet`（`z=52..55`）與金頂帽（`z=56`）。組裝件關聯 `桅-main` `@0,0,0` `turn=0`，meta 標 `kind=mast, mast=main`。
  - `kiara-tunis-sandal-01m-yard`（`84×5×5`, `tags=sub`, `meters_per_voxel=0.1`）：於水平 `+X` 建 `78` 格（`7.8 m`）雙木搭接拉丁帆桁，登記 `22` 個固定點（`pivot` `47,2,2`、`sling` `47,2,3`、`fore` `79,2,2`、`earing-F` `77,2,2`、`peak` `2,2,2`、`earing-A` `4,2,2` 與 `top-00..15`）。
- **帆桁掛載與 meta**：以外部模型 `yard` 掛入 `kiara-tunis-sandal-01m-mast`（`at=81.5,48.5,39.0`, `pivot=47.5,2.5,2.5`, `rotate=0,34,0°`, `scale=1`），meta 標 `id=yard-1, kind=yard, mast=main, yard=gaff, rig=lateen, sail=lateen, pivot_anchor=pivot, turn_axis=z, rotate_y_deg=34.0, rotate_z_deg=0, length_m=7.8`。
- **對帳與負控制檢查**：
  - `mast_cells = 79`（`components = 1`, `mirror_color_diff = 0`, `mast_overlap_hull = 0`, `mast_overlap_deck = 0`）；於 `pivot.z - 40..pivot.z - 10`（`z=0..29`）中線 `±4` 內實占 `48` 格符合 `shipcheck` 認桅規範。
  - `yard_cells = 115`（`components = 1`, `yard_world_hits = 0`）；`fore = (108.03, 48.5, 21.11)`、`peak = (44.19, 48.5, 64.16)`；水平擺幅半徑 `pivot→fore = 2.65 m > 2.5 m`（`lateen` 最大擺角 `70.5°` 不會產生異常域錯誤）。
  - 負控制 `--probe=mast_x=+7`：主桅前移入艏甲板區後 `mast_overlap_deck = 5` 立即告警。
  - 目視 `design/sheet03_masts_v1.png` 與 `design/overlays/stage4_masts_3quarter.png`：主桅與傾斜 34° 拉丁帆桁無穿模、比例穩重低重心。

## 八、索具、拉丁帆與奧圖曼突尼斯旗幟（步驟 8）

- **新增子作品／固定點與關聯**：
  - `kiara-tunis-sandal-01m-flagstaff`（`136×101×30`, `tags=sub`, `meters_per_voxel=0.1`）：船尾右舷 `(19, 54, 11..24)` 細木旗桿，關聯 `旗桿` `@0,0,0` 避開舵位與帆腳。
  - 共登記 `13` 處固定點（`hull`: `shroud-P1/P2/S1/S2`, `belay-sheet-P/S`；`deck-main`: `tack-main`；`mast`: `hound`, `calcet-halyard`, `mast-foot-belay`, `truck`；`flagstaff`: `top`, `bot`）。
- **帆與旗 (`work sub=sail` + `sub=meta part=sail`)**：
  - `lateen`（三角主拉丁帆，`16.04 m²`）：`tack = model:桅-main/yard/fore`、`head = model:桅-main/yard/peak`、`clew = (36.0, 50.5, 19.5) [free]`，`bind=0`、`#f2ead8`、`fullness=1.05`；meta `kind=sail, mast=main, sail=gaff, set=1`。
  - `pennant`（桅頂長旗）：綁 `81.5,50.5,56.5..53.5`，附 `textures/pennant.png` (`64×16`)；meta `kind=flag, flag=pennant, mast=main, nation=ottoman`。
  - `ensign`（奧圖曼突尼斯紅底白新月星國旗）：綁 `旗桿/top..bot`，附 `textures/ensign.png` (`72×48`)；meta `kind=flag, flag=ensign, nation=ottoman`。
- **帆裝三段張帆表（`Ship_Rigging §9.1`）**：
  - 段 `0`（全收）：無（全收帆布，僅留常駐旗幟與船殼／槳）。
  - 段 `1`（收帆）：`lateen`（單帆明確設 `set=1`）。
  - 段 `2`（戰鬥帆）：`lateen`。
  - 段 `3`（滿帆）：`lateen`。
- **繩索（`9` 條，`ropecheck` 確認 `ends_ok=18`, `ropes_broken=0`）**：
  - `standing/shrouds`：`shroud-P1/P2/S1/S2`（焦油黑 `#2b2620`, `slack=1.0`, `kind=shroud`）。
  - `running/halyards`：`main.halyard`、`main.halyard-fall`（`#a08458`, `kind=halyard`）。
  - `running/tacks`：`lateen.tack`（`sail:lateen/tack → 甲板-main/tack-main`, `kind=tack, sail=lateen`）。
  - `running/sheets`：`lateen.sheet-P/S`（`sail:lateen/clew → 船殼/belay-sheet-P/S`, `kind=sheet, sail=lateen`）。
- **對帳、風場設定與負控制檢查**：
  - 組裝件設風 `wind=4.5,-1.5,0`、`sail_seconds=3`：`sails_drawn=3, sails_broken=0, ropes_drawn=9, ropes_broken=0`，主帆最鼓 `8.99` 格，靜態碰撞 `0`（最小淨空 `11.11` 格）。
  - 負控制 `--probe=clew_z=-15`（壓低帆角）：`sail_static_occ_hits` 由 `0` 變 `1`（最小淨空降至 `0.5`）。
  - 目視 `design/overlays/stage5_rig_wind_{3quarter,port}.png`：帆面飽滿不穿模、旗幟隨風展開清晰、雙舷繩索對稱無斷裂。

## 九、甲板貨位對帳與燈具（步驟 10）

- **開放貨艙貨位對帳（`design/draft_cargo.py`，依 `Ship_Fittings §2.1／§9.9` 取樣）**：
  - 於舯開放貨艙 `x=46..78`（站面 `z=2` 鋪板，淨寬 `1.5–1.9 m`）依左右對稱雙列擺放 `10` 件共用貨物模型（掛入 `甲板-main` 子作品、皆標 **`deco=1`**），中央留 `0.2–0.4 m` 通道：
    - `貨箱-1P/1S`、`2P/2S`、`3P/3S`（`summit-rocher-01m-crate`、`scale=0.5`，每只 `0.6×0.6×0.6 m`）於 `x=48.5, 55.5, 62.5`，頂高 `z=8` 齊平舷牆內緣。
    - `貨桶-1P/1S`、`2P/2S`（`summit-rocher-01m-barrel`、`scale=0.5`，每只 `0.6×0.6×0.9 m`）於 `x=69.5, 76.5`，總擺放貨重 `3.12 t`（＋艇員隨身什物約 `0.38 t` 對應目標 `3.5 t` 貨載，全落於 `DWL z=4` 之 `free_payload_t = 3.67 t` 餘裕內）。
  - 本艇無火砲（0 門）與封閉艙房／廚房，依 `75_shipcheck.js:283` 與 `Ship_Steps` 不設彈藥庫、門與廚房。
- **船尾停泊燈（`kind=light`）**：
  - 複用 `gura-tridente-01m-lantern`（`scale=0.18`）於船尾左舷 `(19.5, 46.5, 11.0)`（與右舷旗桿 `(19, 54)` 對稱，實踩 `(19,46,10)` 頂面），meta 標 `id=light-1, kind=light, light=amber`（**不標 `deco=1`**）。
- **對帳與負控制檢查**：
  - `occ_sample_hits = 0`（格心＋四角內外取樣）、`pair_overlaps = 0`、`all_supported = true`、`models_drawn = 21, models_broken = 0`。
  - 負控制 `--probe=shift_out=+4`（貨位往兩舷外推 `0.4 m`）：`occ_sample_hits` 由 `0` 暴增為 `112`。
  - 目視 `design/overlays/stage6_cargo_3quarter.png`：貨箱、酒桶排列整齊不礙坐板與桅桿，艉燈安穩對稱。

## 十、舵、舵柄與地中海四爪錨（步驟 11）

- **艉柱舵與整合式舵柄（`kiara-tunis-sandal-01m-rudder`，`136×101×30`, `tags=sub`, `meters_per_voxel=0.1`）**：
  - 建於 `(x=12..23, y=50, z=1..12)`（`55` 格、`1` 元件）：舵葉底切齊 `z=1`（高於平底船底 `z=0` 確保淺水 `0.40 m` 吃水不先撞底）；`stock-top` 登記於 `(16, 50, 10)` 貼靠艉柱 `x=18`；一體式舵柄於 `z=12` 越過艉鏡 `z=10` 向前伸至 `x=23`（無另設舵輪，依 `Ship_Helm §9.8.1` 歸為操舵桿一體型）。
  - 以外部模型 `舵` 掛入組裝件（`pivot=at=16.5,50.5,1`），meta 標 `id=rudder-1, kind=rudder, hinge_x=16.5, hinge_y=50.5, hinge_z=1.0, axis_x=0.0, axis_y=0.0, axis_z=1.0, max_deg=35, turn_axis=hinge, spin=rudder, spin_k=35, spin_min=-35, spin_max=35, spin_lag=0.3`。
  - **掃掠與負控制檢核（`design/draft_helm.py`）**：於 `−35°..+35°` 逐度掃掠 `rudder_sweep_35deg_hits = 0`（對船殼、艉飾、右舷旗桿與修正後左舷艉燈 `(18.8,46.0,11.0, scale=0.14)` 均零干涉）；負控制 `--probe=rudder_dx=+2` 跳升為 `16` 處撞擊。
- **地中海四爪錨與錨鏈孔（`錨-S` ＋ `hull/hawse-S`）**：
  - 共用元件 `kotoko-fusta-01m-anchor-grapnel`（`0.05 m/格`，`ring/crown/fluke-a/fluke-b` 已齊備），以 `scale=0.3` 懸於右舷艏外側 `at=103.5,58.2,12.2`（`pivot=9.5,9.5,24, rotate=0,0,45°`），錨冠底高 `z=5.15 > DWL z=4` 不拖水；meta `id=anchor-1, kind=anchor, anchor=bower, hawse="103,54,8"`，並於 `hull` 登記 `hawse-S` `@103,54,8`。
  - 對帳 `anchor_hits = 0`；負控制 `--probe=anchor_in=-3` 跳升為 `42` 格穿入船首殼。
- **目視檢查（`design/overlays/stage7_{helm_anchor_3quarter,stern_closeup}.png`）**：艉舵水下部分切齊龍骨底線以上、舵柄暢順越過艉欄，右舷四爪錨垂掛角度與尺寸協調。

## 十一、槳動力與五金材質（步驟 13）

- **每舷 3 支單人坐姿槳（共 6 支，`design/draft_oars.py`）**：
  - 複用共用元件 `basecamp-piragua-01m-oar`（`0.05 m/格, scale=0.5`, 已具 `pivot/blade/seat` 固定點），掛於船殼 `kiara-tunis-sandal-01m` 形成 `船殼/oar-S1..S3`（右舷）與 `船殼/oar-P1..P3`（左舷 `mirror=y`），分別對齊三張划手坐板 `x=35.5` (`at.z=10.65`, `rot_x=-1.8°`)、`x=43.5` (`at.z=9.65`) 與 `x=81.5` (`at.z=9.65`)，meta 標 `kind=oar, rowers=1, side=S|P, stroke_deg=30, dip_deg=12`。
  - **划槳與靠泊對帳**：
    - `static_hits = 0`、`sweep_hits = 0`（`-30°..+30°` 前後掃掠 × `0°..+12°` 抬槳均無碰撞船殼、甲板、坐板、桅、旗桿與護舷）。
    - 槳葉中心皆落於 `DWL z=4.0` 水面下約 `0.02 m`（`±0.1 m` 內）；`all_seats_ok = true`（坐點均實踩 `thwart` 且頭頂保有 `≥ 14` 格 `1.4 m` 淨高）；`all_gunwales_near = true`。
    - 靠泊寬度對帳：划行展開全幅 `rowing_span_m = 7.0 m`，收槳停靠突尼斯湖港口／`berth-boat`（寬上限 `12 m`）以船寬 `2.7 m` 計可寬裕靠泊。
    - 負控制 `--probe=oar_drop=3`（下壓 3 格）：`static_hits` 由 `0 → 34`、`sweep_hits` 由 `0 → 328`。
- **木質與五金材質（`Ship_Materials §9.5`）**：
  - 船殼、鋪板、坐板、桅桁、舵維持木質預設（松木／橡木）；鐵質四爪錨 `錨-S` 標 `material=iron, render=voxel`、黃銅艉燈 `艉燈` 標 `material=brass, render=voxel`（維持方格細節並帶金屬反光）。
- **目視檢查（`design/overlays/stage8_complete_{3quarter,top}.png`）**：六支槳兩舷完全對稱、不干涉貨艙與纜繩，全船 `models_drawn = 29, models_broken = 0`。

## 12. 步驟 14：給遊戲的 Meta、匯入 Blockside 與元件 `render` 檢視

- **船殼設計水線**：已設 `船殼` link meta `kind=ship, waterline_z=4`（0.40 m 吃水）。
- **雕刻端檢查與匯出**：
  - `ropecheck`：`ropes=9, ends_ok=18, loose=0, ok=true`。
  - 匯出 `D:/Unity/Valhalla/Sculpture/exports/sandal.vxk`（`50,584` B，5,110 格，checksum `e2a6b245`/`3802575429`，SHA-256 `B5887126AED971D47279C06C700D9BA7DE11B64A1A58E0A4C1A7BAFD3A907A0C`）。
- **Blockside 匯入（獨立 worktree `D:/Unity/Blocksail/external/.wt-kiara-sandal`，分支 `kiara/sandal-1301`）**：
  - `admin.py import --work kiara-tunis-sandal-01m-assembly --id sandal --name "突尼斯湖轉運划艇"` ＋ `admin.py ids --id sandal`（發號並回寫 `kiara-tunis-sandal-01m-assembly`、`kiara-tunis-sandal-01m-deck-main` 之 `meta_log.jsonl`）＋ `ancbake` ＋ `showlod` ＋ `ropebind`。
  - `config/game.json`：`"role": "merchant"`, `"cargoT": 3.0`, `"material": "pine"`, `"fireEngine": false`, `"cfg": {"base": 4.2, "pump": 2, "agile": 3.8, "upwind": 2.2}`，並將船員調至史實規模 **`10` 人**（船長 1＋槳手 6＋木匠 1＋帆匠 1＋預備水手 `handsK=0.025`→1；`helm=0, top=0, marines=0, surgeon=0, cook=0, navigator=0, quartermaster=0`）。
  - `admin.py disp --id sandal`：**空載 2.6 t（空船浮高 +0.21 m）／標準 3 t／滿載 6 t／壓艙空間 3.2 t／載重 3 t（53%）／固定壓艙 0 t／每 cm 0.16 t**。
  - `admin.py shipcheck --id sandal`：**✗ 0　⚠ 0**（砲 0、船員 10、模型 13＋裝飾 19、繩 9、帆 3＋陣營旗 1、桅 1、單錨 右舷＋ring＋hawse、水線 z 4、槳 6 支 6/6、到沉沒線 +4.2 m/+9 t 都不漏）。
  - `admin.py ladcheck --id sandal`：**0 座 ✗ 0 ⚠ 0**；甲板連通 **1 層（h0 主甲板／艙底鋪板與坐板 `13.4 m²`）都接得到**。
  - `shipthumbs.py --check`：current（已人工核對 `src/art/ships/atlas.png` 格位 `[0, 6]`）；`admin.py check`、`srccheck`（指紋 `b480c62f7f21fc1c`，216 支檔、49 艘船檔一致）、`verify`（1,721 份網格三角形逐個比對一致）全數通過。
- **新做的桶／槳／舵輪（舵柄）元件要不要標 `render`（`Ship_Game §9／§9.4／§12`、`Ship_Render`、`config/meta_kinds.json`）**：
  - **木製與一般件（不標 `render`）**：船殼、甲板、木質船體裝飾，以及本船自製的舵＋一體舵柄（`kiara-tunis-sandal-01m-rudder`，預設隨全船 `pine` 材質）與共用的木質貨箱／木桶（`summit-rocher-01m-crate/barrel`）、木槳（`basecamp-piragua-01m-oar`）皆維持預設方塊風格（不加 `render=smooth`）；若新做純木質桶、槳或舵輪 **不用標 `render`**（遊戲預設就是 `voxel`）。
  - **金屬件（依外觀決定是否標 `render=voxel`）**：`config/game.json` 中若材質標了 `smooth: true`（如鐵甲、鍋爐），遊戲會自動將該材質的格做平滑面與金屬反光；若小艇上引用或新做的金屬元件（如本船的 `錨-S` `material=iron` 與 `艉燈` `material=brass`）要保留體素方塊感，才須明確標 `render=voxel`。

## 13. 突尼斯湖與加貝斯實際地形量測、加貝斯獨立場景測試與史料限度

- **Blocksail 世界地形 16 m 格柵實測（`tools/harbour_grid.cjs`，`step=16 m`、`±1.5 km`）**：
  - **突尼斯內湖西岸 *Bâb al-Bahr*（中心 `[10.2050, 36.8120]`）**：海點 26,808 格，深度分布 `-0.36..1.09 m`（`0` 格 `≥ 2.5 m`，`berth-boat` / `berth-small` 均為 0）；海岸緣往東 `864 m`（`10.2043°E`）達 `0.40 m` 水深；中湖 `[10.24, 36.815]`（250 m step）深約 `0.7..1.27 m`。
  - **拉古萊特口門（中心 `[10.3050, 36.8150]`）**：海點 34,849 格，深 `-0.34..4.52 m`（口內低鞍僅 `-0.47..-0.93 m`，`10.3068°E` 為 `-1.62 m`，需出至 `10.33..10.34°E` 才達 `-4.92..-8.92 m` 可停遠洋商船；另依 `TOWNS_1660S_NORTH_AFRICA.md §3`，拉古萊特沙洲目前 Natural Earth 岸線尚未補畫陸地）。
  - **加貝斯近岸（中心 `[10.1250, 33.8900]`，對應綠洲 `oasis-gabes` `[10.065, 33.874]`、`reach=4500 m`）**：海點 23,983 格，由 `10.1198°E` 陸海交界往東隨離岸距離遞深：`176 m`（`10.1212°E`）達 `0.41 m`（`sandal` 吃水線）、`432 m`（`10.1240°E`）達 `1.03 m`、`976 m`（`10.1298°E`）達 `2.51 m`（`berth-boat`）、`1,792 m`（`10.1387°E`）達 `5.05 m`（`berth-small`）。
- **加貝斯獨立淺岸轉運場景測試（`export_chunks.cjs` 匯出真實 `gabes` 海圖塊＋無頭 Chromium實跑 `verify_sandal_sim.py`）**：
  - **外海母船泊地**：地中海貨運帆船 `tartane`（設計吃水 `1.6 m`）停泊於 `x=+800 m`（`10.14028°E, 33.88996°N`，水深 `-5.7 m` 沙底），其 `1.6 m` 靜水擱淺界限在 `x=-480.3 m`（`10.12643°E`）。
  - **近岸駁運與拋錨實測**：`sandal`（靜水設計吃水 `0.40 m`，深水靜止時 `keelY=-0.386 m`）全收帆純人力划槳以 `3.03 m/s`（約 `5.9 kn`）向西駛入近岸淺區，通過 `-5.4 m → -2.0 m → -1.0 m` 沙底均 `grnd=null`；於 `t=505 s`（`x=-749.6 m`、`10.12351°E`、水深 `-0.9 m`、靜態龍骨餘裕 `+0.50 m`）按單錨鍵 `4` 成功拋錨駐停（`anc.S.st="down"`、`spd=0.12 m/s`、`grnd=null`），完成近岸接駁窗口。
  - **負對照（進岸擱淺與湧浪限制）**：起錨繼續往更淺沙底推進後，於 `x=-754.4 m`（`-0.9 m` 沙底，`t=510 s`）因開放海岸湧浪波谷使瞬間龍骨下探 `keelY=-1.05 m` 而觸發 `grnd={m:1 (SAND), pen:0.15, lost:1}`（合計掉 7 格）。此讀數明確區分兩地操作邊界：**平靜避風的突尼斯湖內靜態餘裕達 `0.40–0.50 m` 水深即可通行；開放海岸加貝斯受湧浪與當地地中海最大潮差影響，安全接駁停泊建議留至約 `-1.0 m` 水深線附近（`~400–450 m` 離岸）**。
- **兩地 1666 史料與模型限度（照實登錄，不補造細節）**：
  - `TOWNS_1660S_NORTH_AFRICA.md §7` 查證：1666 年拉古萊特湖中水道的確實水深、商船數目、「大船停外、小船進湖」報導的年代精確歸屬，以及 1666 年加貝斯港活動與椰棗出口量均缺一手數字紀錄（加貝斯椰棗大宗出口僅見 1911 年大英百科記載）。
  - 加貝斯灣史實擁有約 `1.5–2 m` 地中海少見半日大潮，現階段 Blocksail 世界海平面固定為 `0 m` 基準，未模擬潮汐漲落與沖灘牽引；且 `town-tunis`／`town-gabes` 城鎮與拉古萊特沙洲尚待後續建城單（`TASK-1288`）掛入。

## 14. 步驟 15：交船檢查表、遊戲側 `geo` 高度表與 Checksum 對帳

- **換新船實機檢查表逐條實測（`verify_sandal_sim.py`、`?debug=1&prefs=0`）**：
  - 開場無掉落模型（`lostModels(0)=[]`）、無浮空繩（`ropes(0)=[]`；靜態 9 條全數固定）。
  - 無風純槳航速 `2.997 m/s`（`5.83 kn`）；橫風滿拉丁帆＋全速槳 `6.595 m/s`（`12.82 kn`、`sailFrac=1`）。
  - 操舵與差動轉向：`A` 鍵滿舵左轉實測 `10.62 °/s`（`dif=true`、`side=[-0.5, 1]`、舵鏈 `1.00`）。
  - 單錨操作：`4` 鍵（`ancAll`；單右錨隱藏左右分鍵）下錨咬底（`st="down"`、`spd→0.387 m/s`）與起錨恢復航行（`st="up"`、`spd→7.835 m/s`）正常。
  - 進水與超載極限：`__game.leak(0/10°, 0)` 及負對照破洞（`cut=241`）至沉沒線 `4.2 m`（`+9 t`）均無未預期滲水（開放無蓋小艇以 `floodRim` 與船緣控水）。
  - 旗幟與夜燈：`nation.own={1:"ottoman", 2:"ottoman"}`、`miss=[]`，陣營旗與鄂圖曼新月旗切換不缺圖，船尾黃銅燈掛 `kind=light, light=amber`。
- **遊戲側 `src/config/game.json` (`ships[].geo` 與相關欄，單位：`0.1 m/格`，以本作品座標系與 `waterline_z=4` 量出)**：
  - `waterline_z`: `4`（`0.40 m`）
  - `geo.spar`: `[5, 10]`（露天甲板／坐板站人範圍 `z=5..10`；對應 `deck=main` 鋪板頂面 `z=2` 與坐板／艏艉台頂面 `z=5`、`foot_z=5`）
  - `geo.marines`: `[21, 29]`（艦體前後內縮起訖，對應船體 `x=18..113`）
  - `geo.center`: `10`（船隻中心高度 `1.0 m`）
  - `geo.aim`: `6`（預設瞄準點高度 `0.6 m`）
  - `geo.aimZ`: `[2, 65]`（瞄準高度上下限 `0.2–6.5 m`）
  - `geo.deckAim`: `[4, 10]`（船身／甲板瞄準高度帶 `0.4–1.0 m`）
  - `geo.rigAim`: `[15, 65]`（索具／桅帆高度帶 `1.5–6.5 m`，對應 `mast z=2..56` 與拉丁帆頂點 `z≈65`）
  - `geo.marineY`: `4`（由中線量甲板欄位偏移）
  - `geo.qx`: `5`（無舵輪，軍官站位距外框起點 `+5` 格）
  - `floodRim`: `[[48.5, 38.5, 9], [48.5, 62.5, 9], [76.5, 39.5, 9], [76.5, 61.5, 9]]`（舯部舷牆進水緣 `z=9`，高於設計水線 `0.50 m`）
- **Checksum 對帳**：
  - Sculpture 原始匯出 `D:/Unity/Valhalla/Sculpture/exports/sandal.vxk`：`50,584` B、header checksum `e2a6b245` / `3802575429`、SHA-256 `B5887126AED971D47279C06C700D9BA7DE11B64A1A58E0A4C1A7BAFD3A907A0C`。
  - Blockside 經 `ids` / `ropebind` / `metasync` 後鎖定之 `_cache/sandal.vxk`：`48,976` B、`vxk_lock.json` 指紋 `c:16b39c6cda994c00cdd690981adc92fe3f6851ec`、SHA-256 `569C35BE1E7917D0CDFB2C5BF88E072FDC9F7C0A56FDC26ECE676E8C1D3DE792`。
  - 成品分片 `ships/ship-sandal.js` SHA-256（同步錄於 `src/art/ships/thumbs.json`）：`F8B4979F405A148A542CE170F5F4D6307033BD77251220A9217B27B9DDD3DB7A`。

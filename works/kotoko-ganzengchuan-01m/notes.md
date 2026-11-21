# 福建趕繒船 Ganzengchuan（約 120–150 噸，1666 台海主力戰巡船）—— 建造筆記（0.1 m／格）

委託：Tim 2026-11-21「/scp-task 1314 造船參考 /scp-shipbuilding GO」（TASK-1314，開單 pinnacle；傘 TASK-1311 亞洲船③）。

## 方向（步驟 1；2026-11-21）
- 依 `Ship_Steps` §2 挑選步驟：保留 1–11、14、15；露天舷牆砲與佛郎機迴旋砲（無封閉砲甲板）⇒ 刪 12；步驟 9 讀 `Ship_Guns`＋`Ship_Turrets` §4.5；硬骨帆（趕繒船 junk rig）⇒ 在步驟 7、8、14 補入 `Ship_Battens`；步驟 3 考證確認趕繒船配「櫓配三個」⇒ 依單補回 **步驟 13 `Ship_Oars`**。

## 座標、比例與作品拆法（步驟 2；2026-11-21）
- **比例**：`meters_per_voxel = 0.1`（1 格 = 0.1 m；船殼與組裝件皆明記 `meters_per_voxel`）。
- **框與座標軸**：`384 × 192 × 384`（`38.4 × 19.2 × 38.4 m`），`X` 船長朝 `+X`、`Y` 船寬中線 `y = 96`（`y ↔ 192 − y`）、`Z` 高度 `z = 0` 為龍骨底面。

## 新圖紙與設計讀數（步驟 3；2026-11-21）
- 史料與出處見 `design/sources.md` 與 `design/plan.json`；`LOA = 26.4 m`、`Beam = 6.7 m`、`waterline_z = 24`（`2.4 m`）、`displacement_t_at_wl = 188.31 t`、`hull_mass_t_est = 53.25 t`、`DETERMINISTIC = True`。

## 船殼落格、砲門、塗裝與船尾窗（步驟 4；2026-11-21）
- 結果帳：`87,498` 格（缺 `0`、多 `0`、色差 `0`）；`components = 1`、`cavities = 0`、`mirror_diff = 0`；線形對照 `224` 點 `|差| ≤ 0`；反向對照 `probe_x=156` 報 `11` 點差 `3`；OBJ `20,312` 面。`mark=船殼`（`67444ed9f516`）。

## 甲板、梯子與空艙房（步驟 5；2026-11-21）
- **4 層甲板子作品**（`tags=sub`, `0.1 m/格`, 組裝件關聯 `kind=deck`）：
  - `deck-hold`（`level=0, floor=82:9..300:9, thick=2`）：`23,951` 格（含 9 道橫向水密隔艙壁 `x=112..282` 與底艙壓艙底肋 `9,839` 格 `x=86..300, z=3..7` 防空腔）。
  - `deck-main`（`level=1, floor=68:35..282:35, thick=2`）：`12,831` 格（含主艙口 `x=208..220`、下艙梯井 `x=142..154`、雙桅穿孔）。
  - `deck-fore`（`level=2, floor=282:44..318:44, thick=2`）：`1,634` 格（含前 break 與欄杆梯口）。
  - `deck-poop`（`level=2, floor=62:54..112:54, thick=2`）：`3,371` 格（含舵艙前壁＋中央門 `y=93..99`＋尾樓欄杆梯口）。
- **3 座梯子子作品**（掛各自上層甲板 `name=梯子, kind=ladders`，全帶 `foot/lo/hi/head` 四固定點，0 重疊）：
  - `ladders-main`（`hold`: `228` 格，`8` 階，`foot=[136,96,9]` → `head=[156,96,35]`）。
  - `ladders-poop`（`poop`: `167` 格，`6` 階，`foot=[126,110,35]` → `head=[110,110,54]`）。
  - `ladders-fore`（`fore`: `85` 格，`3` 階，`foot=[274,105,35]` → `head=[284,105,44]`）。
- **2 處空艙房**（`rooms-hold` `hold-cargo` 淨高 `2.4 m`、`rooms-main` `cabin-aft` 淨高 `1.7 m`，`kind=rooms`，`solid_inside=0`、`floor_all_solid=true`）。
- **整船讀數與反向對照**：
  - `assembly stats`：`129,765` 格、`link_overlap = 0`、`components = 1`、`cavities = 0`。
  - `walkback.py`：`起點 2 處；可達 26,468 格、能回 26,468 格、走不回來 0 格`。
  - 反向對照（`hide_links=甲板-main/梯子` ＋ `drop=hold`）：`可達 15,697 格`（`hold` 10,771 格如期被隔斷）。
  - 預覽 preset `藏船殼` 已存，過程圖 `overlays/stage5_decks_{bowq,interior}.png` 已目視檢查。

## 裝飾與窗玻璃（步驟 6；2026-11-21）
- **船尾窗玻璃**（`kotoko-ganzengchuan-01m-stern-glass`，關聯 `meta={"material":"glass"}`，不寫 `render`）：`96` 格（色號 `155`）、斜艉換排已補 6 連通橋接、`components_6 = 2`、`cavities = 0`、`mirror_diff = 0`、與木構重疊 `0`。
- **高尾陽台欄杆**（`kotoko-ganzengchuan-01m-stern-balcony`，結構關聯件）：`678` 格（懸挑陽台底板 `z=52..53`＋支承托架 `z=49..51`＋鏤空欄杆 `z=54..56`＋尾隅立柱攀至尾樓頂望樓欄杆 `z=69..72` 止於 `x=70`，避開 `z=41..46` 艉窗、`z=58..64` 花屁股主徽及 `x=86` 迴旋砲）；`components_6 = 1`、`cavities = 0`、`mirror_diff = 0`、重疊 `0`。
- **可隱藏外部模型（`meta={"deco":1}`，`6` 具，`models_drawn=6, models_broken=0`）**：
  - `船首龍獅彩雕`（`kotoko-ganzengchuan-01m-deco-bow` `12×21×12`）：`251` 格、`components_6 = 1`、`cavities = 0`、`mirror_diff = 0`，貼於斜艏柱前 `x>=324`＋兩頰捲雲眉翼 `z<=54`（預留 `(321,96,57)` 首支索固定位，重疊 `0`）。
  - `高尾翔龍牌飾`（`kotoko-ganzengchuan-01m-deco-stern` `6×31×10`）：`274` 格、`components_6 = 1`、`cavities = 0`、`mirror_diff = 0`，立於尾樓望樓金欄 `z=72` 之上 `z=73..79`（重疊 `0`）。
  - **4 具護舷**（複用 `kiara-tunis-sandal-01m-fender`，外緣緊貼零穿模）：`護舷-S/P-186`（`y=129`/`63`）、`護舷-S/P-252`（`y=126`/`66`），各 `z=32..35`。
- **對照驗證與視圖**：`DETERMINISTIC = True`；`shift_bow=-3` 檢出 `bow_overlap=242`、`shift_fender_in=-1` 檢出 `fender_overlap=40`；組裝件 `stats`（`links=船殼,尾樓陽台欄杆`）：`88,176` 格、`components=1`、`cavities=0`、`mirror_diff=0`、`link_overlap=0`；全關聯 `130,539` 格、`link_overlap=0`。OpenGL 視圖 `overlays/stage6_{full,sternq,bowq,nodeco}.png`（不帶 `parts=1` ＋ `models=0` 成功隱藏 6 具 `deco=1` 模型）已目視檢查。🔍

## 桅、帆桁與扇形竹篾（步驟 7；2026-11-21）
- **雙下桅子作品**（`tags=sub`, `0.1 m/格`，`at=0,0,0` 關聯並標 `kind=mast`＋`mast=fore|main`）：
  - `桅-fore`（`kotoko-ganzengchuan-01m-mast-fore`）：`1,582` 格（前傾 `+6°`，`z_heel=9` 實貼 `z=8` 底艙地板、`z_top=174`, `top_x=291.342`，含木箍・桅夾斗盤・金頂帽；`components_6=1`, `cavities=0`, `mirror_diff=0`, `overlap=0`；設 `heel/hounds/cap/top/head` 五固定點）。
  - `桅-main`（`kotoko-ganzengchuan-01m-mast-main`）：`3,897` 格（微後傾 `-2°`，`z_heel=9` 實貼 `z=8` 底艙地板、`z_top=234`, `top_x=178.143`，含木箍・桅夾斗盤・金頂帽；`components_6=1`, `cavities=0`, `mirror_diff=0`, `overlap=0`；設五固定點）。
- **4 根主帆桁**（`Ship_Masts` ＋ `Ship_Battens`：沿 `+X` 建件、中心線 `y=2,z=2`、`scale=1` 掛在各自桅子作品，`kind=yard, yard=course` — 下桁禁標 `boom`；固定點 `pivot/sling/aft/fore/arm-P/arm-S/earing-P/earing-S/jackstay-*`）：
  - `yard-fore-upper`（`7.2 m` / `23.62 ft`, `245` 格, `z=162`, `rotate=0,15,0`）、`yard-fore-lower`（`7.4 m` / `24.28 ft`, `247` 格, `z=60`, `rotate=0,0,0`）。
  - `yard-main-upper`（`10.0 m` / `32.81 ft`, `337` 格, `z=216`, `rotate=0,16,0`）、`yard-main-lower`（`10.4 m` / `34.12 ft`, `349` 格, `z=70`, `rotate=0,0,0`，清空尾樓牆頂 `z=65` 淨空）。
- **2 套共用竹篾桿＋16 根扇形竹篾模型**（`Ship_Battens` §3：`roach=0.05,0.16`，各掛於對應桅子作品，`kind=yard, yard=batten, batten=1..N, material=bamboo`）：
  - `batten-fore`（`94` 格，複用 7 根 `batten-01..07`）；`batten-main`（`129` 格，複用 9 根 `batten-01..09`）；全 16 根最小出緣餘裕 `1.995` 格（`>= 1.5`）。
- **讀數與反向對照**：`DETERMINISTIC = True`；`shift_mast_fore=-3` 檢出 `fore_deck_hull_hits=11`、`batten_short=-6` 檢出 `fore_min_overhang=-3.442 (passes_1_5=false)`；組裝件 `stats`：`136,018` 格、`link_overlap=0`、`components=1`、`cavities=0`、`models_drawn=26, models_broken=0`；視圖 `overlays/stage7_masts_{side,bowq}.png` 已目視檢查。🔍

## 索具、雙桅硬篷與旗幟（步驟 8；2026-11-21）
- **靜索與橫繩組**：頭桅 6 條＋大桅 6 條 `shrouds`（`x=265/270/275` 與 `175/181/188`，避開全部砲門與護舷）、`fore-stay`（至 `stay-bow=(321,96,57)` 避開 `deco-bow`）、`main-stay`（高空聯桅支索至 `桅-fore/top`，高於 `fore-junk` 峰頂逾 `2.1 m` 不貫穿帆面）；`ratlines` 4 組（`fore/main × P/S`, `climb=0`, `step=4`, 共 76 道子繩）。
- **帆自己的繩與固定點**：`sheet` ×4（綁舷內 `x=218`/`x=98`, `kind=sheet, sail=<name>`）、`tack` ×2（綁實甲板 `甲板-fore/tack-fore` 與 `甲板-main/tack-main`, `kind=tack`）、`halyard` ×2（`桅-fore/cap`・`桅-main/cap` → `yard-*/sling`, `kind=halyard`）。合計 `98` 條繩（22 主＋76 橫繩）、`ends_ok=196`、`ropes_broken=0`。
- **雙桅竹篾扇形硬篷**（角點綁上下帆桁 `fore/aft`、`bind=0,2`、`fullness=1.05`、`roach=0.05,0.16`、`textures/*-junk-battens.png`）：
  - `main-junk`：`40` 格/邊（`1681` 布點）、`battens=9`、`kind=sail, mast=main, sail=gaff, set=1`。
  - `fore-junk`：`32` 格/邊（`1089` 布點）、`battens=7`、`kind=sail, mast=fore, sail=gaff, set=2`。
- **旗與船尾旗桿**（`kotoko-ganzengchuan-01m-ensign-staff`，`31` 格，立於 `x=62,y=96,z=68..98` 清出 `deco-stern`）：
  - `ensign`（`textures/ensign.png` `32×20`, `kind=flag, flag=ensign, nation=ming`）。
  - `pennant`（`textures/pennant.png` `40×6`, `kind=flag, flag=pennant, mast=main, nation=ming`）。
- **帆裝三段各張表**（`Ship_Rigging` §9.1）：
  | 段數 | 狀態 | 張開的帆 | 備註 |
  |---|---|---|---|
  | `0` | 全收（All furled） | （無） | — |
  | `1` | 收帆（Reef） | `main-junk` | 主帆居中平衡，供慢速迴轉／收帆應戰 |
  | `2` | 戰鬥帆（Battle） | `main-junk`＋`fore-junk` | AI 接戰雙帆全張 |
  | `3` | 滿帆（Full） | `main-junk`＋`fore-junk` | 雙桅極速滿帆 |
- **驗證與視圖**：`ropecheck` 98 條 `ends_ok=196`、`ropes_broken=0`、`sails_drawn=4, sails_broken=0`、`link_placed=136,049, link_overlap=0`；已目視檢查 `overlays/stage8_{rig_quarter,rig_side,batten_edge}.png`（確認竹篾與每層篷葉 0 縫緊貼且 `main-stay` 不穿帆面）。🔍

## 露天舷牆砲與佛郎機迴旋砲（步驟 9；2026-11-21）
- **火砲配置（共 `12` 門，`10–14` 門範圍）**：
  - **8 門 4 磅長砲**（複用 `pinnacle-patache-01m-gun-4l`, `0.05 m ⇒ scale 0.5`，掛於 `甲板-main`，`meta kind=gun, gun=4l` 對應 Blockside `guns.long4.code='4l'`，自帶 `muzzle/breech/cascabel/train/trunnion/eye-aft/eye-fwd` 7 個固定點）：分駐 `x=138, 166, 206, 234` 兩舷露天砲門，`back = 1.0..2.0` 格退到零碰撞、砲口伸出船殼 `5.25..6.25` 格（`axis_z=42.25`、`dz=0`、`support=1.0`）。
  - **4 門佛郎機迴旋砲＋4 具叉架座雙生**（複用 `apex-one-reale-01m-gun-pierrier` ＋ `-mount`, `0.05 m ⇒ scale 0.5`，分別掛於 `甲板-poop` `x=86` 與 `甲板-fore` `x=294`，`meta kind=gun, gun=pierrier, mount=turret, arc="-80,80", rate=45` ＋ 雙生 `kind=gunmount, mount_of=gun-N, id=gunmount-N`）：於船殼 `x=75..97` 降切至 `z_rail=60` 與 `x=284..304` 降切至 `z_rail=50`（`carve 1,062` 格＋朱漆護邊 `310` 格），使 `[-80°, 80°]` 全 33 角度掃掠 `sweep_hits=0`、砲口伸出 `7.5` 格、`at_z=61/51` 與甲板 `floor=54/44` 落差僅 `7` 格（確保 `40_crew.js` `z0=b[2]-8` 站位滿編）。
- **結構驗證、對照與視圖**：`DETERMINISTIC = True`、`not_ok=[]`、`gun_gun_clash=[]`、`asymmetric_pairs=[]`；反向對照 `push=砲M-S01:2.0` 檢出 `hit_samples=829`、`swivel_sweep=迴旋砲F-S01:-10` 檢出 `sweep_hits=80,407`；刻完船殼 `stats` `86,436` 格、`components=1`、`cavities=0`、`mirror_diff=0`；整船 `ropecheck` 98 條 `ropes_broken=0`、`models_drawn=42, models_broken=0`、`link_placed=134,987, link_overlap=0`。已目視檢查 `overlays/stage9_{guns_quarter,guns_deck,swivels_poop}.png`。🔍

## 彈藥庫與甲板物件（步驟 10；2026-11-21）
- **底艙艉端彈藥庫**（`kotoko-ganzengchuan-01m-magazine`, `774` 格 `x=111` 銅皮襯壁留中門洞 `y=94..98` 含 `blast=(102,96,15)` 與 `door=(111,96,9)` 固定點；組裝件關聯 `meta kind=magazine, pos=aft, powder_lb=400, hoist=甲板-main/梯子#hold,甲板-poop/梯子#poop,甲板-fore/梯子#fore`）：內掛 **4 具 `basecamp-frigate-constitution-01m-powder-barrel`**（`0.02 m ⇒ scale 0.2`, `kind=powder, powder_lb=100`），確保底艙→三層砲甲板火藥取用連通。
- **門與艙蓋（`kind=door`）**：
  - `貨艙蓋`（`kotoko-ganzengchuan-01m-cargo-hatch`, `30×26×3` @ `0.05 m ⇒ scale 0.5`, `1,334` 格木格柵＋鉸鏈 `hinge-a/b` 沿 `+x` 往上掀）：壓蓋於 `cargo-main` `52/52` 實心圍板上（`open_below=143` 格、`kind=door, open=up, open_deg=100`）。
  - `舵艙門`（複用 `gura-pinas-01m-door`, `scale 0.5,0.6429,0.5313`）：緊貼 `x=112` 隔艙門洞左右各押框 1 格（`y=92..100, z=35..51`, `kind=door, open=side, open_deg=100`）。
- **甲板配備（複用共用組件，全數 `hit_samples=0`、`other_box_overlap=[]`、`support=1.0`）**：
  - `廚房大灶`（`kaguya-gloire-01m-galley ×0.3` 含 `smoke` 固定點，立於左舷主甲板 `152.5,83.5,35` 留出四週走路空間）、`舢舨`（`basecamp-ember-01m-boat ×0.22` 立於前腰中線 `244.5,96.5,35`）、`絞盤`（`basecamp-ember-01m-capstan ×0.14` 立於 `128.5,96.5,35`）、`羅經櫃`（`summit-night-falcon-01m-binnacle ×0.2` 立於 `甲板-poop` `93.5,96.5,54`）、`尾燈-P/S` ×2（`gura-tridente-01m-lantern ×0.3` 分立尾樓金欄兩角 `70.5,76.5/116.5,73`）。
- **驗證與視圖**：`DETERMINISTIC = True`、`shift=舢舨:12` 檢出 `hit_samples=1,666`；整船 `135,761` 格、`link_overlap=0`、`components=1`、`cavities=0`、`models_drawn=54, models_broken=0`、`ropecheck` 98 條 `ends_ok=196`。已目視檢查 `overlays/stage10_{gear_main,magazine_cutaway,poop_door}.png`。🔍

## 舵、舵柄、貓頭錨架與四爪鐵錨（步驟 11；2026-11-21）
- **中式開孔升降舵**（`kotoko-ganzengchuan-01m-rudder`, `2,628` 格、`0.1 m/格`、`tags=sub`）：垂直舵柱 `x=53..55` (`y=95..97, z=2..58`）配鐵箍與紅金舵首、`stock-top` 固定點 `(54,96,58)`，扇面 `x=35..63, z=2..40` 附 5 枚對稱菱形減壓開孔；`components_6=1`、`cavities=0`、`mirror_diff=0`；掛組裝件模型 `舵`（`kind=rudder, turn_axis=hinge, hinge=(54.5,96.5,1), axis=(0,0,1), max_deg=35, spin=rudder, spin_lag=0.3`）。
- **舵孔與舵柄**：依 `Ship_Helm`（1666 中式趕繒船采舵柄操舵，無歐洲舵輪）於 `尾樓陽台欄杆` 開中門（`carve 9` 格 `x=57, y=93..99, z=54..56`，`669` 格保持 `components_6=1`、`cavities=0`）並於 `船殼` 艉封板開舵孔（`carve 60` 格 `x=61..64, y=89..103, z=55..56`，嚴格守在 `"花屁股"` 主徽 `z=58..64` 下方，`86,376` 格保持 `components_6=1`、`cavities=0`）；新建 `kotoko-ganzengchuan-01m-tiller`（`47` 格，含 `spin-a=(54,96,55)` / `spin-b=(54,96,56)`，曲柄踏過 `z=55..57` 止於 `x=78`，避開 `binnacle x=91.7`），掛於 `甲板-poop` 模型 `舵柄`（`kind=tiller, spin=rudder`）。實測 `±35°` 全擺角對船殼／欄杆／甲板 `rudder_sweep_hits=0`、`tiller_sweep_hits=0`。
- **雙舷貓頭錨架與四爪鐵錨**：新建 `kotoko-ganzengchuan-01m-anchor-gear`（`144` 格、`components_6=2`、`cavities=0`、`mirror_diff=0`，關聯 `錨架`），於前腰 `x=279..280` 左右舷牆頂端跨設 `z=51..52` 貓頭架與垂鉤 `z=49`（保留艏甲板中央通路並完全讓開 `bow-eyes` `x=305..310` 與 `迴旋砲F` 掃掠區），下掛 2 具複用 **`kotoko-fusta-01m-anchor-grapnel`**（`scale=0.45`, `pivot=10,10,0`, `at=(279.8, 126.5/66.5, 38)`, `rotate=0,0,±74°`, `kind=anchor, anchor=bower`）；船殼登記 `hawse-S=(282,120,48)`、`hawse-P=(282,72,48)`。
- **驗證與視圖**：`DETERMINISTIC = True`、`anchor_s_hits=0`、`anchor_p_hits=0`；反向探針 `--probe=shift=錨-S:-4` 檢出 `anchor_s_hits=19`；整船 `135,836` 格、`link_overlap=0`、`components=1`、`cavities=0`、`models_drawn=58, models_broken=0`、`ropecheck` `196/196 ok`。已目視檢查 `overlays/stage11_{rudder_stern,anchors_bow,full_quarter}.png`。🔍

## 兩舷輔佐長櫓與渲染方式（步驟 13；2026-11-21）
- **考證與對稱配置**：依明鄭海防考證「趕繒船／櫓配三個」，考量 `Ship_Oars` §9.10 雙舷配平紀律（「左右舷槳數不一樣 ⚠」），於主甲板腰部無火砲／靜索／航衣障礙處設 **雙舷各 2 支＝共 4 支輔佐長櫓**（`x=195.5` 後腰、`x=246.0` 前腰，`y=128.5/64.5` 與 `125.5/67.5`，`z=46.5`）。
- **專用長櫓通用部件**（`kotoko-ganzengchuan-01m-oar`, `5.7 m`、`0.05 m/格 ⇒ scale 0.5`、`size 11,120,60`、`655` 格）：帶雙人搖櫓 T 型曲柄、`pivot=(5,30,49)`、`blade=(5,117,3)`（平水線 `z=23.5` vs `waterline_z=24`）、`seat=(5,12,26)`（精準落於主甲板 `z=35` 站位），`components_6=1`、`cavities=0`、`mirror_x_diff=0`，且作品預設 meta 標 **`render=pole`**（依 `Ship_Render` §8 出低面數長桿網格）。
- **櫓座與前腰櫓槽**：於 `船殼` `x=244..248` 兩舷雕切 `2` 格高 `櫓槽`（`carve 44` 格至 `z=44`，`hull` `86,332` 格保持 `components_6=1`、`cavities=0`、`mirror_diff=0`），使前後兩組櫓樞高一律對齊 `z=46.5`；新建 `kotoko-ganzengchuan-01m-oar-locks`（`16` 格 4 枚櫓栓立於 `x=193`/`243` `櫓座` 關聯旁、`overlap=0`），掛載 4 具模型 `櫓座/oar-{S01,P01,S02,P02}`（左舷 `mirror=y`、`meta kind=oar, rowers=2, side=S|P, stroke_deg=25, dip_deg=12`）。
- **驗證與視圖**：`DETERMINISTIC = True`；靜態與 `±25°` 全擺角掃掠 `total_static_hits=0`、`total_sweep_hits=0`；全船 `8` 位操櫓手站柱皆通過 `floor_ok=true`／`head_ok=true`（≥ 1.4 m 淨空）／`mod_ok=true`；反向探針 `--probe=drop=oar-S01:-3` 檢出 `oar-S01 vox_hits=10, sweep_hits=313`；整船 `135,808` 格、`link_overlap=0`、`components=1`、`cavities=0`、`models_drawn=62, models_broken=0`、`ropecheck` `196/196 ok`。已目視檢查 `overlays/stage13_oars_{detail,quarter}.png`（海水平面 `sea_z=24`）。🔍

## 給遊戲的 Meta、Render 與匯入驗證（步驟 14；2026-11-21）
- **船殼與全局 meta / scale 稽核**：`kotoko-ganzengchuan-01m-assembly` 標題「`福建趕繒船`」，`船殼` 關聯補設 `meta kind=ship, waterline_z=24, id=ship-1`；逐件自動化稽核全 31 件作品（總成＋30 件子作品）均具明確 `meters_per_voxel`（`0.1` 或 `0.05`）與 `tags=["sub"]`，全 62 具模型擺放均明寫 `scale`。
- **`render` 低面數判斷（`Ship_Render` §8／`Ship_Battens` §3）**：
  - `kotoko-ganzengchuan-01m-oar`（雙人輔佐長櫓、`0.05 m`）：截面細長近方桿 ⇒ 作品預設 meta 標 **`render=pole`**。
  - `rudder`（5 枚菱形開孔扁舵）、`tiller`（兩段折曲舵柄）、`anchor-grapnel`（四爪彎爪錨）、`4l`/`pierrier`（砲身與砲架）、`cargo-hatch`（格柵蓋）：彎折、分岔、開孔或多部件組合，依 `Ship_Render` §8 **不標** `render=pole/lathe/wheel`；竹篾 `batten-fore`/`batten-main` 已屬極簡單格竹竿、火藥桶已沿用憲法號 `render=lathe`。
- **`ropecheck`、`vxk` 匯出與 Blockside 隔離 worktree 匯入**：
  - `ropecheck`：`98` 條繩 `ends_ok = 196`（`bind=0, snap=0, odd=0, manual=0, broken=0`）。
  - 隔離 worktree：`D:/Unity/Valhalla/scratchpad/kotoko-1314-blockside`（分支 `kotoko/1314-ganzengchuan`，自 `dev` `bbddbe4` 開出，未動共用工作區）。
  - 執行 `admin.py import --id ganzengchuan --only` → `admin.py ids --id ganzengchuan`（全 80 件發配穩定 ID，`ladders-1..3`）→ 更新 `彈藥庫 hoist="ladders-1#hold,ladders-3#poop,ladders-2#fore"` → `metasync` → 重建（`還原驗算：1 艘、46 份網格三角形與 _cache 逐位元組相同`、`ropebind` `照外框猜 0 端、不靠 0 端`）。
  - **`shipcheck`（`reports/shipcheck_ganzengchuan.md`）**：**`✗ 0　⚠ 0`**（`✓ 沒有發現問題`；`fore-junk` 竹篾 `7/7` 綁 `231` 點、`main-junk` 竹篾 `9/9` 綁 `369` 點、桿距列最遠 `0.05` 格；砲 `12/12` 滿編且全走得到彈藥庫最遠 `8.2 m`；舵令 100%；槳 `4` 支 2P/2S 槳手 `8/8`；廚房 `1` 座 `3` 面 ✓；門艙蓋 `143/112` 格；超載 `+272` 噸 / `+2.10 m`）。
  - **`ladcheck`（`reports/ladcheck_ganzengchuan.md`）**：`3` 座梯子 **`✗ 0、⚠ 0、✓ 3`**，4 層甲板 `64.8 / 76.7 / 9.9 / 19.4 m²` 全連通 **`✗ 0、⚠ 0`**；`disp`：`空載 100.5 / 標準 143 / 滿載 188 噸（載重 45 t，24%）`。

## 交船檢查表、高度基準與 Checksum 對帳（步驟 15；2026-11-21）
- **元件複用與新建清單（`Ship_Game §10`）**：
  - **直接複用**：`kiara-tunis-sandal-01m-fender` ×4、`pinnacle-patache-01m-gun-4l` ×8、`apex-one-reale-01m-gun-pierrier` ×4 ＋ `-mount` ×4、`basecamp-frigate-constitution-01m-powder-barrel` ×4、`gura-pinas-01m-door` ×1、`kaguya-gloire-01m-galley` ×1、`basecamp-ember-01m-boat` ×1、`basecamp-ember-01m-capstan` ×1、`summit-night-falcon-01m-binnacle` ×1、`gura-tridente-01m-lantern` ×2、`kotoko-fusta-01m-anchor-grapnel` ×2（共 **35** 具複用組件）。
  - **新建專用元件（與理由）**：`deco-bow` / `deco-stern`（明鄭龍獅艏飾與翔龍彩牌獨特外型）、`cargo-hatch`（依 `28×24` 格實心圍板定制上掀格柵）、`batten-fore` / `batten-main` ＋ 4 根 `yard-*`（趕繒雙桅 `roach=0.05,0.16` 扇形竹篾長度無法直接沿用他船）、`rudder` / `tiller`（5 開孔中式升降舵與兩段折曲舵柄配尾樓舵孔）、`oar`（`5.7 m` 雙人搖彎柄輔佐長櫓，既有共用槳 `seat` 高度不符 `35` 主甲板）。
- **給遊戲側 `geo` / `cfg` / `crew` 的實測高度基準（單位：voxel = `0.1 m`）**：
  - 船殼外框：`X = 60..323`（`LOA = 26.4 m`）、`Y = 63..129`（`Beam = 6.7 m`, `CY = 96.5`）、`Z = 0..69`（含帆桅最高 `z = 234`）；設計水線 **`waterline_z = 24`**（`2.4 m`）。
  - 各層甲板 `floor`：`底艙 hold = 9`、`主甲板 main = 35`、`艏平台 fore = 44`、`尾樓 poop = 54`。
  - 砲口軸線 `muzzle.z`：主甲板 8 門 `4l = 42.25`、艏迴旋砲 2 門 `pierrier = 55.75`、艉迴旋砲 2 門 `pierrier = 65.75`。
  - 雙桅高度：`頭桅 fore` `cap=172.5, top=174.5`、`fore-junk` 峰頂 `175.98`；`大桅 main` `cap=232.5, top=234.5`、`main-junk` 峰頂 `236.4`（帆裝 3 段：`0` 全收、`1` 收帆張 `main-junk`、`2/3` 戰鬥／滿帆雙桅全張）。
  - 實測通過 `shipcheck ✗ 0 ⚠ 0` 之遊戲設定參照（已存 `design/out/handover/ganzengchuan.json`）：
    - `"cfg": {"base": 3.5, "agile": 2.4, "upwind": 2.1, "pump": 4}`、`"cargoT": 45`
    - `"geo": {"spar": [34, 56], "marines": [45, 55], "marineY": 10, "qx": 5, "center": 48, "aim": 40, "aimZ": [8, 226], "deckAim": [34, 58], "rigAim": [70, 226]}`
    - `"crew": {"officers": 2, "helm": 1, "top": 0, "marines": 6, "marineGap": 14, "monkeys": 2, "navigator": 1, "hands": 12, "carpenter": 1, "sailmaker": 1, "quartermaster": 1, "surgeon": 0}`
- **VXK 與 Checksum 雙邊對帳**：
  - 雕刻匯出：`D:/Unity/Valhalla/Sculpture/exports/kotoko-ganzengchuan-01m-assembly.vxk`（`421,379` bytes、`sha256: 4a3774d90478a5229352523dca430638f8fcec3ca19309adc9eb229a30b8d66d`）。
  - Blockside `_cache`：`D:/Unity/Valhalla/scratchpad/kotoko-1314-blockside/VoxelKit/_cache/ganzengchuan.vxk`（`404,127` bytes）。
  - 兩份 `.vxk` 與 `vxk_compare.py` 對帳結果：**`voxels = 135,808`、`checksum = 3783087331`（`0xe17d54e3`）**、header 20 欄、`98` 條繩、`4` 面帆、`62` 模型（`46` 份網格）、`18` 條關聯全數吻合；交船報告與設定檔另備份於 `design/out/handover/`。🔍

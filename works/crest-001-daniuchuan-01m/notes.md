# 明鄭一號大鳥船／戰座大福船（1666 亞洲船⑤，約 500–650 噸）—— 建造筆記（0.1 m／格）

委託：Tim 2026-11-21「/scp-task 1316 GO」（TASK-1316，開單 pinnacle；傘 TASK-1311 亞洲船⑤）。

## 方向（步驟 1；2026-11-21）
- 依 `Ship_Steps` §2 挑選步驟：保留全部 1–15 步（封閉下層砲甲板做步驟 12 `Ship_Portlids`；銅砲／鐵砲／鐵錨／木殼混合材質做步驟 13 `Ship_Materials`；步驟 9 含 `Ship_Guns`＋`Ship_Turrets` 並依 `Ship_Guns` §2.2 新建紅夷大銅砲／發熕通用部件；硬骨帆大鳥船 junk rig 於步驟 7、8、14 補入 `Ship_Battens`）。

## 座標、比例與作品拆法（步驟 2；2026-11-21）
- **比例**：`meters_per_voxel = 0.1`（1 格 = 0.1 m；船殼 `crest-001-daniuchuan-01m` 與組裝件 `crest-001-daniuchuan-01m-assembly` 皆明記 `meters_per_voxel`）。
- **框與座標軸**：`512 × 256 × 512`（`51.2 × 25.6 × 51.2 m`），`X` 船長朝 `+X`、`Y` 船寬中線 `y = 128`（`y ↔ 256 − y`，P < 128 < S）、`Z` 高度 `z = 0` 為龍骨底面。
- **作品拆法**：
  - 船殼（任務作品）：`crest-001-daniuchuan-01m`「明鄭一號大鳥船 船殼」（`tags=sub`）。
  - 組裝件（主作品）：`crest-001-daniuchuan-01m-assembly`「明鄭一號大鳥船」（無 `sub`；關聯 `船殼` 標 `kind=ship, waterline_z=42`）。
  - 查過 `sub=components` 現有通用元件：複用 `apex-one-reale-01m-gun-pierrier`（＋`-mount`）、`basecamp-frigate-constitution-01m-powder-barrel`、`gura-pinas-01m-door`、`kaguya-gloire-01m-galley`、`basecamp-ember-01m-boat`、`basecamp-ember-01m-capstan`、`summit-night-falcon-01m-binnacle`、`gura-tridente-01m-lantern`、`kotoko-fusta-01m-anchor-grapnel`、`kiara-tunis-sandal-01m-fender`；新建明清專屬通用砲種 `hongyi`、`fagong` 及專用開孔升降舵、舵柄、貨艙蓋、竹篾硬帆等。

## 設計底稿與船殼線形（步驟 3；2026-11-21）
- 考據定案：`design/sources.md`、`design/plan.json`、`design/lines.py`、`design/draft_{lines,layout,ports}.py`。
- 主要尺度：`LOA = 39.9 m`（`x = 56..454`）、最大船寬 `10.1 m`（`2·half_beam + 1 = 101` 格）、吃水線 `z = 42`（設計排水量 `776.83 t`、船殼估算木重 `130.05 t`）、20 道水密隔艙（21 艙）、兩重弦側砲門＋艦艏 2 追擊砲門＋雙層花屁股艉窗。
- 雙趟一致與反證：`draft_lines.py`（`hull_01` 200,000＋`hull_02` 16,758；`components_6=1, cavities=0, mirror_diff=0`；`sheet01` SHA-256 `4bf4ebe8...`）、`draft_layout.py`（全帆面積 `449.7 m²`，`30` 門火砲；`sheet02` SHA-256 `66af329d...`）、`draft_ports.py`（`carve` `3,592`、`paint` `8,336`、`glass` `192`；`sheet03` SHA-256 `acbafe0e...`）；兩趟 SHA-256 完全一致，`half_beam=+3` 與 `skip_port` 探針如期報警。

## 船殼、砲門與塗裝落格（步驟 4；2026-11-21）
- `design/tools/step4_apply.py`（先標記 `船殼:begin`/`end`、`砲門:begin`/`end`）分兩塊貼上 216,758 格船殼、刻除 3,592 格砲門／雙層艉窗、覆寫 8,336 格雙黑護木／朱漆戰棚／白腹綠龍眼／花屁股艉彩。
- `check_hull.py .` 對帳：實存 `213,166`＝應有 `213,166`（缺 `0`、多 `0`、色差 `0`），連通元件 `1`、封閉空腔 `0`、鏡像差 `0`，線形 515 點最大誤差 `0`；反證 `probe_x=264` 報 19 點（最大差 `3`）。
- GPU 預覽圖 `design/overlays/stage4_hull.png`（`213166/213166 voxels`，`yaw=135, pitch=20`）目檢通過：大鳥船尖首平頭鴨嘴、上層朱漆戰棚開砲門／雙黑護木、方艉紅欄綠彩花屁股與雙層大艉窗比例正確。

## 甲板、20 道水密隔艙、梯子與機能艙房（步驟 5；2026-11-21）
- 生成與落格：`design/draft_decks.py` → `design/tools/build_decks.py` 建立 9 件子作品並掛入組裝件（計 377,824 格，`link_overlap=0`、`components=1`、`cavities=0`、`post_cavities=0`）：
  - 四層甲板：`甲板-hold`（`level=0, floor="93:12,420:12", thick=2`，含 20 道帶門洞水密隔艙壁 `x=110..418` 與尖底壓艙底肋填實 37,986 格，共 90,259 格）、`甲板-main`（`level=1, floor="74:48,434:48", thick=2`，30,318 格）、`甲板-upper`（`level=2, floor="66:70,444:70", thick=2`，33,740 格）、`甲板-poop`（`level=3, floor="60:92,132:92", thick=2`，含 `x=132` 斷牆與樓頂護欄，7,027 格）。
  - 五座梯子（共 20 個固定點，全數通過 air/floor/14 格淨高與 `ports_blocked_inside=[]`）：`ladders-main`（`hold` 梯 308 格）、`ladders-upper`（`upper-aft`／`upper-fwd` 412 格）、`ladders-poop`（`poop-S`／`poop-P` 388 格）。
  - 兩間機能艙房（`kind=rooms`）：`upper/1` 後將臺艙房（`min=[102,108,70], max=[131,148,89], door=[132,128,70]`，避開尾桅 `x=96`，隔屏 `x=101` 在 `y=133..141` 留偏心門洞，`room_problems=[]`）與 `hold/1` 中央貨艙間（`min=[259,110,12], max=[275,146,45], door=[258,128,12]`）；`rooms-upper` 偏心門洞造成整船鏡像差 `153` 格屬設計刻意偏移（避開尾桅）。
- 第一人稱回溯驗證（`walkback.py`）：全船 `up=6 down=8` 起點 4 處可達 `89,619`／能回 `89,619`／**走不回來 `0` 格**；嚴格 `up=3` (`0.3 m`) ＋隱藏 `hold` 梯仍可走回 `88,449` 格、**走不回來 `0` 格**。圖紙 `sheet04_decks_v1.png` 與預覽 `design/overlays/stage5_decks.png` 目檢通過。

## 裝飾、雙層戰棚女牆、高尾樓與窗玻璃（步驟 6；2026-11-21）
- 生成與落格：`design/draft_deco.py`（雙趟 SHA-256 一致；反證 `--probe=shift_balcony=+3` 報 296 格衝突）→ `design/tools/build_deco.py`：
  - `艉樓窗玻璃`（`crest-001-daniuchuan-01m-stern-glass`，關聯 `meta={"material":"glass"}`）：於斜艉牆補齊上下階連通格後計 `272` 格（`4` 塊獨立 6 連通整片窗、`overlap=0`）。
  - `艉迴廊`（`crest-001-daniuchuan-01m-stern-balcony`）：`3,358` 格（高尾樓懸挑迴廊＋預留舵柄槽＋高尾樓飛簷冠框＋上戰棚與高尾樓雙層朱漆戰棚女牆與箭窗；`overlap=0, mirror_diff=0`）。
  - 可隱藏裝飾模型（8 件 `meta={"deco":1}`）：新建 0.05 m/voxel `船首飾`（`crest-001-daniuchuan-01m-deco-bow`，2,266 格、鳥喙鳳首雙翼彩繪）與 `船尾飾`（`crest-001-daniuchuan-01m-deco-stern`，2,456 格、朱金雲紋牌匾），另複用 6 具 `kiara-tunis-sandal-01m-fender`（`護舷-S1..S3／P1..P3` 貼於黑護木帶下）。
- 驗收：`stats` 全船 `381,454` 格（`link_overlap=0, components=1, cavities=0, models_drawn=8, models_broken=0`）；比對 `stage6_deco.png`／`stage6_deco_aft.png`（`models=1`）與 `stage6_deco_off.png`（`models=0` 隱藏 8 件裝飾）確認無錯位與遮擋。

## 三桅、硬骨帆桁與實體竹篾（步驟 7；2026-11-21）
- 生成與驗證：`design/draft_masts.py`（雙趟 SHA-256 完全一致；反證 `--probe=shift_mast_fore=-3` 觸發 26 格穿孔衝突、`--probe=short_batten` 檢出最低伸出 `-27.683` 格）→ `design/tools/build_masts.py`：
  - 三根下桅子作品：`前桅`（`crest-001-daniuchuan-01m-mast-fore`，`x=374`, `+5°` 前傾, `heel=12`, 3,116 格）、`主桅`（`crest-001-daniuchuan-01m-mast-main`，`x=246`, `-2°` 後傾, `heel=12`, 7,412 格）、`尾桅`（`crest-001-daniuchuan-01m-mast-mizzen`，`x=96`, `-4°` 後傾, `heel=48`, 1,489 格），均以 `kind=mast, mast=<name>` 關聯至組裝件。
  - 六根 `yard=course` 橫桁（上桁＋下桁皆標 `yard=course`，不用 `boom`）：分別掛入對應桅子作品（`yard-upper`/`yard-lower`，轉軸 `pivot_anchor=pivot, turn_axis=z`；上桁前低後高俯仰 `15°`/`16°`/`15°`）。
  - 22 根實體弧形竹篾（前 7／主 9／尾 6）：共用 3 件 `0.1 m` 竹篾通用模板（`material=bamboo, render=pole`），以 `yard=batten, batten=1..N, material=bamboo` 依 `(0.16, 0.05)` roach 拱腹與收帆雙限縮放，最小突出帆緣 `1.6` 格（≥ 1.5）；三帆包絡縱距 `[25.64, 24.41]` 格（≥ 4）；估算總帆面積 `410.8 m²`（前 `127.5`＋主 `232.8`＋尾 `50.5`）。
- 驗收：`stats` 全船 `393,471` 格（`link_overlap=0, components=1, cavities=0, models_drawn=36, models_broken=0`）；GPU 預覽 `stage7_masts.png` 目檢三桅、帆桁傾角與弧形竹篾間距均準確無穿刺。

## 索具、竹篾硬帆、三段帆裝表與明鄭戰旗（步驟 8；2026-11-21）
- 生成與掛設：`design/tools/rigging_apply.py`：
  - 貼圖：`design/textures/{fore,main,mizzen}-junk-battens.png`（竹蓆接縫與朱漆邊框）、`ensign.png`（明鄭朱底金日「明」字鋸齒大旗）、`pennant.png`（燕尾長幡）。
  - 艉斜旗桿 `旗桿`（`crest-001-daniuchuan-01m-ensign-staff`，`x=31..53, z=107..114`，低於尾帆下桁 `z=116.5` 且在尾帆後方，轉帆零碰撞）。
  - 靜索與橫繩梯組：三桅雙舷 shrouds（前 4×2、大 5×2、尾 3×2）、頂索 `stay-fore-main`／`stay-fore-bow-S/P`（外張繞避前帆）與斜後撐索 `stay-main-aft-S/P`（落於 `bkst-main-S/P` 尾樓斷牆外緣）／`stay-miz-aft-S/P`，另於前／大桅下層綁定 `ratlines`（`climb=1`, `step=4, start=7, stop=14`）。
  - 三面竹篾硬帆（`bind=0,2` 釘於上下 `yard=course` 帆桁，`roach=0.16,0.05`，各自綁齊 `halyard`、`lift-aft/fore`、`sheet-S/P`、`tack-S/P` 且明標 `sail=` 與 `kind=`）：
    - **帆裝三段對照表**：
      | 帆裝段 | 張開之帆（全數通過兩端至少一面對照） | `meta` 關鍵值 |
      |---|---|---|
      | `0` 停帆 | 全收 | — |
      | `1` 收帆 (Reef) | `main-junk` | `mast=main, sail=course, set=1, battens=9, roach=0.16,0.05` |
      | `2` 戰鬥帆 (Battle) | `main-junk` + `fore-junk` | 前帆：`mast=fore, sail=course, set=2, battens=7, roach=0.16,0.05` |
      | `3` 滿帆 (Full) | `main-junk` + `fore-junk` + `mizzen-junk` | 尾帆：`mast=mizzen, sail=course, set=3, battens=6, roach=0.16,0.05` |
  - 旗幟（3 面）：`ensign`（`kind=flag, flag=ensign, nation=mingzheng`, UV 貼圖）、`pennant-main`、`pennant-fore`（`kind=flag, flag=pennant`）。
- 驗收：`ropecheck` 報繩 `82` 條／`164` 端全數通過（`ropes_broken=0`）；`sails` 布料模擬 `6` 面全通過（`sails_drawn=6, sails_broken=0, sail_max_billow=7.08`）；GPU 預覽 `stage8_sails.png`／`stage8_sails_side.png` 目檢飽滿無穿帆。

## 兩重火砲、新建明清通用砲種與砲索砲具（步驟 9；2026-11-21）
- 新建明清專屬通用火砲元件（`tags=sub`, `0.05 m/voxel`, `+Y` 朝砲口, `scale=0.5`, 各自齊備 `muzzle, breech, cascabel, train, trunnion, eye-aft, eye-fwd` 七點與 `components=1, cavities=0, mirror_diff=0`）：
  - `crest-001-daniuchuan-01m-gun-hongyi`（紅夷大銅砲，`15×64×23`，3,990 格，`kind=gun, gun=hongyi`，青銅砲管＋朱漆四輪戰架）。
  - `crest-001-daniuchuan-01m-gun-fagong`（明清發熕，`13×52×21`，2,104 格，`kind=gun, gun=fagong`，熟鐵裹箍長管＋輕戰架）。
- 生成與配置：`design/draft_guns.py`（雙趟 SHA-256 `a3149606...` 一致；反證 `--probe=shift_fwd=+4` 檢出 `max_hits=230, sweep5_hits=477, min_wheel_support=0.411`）＋ `design/tools/build_guns.py`：
  - 先刻除 3 段迴旋砲舷牆淺凹口 2,390 格＋坎緣朱漆 306 格，並重貼 `ch-miz-S/P` 至 `x=100,95,90` 避開缺口。
  - 共掛載 **30 門火砲**（＋6 門座 `-mount`）：`甲板-main` 12 門封閉下層 `hongyi`（`material=bronze`）；`甲板-upper` 2 門艏追擊 `hongyi` ＋ 10 門兩舷 `fagong`（`material=iron`）＋ 2 門艏舷 `pierrier`＋`-mount`；`甲板-poop` 4 門 `pierrier`＋`-mount`（`arc=-80,80, rate=45, material=iron`）。全船 `max_hits=0`, `max_carriage_sweep5_hits=0`, `max_swivel_sweep80_hits=0`, `min_muzzle_out_cells=5.25`, `min_wheel_support=1.0`, `all_swivel_crew_z_ok=True`。
- 砲具與砲索：`design/draft_gunfittings.py` → `design/tools/build_gunfittings.py` 建立 `crest-001-daniuchuan-01m-gunfittings`（`72` 格 `72` 環固定點，`mirror_diff=0, overlap=0`）以 `kind=gunfittings` 掛入組裝件，並為 24 門輪式砲各掛齊 2 breeching＋2 tackle＋1 train ＝ **120 條砲索**。
- 驗收：`ropecheck` 全船 **194 條繩／388 端全數通過**（`ends_ok=388`）；`link_placed=391,176, link_overlap=0`；`models_broken=0`；預覽 `stage9_guns.png`／`stage9_guns_main_cut.png` 目檢雙層火砲與砲索均整齊零穿模。

## 步驟 10：火藥庫、貨艙口蓋與甲板裝備（Ship_Magazine / Ship_Fittings §9.7, §9.13）

- 設計圖與驗證：`design/draft_gear.py`（兩次執行 `spec_sha256` 一致 `951ab25938814b3d1979bb72f4d081eff528978b818dbd57e7c85bdda51a97e9`，出圖 `design/sheet08_gear_v1.png`；反事實探針 `--probe=shift_galley=-24` 檢出 `廚房` 616 格碰撞、`support=0.594`）。
- 落格執行：`design/tools/build_gear.py`：
  - `火藥庫`（`crest-001-daniuchuan-01m-magazine`）：`2,469` 格水線下右舷銅皮隔艙（`x=208..219, y=133..158, z=12..37 < waterline 42`），含門框缺口不擋中線通路，補齊與傾角船殼夾縫 `52` 格，`components=1, cavities=0`；內掛 **16 桶** `basecamp-frigate-constitution-01m-powder-barrel`（`scale=0.2, kind=powder, powder_lb=100`），`barrel_hits=0`。
  - `貨艙口`（`crest-001-daniuchuan-01m-cargo-hatch`，`247` 格，`components=1, cavities=0`，`kind=door, open=up`）與 8 件甲板外部模型（`艙門-尾樓`, `廚房` galley, `小艇` boat, `絞盤` capstan, `羅經櫃` binnacle, `艉燈-S/P`, `艏燈`）：`ext_hits_total=0`，全數 `support=1.0`。
- 驗收：`op=stats structure=1`（`total_voxels=393,645, link_overlap=0, cavities=0`；`-magazine` 與 `-cargo-hatch` 皆 `components=1, cavities=0`），`op=view`（`models_drawn=97, models_broken=0`）目檢 `overlays/stage10_gear.png` 與 `overlays/stage10_mag.png` 無穿模浮空。

## 步驟 11：開孔升降舵、舵柄（tiller）與貓頭四爪錨（Ship_Helm §9.8 / §9.8.1）

- 設計圖與驗證：`design/draft_rudder_anchor.py`（兩次重跑 `spec_sha256` 一致 `6092cce0cb9c1745dfff9390ed2dfe3e730da3b6797b14f081f0e1976a114bef`，出圖 `design/sheet09_rudder_anchor_v1.png`；±35° 舵葉與舵柄掃掠 `rudder_sweep_hits=0, tiller_sweep_hits=0`；反事實探針 `--probe=shift=錨-S:-5` 檢出 `anchor_s_hits=18`）。
- 落格執行：`design/tools/build_rudder_anchor.py`：
  - `carvevox` 於 `船殼` 尾樓開出舵柄穿孔（`95` 格，切後 `components=1, cavities=0, mirror_diff=0`）。
  - `舵`（`crest-001-daniuchuan-01m-rudder`，`5,146` 格 5 菱形泄水開孔升降舵，`stock-top=[48,128,95]`）以 `kind=rudder, turn_axis=hinge, max_deg=35, spin=rudder, spin_k=35, spin_min=-35, spin_max=35, spin_lag=0.3` 掛載組裝件。
  - `舵柄`（`crest-001-daniuchuan-01m-tiller`，`67` 格，`spin-a=[48,128,93], spin-b=[48,128,94]`）以 `kind=tiller`＋同軸 `spin` 掛載於 `甲板-poop`（淨距羅經櫃 `x=82 < 85.3`）。
  - `錨架`（`crest-001-daniuchuan-01m-anchor-gear`，`348` 格，`z_in_bot=70` 實接 `甲板-upper`、`z_beam=82` 實接舷牆頂）以關聯掛入，內掛 2 具 `kotoko-fusta-01m-anchor-grapnel`（`scale=0.65, kind=anchor, anchor=bower, material=iron`）並拉 2 條錨索 `anchor-cable-S/P`（`船殼/hawse-S/P` ↔ `model:錨架/錨-S/P#ring`）。
  - 順手補齊 `旗桿`（`ensign-staff`）9 格 6 連通橋接格（`32` 格）。
- 驗收：`ropecheck` 全船 **196 條繩／392 端全數 ok**（`ends_manual=0`）；`op=stats structure=1` 整組 **393,907 格、`components=1`（全船 1 連通塊）、`cavities=0`、`link_overlap=0`**；`op=view`（`models_drawn=101, models_broken=0, ropes_drawn=196, ropes_broken=0`）目檢 `overlays/stage11_helm.png` 與 `overlays/stage11_bow.png` 清晰無誤。

## 步驟 13：材質稽核（Ship_Materials）

- 由 `op=export format=parts` 稽核全船 19 條關聯與 101 個模型（與來源子作品預設 meta 合併）：
  - `bronze`：14 門紅夷砲 `hongyi`（`甲板-main` 12 ＋ `甲板-upper` 首追擊 2）。
  - `iron`：10 門發貢砲 `fagong` ＋ 6 門佛朗機 `pierrier` ＋ 2 具 `anchor`（`錨-S/P`）。
  - `bamboo`：22 條竹帆肋模型 ＋ 3 件帆肋模板子作品（含 `render=pole`）。
  - `glass`：`艉樓窗玻璃`（`crest-001-daniuchuan-01m-stern-glass`，4 扇獨立 6 連通透空窗）。
  - 其餘船殼（`kind=ship, waterline_z=42`）、甲板、桅桿、帆桁、舵、舵柄、貨艙口與木構預設木質（`wood`）。

## 步驟 12：下層紅夷砲門蓋板（Ship_Portlids §9.12）

- 工具與驗證：`design/tools/portlids.py`（`draft` / `check` / `apply` / 重查），先由 Blockside `admin.py ids` 發給 30 門砲 `gun-1..gun-30`，再自動量取 12 門封閉下層 `甲板-main` 紅夷砲開口：
  - `crest-001-daniuchuan-01m-portlid`（`10×9×2`, `180` 格：外橡木焦油褐 `136`、內朱紅 `192`、鍛鐵鉸鏈板 `104`），`hinge-a=[0,0,0], hinge-b=[9,0,0]`。
  - 掛載 12 片 `砲門蓋-M-1..6-S/P` 於 `甲板-main`（P 舷採 `rotate=0,0,180-rz`，嚴禁 `mirror=y`），`lid_of=gun-*`，`close_deg=95.4..98.1`，`house ∈ {8, 9}`（`house_slack=1.0`）。
  - 驗收：`lids=12, skipped=0, open_hits_ship=0, open_hits_gun=0, closed_hits_gun_housed=0, gun_housed_hits_ship=0, hole_not_covered=[], closed_ship_pct_max=1.3%`；反事實 `house=0` 撞 12 片、`mirror=y` 6 片 P 舷朝上；`applied` 對拍 `anchors_ok=True, models_bad=[], parts_hinge_max_diff=0.0005`；預覽 `overlays/stage12_portlids.png`（`models_drawn=113, models_broken=0`）。

## 步驟 14：給遊戲的 meta、新砲種對拍與 Blockside 匯入驗收（Ship_Game / Ship_Render）

- **Blockside 新通用砲種登錄**（`external/Blockside` 分支 `crest/1316-daniuchuan`）：
  - `src/config/game.json`（`lim` 與 `guns`）、`src/js/04_state.js`（`DMG`）、`src/js/69_prefs.js`（`DMG_Q`／`PREF_Q`）與 `admin.html`（`LIM_NAME`／`DMG_Q`）新增 `hongyi`（`dmghy=85`, `shot=7.2 kg`, `V=172`, `reload=0.95`, `crew=5, min=3, mass=2.0`）與 `fagong`（`dmgfg=38`, `shot=2.5 kg`, `V=165`, `reload=0.72`, `crew=3, min=2, mass=0.9`）；`admin.py parts` 自動登記 `hongyi -> daniuchuan#gun-1` 與 `fagong -> daniuchuan#gun-15`。
  - 反事實基準驗證：改動前後跑無頭 Chrome `?demo=5&dump=1&headless=1&seed=3&ship=ganzengchuan,tungning_trader&prefs=0&cache=0`，戰局 `#dump` SHA-1 皆為 `ac4e49cf98a8232790b7a08a7c7c71178a32f39f`（1,224 bytes）逐位元相同；`daniuchuan,ganzengchuan` 戰局 SHA-1 為 `b9ee9da8b7be72f95167cd6ba94215ecf6de2bbe`（1,226 bytes）。
- **船型設定與高度量測（供 `geo` 與 `disp` 對照）**：
  - `waterline_z = 42`（`4.20 m`）；LOA `36.7 m`；四層甲板地板頂：`hold=12`、`main=48`、`upper=70`、`poop=92`；下層紅夷砲軸 `z ≈ 57`、`upper` 發貢砲軸 `z ≈ 77`、`poop` 佛朗機 `z ≈ 100`；桅頂平台／頂環 `232..300`。
  - `src/config/ships/daniuchuan.json`（`order: 570`）：`cargoT: 165`, `cfg: {speed: 1.25, agile: 1.65, upwind: 1.15, pump: 6}`, `crew` 實配 185 人（含 `officers: 2`, `helm: 2`, `top: 0`, `marines: 18`, `monkeys: 1`, `hands: 36`），尾樓甲板設 `post-officer1`（`80,122,92`）與 `post-officer2`（`80,134,92`）。
- **全套建置與檢查結果**：
  - `admin.py check`：57 艘船、94 滑桿、40 種砲全數合法。
  - `admin.py ids --id daniuchuan`：132 件全數編碼並回寫 Sculpture；`火藥庫` 設 `powder_lb=1600, hoist=ladders-1#hold,ladders-2#upper-fwd,ladders-3#poop-S`；6 座 `gunmount` 綁定 `mount_of=gun-25..30`。
  - `admin.py ropebind --id daniuchuan`：全船 196 條繩 392 端全數明綁（格子 `240`、指定模型 `96`、母繩 `40`、帆桁 `16`，0 靠猜）。
  - `admin.py ancbake`（373 筆）與 `admin.py showlod`（131×67×131 降採樣，模型 49＋裝飾 20 烘入，縮圖已更新 `57/57`）與完整 `admin.py build`（`srccheck` 指紋 `89b8f96353f2d283`、`verify` 2,100 網格三角形與 header 一致）。
  - `admin.py shipcheck --id daniuchuan`：**`✗ 0　⚠ 0`**（30／30 門砲走得到取用點、`0 門缺 0 人`、竹帆肋 `22/22` 距離 `0.05` 格、`舵令 ⇒ 舵柄 ⇒ 舵 100%`、超載極限 `+1,055 t`）。
  - `admin.py ladcheck --id daniuchuan`：**`5 座，✗ 0、⚠ 0；甲板連通 4 層 ✗ 0、⚠ 0`**。
  - `admin.py disp --id daniuchuan`：**空載 `315.4`／標準 `612`／滿載 `777` 噸**（壓艙空間 `461.8 t`、載重 `165 t` 佔 `21%`、固定壓艙 `296 t`），符合目標 500–650 噸級。
  - 重現腳本文件：`design/REPRODUCE.md`。

## 步驟 15：交船檢查表（Ship_Game §10）

- [x] `work sub=ropecheck`：196 條繩／392 端全數 `ok`（bind `0`、snap `0`、manual `0`）。
- [x] 組裝件 `crest-001-daniuchuan-01m-assembly`（明鄭一號大鳥船）、主船殼 `crest-001-daniuchuan-01m`（`tags=sub`）。
- [x] 組裝件與所有子作品均設 `meters_per_voxel=0.1`（新砲種 `0.05 m`、`scale=0.5`），每個模型均明寫 `scale`。
- [x] 開工前已查現有通用元件：沿用 `kiara-tunis-sandal-01m-fender`（護舷 ×6）、`basecamp-frigate-constitution-01m-powder-barrel`（桶 ×16）、`gura-pinas-01m-door`（艙門）、`kaguya-gloire-01m-galley`（廚房）、`basecamp-ember-01m-boat`（小艇）、`basecamp-ember-01m-capstan`（絞盤）、`basecamp-ember-01m-binnacle`（羅經櫃）、`basecamp-frigate-constitution-01m-lantern`（船燈 ×3）、`apex-one-reale-01m-gun-pierrier`／`-mount`（佛朗機 ×6）、`kotoko-fusta-01m-anchor-grapnel`（四爪錨 ×2）；無現有東亞青銅紅夷砲與鐵箍發貢砲故新做 `crest-001-daniuchuan-01m-gun-{hongyi,fagong}`（0.05 m／格、`tags=sub`）＋專用中式開孔舵／舵柄／貨艙口／砲門蓋與 3 種竹帆肋模板。
- [x] `kind=galley`（`廚房`，非 `deco`，四面 `4/4` 站位 ✓）。
- [x] 砲、帆桁（竹帆肋）、火藥桶、舵、舵柄、羅經櫃、絞盤、小艇、燈具皆為帶完整 `meta` 與固定點之外部模型。
- [x] `舵` 為外部模型（`kind=rudder`, `stock-top=[48,128,95]`, `max_deg=35`, `spin=rudder`），`舵柄` 為獨立外部模型（`kind=tiller`, `spin=rudder`, `spin-a/b`），操舵鏈 `100%`。
- [x] `船殼` 關聯標 `kind=ship, waterline_z=42`；所有高度整理於步驟 14；無歐式桅樓故 `top=0`。
- [x] 梯子 `kind=ladders` 5 座（20 錨點），`ladcheck ✗ 0 ⚠ 0`；底艙／主／上／尾樓四層 `kind=deck` 全連通；`rooms-hold`/`upper` 標 `kind=rooms`。
- [x] `ratlines` 為橫繩組（`climb=1` 掛於前／主下桅）；`火藥庫` 內含 16 桶 `kind=powder`（`render=lathe`）且三層砲甲板均由 `hoist` 通達 (`30/30` 門)。
- [x] 材質：`bronze` 14 門紅夷砲、`iron` 10 門發貢＋6 門佛朗機＋2 錨、`bamboo` 22 根竹帆肋、`glass` 272 格艉樓玻璃窗、`oak` 393,635 格；`deco=1` 裝飾 8 件不計重。
- [x] 12 門封閉下層紅夷砲全數配置 `kind=portlid`（`lid_of=gun-*`、`close_deg`、`house=8..9`、`rotate=0,0,180-rz`）。
- [x] 3 面中式硬骨帆（`set=1/2/3`, `roach="0.16,0.05"`, `battens=7/9/6` 誤差 ≤ `0.05` 格）與 3 面旗（`nation=mingzheng`）全數含完整 `meta` 與帆索綁定，`sails_broken=0, ropes_broken=0, models_broken=0`。
- [x] 整組 `components=1`（393,907 格單一 6 連通塊）、`cavities=0`、`link_overlap=0`，雙舷完全鏡像對稱（僅上甲板為避讓尾桅之既有走廊不對稱 153 格）。
- [x] Checksum 與檔案指紋對拍：
  - Sculpture `exports/crest-001-daniuchuan-01m-assembly.vxk`：`560,034` bytes，SHA-256 `98386439be0aa6a3687d0c691413484e453d7c8e27c75d9e3193cbf36591f221`（voxel checksum `83987995`）。
  - Blockside `VoxelKit/_cache/daniuchuan.vxk`（含 `ropebind` 196 條繩端綁定檔頭）：`538,012` bytes，SHA-256 `d1c3aea54019ad86297d5dd51c1ca2ee878b5bb1f5bea3e4c20724972f84861d`，`lock` 指紋 `c:b63315775c`；與拆檔成品 `ships/ship-daniuchuan.js` 經 `admin.py verify` 與 `admin.py cache` 逐格逐三角形驗證一致。

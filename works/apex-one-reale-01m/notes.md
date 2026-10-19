# 皇家號 La Réale（1694）—— 法國皇家旗艦槳帆船（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-18（TASK-0694 傘）：「那妳找一艘經典的有火炮的獎帆船來建造吧 參考裡歷史資料與圖紙 最後由妳繪製圖紙並建造(資訊不足的部分由妳設計) GO」「獎的部分可以先不做 等獎動力系統確認規格再加」；開工後補一句「可以加炮種」。
範圍（遊戲用，Blockside）：外部完整；內部只做遊戲用得到的構造。槳、槳手、`kind=oar` 等 TASK-0691 定規格再加 —— 槳座、划手座照做。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 座標約定
- 船殼 720×321×140、組裝件 720×321×460；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 160 格**，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（船殼與組裝件的書卡都記了）。1 pied de roi ＝ 0.3248 m ＝ 3.248 格。

## 為什麼是 La Réale、資料怎麼拼
- 史料讀數與看過的圖：`references/research_galley_2026-10-18.md`。
- **主尺寸是 Réale 本身的**（Demerliac 經 threedecks）：兩柱間 175'7"、龍骨 148'、寬 23'10"、艙深 7'2"；32 對槳、每槳 7 人；1×36、2×8、2×6 磅＋14 門迴旋砲；船尾 3 盞燈。
- **細部只有普通槳帆船有**（1691 手冊、Marseille 1685 手稿；經 Fourquin & Rigaud 詞彙表轉引，⚠ 沒逐頁讀原書）⇒ 照主尺寸放大：長 ×1.22、寬 ×1.32。plan.json 每個數字的 `src` 寫明是史料、換算還是設計決定。
- 外觀照 Musée national de la Marine 的模型（普通船殼「armée en Réale」）：船殼深藍近黑、水線下白、船尾鍍金、紅色船尾篷。

## 階段一 新圖紙 01＋船殼落格（2026-10-18，TASK-0695）
設計 `design/plan.json`（lines、waterline、hull_build）；程式：
- `lines.py`：線形 ⇒ 每個 (x, z) 的半寬（結構照收穫號：船中剖面 × 長度方向收縮）。船中剖面平底（半寬 22 ＝ 1691 底肋 10½ pi × 1.32）＋橢圓圓舭、最寬在甲板邊；中段 32%–66% 平行；艏柱一段圓弧（跟龍骨相切、經過艏柱頂）、艉柱往上往後彎到頂上直立；舷頂船中 z 25、船尾抬 10、船頭抬 5。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`verify_lines.json`、`masks/hull/hull_01.vox.txt`。船殼 ＝ 線形實心往裡留 3 格牆；舷頂以上多算 40 層再量距離；兩柱在舷頂以上那一段 5 格厚、龍骨寬。
  色：外面那一層水線下（z ≤ 19）白 218、以上深藍 37；牆裡 141；舷頂最上一格金 244、舷頂下 4 格一條金線。

| 項目 | 讀數（從清單的格子量） | 史料 |
|---|---|---|
| 兩柱間（艏柱頂最前 x 639、艉柱頂最後 x 70） | 570 格 ＝ 57.0 m | 175'7" ＝ 57.03 m（TD） |
| 龍骨直段 | x 104–585 ＝ 481 格 ＝ 48.1 m（設計） | 148' ＝ 48.07 m（TD） |
| z 0 那一層的長 | 48.9 m（多的是艏柱圓弧貼地的那一段） | — |
| 最寬（含外板） | 77 格 ＝ 7.7 m | 23'10" ＝ 7.74 m（TD） |
| 龍骨底到甲板邊（船中） | 2.6 m | 艙深 2.33 m ＋ 龍骨（TD） |
| 設計水線／吃水 | z 19 ／ 2.0 m | 普通船約 1.8 m（Briais，二手） |
| 乾舷（船中甲板邊） | 0.6 m | 普通船約 0.7 m（Briais，二手） |
| 水線長 | 54.5 m | — |
| 排水量（水線下實心 × 1.025） | 419 t | 沒找到 |
| 船殼格數 | 151,152（白 43k、深藍 8k、金 4.6k、牆裡 95k） | — |

- 🩸 v1 圓舭指數 2.4 ⇒ 剖面太方（側邊從 z 10 起幾乎直立），跟 1913 年那張 Réale 橫剖面的圓弧不像 ⇒ 改 2.0（橢圓）；排水量 433 → 419 t。
- 落格：標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py`（1 刀，placed 151,152 ＝ 清單）→ `船殼:end`。
- **結果帳**（`design/tools/check_hull.py`，作品從 `export format=list links=none mark=船殼:end` 讀）：作品 151,152 ＝ 設計 151,152，缺 0、多 0、色差 0。
- **結構**（引擎 `stats structure=1 mirror=y:160`）：1 元件、封閉空腔 0、鏡像差 0／0／0。
- **線形對照**：右舷外緣（每個 (x, z) 最大的 dy）vs `lines.hb` 取 floor，x 100–620 每 20、z 4–24 每 4，159 點、差 0。
  **反向對照**：`check_hull.py --probe=half_beam=3`（線形那一側 +3、作品不動）⇒ 159 點中 110 點報差、最大 3（其餘 49 點在兩頭：收縮 × 3 再取整，差 0–2）。
- **組裝件** `apex-one-reale-01m-assembly`「皇家號」：0.1 m、720×321×460（parent 船殼，沒標 sub ＝ 主作品）；關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=19`。船殼標 `tags=sub`、名稱「皇家號 船殼」。
- 過程圖：`overlays/stage1_hull_{bowq,sternq,side}.png`。
- ⚠ 看得到的：船殼是一隻空殼（甲板、中央走道、划手座、槳架、船頭砲台、船尾在階段二）；兩柱頂是細細一根（撞角、船尾翹尾與雕飾在階段二）。

## 階段二 甲板以上的構造（2026-10-18，TASK-0698）
設計 plan.json `layout`；產生 `design/draft_upper.py`（讀船殼清單 ＝ 作品，階段一證過）⇒ `masks/upper/<件>.vox.txt`、`masks/paint/stern.vox.txt`、`ladder_points.json`、`lanterns.json`、`verify_upper.json`、`sheet02_layout_v1.png`；落格 `design/tools/build_upper.py`，之後的修正 `design/tools/delta_apply.py`（作品對清單：多的帶顏色守門刻、少的貼、顏色不同的換）。
每件子作品用整船的框（720×321×140、0.1 m、parent 船殼、tags sub、at 0,0,0），兩舷照 |dy| 產 ⇒ 逐格對稱。重疊的處理：船殼 ＞ 甲板 ＞ 槳架 ＞ 砲台 ＞ 撞角 ＞ 船尾 ＞ 梯子（後面的扣掉前面已經有的格）。

| 件（關聯名） | 內容 | 格數 |
|---|---|---|
| `-deck-main`（甲板-main） | 甲板（2 層板＋每 8 格一根橫樑、拱照當地半寬縮）；中央走道 coursier（x 150–550、13 寬、高 0.9 m，兩頭各兩級台階）；**每舷 32 張划手座**（間距 12.52 格 ＝ 1.252 m，第一張離艉柱頂 8.7 m；紅絨座墊、兩根柱、座後 6 格一根水平腳踏）；espale 中線往艙底的艙口（8×9）＋圍欄 | 149,584 |
| `-apostis`（舷外槳架） | 縱樑（\|dy\| 56–58、深藍＋金頂）、舷外走道（\|dy\| 50–55）、兩頭橫樑 joug（躺在甲板上、外端立到縱樑）、每兩張座之間一個彎托架 bacalat、每張座一根槳座 tolet | 29,182 |
| `-rambade`（甲板-rambade） | 船頭砲台：中央走道兩旁兩座平台（\|dy\| 8 到外緣，外緣 56 收到 26）、頂 z 44（甲板上淨空 14 格）、外緣與船頭那邊 1.4 m 胸牆（金頂）、柱；底下船殼外的角落平台 conilles（頂齊舷頂，放外側的砲） | 11,162 |
| `-ladders-rambade`（甲板-rambade/梯子，meta kind=ladders） | 兩座梯子 ram-P／ram-S（甲板 → 砲台），固定點 foot／lo／hi／head | 188 |
| `-eperon`（撞角） | x 626–686，往上翹（z 33 → 40）、7 → 3 高、5 → 3 寬；上緣與最後 6 格金；尖端金球；一根斜撐回艏柱 | 1,540 |
| `-stern`（船尾） | 紅絨船尾篷（x 78–138，脊比甲板中線高 2.1 m、篷邊比舷頂高 0.9 m，金拱肋每 12 格、金百合點、金流蘇）＋篷柱；船尾金欄杆；三根燈桿＋**三盞船尾燈**（模型 `lantern-P／C／S`，沿用 `gura-tridente-01m-lantern`、scale 0.5、meta kind=light）；金色翹尾（中線的 Catmull-Rom 曲線、半徑 2.6 → 1.4） | 6,100 |
| 船殼塗裝（標記 `船尾塗裝`） | x ≤ 150、水線上 2 格到舷頂下 1 格的外板：藍 42 底、金 244 菱格與花、上下金框（只換色） | 1,418 |

- 🩸 v1 組起來 **65 個元件**：腳踏照甲板拱走，每一階只靠邊相接 ⇒ 每舷 32 根各斷出一段 4 格（64 小塊）。改成一根水平的桿（z ＝ 中線甲板 ＋ 3），用 delta 刻 1,648／補 1,580。
- 🩸 v1 有一個 **441,314 格的封閉空腔**：甲板把整個艙底封死了 ⇒ espale 中線開艙口（之後彈藥庫的梯子從這裡下去）。
- **甲板 meta**（§9.3）：⚠ 沒用 Blockside `decks.py` —— 它取「每一柱最高的實心 ＋ 1」，這層甲板上最高的是划手座與中央走道，會量成座的高度。改照設計算（`design/decks_meta.tsv`）：`甲板-main` kind=deck、deck=main、level 0、name 甲板（couverte）、floor ＝ 中線旁 10 格的甲板面 ＋ 1（x 73–620，船中 z 27）、thick 4；`甲板-rambade` level 1、floor 556:45,606:45、thick 2。
- **結果帳**（`design/tools/check_upper.py`，每件從匯出讀）：船殼（＋塗裝）與 6 件子作品全部缺 0、多 0、色差 0；作品那側兩兩重疊 0。
- **組起來**（引擎 `stats structure=1 mirror=y:160`，組裝件）：348,908 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 `export format=parts`，遊戲讀的那一份）：8 點跟設計差 0、那一格空、腳下實心。
- **反向對照**：`draft_upper.py --probe=drop_bench=5` ⇒ 每舷 31 張（甲板 149,584 → 148,990 格）。
- 讀數：划手座每舷 32、平均間距 12.516 格（史料 1.252 m）；舷外槳架全寬 11.7 m；砲台底 z 43。
- 過程圖：`design/sheet02_layout_v1.png`、`overlays/stage2_{bowq,sternq,side,top,stern_close,bow_close}.png`（bow_close 用 `models=0`：region 不裁模型，框會被船尾燈拉走）。
- ⚠ 看得到的／還沒做：沒有桅（階段三）；砲台底下是空的（砲在階段四）；艙底沒有地板與梯子（彈藥庫在階段五）；舷側登船梯、船尾篷兩側的長椅沒做。

## 階段三 桅、三角帆桁、三角帆、靜索、旗（2026-10-18，TASK-0701）
設計 plan.json `rig`；產生 `design/draft_masts.py`（讀船殼與階段二清單 ＝ 作品）⇒ `masks/masts/{main,fore,deck_holes}.vox.txt`、`masks/yards/{main,fore}.vox.txt`、`yards.json`、`rig_plan.json`、`textures/{ensign,pennant}.png`、`verify_masts.json`、`sheet03_rig_v1.png`；落格 `design/tools/build_rig.py`。

- **桅**（每根一件子作品，整船的框 720×321×460，關聯 `主桅`／`前桅`）：圓桿從船底往上（跟船殼重疊的格不放 ⇒ 坐在船殼上）、往前傾、頂上 9 格粗一格的 calcet（滑輪箱）、最頂兩格金。
  - 主桅：甲板處 x 401.8、中線、傾 4°、頂 z 259（25.9 m；史料 28 goues ＝ 21.1 m × 1.22）、半徑 2.5 → 1.5（根部徑 0.50 m，MsA）。
  - 前桅：甲板處 x 553.0、**偏左舷 5 格**、傾 8°、頂 z 204（20.4 m；22 goues × 1.22）、半徑 2 → 1.2。史料「靠 bitts、略偏中線」（Br）—— 讓開中線的 36 磅主砲；只偏 0.5 m 是因為遊戲找桅只數中線 ±4 格（`10_ship.js` findMasts），偏更多會找不到。
  - **桅孔**：桅穿過甲板-main（甲板板、橫樑、中央走道、前端台階）的 301 格 ⇒ 從甲板刻掉（carvevox 帶顏色守門，標記 `桅孔`），由桅填滿。
- **三角帆桁**（每根一件緊框的子作品，固定點 pivot／fore／peak；外部模型放在各自的桅子作品裡，rotate 0、scale 1、在桅的**左舷側**）：
  | 帆桁 | 長 | 傾角 | 吊點（離前端） | 前端（世界） | 頂（世界） |
  |---|---|---|---|---|---|
  | 主（yard-main） | 41.0 m | 35° | 40% | (551, 155, 154) | (215, 155, 389) |
  | 前（yard-fore） | 33.0 m | 35° | 45% | (697, 150, 108) | (427, 150, 297) |
  - meta `kind=yard、mast、yard=gaff、rig=lateen、sail、length_m、pivot_anchor=pivot、turn_axis=z、rotate_z_deg=0`（收穫號的 lateen 標法，ame 2026-10-15 確認遊戲照 gaff 往下風擺）。中段粗（兩段綁成，徑 0.36 m）、綁的地方金箍。
  - 🩸 主帆桁吊點先照前帆桁的 45% ⇒ 前端剛好撞進前桅（兩根都在左舷 dy −5）⇒ 改 40%，前端停在前桅後 20 格。
- **帆**（`work sub=sail`，組裝件）：`main-lateen`、`fore-lateen` 三角帆（前緣 bind 在帆桁 fore → peak、帆腳角 clew 自由、兩舷帆腳索綁槳架縱樑、tack 綁中央走道前端／撞角尖）；帆形照 1691 grand trinquet 的比例、帆腳角拉到甲板上 3.5 m：主帆前緣 41.0／後緣 33.6／帆腳 23.5 m、前帆 33.0／24.7／17.0 m。
  旗：`main-pennant`、`fore-pennant`（桅頂、8 m 紅底金百合，Deb）、`ensign`（主帆桁頂、3.6 × 2.4 m 白底金百合 ＝ 王旗，MnM img_0270；貼圖 `textures/`）。預設風 4.5,−1.5,0、3 秒（`sub=wind`）。
- **靜索**：每舷主桅 3、前桅 2 條（sartie），從桅頂下的 hound 綁到槳架縱樑（避開槳座）。⚠ 沒有 ratlines —— 地中海三角帆船爬的是帆桁，不是繩梯；遊戲要不要桅頂水手的通道，交船檢查時看匯入檢查。
- **meta**（§9.1）：帆 5／5（sail ×2 `sail=gaff`、flag ×3）、帆自己的繩 6（sheet ×4、tack ×2）、shroud ×10（kind=shroud）。
- 讀數（`design/tools/check_rig.py`）：
  - **結果帳**：兩根桅、兩根帆桁缺 0、多 0、色差 0；甲板-main ＝ 階段二清單 − 桅孔 301 ＝ 149,283，缺 0、多 0、色差 0。
  - CLI：繩 16、ropes_broken 0；帆 5、sails_broken 0（預設風下最大鼓 42 格）；兩件桅子作品 models_broken 0。
  - 帆桁掃過的格、帆面（三角形取樣）撞到別的實心：兩根都 0。**反向對照**：`draft_masts.py --probe=yard_z=main:-140`（主帆桁整根往下 14 m）⇒ 主帆桁 47 格、帆面 62 點；前帆桁照樣 0。
  - **組起來**：353,709 格、1 元件、空腔 0；鏡像差：左舷有右舷空 1,628、顏色不同 41 對 —— **全是偏左舷的前桅**（前桅 1,713 格；顏色不同的是右舷那一側還留著的甲板與台階），照實報、不修。
- 過程圖：`design/sheet03_rig_v1.png`、`overlays/stage3_{full,side,sternq,portq}.png`。

## 階段四 砲（2026-10-18，TASK-0702；砲種 TASK-0703）
設計 plan.json `guns`；產生 `design/draft_guns.py`（讀船殼、階段二、階段三的清單 ＝ 作品；砲元件從 CLI 匯出）⇒ `masks/guns/pierrier.vox.txt`、`guns_placement.json`、`verify_guns.json`、`sheet04_guns_v1.png`；落格 `design/tools/build_guns.py`。

- **先改兩處讓出主砲的射線**（設計決定，照實記）：中線 36 磅的砲軸在 z 40，v1 的艏柱頂 z 45、撞角 z 33–40 都擋在砲口前 —— 等於對自己的船頭開火。Barras 1697 圖的船頭沒有高起的艏柱、撞角從甲板高度往前上翹 ⇒
  - 艏柱露出舷頂的那一段只到 z 34（plan `hull_build.stem_post_top_z`；線形的圓弧照 stem_head_z 45 算、不動）：船殼刻 275 格（標記 `艏柱降低`）。⚠ 兩柱間的讀數因此 57.0 → **56.6 m**（量的是艏柱頂那一層最前面；線形本身照 57.0 設計）。
  - 撞角整根往下（z 33→28、40→34）：delta 刻 1,200／補 1,062／換色 124；前帆的 tack 固定點跟著搬到新的尖端（`撞角/tack-fore` 690,160,35，overwrite）。
- **船頭 5 門**（外部模型、掛在 `-deck-main`，路徑 `甲板-main/gun-…`；全部朝前 rotate z −90，靠轉船瞄準）：
  | 砲 | 元件（沿用） | scale | 位置（pivot 落點） | 砲口 | meta |
  |---|---|---|---|---|---|
  | gun-36（中線） | 餘燼號 32 磅長砲 `basecamp-ember-01m-gun-long32` | 0.52（＝ 0.5 × (36/32)^⅓） | (574.9, 160.5, 29) | (609.0, 160.5, 40.7) | `gun=36l` |
  | gun-8-P／S（dy ±14） | 風暴角號 6 磅砲 `summit-stormkaap-01m-gun-6l` | 0.55（× (8/6)^⅓） | (580.6, 160.5 ± 14, 29) | x 610.0、z 36.4 | `gun=8l` |
  | gun-6-P／S（dy ±29，角落平台上） | 同上 | 0.5 | (573.3, 160.5 ± 29, 29) | x 600.0、z 35.8 | `gun=6l` |
  擺法：從砲口目標位置開始，先往上抬、不行再往船尾退，直到模型每一格的格心＋八個角都不落在船的實心格（36 磅退 3 格、6 磅退 2 格）。
- **14 門迴旋砲 pierrier**（新元件 `apex-one-reale-01m-gun-pierrier`，0.05 m、11×38×13、662 格：叉架上的後膛砲，砲管鐵 73、叉架黑 36；固定點 muzzle（內膛空格）／breech／cascabel／pivot（插銷底）；沒有現成的迴旋砲可用 —— `sub=components` 只有固定砲）：
  兩舷各 5 門站在槳架縱樑上（x 145、226、326、426、514 —— 兩張划手座正中間，避開槳座），朝舷外；船頭 4 門站在砲台前緣胸牆的金頂上（dy ±12、±22），朝前。scale 0.5；meta `kind=gun、gun=pierrier、mount=turret、arc=-80,80、rate=45`。
- **砲種**：Tim「可以加炮種」⇒ Blockside 砲種表加 `36l`／`8l`／`pierrier`（TASK-0703，Blockside 那側）；之前遊戲裡沒有 36 磅與 8 磅。
- 讀數（`draft_guns.py`，設計那側；模型的擺法 ＝ 作品裡那一份）：19 門 碰撞 0、射線（砲口往砲軸方向 40 格；迴旋砲 20 格）碰到自己船的實心 0；迴旋砲腳下實心 14／14。三件掛砲的子作品 models_broken 0。
  **反向對照**：`--probe=push=gun-8-S:+10`（往船頭推 10 格）⇒ 只有那門報碰撞 16 格；`--probe=push=pierrier-326-S:2`（往下沉 2 格進欄杆）⇒ 只有那門報 36 格。
- 過程圖：`design/sheet04_guns_v1.png`、`overlays/stage4_{bow,side_pierrier}.png`。
- ⚠ 沒做：砲索、砲具（breeching、tackle —— 槳帆船的船頭砲沿滑軌後座，跟舷側砲的繩法不一樣）；36 磅的滑軌（中央走道裡的 35 pi 軌道）。
- ⚠ 階段五改過：船頭 4 門迴旋砲 v1 站在砲台胸牆上 ⇒ 匯入檢查 ✗「這一層沒有送藥手」（砲台中線是 36 磅的通道、沒有站位）⇒ 搬到槳架：每舷再加 1 門朝舷外（x 539）＋槳架前端每舷 1 門朝前（x 563），總數照舊 14。

## 階段五 舵、艙底與彈藥庫、艙口梯、錨、甲板 meta（2026-10-18，TASK-0704）
設計 plan.json `hold`；產生 `design/draft_hold.py`（讀前四階段的清單 ＝ 作品；模型照 draft_guns 的格心＋八角取樣）⇒ `masks/hold/{rudder,hold,magazine,ladder}.vox.txt`、`hold_placement.json`、`verify_hold.json`；落格 `design/tools/build_hold.py`。

- **舵**（`-rudder`，整船的框；組裝件的外部模型 `舵`，at ＝ pivot ＝ 鉸鏈下端）：舵葉 13 → 5 格寬（TG 3 pi → 1 pi × 1.32）、3 格厚，水線下白、以上深藍；舵頭（stock）到 z 44、頂一格金；**舵柄**從舵頭水平往前到 x 69（貼著艉柱頭）。meta `kind=rudder、hinge (94.5, 160.5, 0)、axis (−0.562, 0, 0.827)、max_deg 35、turn_axis=hinge、spin=rudder ±35`；固定點 `stock-top` (64,160,42)，離船尾船殼 6.3 格（遊戲在 8 格內找掛點）。
  - 鉸鏈一定是直線，可艉柱是彎的（階段一的設計決定）⇒ 取艉柱在 z 25 的切線、往後 1 格當鉸鏈：🩸 先取 z 20 的切線 ⇒ 舵頭離船尾 9.2 格（遊戲找不到掛點）；舵柄頭 v1 伸到 x 71 ⇒ 4 格插進艉柱頭 ⇒ 縮到 69。代價：舵底離龍骨後端約 8 格（彎的艉柱鼓出去的那一段）。
  - **沒有舵輪**：槳帆船是舵柄＋兩條繩（Hob）。造船規格 §9.8.1 要舵輪 —— 照史料不放；遊戲照 meta 轉舵，舵柄是舵模型的一部分、跟著轉。
- **艙底**（`-deck-hold`，關聯 `甲板-hold`）：x 132–182 鋪地板（頂 z 14，2 層）、地板下一路填到船底（壓艙碎石 146；槳帆船壓艙用砂石，Br）⇒ 不封出空腔。頭頂淨空 11–13 格（到甲板橫樑）。
- **彈藥庫**（`-magazine`，關聯 `甲板-hold/彈藥庫`）：x 150–178、半寬 12，銅皮牆 168 從地板到甲板底、門洞 5 格朝船尾（艙口那側）；**25 個火藥桶**（沿用憲法號火藥桶，scale 0.2、meta `kind=powder, powder_lb=100`，5 × 5、兩舷對稱，碰撞 0）。關聯 meta `kind=magazine、pos=aft、powder_lb=2500、hoist=甲板-main/梯子/hold`（火藥從 espale 艙口吊上來）。
  - 史料：火藥艙在船尾艙底（soute，Br 二手）；船尾那一段艙底太淺（地板到橫樑不到 1 m）⇒ 放在 espale 艙口下、往前一點。桶數沒找到 ⇒ 擺得下幾桶算幾桶。
- **艙口梯**（`-ladders-hold`，關聯 `甲板-main/梯子`，meta `kind=ladders`）：艙底 → espale 甲板，4 階、每 3 格；梯名 `hold`，foot (142,160,15)／lo／hi／head (133,160,32)（梯頭站在橫躺在甲板上的 joug 上）。
- **錨**：沿用憲法號的錨 × 0.4、掛在砲台前緣外側兩角（ring z 45、旋轉 ±45°、錨冠 z 23.4 在水線上）；meta `kind=anchor、anchor=bower、hawse`（錨鏈孔 ＝ 船殼在 x 612、z 26 的外緣）。⚠ 槳帆船用的是四爪錨（fer），沒有現成元件。
- **甲板 meta 重排**：`甲板-hold` level 0（艙底（彈藥庫），floor 132:15,182:15、thick 2）、`甲板-main` level 1、`甲板-rambade` level 2。
- **封閉空腔**：階段四撞角改低後，船頭 x 626–628 留下兩個 9 格的空腔（撞角根、甲板、船殼之間）⇒ `draft_upper.py` 最後加一步「≤ 50 格的空腔照鄰居最多的那一件填」（造船規格 §8）⇒ 填進甲板-main（標記 `空腔填實`，18 格）。
- 讀數：
  - **結果帳**：舵 931、艙底 3,830、彈藥庫 1,148、艙口梯 93，缺 0、多 0、色差 0；舵跟船重疊 0。
  - **組起來**：358,385 格、1 元件、空腔 0；鏡像差照舊只有前桅（1,628＋41 對）。models_broken 0（組裝件、彈藥庫、砲台）。
  - 梯子四點那一格空、腳下實心、頭頂 7 格內不擋。**反向對照**：`draft_hold.py --probe=floor=+3`（地板抬 3 格）⇒ 頭頂淨空最小 11 → 8。
  - **匯入檢查**（Blockside 暫存 worktree，帶 TASK-0703 的三種砲；報告 `references/shipcheck_reale_stage5.md`）：**✗ 0　⚠ 17**。⚠ 是：
    ① `geo` 沒填（遊戲那側）；② 船頭 36／8 磅砲班站不滿（3 門缺 4 人：船頭窄，砲擺得很擠）；③ 軍官 0／4、陸戰隊 0／12、桅頂水手 0／8 站不下（槳帆船沒有後甲板、沒有桅頂平台 —— 船員配置要遊戲那側調）；
    ④ **送藥手的走路格不連通**（10 門）：遊戲的走路格只看甲板地板上下 −2～+3 格，而槳帆船的甲板上排滿划手座、中央走道高 0.9 m ⇒ 甲板被切成三十幾塊；史料上人是走中央走道與舷外走道的 ⇒ 該讓中央走道成為走路格（甲板 meta 的 floor、梯子怎麼接層）—— 跟遊戲那側（ame，槳手也在她那張單）對過再做。
- 過程圖：`overlays/stage5_{stern,hold}.png`。

## 階段六 槳＋匯進遊戲（2026-10-18，TASK-0705；砲種 TASK-0703）
Tim：「槳目前可用了 可以嘗試套用看看」「完成槳後就匯入遊戲吧 我實際測試看看」。照造船規格 §9.10（ame）標；做法寫進 §9.10.1（Senate 1d4c3ff）。
設計 plan.json `oars`；產生 `design/draft_oars.py` ⇒ `masks/oars/oar.vox.txt`、`oars_placement.json`、`verify_oars.json`；落格 `design/tools/build_oars.py`。

- **槳元件**（通用部件 `apex-one-reale-01m-oar`「槳（galère，13 m、7 人划；通用部件，0.05 m）」，7×263×61、1,238 格）：往裡 4.4 m、往外 8.6 m（普通船 12.18 m；Réale 每槳 7 人 ⇒ 往裡照 7 × 0.6 m 拉長，設計決定）、槳葉 1.6 × 0.18 m、槳柄徑 0.153 → 0.09 m（Deb）、槳座那一段深色。姿勢「掃到一半」：垂直於船身、往外往下 11°（槳葉中心落在水線）。固定點 pivot (3,88,38)、blade (3,260,5)、seat (5,68,33)。
- **64 支**（`舷外槳架/oar-S01…S32`、`oar-P01…P32`）：每張划手座一支，pivot 落在槳座船尾那一側 x −2、縱樑頂上 0.8 格；右舷原樣、左舷 mirror=y；meta `kind=oar、rowers 7、side、stroke_deg 30、dip_deg 12`。
  - 🩸 v1 x −1 ⇒ 槳柄跟槳座（tolet）重疊（64 支 378 格）⇒ x −2；🩸 第 2 張座的 seat 差一格：座高用了槳的 x 去量 ⇒ 改照座的中心。
- 讀數：碰撞 0、seat 站得住 64／64、槳座旁 8 格有縱樑 64／64、左右 32／32、槳葉中心離水線 −0.2～+1.8 格。models_broken 0（舷外槳架 78 個模型 ＝ 64 槳＋14 迴旋砲）。
  **反向對照**：`--probe=drop_oar=S05` ⇒ 右舷 31 支；`--probe=sink=S05:3` ⇒ 只有那一支報碰撞 42 格。
- **匯進遊戲**（Blockside dev 5ba45d0，已推上測試版）：`admin.py import --id reale`；game.json 照 kaguya 的做法還原後只手寫 reale 一筆：`cfg.base 6`（划槳全速；巡航 4–5、衝刺 6–7 節，Musée）、`geo`（spar 30–46、marines +75／−115、center 60、aim 38、aimZ 20–380、deckAim 28–45、rigAim 120–330）。
  - shipcheck：✗ 0　⚠ 15；槳 64（左 32／右 32）、槳手 448／448；船員 542。⚠：船頭三門砲班站不滿、陸戰隊 7／12、桅頂水手 0／8、送藥手走路格不連通 ×10（同階段五）。
  - `?demo=60&dump=1&seed=3&ship=reale,constitution`：跑得完、航速 6–7.8 節、開 39 砲。對拍（沒有皇家號的戰局）跟 dev 逐位元組相同。
  - 砲種表 36l／8l／pierrier 同一批合進 dev（TASK-0703 結單）。報告存 `references/shipcheck_reale_stage6.md`。
- 過程圖：`overlays/stage6_{full,oars_close}.png`。

## 階段七 艙底分間、中央走道當走路格、三角帆桁擺角（2026-10-18，TASK-0694 傘）
Tim：「可以試著加一些艙室嗎(或是原本就沒有)」「送藥手&其他問題發現的話一起修復」「皇家號 發現浮空纜線」。
設計 plan.json `cabins`（史料 Marteilhe 1757 附錄〈Description d'une galère armée〉）；產生 `design/draft_cabins.py`（讀遊戲匯入的 .vxk ＝ 作品）⇒ `masks/cabins/{cabins,ladders,deck_carve}.vox.txt`、`cabins_placement.json`、`verify_cabins.json`；落格 `design/tools/build_cabins.py`。

- **史料**：艙底六間，船尾到船頭 gavon、escandolat、compagne（酒水、醃肉）、paillot（餅乾、豆）、taverne（船中：賣酒＋收帆與篷；火藥艙從這間進）、chambre de proue（纜繩、外科醫生的箱子；**病人躺這裡**）。艙深船中 7 pieds ≈ 2.27 m —— 作品船中內底 z 3 到甲板底 z 25（2.3 m），對得上，不用挖。艙口「墊高到中央走道的高度」⇒ 每間從中央走道開艙口放梯子。各間長度史料沒有 ⇒ 設計決定；gavon、escandolat 在船尾、艙底太淺 ⇒ 不做。
- **子作品**：`-cabins`（關聯 `甲板-hold/艙房`，meta `kind=rooms`）：每間地板（z 8、|dy| ≤ 16，兩旁留縫通底艙 ⇒ 不封空腔）、五道隔艙壁（最前面那道開門通船頭的艙）；`-ladders-cabins`（關聯 `甲板-main/梯子-艙房`，meta `kind=ladders`）：四座梯子（每 3 格一階、兩邊扶手 dy −6／0；v1 只做靠中線那一根，Tim 2026-10-20 在遊戲裡看到「少一邊扶手」⇒ 補另一邊 120 格：每座 32／32／28／28，跟原本那根逐座同數，甲板裡那一段由艙口邊代替）。甲板-main 刻四個艙口（中央走道左半邊 dy −5～−1，右半邊 7 格照樣走）2,300 格。
- **空艙房**（§9.2）：compagne 5.5 × 3.1、paillot 3.9 × 3.1、taverne 2.9 × 3.1（框碰到主桅腳就停）、proue 5.3 × 3.1，淨空都 1.4 m；門 ＝ 梯腳旁那一格。遊戲預設：proue ＝ 醫療艙、taverne ＝ 工坊；compagne、paillot 空著讓玩家配。
- **甲板 meta**：`甲板-hold` floor 延伸到各間（132:15,182:15,232:9,477:9）；`甲板-main` 加 **`walk`**（遊戲新鍵：走路格照它、判層照 floor）＝ 中央走道頂＋1，兩頭連台階（23 點）。
- **三角帆桁**：遊戲照 `yard=gaff` 往下風擺到 80° ⇒ 主帆桁前端甩出舷外 13 m、tack 從那裡斜拉到中央走道前端（Tim 看到的「浮空纜線」）。帆桁 meta 本來就有 `rig=lateen`、固定點 `fore` ⇒ 遊戲照它限擺角（前端只能左右移 2.5 m：主 10.7°、前 11.9°）。作品不用改。
- 讀數：
  - draft：四間框裡不是空氣的 0、地板洞 0、淨空 1.4 m；梯子 16 點那一格空、腳下實心、頭上 12 格空。**反向對照** `--probe=floor=3` ⇒ 四間淨空 1.1 m、head_ok false。
  - 走路格（照遊戲 navZ／navStep 算）：只照 floor ⇒ 取用點（艙口梯頭）跟船頭砲台底下、中央走道、四座梯頭都不連通；加 walk ⇒ 全部連通。
  - **組起來**：375,166 格、1 元件、空腔 0、關聯重疊 0；鏡像差多了艙口與梯子（只開在左半邊）。
  - **匯入檢查**（Blockside worktree）：✗ 0　⚠ 15 → 7。火藥 0／19 → 5／19 門走得到（8 門走路格量不到）；剩下的 ⚠：舷外槳架的迴旋砲 6 門（145、539、563；槳架不是走道 ⇒ 照直線送）、36 磅砲班 4／5。船員配置 `top 0`（三角帆沒有桅頂平台）、`marines 7`（站得下的數）、`guns long36 5、long8 2`。

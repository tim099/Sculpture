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

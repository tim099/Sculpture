# 杉心號 —— 1666 年前後加勒比海盜的大獨木舟 piragua／periago（0.1 m／格）—— 建造筆記

TASK-1152（主單 TASK-1146）。Tim 2026-11-01「/scp-task 1152 GO」。
船名是設計決定：Dampier 說最好的 periago 是雪松（cedar）挖的、「nothing but the tree itself made hollow」⇒ 杉心號。

## 座標約定（步驟 2）

- 0.1 m／格（Blockside 模擬只吃同一個比例 ⇒ 船殼一定 0.1；0.05 m 的元件當模型縮 0.5 用）。
- X 船長、船頭朝 +X；Y 船寬、中線 y 50；Z 高，z 0 ＝ 船底外面。
- 船殼 `basecamp-piragua-01m`「杉心號 船殼」（tags=sub、任務作品）框 140×101×40；組裝件 `basecamp-piragua-01m-assembly`「杉心號」框 140×101×100（關聯「船殼」at 0,0,0）。兩件都記 meters_per_voxel 0.1。
- 寬 101：船只有 1.8 m 寬，留給舷外的槳（槳是組裝件裡的模型）；長 140：船身 11 m 前後各留約 1.5 m 給舵槳與艏。

## 作品怎麼拆（步驟 2）

| 件 | 是什麼 | 備註 |
|---|---|---|
| 船殼 | 挖空的樹幹：平底、船頭尖、船尾平（transom）、塗裝 | 任務作品 |
| 甲板-main | 船底板（站的地方）、坐板 | 子作品、meta kind=deck |
| 桅、帆桁 | 一到兩根可拆的桅、帆桁一根一件＋外部模型 | 步驟 7 照資料定 |
| 槳、舵槳、錨、迴旋砲 | 外部模型 | 先用現成元件（下表） |

現成元件候選（`sub=components` 2026-11-01 查）：
- 槳：`erina-dromon-01m-oar-upper`（4.7 m，蓬特號用 scale 0.5）、`kotoko-fusta-01m-oar-inner／outer`（7.2／6.6 m，太長）、`apex-one-reale-01m-oar` —— 步驟 13 照船寬挑。
- 錨：`kotoko-fusta-01m-anchor-grapnel` 四爪錨（0.05 m）。
- 迴旋砲：`apex-one-reale-01m-gun-pierrier`、`apex-one-punt-01m-gun-bow` —— 步驟 9 挑。
- 舵槳：蓬特號的 `apex-one-punt-01m-rudder` 是整船的框（綁它自己的舵柱）⇒ 大概要自己做一支，步驟 11 再定。

## 步驟 3 資料與新圖紙 01（`design/plan.json`、`lines.py`、`draft_lines.py` → `sheet01_lines_v1.png`）

- 資料：`references/research_piragua_2026-11-01.md`。研究 agent 先查一輪，**用到的原句 basecamp 都在原文網頁裡自己找到過**（Dampier 第 1、3、5、8 章，Exquemelin 第 V、VII、XVII 章，Ringrose 第 V、VII 章）；agent 說「第 6 章」的 thwarts 那句其實在第 5 章。
- 一手查得到的：全長 36 呎、寬 5–6 呎（Davis 1685）；平底、一頭尖一頭平（periago 跟 canoe 分開就在這）；雪松；底 3 吋、舷 2–1.5 吋；划 14 支槳；坐板、繩環；一面大帆；Perico 1680 periagua 重、划不快。
- 查不到、自己定的（plan.json 每格 `src` 寫「設計決定」）：深 0.8 m、吃水 0.3 m、舷弧、船頭翹、船尾平板寬、帆型（拉丁帆）、桅高、坐板間距、船頭一門迴旋砲。
- 線形：抄蓬特號的 lines.py，拿掉柱、船尾改平板（x 15 那一站就是整片的板）、兩頭各自的收尖寬度。
- 坑：
  - 牆厚用「距離 ≤ 1」剝 ⇒ 舷側一階一階的地方只靠斜角相連，斷成 7 塊。改成 26 鄰居剝一層 ⇒ 1 塊（斜角那幾格多一格）。
  - half_beam 寫 8 只有 15 格寬（舷頂下那一格的格心量不到 |dy| 8）⇒ 8.6。
  - 外面／內面判斷沒補邊 ⇒ z 0 那層算不到底下的船外。
  - 艙底只有 1 格厚、又在水線下 ⇒ 第一次整片塗成焦油色。改成艙底一律內面色。
- 反向對照：half_beam +3 ⇒ 寬 17 → 23；x_fwd −10 ⇒ LOA 110 → 100。重跑逐位元組相同。

## 步驟 4 船殼落格（`masks/hull/hull.vox.txt`、`tools/check_hull.py`）

- 落一刀 3,073 格（placed 3,073）。第一次用的色（外皮 169 偏粉紅、艙底焦油色）是渲圖之後才看到的 ⇒ undo、改色、重落。
- 結果帳：缺 0／多 0／色差 0、1 元件、空腔 0、鏡像差 0。反向對照：清單往上搬 3 格 ⇒ 缺 2,510、多 2,510、色差 455。
- 舷頂以下穿透的針孔 0；側面渲圖那排小黑點是舷側往外張的台階朝下的面（陰影），不是洞。

| 讀數 | 值 |
|---|---|
| LOA | 110 格（x 15–124）＝ 11.0 m（Davis 36 呎） |
| 寬 | 17 格 ＝ 1.7 m（5–6 呎） |
| 舷頂 | 船中 z 8、船頭 z 10；船尾平板寬 11 格 |
| DWL | z 3（吃水 0.3 m，設計決定）；LWL 102、BWL 13 |
| 排水量 | 3.06 t；殼（雪松 0.45 t/m³〔估〕）1.38 t ⇒ 可載 1.68 t ≈ 22 人（實物殼薄，0.1 m 牆比實物厚 2 倍） |
| 艙底 | z 1 能站 678 格 |

## 步驟 5 甲板-main：坐板 7 塊＋船頭平台（`design/draft_deck.py` → `sheet02_deck_v1.png`、`decks_meta.tsv`）

- 露天船只有一層：站的地方是船殼自己的艙底（z 1）；子作品 `basecamp-piragua-01m-deck-main`「杉心號 甲板-main」只有坐板（x 33、42 … 87，各 3 格寬）與船頭平台（x 100–118），全在 z 3、從左舷內面鋪到右舷內面。沒有下層 ⇒ 不做梯子。
- 坐板高度照遊戲走路一步的上限定：板在 z 3、坐面離艙底 0.3 m（3 格）。
- meta（組裝件那條關聯）：`kind=deck deck=main level=0 name=艙底（坐板） thick=1`；floor 照中線艙底量 `16:1,105:1,106:2,111:2,112:3,115:3,116:4,118:4,119:5,120:7`。
- 讀數：269 格、疊船殼 0、跟船殼合起來 1 元件、鏡像差 0、每塊兩頭都貼船殼；組裝件 3,342 格、1 元件；子作品逐格對清單缺 0／多 0／色差 0。
- 走路格（照 navBuild：腳下實心、頭上 1.2 m 空、一步 ≤ 3 格、只收 floor −2～+3）：1 群、9.53 m²。
  - 反向對照：坐板升 1 格（坐面 0.4 m）⇒ 斷成 9 群。
  - 🩸 v1 沒限高度 ⇒ 升了照樣 1 群：人沿著舷側內面一階一階的牆走上舷頂繞過去。遊戲只收 floor −2～+3，所以 v1 的尺比遊戲寬。
- ⚠ 第一人稱與樓梯自檢要匯進遊戲才量得到 ⇒ 步驟 14 一起讀。

## 步驟 7–8 桅、拉丁帆桁、帆、索具、長旗（`design/draft_rig.py` → `sheet03_rig_v1.png`、`yards.json`、`rig_plan.json`；落格 `tools/build_rig.py`）

- 出處：越嶺號的 draft_masts.py／build_rig.py（一根桅、拉丁帆桁）。改的地方：靜索、帆腳索綁舷頂（沒有舷外槳架），tack 綁船頭，只掛一面長旗。
- 桅 `basecamp-piragua-01m-mast`：x 87、穿過第七塊坐板（坐板刻 1 格桅孔）、腳踩艙底、艙底到桅頂 5.0 m、桅頭 3×3×4 格（色 68）。可拆 ⇒ 不做桅座。
- 帆桁 `basecamp-piragua-01m-yard`：8.5 m、45°、吊點離前端 40%、掛在桅的左舷側；外部模型放在桅子作品裡（scale 1、rotate 0）。
  - meta：`kind=yard mast=main yard=gaff rig=lateen sail=lateen`；固定點 pivot／fore／peak。
- 帆 `lateen` 17.6 m²（前緣 1、後緣 0.75、帆腳 0.65）：帆腳角離舷頂 1.1 m、前端離舷頂 1.35 m。meta `kind=sail mast=main sail=gaff set=1`。
- 繩 7 條：靜索每舷 2（hound → 舷頂 x 83、92）、帆腳索兩舷（→ 舷頂 x 50）、tack（帆桁前端 → 船頭 x 122）；帆自己的繩都標了 `kind=sheet／tack sail=lateen`。
- 長旗：暗紅、桅頂；meta `kind=flag flag=pennant`。
- 🩸 v1 照越嶺號的帆比例（0.82／0.575）＋帆桁 35°：帆腳那條邊往後下斜 20°，帆腳角比前端低 1.7 m、落進艙裡（帆面碰撞 1）⇒ 帆桁改 45°、比例改 0.75／0.65、桅加高到 5 m。
- 讀數：帆桁碰撞 0、帆面碰撞 0；ropecheck 7 條／14 端全綁好；觀測 ropes_broken 0、sails_broken 0；組裝件 link_overlap 0。
  - 反向對照：帆桁往下 3 m ⇒ 帆桁碰撞 7、帆面 30。
- 拉丁帆擺角：pivot 到 fore 的水平距離 2.4 m < 遊戲的 2.5 m ⇒ 遊戲的拉丁帆限制在這艘船上不起作用（照 gaff 擺）。⚠ 遊戲裡要看一次會不會甩出舷外。

帆裝三段（Ship_Rigging §9.1）：

| 帆裝 | 張哪幾面 |
|---|---|
| 收帆（1） | lateen |
| 戰鬥帆（2） | lateen |
| 滿帆（3） | lateen |

只有一面帆 ⇒ `set 1`：三段都張，收帆、戰鬥帆都不會一面都沒有。

## 步驟 9 船頭迴旋砲（`design/draft_guns.py` → `guns_placement.json`、`guns_meta.tsv`、`verify_guns.json`）

- 一手出處只有火槍（Ringrose：Perico 那一仗是排槍）⇒ 船頭一門迴旋砲是**設計決定**（Little 2014 經 Wikipedia 轉述 one cannon and four swivel guns，沒核）。
- 用共用件 `apex-one-reale-01m-gun-pierrier`＋拆好的座 `-mount`（6 艘在用）。scale 0.5 ＝ 原尺寸（0.05 m 的件；拉貝爾號那批 0.39 是縮過的）、rotate 0,0,−90（朝前）。
- 兩件模型掛在甲板-main：`迴旋砲-F01`（`kind=gun gun=pierrier deck=main id=gun-1 mount=turret arc=-90,90 rate=45 port=bow`）、`迴旋砲-F01座`（`kind=gunmount id=gunmount-1 mount_of=gun-1`）。座的雙生是自己補的（Ship_Guns §4.2.1）。
- 砲柱：船頭平台上 x 108、z 4–9 一根 1 格的柱（落在甲板-main，6 格）；叉架底擱柱頂 z 10。
- 讀數：
  - 砲膛離站面 1.07 m、高過船頭舷頂 0.53 m；砲口 (117.5, 50.5, 14.75) 在船殼線形外。
  - 碰撞（格心＋八角）砲 0、座 0；轉到 −90／−45／0／45／90 都是 0。
  - 反向對照：整門往下 4 格 ⇒ 砲 10、座 252。
- 🩸 渲圖抓到 tack 從砲管穿過去（v1 綁船頭中線 x 122，離砲管外框 −0.34 格）⇒ 改綁左舷舷頂 x 110（1.18 格）。x 112–118 那幾格舷頂太靠中線，只剩 0.1–0.8 格。tack 的 slack 1.02 ⇒ 短而陡的繩垂 0.8 m ⇒ 改 1.0。
  - ⚠ 迴旋砲轉起來照樣會掃過 tack；遊戲裡繩不算碰撞，留著。

## 步驟 10 彈藥庫與甲板物件（`design/draft_magazine.py` → `magazine_placement.json`、`verify_magazine.json`；落格 `tools/build_magazine.py`）

- 露天船沒有艙房 ⇒ 彈藥庫 `basecamp-piragua-01m-magazine`「杉心號 彈藥庫」＝ 舵手腳前一塊 0.5 × 0.5 m 墊板（x 21–25、z 1，25 格；讓火藥離開艙底積水〔設計決定〕）＋一個火藥桶。
  - 桶引用憲法號的 `basecamp-frigate-constitution-01m-powder-barrel`（scale 0.2、pivot 11,11,0），meta `kind=powder powder_lb=50 id=powder-1`。
  - 固定點：blast (23,50,4)、door (26,50,1)。
  - 關聯「彈藥庫」meta：`kind=magazine pos=aft powder_lb=50 id=magazine-1`；沒有梯子 ⇒ 不寫 hoist。
- 讀數：桶碰撞（格心＋八角）0；反向對照桶往下 1 格 ⇒ 12,748。墊板＋桶的外框當擋路之後，走路格照樣 1 群、9.28 m²（坐板那一步是 9.53）。
- 這艘船沒有的：門與艙蓋（沒有艙口）、廚房（獨木舟上不生火）、小艇（它自己就是小艇）、絞盤、羅經櫃。被打掉怎麼演照預設（帆桁照規格表是 fall）。

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

## 步驟 11 舵槳與錨（`design/draft_helm.py` → `helm_placement.json`、`verify_helm.json`；落格 `tools/build_helm.py`）

- 舵槳：一手出處沒寫怎麼操舵 ⇒ 推論（研究筆記：船尾一支舵槳最可能）。
  - 本來想做中線、搭在船尾平板上。但船尾後面只有 1.5 m、組裝件底是 z 0，槳葉會穿出框底 ⇒ 改**右舷船尾側**（同蓬特號）。
  - 子作品 `basecamp-piragua-01m-rudder`「杉心號 舵槳（右舷船尾側）」整船的框、47 格、長 2.1 m；綁點 P (26.5, 58.5, 8.5)（右舷舷頂外 1 格）、槳葉中心在 DWL、舵柄往船裡伸給站在船尾的舵手。
  - 模型「舵槳」掛在組裝件：`kind=rudder rudder=quarter`、hinge ＝ P、axis 沿槳柄、`max_deg 35`、`spin=rudder spin_k=35 ±35 lag 0.3`、`id=rudder-1`。
  - 固定點：stock-top（綁點那一格，旁邊 8 格內有 283 格船）、loom-top、blade-tip、tiller-end。
  - 讀數：碰撞（格心＋八角）0°／+35°／−35° 都 0；全部格 z ≥ 0.55。
  - 反向對照：往下沉 3 格 ⇒ 13／6／20。
  - 🩸 v1 綁點貼著舷頂外緣 ⇒ 轉 ±35° 槳柄的格角擦進舷頂 5／3 格 ⇒ 往外挪 1 格。
  - 沒有舵輪（舵柄畫在舵槳上，同 fusta、蓬特號）。
- 錨：一隻四爪錨（共用件 `kotoko-fusta-01m-anchor-grapnel`，scale 0.3 ⇒ 高 0.69 m）。
  - 掛在右舷船頭外側（錨環頂 ＝ pivot，同越嶺號），模型在甲板-main，meta `kind=anchor anchor=bower id=anchor-1`。
  - 船殼登記錨鏈孔 `hawse-S` (112, 52, 8)。
  - 讀數：碰撞 0。反向對照：往船殼推 3 格 ⇒ 178（往下沉碰不到東西，那把尺不會叫）。

## 步驟 13 槳（`design/draft_oars.py` → `masks/oar/oar.vox.txt`、`oars_placement.json`、`verify_oars.json`；落格 `tools/build_oars.py`）

- Dampier 第 1 章 14 支槳 ⇒ 每舷 7 支、每支 1 人。第 5 章用繩環（straps）掛 ⇒ 槳柄直接靠在舷頂上，沒有槳栓。
- 新做一件通用槳 `basecamp-piragua-01m-oar`「杉心號 槳（3.4 m、1 人划；通用部件，0.05 m）」，126 格。
  - 尺寸：裡 0.8、外 2.6 m；槳葉 0.7 × 0.15 m；入水 14°。
  - 固定點：pivot (1,16,16)、blade (1,66,4)、seat (1,3,8)。
  - 為什麼不引用持火號的下層槳（3.85 m）：它的 seat 在槳座下 1.05 m（槳手站在艙底），擺到這艘的舷頂上換算出來落在船殼外（z −2）。
- 14 支模型掛在船殼（槳座 ＝ 舷頂）：
  - 擺法：`at ＝ pivot ＝` 舷頂外緣那條稜上、槳柄底的格角離舷頂面半格。同一塊坐板兩支前後錯開 1 格（右舷 x＋1、左舷 x−1）。
  - 角度：右舷 rotate x −0.54°、左舷 mirror=y ＋0.54°（引擎先翻再轉 ⇒ 反號）⇒ 槳葉中心都在水面。
  - meta：`kind=oar rowers=1 side stroke_deg=30 dip_deg=12 id=oar-1…14`。
- 讀數：
  - 碰撞（格心＋八角；船殼、甲板、桅、砲柱、墊板、舵槳全算）14 支都 0。跟迴旋砲、座、錨、火藥桶的外框 0；槳與槳共用的格 0。
  - seat 14／14 站得住：落在坐板頂上一格、腳下是坐板、頭上 1.4 m 空。
  - 每支槳座旁 8 格內有 302–360 格船殼。模擬的外框跟引擎回報的對上（右舷 y 50.3–83.2、z 1.7–11）。
  - 反向對照：S3 往下沉 3 格 ⇒ 只有它報 38 格；拿掉 P7 ⇒ 左舷 6、右舷 7。
- 坑：
  - 🩸 v1 seat 落在坐板那一格本身（z 3）⇒ seat_down 9 → 8。
  - 🩸 v1 pivot 在舷頂那一格正上方 ⇒ 往外往下跨出半格就擦到舷頂外緣（每支 2 格）⇒ 移到外緣那條稜上。
  - 🩸 左舷用了跟右舷同號的 x 角 ⇒ 引擎回報的外框左舷 z 2.1、右舷 1.7（槳葉高 0.04 m）⇒ 反號。
- ⚠ 遊戲那側要填 `ships[].cfg.base`（划槳全速，節）；沒填 ⇒ 每支槳報 ⚠「槳不划」（步驟 14）。

## 步驟 14 匯進 Blockside 之前作品這側改的（匯入檢查抓到的）

- **水線 meta 要標在「船殼」那條關聯上**：第一次標在組裝件本身（part=work），遊戲沒讀到 ⇒ 退回憲法號的 z 63 ⇒ 那一層一格都沒有、淹水的殼寬算成負的 ⇒ 開局就丟 `Invalid typed array length`（33_flood.js flSkin）。改標關聯「船殼」`kind=ship waterline_z=3`（同蓬特號、越嶺號）就好了。組裝件本身那筆照留（遊戲不讀）。
- **✗ 取用點**：火藥的取用點要一塊 9×9 格平地、頭上 8 格空。艙底只有約 7 格寬、又被坐板每 0.9 m 隔開 ⇒ 船尾做一塊舵手站的平台（x 16–30、板 z 3，跟坐板同高，甲板-main 多 123 格）。
  - 平台 x 22–30 剛好 9 格寬（y 46–54）。
  - 火藥桶挪到平台最後面的角落 (18.5, 50.5, 4)，彈藥庫的墊板刻掉（25 格；子作品現在 0 格，只剩桶模型與 blast／door）。
  - 舵柄端 (27.5, 53.5, 12) → (27.5, 55.5, 13)：v1 那一格擋在 9×9 的頭頂上，模型外框也蓋到 y 53。現在舵手站在平台上、舵柄離站面 0.9 m。
- 重量：
  - 結果帳：甲板-main 397 格（清單 − 桅孔 ＋ 砲柱）、舵槳 47、彈藥庫 0，缺 0／多 0／色差 0。
  - 走路格 1 群 9.28 m²；桶碰撞 0（反向對照 12,748）。
  - 舵槳 0／±35° 碰撞 0（反向對照沉 3 格 6／5／22）；14 支槳碰撞 0、seat 14／14。

## 步驟 14 匯進 Blockside（Blockside 分支 basecamp/piragua 39095b5）

- `admin.py import --id piragua` ⇒ reimport ⇒ `ids`（發號：船殼關聯 ship-1、甲板 deck-1、帆桁 yard-1、桅 part-1；我手寫的 gun-1／gunmount-1／oar-1…14／anchor-1／rudder-1／magazine-1／powder-1 照留）⇒ metasync。
- 槳元件標預設 meta `render=pole`（長桿式低面數網格，Ship_Render）；舵槳不標（有一支往裡彎的舵柄，不是直的）。
- 匯入檢查 ✗ 0、⚠ 0；樓梯自檢 0 座、甲板連通 1 層都接得到。
- 遊戲裡量到的：帆裝 0 收、1–3 張（＝ 步驟 8 那張表）；只排它一艘、收帆、俥鐘全速 ⇒ 槳 5.6 節（`cfg.base` 4 × 娛樂加成 1.4）；第一人稱從船頭走到船尾。
- 遊戲那側為這艘補了三條退路（只在原本那條路完全找不到時才走；全船對照 39 艘報告逐份相同）：取用點排成一排、木工台挑撐得住的腳、geo.marineY／qx。

## 步驟 15 交船（Ship_Game §10 檢查表逐條看過）

- ropecheck：7 條、14 端全 ok（bind／snap／odd 都 0）；link_overlap 0；組裝件 3,556 格、1 元件、空腔 0。
- 作品匯出 vxk checksum 2328241092（0x8ac623c4）＝ Blockside `_cache/piragua.vxk`（3,556 格）。
- 不適用的條目：撞角、爐灶、甲板下的槳、梯子（只有一層）、ratlines、金屬部件、窗、空艙房、砲門蓋板、門（沒有艙口）、蒸汽。
- 槳帆船那一條：14 支、左右各 7、碰撞 0、`cfg.base` 4、槳手 14／14。
- 舵那一條：舵槳是模型（kind=rudder＋stock-top＋spin），開局 lostModels 空；沒有舵輪（舵柄畫在舵槳上）。

給遊戲那側填 geo 的高度（格；0.1 m）：

| 項目 | 值 |
|---|---|
| 船殼前後端 | x 15（船尾平板）– 124（船頭尖）；外框含舵槳 x 10 |
| 水線 | z 3（`waterline_z`） |
| 艙底（站） | z 1；坐板頂、船尾／船頭平台頂 z 4 |
| 舷頂 | 船中 z 8、船頭 z 10 |
| 迴旋砲口 | (117.5, 50.5, 14.75) |
| 桅頂 | z 50；帆桁 peak z 82.6、前端 z 22.5 |
| 帆 | 帆腳角 z 19、頂 z 83 |
| 遊戲側 geo（已填） | spar 1–5、marines 21／26、center 20、aim 6、aimZ 1–60、deckAim 1–10、rigAim 20–80、marineY 2、qx 0 |

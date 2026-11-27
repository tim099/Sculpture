# 蠍子號（al-ʿAqrab，العقرب）—— 1666 年的黎波里的加利奧特（galiot）（0.1 m／格）

委託：Tim（Paperclip FAR-92，2026-11-23 09:36 UTC 按了確認卡「開工蠍子號」；規劃見 FAR-87 的 plan 文件，北非船隊第 5 艘）；Senate TASK-0023。
船殼＝任務作品 `claude-galiot-01m`（tags=sub），組裝件 `claude-galiot-01m-assembly`（主作品，名稱「蠍子號」）。
船名是設計決定（FAR-87 規劃）：史料沒有留下的黎波里哪一艘 galiot 的名字；取蠍子，配這艘低、窄、船首帶 spur 的海盜槳船。

## 步驟 2 開工前（2026-11-23）

- 已讀：Ship_Steps、Ship_Setup §0–§2.1、scp-sculpture §0（委託與收費）。

### 座標、比例、方向
- 一格 0.1 m（船殼、組裝件都記了 meters_per_voxel=0.1；子作品建立時也要記）。0.05 m 的元件當模型 scale 0.5，0.02 m 的 scale 0.2。
- 框暫定：船殼 400 × 241 × 90、組裝件 400 × 241 × 280（40 × 24.1 × 28 m）；步驟 3 定主尺寸後再調（調尺寸免費）。**⇒ 步驟 3 改成船殼 420 × 241 × 90、組裝件 420 × 241 × 300（船身 35.1 m、單桅；見下）。**
  - 長 400：甲板約 28 m（規劃），船頭再加 spur（越嶺號的衝角伸出約 2.8 m），船尾留給舵和艉台。
  - 寬 241（中線 y=120）：船約 4.5 m（45 格）、加上舷外槳架約 6–7 m；預期槳的舷外段會比越嶺號（7.2 m 的槳、161 寬，槳尖離框邊只剩約 6 格）長 ⇒ 從中線到框邊兩側各 12 m（舷外約 9.8 m）。寬維持奇數，鏡像才落在中線格。
  - 高 280：兩根桅（FAR-87 規劃引 Wikipedia「北非海盜的 galiot 兩桅」；步驟 3 照史料定）與帆桁尖（越嶺號一根桅，桅頂 z 135、帆桁尖 z 195，組裝件 230）。
  - ⚠ 框要在步驟 4 落格前定案：縮小會切到格子時被拒、內容不縮放。
- X 船長、船頭朝 +X；Y 船寬，中線 y=120（P 舷 y < 120、S 舷 y > 120）；Z 高度，z=0＝龍骨底面。
- 鏡像：格 y ↔ 240 − y（120 那一格是自己）；一舷子作品的另一舷關聯 mirror=y、at.y＝241 − at.y − 高；外部模型繞 pivot 翻。
- 固定點只收整數格、要在作品框裡；繩端要精準就寫小數。

### 作品怎麼拆
- 船殼（任務作品，tags=sub）：龍骨、艏艉柱、船殼板、舷牆、塗裝。
- 組裝件（主作品）：只放關聯與外部模型；船殼關聯「船殼」at 0,0,0（已建）。
- 子作品（parent_work 指船殼、tags=sub、記 0.1、關聯 at 0,0,0）的框照越嶺號分三種：甲板層的件用船殼的框（400 × 241 × 90）、桅用組裝件的框（400 × 241 × 280，固定點要在框裡）、帆桁與元件用緊框。子作品有：甲板（含中央走道 corsia、划手座）、舷外槳架（apostis）、船首平台與 spur、船尾艉台與遮陽篷架、桅（一到兩根，步驟 3 定）、每根三角帆桁一件＋外部模型、舵、舵柄、船首與船尾裝飾、彈藥庫。
- 一舷的東西只做一舷，另一舷 mirror=y。

### 打算引用的現有元件（`sub=components` 2026-11-23 09:42 UTC 查：450 件、掃 2,789 件作品；步驟 9–13 再定 scale 與擺法）
（步驟 3：砲照史料改成 `8l` ×1 ＋ `pierrier` ×2，下表的 `4l` 不用了；桅只有一根。）
| 用途 | 元件 | 一格 | 備註 |
|---|---|---|---|
| 船首中線砲 8l | `ridge-two-centurion-01m-gun-8l` | 0.05 | gun:8l，通用部件，88 次；皇家號的甲板（couverte・中央走道・划手座）上有 2 門 |
| 船首兩旁 4l | `pinnacle-patache-01m-gun-4l` | 0.05 | gun:4l，通用部件，102 次 |
| 迴旋砲 | `apex-one-reale-01m-gun-pierrier`＋`-mount` | 0.05 | gun:pierrier／gunmount，95 次（越嶺號船首平台 2、皇家號舷外槳架 14） |
| 槳 | `kotoko-fusta-01m-oar-inner`／`-outer`（7.2／6.6 m，alla sensile 一人一支） | 0.05 | 步驟 3 定划法（每座幾人、一人一槳還是共用一支）；不合就照 `Ship_Oars` 做新的 |
| 錨 | `kotoko-fusta-01m-anchor-grapnel` | 0.05 | 地中海槳帆船的四爪錨，20 次 |
| 火藥桶 | `basecamp-frigate-constitution-01m-powder-barrel` | 0.02 | meta powder |
| 燈 | `gura-tridente-01m-lantern` | 0.05 | light:amber；皇家號的船尾燈桿也用它 |
| 廚房 | `claude-baghlah-01m-hearth` | 0.05 | kind=galley；星辰號的沙箱灶 |
| 小艇 | `basecamp-ember-01m-boat` | 0.05 | boat:cutter 9 m；步驟 10 看要縮放還是不帶 |
| 舵 | `kotoko-fusta-01m-rudder`（尾柱舵＋舵柄） | 0.1 | 步驟 11 定：引用（縮放）或照海鷗號自己做 |

自己做的：船殼、甲板、中央走道、划手座、舷外槳架、船首平台與 spur、艉台與遮陽篷架、桅、三角帆桁、舵柄、裝飾、船名、旗。
範本程式（照 `Ship_Steps` §5，複製時檔頭寫出處）：
- 同一家族、尺寸最接近的越嶺號 `kotoko-fusta-01m/design/`（線形、甲板以上的 corsia／划手座／apostis／船首平台／衝角／船尾篷、槳）。
- 兩根三角帆、帆裝三段、舵柄、迴旋砲、彈藥庫看海鷗號 `claude-felucca-01m/design/`。
- 大型槳帆船的船首砲台、槳看皇家號 `apex-one-reale-01m/design/`。

### 獨立 verifier（verifier2，唯讀，09:52–10:14 UTC；草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier2/`）
- 七條都推翻不了：兩件作品的 work.json 與關聯（commission_ref 全庫 107 種值、只有船殼用這一個；委託薪水帳本只有一筆 10 token）；元件表 12 件的 ID、一格、meta、引用次數（從全庫 models.json 自己重數，450 件、加總 6,063 跟查詢結果一樣）；越嶺號的 2.8 m、7.2 m、161、z 135／195／230；鏡像公式（全庫 59 對鏡像關聯實測，奇數寬的 18 對全中）；框放得下。
- 它提醒、已照改：「12 m」是中線到框邊（舷外約 9.8 m）；子作品的框分甲板層／桅／緊框三種；框在步驟 4 落格前定案。
- 沒有讀數撐著的是設計意圖與預測（船名、「低」、槳的舷外段會比較長、桅一到兩根），步驟 3 照史料定。

## 步驟 3 找資料與新圖紙（2026-11-23）

- 已讀：Sculpture_Blueprint_Build §1–§4、Ship_Setup §3。
- **研究**：三個唯讀研究子代理（12:47–13:10 UTC）讀已下載的掃描，分三組：義大利／德國造船書與度量衡表、法國／荷蘭造船書與辭典、北非記載與同時代的畫。原文照抄、換成公尺、標可信度。
  - 合本與「本船用了哪一條」總表：`references/research_galiot_1666_2026-11-23.md`。
  - Nooms 畫在的黎波里港外那艘的裁圖：`references/nooms_1662-68_SK-A-1398_galley.jpg`（Rijksmuseum SK-A-1398，公有領域）。
  - `plan.json` 的 `sources` 是代號表；每個數字的 `src` 寫代號＋頁碼，或寫明是設計決定。
- **跟 FAR-87 規劃不一樣的三件**（規劃的數字本來就是推測，步驟 3 照史料定）：
  1. **單桅**：FOU p.49「n'ont que l'Arbre de Maistre」（DAS p.10 照抄）、PAN p.48（北非的 galeotta 不立前桅）、DAN p.308、JAL、AUB；畫 NOO、NOO2、LUY 都單桅。只有 DEW 地圖邊景畫雙桅（可信度低）。
  2. **船比規劃大**：每舷 20 座（HAE f18r 1581 年阿爾及爾 36 艘的中位數，雙峰 18／22）、每槳 3 人（HAE f16r、FOU、PAN）。主尺寸借 JAL 轉引 Dortières 的 galiote：35.08 × 4.68 × 1.705 m（法國約 1680 年、20 座；Jal 寫北非的 25–26 座）。規劃原本是約 28 m／4.5 m／80 t。
  3. **砲 3 門、船首低平台**：FUR p.80 galeotta 船首只有 3 門（中間最大、兩旁後膛小砲 Cammerstücklin）⇒ `8l` ×1 ＋ `pierrier` ×2。HAE f17r、DAN、PAN 都說北非的船不設船首高平台 ⇒ 做成低平台、不做梯子。規劃的 `4l` ×2 與舷側、船尾 `pierrier` ×6 沒有史料，拿掉；要照遊戲平衡加回來，由 Tim 決定。
- **框放大**（免費、還沒落格；13:28–13:30 UTC `work sub=update`）：
  - 船殼 400 × 241 × 90 → **420 × 241 × 90**。
  - 組裝件 400 × 241 × 280 → **420 × 241 × 300**（船身 351 格＋spur 伸出 43 格；帆桁上端 z 279）。

### 新圖紙 01：線形（`lines.py`、`draft_lines.py` ⇒ `sheet01_lines_v1.png`、`verify_lines.json`、`masks/hull/hull_01.vox.txt`）
- 讀數（v3）：
  - 兩柱頂間 **35.1 m**（JAL 35.08）、寬 **4.7 m**（4.68）、龍骨頂到船中舷頂 **1.7 m**（creux 1.705）。
  - 龍骨（z 0 層）27.7 m；艉柱頂 z 39、艏柱頂 z 27。
  - 吃水 1.1 m、乾舷 0.8 m、水線長 31.7 m、水線寬 4.3 m。
  - **排水量 65.9 t**、方形係數 0.43、L／B 7.47；34,328 格（5 色）。
- 史料對照（`source_checks`，史料 → 作品）：
  - 長 35.08 → 35.1、寬 4.68 → 4.7、creux 1.705 → 1.7。
  - 龍骨 26.96 → 27.7：z 0 那一層把艏柱圓弧最底下 6 格也算進去；直的那段 61 → 330 是 26.9 m。
  - Furttenbach 平面圖三站的寬 ÷ 最大寬：
    - V 線（艏柱頂往後 27 格，x 344）0.64 → **0.644**。
    - X 站（槳架後端 x 64）0.53 → **0.511**。
    - 船尾端 A–B（舷頂下一層的最後一欄 x 25）0.20 → **0.200**。
  - 分母用船中同一層（舷頂下一層，4.5 m）。FUR 的 25 palmi 是甲板那一層最寬處；本船甲板邊就在舷頂下一層。若改用最大寬 4.7 m 當分母，是 0.617／0.489／0.191（verifier3 量的）。
- 調過的參數：
  - v1 照越嶺號的收法，V 線只有 0.56、X 站 0.82。v2 格點掃 `s_aft × aft_pow × s_fwd × fwd_pow`（5⁴ 組），取兩站誤差和最小的一組：`s_aft` 0.3 → 0.4、`aft_pow` 2.0 → 1.2、`fwd_pow` 1.8 → 2.0。
  - `stern_top_ratio` 0.16：0.2 是 11 格（0.24）、0.16 是 9 格（0.20）。
  - 船殼變成槳帆船的梭形，長方形的槳架架在上面（FUR 的兩個 Giogo 放在 X 站與 V 線）。
- 反向對照（`--probe`，不寫檔）：
  - half_beam +3 ⇒ 寬 4.7 → 5.3。
  - stem_head_x +3 ⇒ 長 35.1 → 35.4。
  - deck_side_z +3 ⇒ creux 1.7 → 2.0。
  - s_aft +0.1 ⇒ X 站 0.511 → 0.467。
  - stern_top_ratio +0.1 ⇒ 船尾端 0.20 → 0.29（v2 量）；X 站也跟著 0.51 → 0.56，因為 rt 管整個船尾的上面幾層。
  - sternpost_head_z +3 ⇒ x 25 那一欄沒了（0.20 → 0）。

### 新圖紙 02：配置（`layout.py`、`draft_layout.py` ⇒ `sheet02_layout_v1.png`、`verify_layout.json`）
- 划手座：
  - 每舷 **20 張**、間距 13 格（1.3 m；CRE 1.32、FUR 1.39）、x 72–319。
  - 第一張離艉柱 5.2 m、最後一張離船首低平台 7 格；座面 dy 4–28（2.5 m）。
  - 20 張的槳手頭上 14 格全空。
- 中央走道：0.5 m 寬、0.6 m 高（FUR galeotta 2¼ palmi ＝ 0.57 m）、x 65–325。
- 槳架：外緣總寬 **6.3 m**（1.34 倍船寬）、x 64–327。這是設計決定，落在 FUR 1.28 與 CRE 外緣約 1.59 之間。
- 槳：
  - 槳栓每舷 20 根、離水 1.2–1.5 m；槳栓到中央走道邊 2.7 m。
  - 槳 40 支、每支 3 人，槳手 120 人。遊戲沿槳柄每 0.6 m 排一人，3 人要 1.8 m，放得下。
  - 舷外 5.6 m、入水 12.4°（船尾第一支 15.5°）。
- 船首：
  - 低平台 x 326–352、板面 z 25；中央走道末端 z 24，高低差 1 格（遊戲一步最多 3 格）。
  - spur x 366–413、伸出船身 4.3 m；全長含 spur 39.4 m。
- 船尾：
  - 艉台 x 22–56，實心、板面 z 25。
  - 紅布拱篷 x 24–60，篷頂 z 43；站在艉台上頭上還有 1.7 m。
  - 艉燈桿 x 24，燈在 z 62。
  - 艙口 x 57–61，在艉台和中央走道之間。
- 桅：
  - x 232，在第 13、14 張座之間，沒穿過座。離艏柱頂 0.40 船身、直立、甲板以上 16.0 m（桅頂 z 179）。
  - 帆桁 31.5 m、斜 35°：前端 (336, 99)、上端 (78, 279)，都在組裝件框裡。
  - 三角帆三邊 29.0／23.8／16.7 m、198 m²。
  - 帆裝三段：全收不張；收帆、戰鬥帆、滿帆都張主帆（只有一面帆）。
- 砲門：沒有（開放甲板的槳帆船，砲在船首低平台上）。
- 砲：`8l` 中線 x 344、`pierrier` x 338 dy ±9。腳下都是平台板，上面 14 格空；位置步驟 9 再退到零碰撞。
- 結構：件與件、件與船殼重疊 0；船殼＋各件 **1 個連通塊、封閉空腔 0**、鏡像差 0。
- v2 修的：
  1. v1 的艙口在中央走道底下被蓋住，船艙變成 84,246 格的封閉空腔 ⇒ 艙口挪到中央走道後面。
  2. 艉台板只有一層時，x 43–45 跟著舷弧降一格，只靠邊相碰，斷成另一塊；改兩層又在船尾末端封出 40 格空腔 ⇒ 改成實心艉台。
  3. 第 1、2 張座的腳踏撐柱落在船殼外、腳踏懸空 ⇒ 撐柱收到船殼內緣。
  4. 反向對照抓到「每舷幾張座」照設計清單數，拿掉一張照樣報 20 ⇒ 改照格子數；拿掉第 5 張 ⇒ 報 19、指出 x 137。
- 反向對照：
  - benches.first_x +3 ⇒ 第一張 5.2 → 5.5 m、離平台 7 → 4 格。
  - drop_bench 5 ⇒ 19 張。
  - rambade.clear +3 ⇒ 平台板 z 25 → 28。
  - apostis.half +3 ⇒ 槳栓到走道 2.7 → 3.0 m。
  - corsia.half +1 ⇒ 2.7 → 2.6 m。
- 圖紙多了三段（Ship_Steps 步驟 3 要的）：甲板高度表（每一層的 z 與離水線）、桅帆表（三角帆三邊與面積）、帆裝三段與砲門。

### 獨立 verifier（verifier3，唯讀；量測程式與原始讀數在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier3/`）
- **第一輪**（13:28–13:39 UTC，22 條）：設計的主要數字推翻不了。
  - 線形、配置、重跑都 pass。線形是直接從船殼清單量的，沒 import 作者的程式；配置只用 `layout.py` 產件，量測是自己寫的。
  - Jal、Haedo、Furttenbach、Fournier／Dassié 都回頁面圖重讀。
  - **推翻一個讀數**：Nooms SK-A-1398 的帆桁是船身的 **0.97**（端點怎麼取都在 0.93–1.04），研究子代理讀成 1.05。設計取 0.9，數字不用改，`src` 改了。
  - **基準不一致**：艉柱高拿「龍骨頂起算的 8⅓ palmi」去除「量到龍骨底的 18 palmi」。照同一個基準是 38.7 ⇒ `sternpost_head_z` 41 → **39**；船尾端那一欄跟著挪到 x 25。
  - 其他 minor 都照改：
    - Jal 的 20 座是法國船，北非的他寫 25–26 座。
    - Crescentio 的 telaro 28 palmi 是淨寬，不是外緣。
    - 原文拼法是 Cammerstücklin；頁碼 p.26／p.28 寫反了。
    - 平台跟中央走道差 1 格，不是同高；spur 伸出 4.3 m，不是 4.2 m。
    - 「3 人要 1.5 m」改成 1.8 m；`sheer_fwd` 改標設計決定。
  - Jal p.760 頁面圖上寫的是「Galiote à 20 rames」，研究報告裡 OCR 讀成的「70」是誤讀，這件事結案。
- **第二輪**（13:41–13:44 UTC，只驗修過的，24 條）：17 pass、7 minor，沒有 fail。
  - 艉柱頂 z 39（最高格 38）、x 25 寬 9 格 ＝ 0.200；長、寬、深、排水量 65.89 t 都等於 `verify_lines.json`。
  - 配置：1 個連通塊（77,477 格）、空腔 0、重疊 0、鏡像差 0；艉燈桿 z 32–61 腳下是艉柱實心格。
  - 7 條 minor 都是 `src` 的字，已照改（數字不動）：
    - 只有艉柱寫了 4 palmi 榫頭。
    - 龍骨 27.7 還多算艉柱圓弧 1 格。
    - `stem_head_z` 取 27 是選了一個解讀，改標設計決定。
    - `sheer_fwd` 的理由只對舷側。
    - 「每槳 5 人」出自 PAN／DAS，不是 CRE。
    - FUR 的桅、帆桁要除以他那艘 190 palmi（得 0.47、0.97）。
    - JAL 的「只讀 OCR」拿掉。
  - `draft_layout.py` 的「槳手放得下」門檻也改成跟印出來的一樣，用 3 × 0.6 ＝ 1.8 m。

### 重跑（v3 定稿，13:47 UTC）
- `draft_lines.py`、`draft_layout.py` 連跑兩次，5 個輸出的 sha256 一樣：
  - `verify_lines.json` d7060b5f…
  - `sheet01_lines_v1.png` ec613411…
  - `masks/hull/hull_01.vox.txt` 4a90ad82…
  - `verify_layout.json` 66bfb53e…
  - `sheet02_layout_v1.png` dcbc73d5…
- 圖紙的字用英文、Pillow 內建字型。

### 留給後面的步驟
- 步驟 4 船殼落格：清單 `masks/hull/hull_01.vox.txt`（34,328 格，at 0,0,0）。
- 步驟 9 砲：三門的位置是設計決定，要退到零碰撞；`8l` 擺在平台中線、砲口朝船頭，要讓開 spur 與胸牆的砲口。
- 步驟 13 槳：每支 3 人、舷內 2.6 m、舷外 5.6 m；越嶺號的槳元件（7.2／6.6 m、一人一支）不合 ⇒ 照 `Ship_Oars` 做一件新的。
- 規劃的舷側、船尾迴旋砲拿掉了；要照遊戲平衡加回來，等 Tim 說。

## 步驟 4 船殼落格、塗裝（2026-11-23）

- 已讀：Sculpture_Blueprint_Build §5–§8。
- 這艘沒有砲門、沒有船尾窗：開放甲板的槳帆船，砲在船首低平台上 ⇒ 步驟 4 只有船殼與塗裝。
- 塗裝就在清單的顏色裡：水線下牛脂白 218、舷側黑 36、舷頂紅 196、往下第 2 格金 244、牆裡 141。
- **預檢**（落格前，在設計清單上）：34,328 格、沒有重複格、1 元件、空腔 0、鏡像差 0。
- **雕刻**（13:47–13:49 UTC，兩刀都帶 expect_pixels、免費；清單切自 `masks/hull/hull_01.vox.txt`，在 `masks/stamp4/`）：
  1. 先貼船中 x 190–199 一片：stampvox 1,220 ⇒ placed 1,220。
  2. 切 x 195 剖面看形狀（`overlays/stage4_section_x195.png`）：龍骨、微微上抬的平底、圓舭、直舷、黑舷側、金帶、紅舷頂，對了。
  3. 再貼其他：33,108 ⇒ placed 33,108。
- **讀數**：
  - 結果帳一：自己重播 events vs 設計清單（`tools/replay.py` ⇒ `verify_step4_replay.json`）。34,328／34,328，**缺 0、多 0、色差 0**；正向對照：設計第一格 (20,119,35) 色 36，重播也是 36。
  - 結果帳二：CLI export（`tools/check_hull.py` ⇒ `verify_step4.json`），也是 0／0／0。
  - 結構：重播出來的格子上 **1 元件、空腔 0、鏡像差 0**。引擎的 `stats structure=1 mirror=y:120` 一樣：34,328 格、1 塊、空腔 0、鏡像缺 0／0、色差 0。
  - 線形對照：作品右舷外緣 vs `lines.hb`，兩柱間每 20 格、z 1–18 每 3，94 點差 0。
- **反向對照**：
  - 設計整片往上搬 3 格 ⇒ 缺 28,458、多 28,458、色差 3,416。
  - half_beam +3 ⇒ 線形 60 點報差、最大 3。
  - 尺會說話。
- **過程圖**：
  - `overlays/stage4_section_x195.png`（船中剖面）。
  - `overlays/stage4_profile_stbd.png`（中線剖開、看右舷內側的側面）。
  - 3D 全景留到有 GPU 的機器補：這台沒有 GPU，`op=view` 寫不出圖（海鷗號、星辰號同）。

## 步驟 5 甲板、梯子、艙房（2026-11-23）

- 已讀：Ship_Decks（§9.2 空艙房、§9.3 甲板與通道與槳帆船的 walk／walk_y、樓梯自檢 ①–⑦、第一人稱爬得出來）。
- 程式：
  - `design/draft_decks.py`（新圖紙 03 ⇒ `sheet03_decks_v1.png`、`verify_decks.json`、`masks/decks/{deck_main,bow}.vox.txt`、`decks_meta.tsv`）。件的格子照 `layout.py`（步驟 3 圖紙 02 同一支）；走路格照海鷗號 `draft_decks.py` 改。
  - 落格 `tools/build_decks.py`（照越嶺號 `build_upper.py`）。
- **只有一層甲板 main**（`plan.json` 的 `decks`）：
  - 艙底不做：艙口在船尾 V 形船底的正上方，底下只有一條縫，梯子下不去。船中雖然有 1.2 m 深，上面整排都是划手座，開不了艙口。
  - 艙口（x 57–61）改成**格柵**：每 2 格一根條、8 個 1 格的孔。船艙通氣，不會變成封閉空腔；人也掉不進去（Ship_Decks：掉得進去的地方都要爬得出來）。
  - 船首低平台的板面比中央走道末端高 1 格，所以掛在甲板-main 底下（`甲板-main/船首平台`），跟甲板同一層，不用梯子。
  - 艉台留到步驟 6（驗收格把它放在裝飾那一步）；舷外槳架留到步驟 13（槳）。
- **子作品**（13:57 UTC 建，免費）：
  - `claude-galiot-01m-deck-main`「蠍子號 甲板（中央走道、划手座、腳踏、艙口格柵）」34,104 格。
  - `claude-galiot-01m-bow`「蠍子號 船首低平台」2,010 格。
  - 兩件都是 parent 船殼、tags=sub、0.1 m／格、框 420 × 241 × 90。
  - 關聯：組裝件 `甲板-main` at 0,0,0；甲板-main 裡 `船首平台` at 0,0,0。
- **甲板 meta**（`sub=meta file=decks_meta.tsv`，讀回 links.json 一樣）：
  - `kind=deck deck=main level=0 name=甲板（中央走道、划手座、船首低平台） thick=2`
  - `floor`：甲板面中線 ＋1，船首平台那段是平台板 ＋1。
  - `walk`：中央走道頂 ＋1，包含後端 3 格台階 x 62–64 與船首平台。
  - `walk_y=118:122`：walk 只管走道那 5 欄；兩舷照 floor，跟皇家號一樣。
- **讀數**：
  - 設計（`verify_decks.json`）：甲板與船殼、平台與船殼、甲板與平台都重疊 0；船殼＋甲板＋平台 70,442 格，1 元件、空腔 0、鏡像差 0。
  - 走路格（照遊戲 navBuild：腳下實心、頭上 12 格空、一步 ≤ 3、參考面 −2～+3；walk_y 那幾欄的參考面是 walk）：
    - 最大一群 **117.28 m²**。中央走道、走道後端台階、船首平台、格柵旁的甲板、三個砲位都在這一群裡。
    - ⚠ 更正（verifier456）：「划手座之間的甲板靠腳踏 → 座 → 下一格甲板一階一階接起來」只在逐格量時成立。遊戲的走路格是每 2 格取樣（NAV_C 2）⇒ 座與座之間的甲板在遊戲裡是各自的小區：主群 107.28 m²、另外 11 塊（≥ 12 點）合計 16.88 m²、最大 2.08 m²，沒有 ≥ 10 m² 的 ⇒ 不報 ⚠。那些本來就是划手的位置（皇家號同）。
    - 另外兩小塊：船首平台前面的船頭 1.92 m²、0.07 m²，都在遊戲報 ⚠ 的 10 m² 以下。
    - 中央走道末端到船首平台高 1 格。
  - 結果帳（`tools/replay.py`）：
    - 甲板-main 34,104／34,104、船首平台 2,010／2,010，缺 0、多 0、色差 0。
    - 正向對照：(25,118,24) 177／177、(326,100,24) 104／104。
    - 甲板-main 單獨看是 4 塊，靠船殼連成一塊。
  - **引擎組出來的組裝件**（export format=list links=all）70,442 格 ＝ 船殼＋甲板＋平台的設計，缺 0、多 0、色差 0（`verify_step5_assembly.json`）。
- **反向對照**（`draft_decks.py --probe`，不寫檔）：
  - 船首平台抬 4 格（一步 5 格）⇒ 平台與三門砲掉出主群（多一塊 7.81 m²）。
  - 平台抬 2 格（一步 3 格）⇒ 照樣連通（遊戲的上限）。
  - 中央走道加高 3 格 ⇒ 走道整條斷開（20.86 m²）。
- **沒做的**：
  - 梯子：只有一層，不用。
  - 空艙房（§9.2）：船首平台底下只有 0.4 m、艉台是實心的，放不了東西。
- 艙底：船中艙底頭上有 1.2 m、沒有梯子下得去。本來預告樓梯自檢 ⑥ 會報 ⚠，但 verifier456 照 `75_ladcheck.js` 查：要 zlo − 1 > 12 才檢查艙底，這艘 zlo 9 ⇒ 不會跑這項。樓梯自檢、第一人稱要匯進遊戲才量得到，步驟 14 一起讀。
- 步驟 3 的圖紙 02 跟著重跑：艙口加了格柵，`verify_layout.json`、`sheet02_layout_v1.png` 變了；仍然 1 元件、空腔 0、重疊 0。
- 重跑（步驟 5 當時；步驟 6 改了 floor 與艉台，新的 sha 見步驟 6）：三支產生程式各跑兩次，10 個輸出的 sha256 一樣：
  - `verify_decks.json` b4dac772…、`sheet03_decks_v1.png` 80a2f2f6…
  - `deck_main.vox.txt` 9c2ebf49…、`bow.vox.txt` 722a7e63…、`decks_meta.tsv` 7a6ad113…
  - `verify_layout.json` 745e0b3e…、`sheet02_layout_v1.png` c3aa8efd…

## 步驟 6 裝飾（2026-11-23）

- 已讀：Ship_Fittings §9.9（deco=1 只有外部模型能標；有功能的、有東西掛在上面的不能標）。Ship_Materials「窗的玻璃」：這艘沒有窗，不用。
- 程式：
  - `design/draft_deco.py`（新圖紙 04 ⇒ `sheet04_deco_v1.png`、`verify_deco.json`、`masks/deco/{spur,poop,awning}.vox.txt`、`masks/step6/hull_paint.vox.txt`）。
  - 落格 `tools/build_deco.py`。
  - 參數在 `plan.json` 的 `deco`（每一項有 src）。件的格子照 `layout.py`；步驟 6 把船尾拆成兩件：`poop`（艉台、燈桿）、`awning`（篷）。
- **做了什麼**（14:03–14:04 UTC，免費子作品，parent 船殼、tags=sub、0.1 m／格、框 420 × 241 × 90）：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | `claude-galiot-01m-spur` | 組裝件關聯 `spur` | 686 | spur（sperone）x 366–413、伸出艏柱頂 4.3 m、尖端包鐵、斜撐回艏柱；不是撞角，不標 kind=ram（Ship_Steps：壓斷槳的 spur 不算撞角） |
  | `claude-galiot-01m-poop` | 甲板-main 底下的關聯 `艉台`（同一層甲板） | 1,254 | 實心艉台 x 22–56（板面 z 25）＋艉燈桿 x 24（z 32–61，立在艉柱上；燈在 z 62，是步驟 10 的模型） |
  | `claude-galiot-01m-awning` | 組裝件的**外部模型** `船尾篷`，meta **deco=1**、at／pivot 0,0,0、scale 1 | 1,614 | 骨架加紅布的拱篷 x 25–60、篷柱 3 對立在舷頂上；純看的、上面不掛東西 ⇒ 遊戲畫質低時不載入，不算重量、不擋人；艉台中線頭上到篷最低一格 1.5 m |
  | 船殼換色 | stampvox overwrite=1 | 換色 28、加 0 | **船名**：天蠍座的 14 顆星（al-ʿAqrab 是天蠍座的阿拉伯名），兩舷船尾的黑舷側 x 38–49、z 12–19；金 244，心宿二紅 196；頭朝船頭。星連成線，遠看是一隻金線畫的蠍子 |
- 沒做的：
  - 船首像：Nooms、Luyken 畫的北非槳帆船船首都看不到船首像。
  - 艉柱頂飾：艉燈桿就立在那裡。
  - 艉燈本身：是 kind=light 的模型，步驟 10 放。
- **甲板 meta 重標**：`floor` 在 x 27–56 改成艉台板面 ＋1（z 27–29）。走路格照遊戲 navBuild 重量：
  - 最大一群 116.88 m²，艉台也在主群裡。
  - 艉台抬 2 格 ⇒ 艉台掉出主群（反向對照）。
- **讀數**：
  - 設計（`verify_deco.json`）：
    - 三件跟船殼、甲板、平台重疊 0，艉台與篷重疊 0；鏡像差都是 0。
    - 船殼＋甲板＋平台＋spur＋艉台 72,382 格，1 元件、空腔 0。
    - 篷貼著舷頂（8 格相接）。
    - 燈的位置 (24,120,62) 是空氣。
    - 紋章 28 格都在船殼最外一層、原本都是黑 36；換色後船殼鏡像差 0。
    - v1 → v2（verifier456 抓到）：紋章 z 13–20 頭頂那顆 (49,±8,20) 跟 x 49 的金帶 (z 21) 稜邊相鄰、同色，側面看黏成一根金條 ⇒ 整個往下挪 1 格（z 12–19）。作品照補差改：`tools/delta_apply.py` 對「hull_01＋新換色清單」⇒ 換色 44（舊星改回黑、新星上色，12 格位置重疊、顏色不變），讀回 44。
  - 結果帳（`tools/replay.py`）：
    - spur 686、艉台 1,254、篷 1,614，都是缺 0、多 0、色差 0。
    - 船殼重播（4 刀）vs hull_01＋換色清單 v2：34,328 格缺 0、多 0、色差 0、1 元件、空腔 0、鏡像差 0。
    - 反向對照：不疊換色清單 ⇒ 色差 28。
  - **引擎組出來的組裝件**（links=all）72,382 格 ＝ 設計（船殼換色後＋甲板＋平台＋spur＋艉台），缺 0、多 0、色差 0。
  - 模型讀回：`船尾篷` meta {"deco":1}、at／pivot 0,0,0。
  - 反向對照：紋章往船頭挪 3 格 ⇒ 換色清單 52 格不同。
- 重跑（v2 定稿）：四支產生程式各跑兩次，16 個輸出 sha256 一樣：
  - `verify_deco.json` 6f01b99a…、`sheet04_deco_v1.png` 30a2b40c…
  - `spur` ebcba944…、`poop` 826adcf4…、`awning` c6b90f5f…、`hull_paint` 5fea13bc…
  - `verify_decks.json` 969666df…、`sheet03_decks_v1.png` 60c1d3ad…、`decks_meta.tsv` d0689ee7…；`verify_layout.json` 8bfb3f33…、`sheet02_layout_v1.png` c3aa8efd…（步驟 6 拆了 poop／awning）
- 組裝件裡「船殼」關聯的 pivot 還是建立時的 [400,241,90]（v1 舊框；重登 overwrite 也沒變）。turn 0、不鏡像時 pivot 不起作用，照實記。

### 獨立 verifier（verifier456，唯讀、自己重播 events、照 Blockside 原始碼自己寫走路格，不 import 作者的檢查程式；14:05–14:16 UTC；草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier456/`）
- 9 條：作品＝設計、結構、線形（16 站 202 點差 0）、艙口格柵、子作品設定、反向對照（8 種故意弄錯都報得出來）pass；甲板 meta、裝飾、筆記 minor；**沒有 fail**。
- minor 已照改：
  - 紋章黏到金帶 ⇒ 往下挪 1 格。
  - 篷下淨高寫成 1.7 m、其實 1.5 m ⇒ 改 src。
  - 步驟 5 的「座間甲板一階一階接起來」在遊戲 2 格取樣下不成立、艙底 ⑥ 這艘不會跑 ⇒ 改步驟 5 筆記。
- 照實記、不改：
  - 星連成線（不是點狀星）：遠看是一隻蠍子的線畫，留著。
  - floor 在 x 25、26、364 差 1–3 格：都在遊戲找站位的 −2～+3 範圍內，站得到。
  - 划手座伸出船殼到 dy 28：設計本來就是這樣，舷外槳架步驟 13 才接。
  - 換色那刀的 event 沒記 overwrite 旗標：照 placed_colored 重播正確。

## 步驟 7 桅與帆桁（2026-11-24）

- 已讀：Ship_Masts §5（每根桅一件子作品、下桅的關聯標 kind=mast＋mast、帆桁子作品＋外部模型放在它那根桅的子作品裡、三角帆桁 yard=gaff＋rig=lateen＋固定點 fore、匯入檢查「桅的格在帆桁轉軸往下 10–40 格、中線 ±4」）。
- Tim 11-24 04:41 UTC 在 FAR-92 的問題卡選了「GO：繼續步驟 7」，步驟 9 的砲選「照史料：8l ×1 加 pierrier ×2」（做到步驟 9 時照這個改驗收格）。
- 程式：
  - `design/draft_masts.py`（新圖紙 05 ⇒ `sheet05_masts_v1.png`、`verify_masts.json`、`masks/masts/{main,deck_hole}.vox.txt`、`masks/yards/lateen-main.vox.txt`、`yards_lateen.json`、`yards_placement.json`）。帆桁的做法照海鷗號 draft_masts（三角帆桁在自己的框裡就做成斜的、模型 rotate 0）；桅孔照皇家號、越嶺號。
  - 落格 `tools/build_masts.py`（hole／mast／yard／links）；讀數 `tools/check_masts.py`（⇒ `verify_step7_assembly.json`）。
  - `tools/replay.py` 多收「+~清單」＝ 從設計拿掉這些格（甲板-main 的桅孔）。
  - 參數在 `plan.json` 的 `rig_build`（每一項有 src）；桅位、桅高、帆桁長與角度照 `layout.rig`（步驟 3）。
- **做了什麼**（04:53 UTC，免費任務子作品，parent 船殼、tags=sub、0.1 m／格）：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | 甲板-main 刻桅孔 | carvevox 帶顏色守門，前後夾 mark `桅孔` begin／end | −75 | 桅穿過的甲板板、橫樑、中央走道（刻之前 177×27、141×45、136×3）；甲板-main 34,104 → 34,029 |
  | `claude-galiot-01m-mast-main` 主桅（框 420 × 241 × 300） | 組裝件關聯 `主桅` at 0,0,0，meta `kind=mast, mast=main` | 1,641 | x 232 直立（格 231–233、y 119–121，3 × 3）；腳坐在船殼上（中線龍骨頂 z 2、兩旁 z 3），頂 z 179 ⇒ 全長 17.7 m、甲板以上 16 m；頂上 9 格 calcet 5 × 3（x 230–234），離頂 2–3 格兩端各一格黑滑輪槽、頂 1 格金帽 |
  | `claude-galiot-01m-yard-main` 三角帆桁（框 265 × 7 × 187） | 外部模型 `yard-main-lateen`，放在主桅子作品裡；at (232.5,116.5,171.5)、pivot (158.5,3.5,75.5)、rotate 0、scale 1 | 1,645 | 31.5 m、斜 35°、吊點離前端 40%（在桅頂下 8 格）；中段粗 0.3 m、兩端 0.1 m；吊點前後 2.5 m 每 6 格一道黑綁紮（兩段綁成）；掛在桅的左舷側（y 115–117，跟桅空 1 格）；固定點 42（pivot、sling、fore、peak、jackstay-01…38） |
  - 帆桁模型 meta：`kind=yard, mast=main, yard=gaff, rig=lateen, sail=main-lateen, length_m 31.5, length_ft 103.3, diameter_in 11.8, pivot_anchor=pivot, turn_axis=z, rotate_z_deg=0`。只有一根帆桁、是三角帆，不碰「方帆的下帆桁不標 boom」那條。
- **桅只做 0.3 m 粗（設計決定）**：
  - 史料 DAS p.135 galère 主桅 30 goües（21.93 m）、周長粗端 60 pouces、細端 40 pouces ⇒ 直徑 0.52／0.34 m；照桅長 17.7 ÷ 21.93 縮 ⇒ 0.42／0.28 m（5 格／3 格）。
  - 中央走道只有 5 格寬（dy ±2）。遊戲的走路格每 2 格取一點、y 取偶數（Blockside 42_hands.js navBuild，NAV_C 2；x 從 hx0 − 4 ＝ 16 起）⇒ 5 格寬的桅把走道在桅那裡的 y 118／120／122 三點全佔掉。
  - ⚠ 一開始以為這樣走道會「斷成兩段」，量了不是：整張走路格照樣連通，因為會從第 13、14 張划手座繞（座 z 23 → 甲板 z 20 → 座 → 走道 z 26，每步 ≤ 3）。真正的差別是**只走中央走道**過不過得了桅：5 格寬過不了（前後要從划手身上翻過去），3 格寬留下 y 118、122 兩條，走道本身照樣通。所以取 3 格。
- **讀數**（設計，`verify_masts.json`，problems 0）：
  - 桅：1,641 格、1 元件、鏡像差 0、跟船殼重疊 0；桅孔 75 格全部由桅填滿。
  - 船殼＋甲板（扣孔）＋船首平台＋spur＋艉台＋桅：73,948 格、1 元件、空腔 0；桅跟船、篷重疊 0。
  - 帆桁：1 元件；世界範圍 x 77–336、y 115–117、z 98–279（前端 fore (335,116,99)、上端 peak (78,116,279)），在組裝件框裡；跟世界上任何格（船、桅、篷）重疊 0、最近空 1 格。
  - 匯入檢查那一段（pivot z 171 往下 10–40 格 ＝ z 131–161、中線 ±4）：桅 279 格。三角帆擺角上限 asin(2.5 m ÷ 10.3 m) ＝ 14.0°。
  - 走路格（照遊戲取樣）：桅之前 3,104 點、主群 2,682（107.28 m²）；桅之後 3,103、主群 2,681（少了 (232,120) 那一點）；≥ 12 點的群都是 12 個。桅旁 (232,118)、(232,122)、桅前後 (226,120)、(238,120)、走道兩端、船首平台、艉台都在主群。
  - 只走中央走道（y 118–122）：桅前後連得通、走道後端到前端連得通（主群 491 點；另一塊 18 點是船首平台前面的船頭尖 x 354–364，步驟 5 就有）。
- **反向對照**（`draft_masts.py --probe=…`，不寫檔）：
  - `r=2.1`（桅 5 格寬）⇒ 桅孔 107 格；只走中央走道斷成 3 塊、桅前後連不通（整張走路格照樣 12 塊）。
  - `pivot=-80`（帆桁吊點往下 8 m）⇒ 帆桁撞到 16 格。
  - `pivot=-40` ⇒ 匯入檢查那一段跟著往下到 z 91–121，照樣 279 格（桅身是直的、一樣粗）。
  - `hole=0`（不刻桅孔）⇒ 桅斷成 2 塊。
- **落格**（每一刀 exit 0、讀回跟清單一樣）：carvevox 75；stampvox 桅 1,641、帆桁 1,645；固定點 42；關聯 1；模型 1。
- **結果帳**（`tools/replay.py`，自己重播 events）：
  - 桅 1,641／1,641、帆桁 1,645／1,645、甲板-main（設計扣桅孔）34,029／34,029：都是缺 0、多 0、色差 0。桅 1 元件、空腔 0、鏡像差 0。
  - 反向對照：甲板不扣桅孔 ⇒ 缺 75；桅整根抬 3 格 ⇒ 缺 45、多 45、色差 19。
  - **引擎組出來的組裝件**（export list links=all）73,948 格 ＝ 設計，缺 0、多 0、色差 0、1 元件、空腔 0（`verify_step7_assembly.json`）。
  - 回讀：關聯 `主桅` meta {kind: mast, mast: main}、turn 0、不鏡像，只有這一條 kind=mast；模型 `yard-main-lateen` 的 at／pivot／meta ＝ 設計，帆桁的 mast=main 對得上；固定點 42／42 格位置一樣。引擎回報的模型外框 (77,115,98)–(337,118,280) ＝ 設計的世界範圍。
- **重跑**：
  - `draft_masts.py` 跑兩次，7 個輸出 sha256 一樣：`main` a0c3e790…、`deck_hole` 14de54a5…、`lateen-main` 39216b4c…、`yards_lateen.json` c8651fe7…、`yards_placement.json` a713c59a…、`verify_masts.json` 1421afa7…、`sheet05_masts_v1.png` 0df28537…（v1 969a9771…：側視圖帆桁畫在桅前面，verifier7 抓到，改成照 y 排、從右舷看桅擋住左舷的帆桁；只有圖變）。
  - plan.json 加了 `rig_build` 之後，步驟 3–6 的四支產生程式重跑，16 個輸出的 sha256 跟步驟 6 記的一樣。
- 過程圖：圖紙 `design/sheet05_masts_v1.png`（1. 右舷側面：桅、帆桁、pivot／fore／peak、匯入檢查那一段；2. 桅孔平面特寫與遊戲的走路取樣點）。3D 照舊等有 GPU 的機器。
### 獨立 verifier（verifier7，唯讀、自己重播 events、照 Blockside 原始碼自己寫 navBuild／findMasts／擺角，不 import 作者的程式；04:56–05:06 UTC；草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier7/`）
- 12 條：作品＝設計、桅的幾何、桅孔（用 `mark=桅孔:begin`／`:end` 匯出 34,104 → 34,029，這一刀確實夾在中間）、組裝件、帆桁、shipcheck「桅」、走路格、0.3 m 的理由與史料換算（60 pouces → 0.517 m → 縮後 0.417 m）、重跑、反向對照 pass；圖紙、Ship_Masts §5 對照 minor；**沒有 fail**。
- 它照遊戲 10_ship.js findMasts 查到：band 照帆桁的**固定點 pivot**（parts 匯出 232.5,116.5,171.5，z 取 floor 171）算，剛好等於模型 at；另外一關 seg（z 131–151、mx ±8）189 格，遊戲要 > 20，過。
- minor 已改：側視圖帆桁畫在桅前面 ⇒ 改照 y 排（sheet05 v2）。
- minor 照實記、不改：
  - §5 寫 gaff 的 pivot 是「桅在 jaws 高度的軸心」，這裡在帆桁自己身上（離桅軸 4 格）；35° 斜角直接用格子雕。兩處都跟皇家號、越嶺號、海鷗號一樣，6 連通沒斷。
  - 桅的 meta 是 `sub=link meta=` 建關聯時寫進去的，不是 `sub=meta part=link` ⇒ 組裝件 meta_log 沒有「主桅」那筆；parts 匯出讀得到，功能沒差。
  - 滑輪槽在 y 120，側視圖被 y 121 那排蓋住、看不到。
- 它提醒、留給後面的：
  - ⚠ **tack 會甩到舷外**：遊戲把三角帆前端左右移寫死 2.5 m（LATEEN_SWING 25 格，照比較寬的 galère 定的），pivot 又偏左舷 0.4 m ⇒ 擺到底時前端 y 91.5–141.5，船首 x 330–335 只有 y 102–138 ⇒ 前端在舷外約 1.15 m（左）／0.45 m（右）。皇家號「浮空纜線」的小號版本；步驟 14 在遊戲裡看，要的話請遊戲那側把 2.5 m 改成照船首寬。
  - `rig=lateen` 這條 meta 不能掉：照一般 gaff 擺到 ±80° 會撞桅 19／27 格（±8°、±14°、±30° 都不撞）。
  - 遊戲認桅的那一段照吊點往下算；吊點往下 16 m 就認不到桅了，以後改吊點高度要重量。
  - 想要更接近史料的粗細，可以把截面改成 5 × 3（只往前後加寬，跟 calcet 一樣），走道 y 118／122 照樣不佔。本小姐留 3 × 3（圓桿不做成扁的），照實記。

- ⚠ 留給步驟 8：帆桁前端 fore (335,116,99) 在船首平台（x 326–352、板面 z 25）正上方 7.4 m，tack 往下綁平台；帆在左舷（帆桁那一舷），照預設風 4.5,−1.5,0 模擬看會不會穿過桅。

## 步驟 8 索具、帆、旗（2026-11-24）

- 已讀：Ship_Rigging §6（繩的色、粗、slack；固定點量在實際的格子上）、§7（帆角綁帆桁模型、三角帆、預設風 4.5,−1.5,0）、§9.1（帆／旗／帆自己的繩的 meta、帆裝三段要排一次）。
- 程式：
  - `design/draft_rigging.py`（新圖紙 06；出處海鷗號 draft_rigging，它出自杉心號的 rig_plan 格式）⇒ `rig_plan.json`、`rig_meta.tsv`、`verify_rigging.json`、`sheet06_rigging_v1.png`。
  - 落格 `tools/build_rigging.py`（anchors／sails／ropes／meta／wind）；掛好的帆布 `tools/check_sails_sim.py` ⇒ `verify_step8_sails.json`（出處海鷗號；多量「離每一件最近幾格」）。
  - 參數在 `plan.json` 的 `rigging`（每一項有 src）；帆形照 `layout.rig.sail`（步驟 3 的桅帆表）。
- **沒有 channels、沒有 ratlines**：三角帆槳帆船的水手順著帆桁爬，不爬繩梯（皇家號、越嶺號、海鷗號同），驗收格那兩項不適用。
- **做了什麼**（05:05 UTC）：
  - **帆 `main-lateen`**：tack ＝ 帆桁 `fore`、head ＝ `jackstay-36`（前緣 ＝ 帆桁 × 0.92 最近的那一個 jackstay）、clew 自由 (180.4,116.5,43.0)；邊 0 沿帆桁釘住；本色 #f2ead8。
    - 三邊 28.71／23.55／16.51 m（設計表 29.0／23.8／16.7，差在 head 取最近的 jackstay）；平面三角形 194.3 m²。
    - clew 照三邊解：在帆桁那一舷的鉛直面（y 116.5）、帆桁下面；離甲板 2.3 m（划手頭上）。
    - meta `kind=sail, mast=main, sail=gaff, set=1`。
  - **長旗 `pennant`**：紅 #7a1a14、4 m，hoist 沿帆桁尖最後 1 m（peak → jackstay-38）、fly 自由；meta `kind=flag, flag=pennant`：不是國旗 ⇒ 不寫 nation；**也不寫 mast**（v2，見下）。
    - v1 掛桅頂：照預設風掛好之後垂到離帆桁 0.98 格（桅頂正下方 8 格就是帆桁吊點，往前飄碰到往前下的那一段、往後飄碰到往後上的那一段）⇒ 改掛帆桁尖（尖的正下方是空的；越嶺號的旗也掛帆桁尖）。
  - **繩 6 條**：
    | 繩 | 從 → 到 | 粗／色／slack | meta |
    |---|---|---|---|
    | `main-shroud-S1…S3` | 主桅右舷 `hound-S` (232,121,165)（calcet 底下）→ 船殼右舷舷頂 x 208／221／234 | 0.5／#2b2620／1.0 | kind=shroud |
    | `main-lateen.sheet-P`／`-S` | 帆 clew → 兩舷舷頂 x 151 | 0.4／#a08458／1.03 | kind=sheet, sail=main-lateen |
    | `main-lateen.tack` | 帆桁 `fore` → 船首低平台板 (330,114,25)（v2；v1 (335,116,25)） | 0.5／#a08458／1.0 | kind=tack, sail=main-lateen |
    - 靜索只拉右舷：帆在左舷（帆桁那一舷），那一舷的靜索會穿過帆（海鷗號步驟 8 的教訓）。
    - 繩腳都不在划手座底下：靜索取「兩張座中間」那一欄；sheet 取「緊接一張座後面」那一欄（往船頭 7 格沒有座與腳踏）。v1 sheet 也取兩張座中間 ⇒ 左舷 sheet 的直線穿過下一張座的腳踏 (158,100,21) ⇒ 改。
  - 固定點 7（船殼 5、主桅 1、船首平台 1；船首平台的路徑是 `甲板-main/船首平台/tack-main`）；分 3 組（standing/shrouds、running/sheets、running/tacks）；作品預設風 4.5,−1.5,0、3 秒。
- **帆裝三段**（Ship_Rigging §9.1；只有一面帆 ⇒ `set 1`）：
  | 帆裝 | 張哪幾面 |
  |---|---|
  | 收帆（1） | main-lateen |
  | 戰鬥帆（2） | main-lateen |
  | 滿帆（3） | main-lateen |
  - 收帆、戰鬥帆都至少一面；只有一面帆，三段分不出來（德羅蒙號、fusta、蓬特號同）。
- **讀數**：
  - 設計（`verify_rigging.json`，problems 0）：
    - 每個固定點都在它那件的實心格上；平面帆離船的格最近 3 格；繩穿過帆 0 條。
    - 繩的直線（拉直、還沒下垂）穿過實心格 0：端點那一件、端點 5 格以內的格不算（靜索從桅面往下那 3–4 格、tack 從帆桁 fore 往下那 1 格）。
  - CLI：`work sub=sails` sails_broken 0（2 面）、sail_max_billow 31.16 格；`sub=ropes` 6 條、ropes_broken 0；`sub=ropecheck` 12 端全 ok、link_overlap 0、link_placed 73,948（`.work/FAR-92/step7/ropecheck_step8.md`）。
  - 掛好的帆布（`tools/check_sails_sim.py`，export obj、預設風）：
    - 主帆 650 個頂點只有 50 個在帆桁裡（就是沿帆桁釘住的那條邊）；離桅最近 4.05 格、甲板 18.19、船殼 30.62；往左舷鼓到 y 85.3、最低 z 43.5（划手頭上）。
    - 長旗 156 個頂點、25 個在帆桁裡，都在 hoist 那一段 1.75 格以內（綁在帆桁上的那條邊）；最低點 (105–108, 109–110, 253) 在帆桁旁左舷 6 格，沒穿過。
  - **反向對照**：風改 4.5,+1.5,0（往右舷吹）⇒ 主帆 2 個頂點穿進桅、離桅 0.46 格 —— 尺會說話。
- **v2（05:29–05:30 UTC）**：
  - **tack 落點挪開**：步驟 9 的 8l 擺在中線 x 328–357、寬 0.75 m ⇒ v1 的 tack（帆桁 fore 正下方 (335,116,25)）離砲 1.0 格（`draft_guns.py` 的「繩離砲」讀數抓到）⇒ 改綁 (330,114,25)：8l 左舷，離砲（含 pierrier 整圈掃過的範圍）3.53 格；tack 長 7.40 → 7.42 m。
  - **長旗拿掉 meta `mast`**：verifier8 照 Blockside 77_colours.js teamFlagsSetup（TASK-1208）查到：作品自己有 `mast=main` 的旗 ⇒ 船掛國籍時，遊戲把主桅頂那面國旗收起來；這面長旗沒有 nation、沒有貼圖 uv、換不成國旗 ⇒ 整艘船不掛國旗，遊戲也不會喊（海鷗號同一個坑，要回頭修）。長旗掛在帆桁尖、不在桅頂 ⇒ 用 `sub=meta part=sail name=pennant meta={"mast":null}` 拿掉（merge 寫入不會自己刪鍵），meta_log 記了前後。
  - 重跑：`draft_rigging.py` 兩次，4 個輸出 sha256 一樣：`rig_plan.json` d0a4b4a7…、`rig_meta.tsv` 53efbc5e…、`verify_rigging.json` 94f73469…、`sheet06_rigging_v1.png` 29beb191…（v1 985324fe…／390edcf2…／66e8fd13…／46de6aa6…）。
  - v2 之後重量：sails_broken 0、ropes_broken 0、ropecheck 12 端 ok、link_overlap 0；掛好的帆布讀數跟 v1 一樣。
- **v3（05:58 UTC，步驟 9 改砲位之後）**：左舷 pierrier 搬到平台上的砲柱（dy −10），v2 的 tack 落點 (330,114) 離它的掃掠圈只剩 0.38 格 ⇒ tack 再挪到 (327,114,25)（8l 砲架尾後面、左舷；離砲 1.62 格），長 7.45 m；rig 檔的 sha 見步驟 9。

### 獨立 verifier（verifier8，唯讀、自己寫尺，不 import 作者的程式；05:10–05:29 UTC；草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier8/`）
- 10 條：帆、長旗、6 條繩、直線穿格、沒有 channels／ratlines、CLI、掛好的帆布、重跑、前端擺出舷外、鼓度 pass；帆裝三段 minor（notes 裡沒有步驟 8 的對照表 ⇒ 上面那張就是）；**沒有 fail**。
- 它自己重量的：
  - 帆三邊 28.714／23.547／16.507 m、194.34 m²；繩腳都不在座（x 149–150、201–202、214–215、227–228）或腳踏（145、210、223、236）上。反向對照：sheet 腳改回 x 156 ⇒ **兩舷**都穿過腳踏（不只左舷）。
  - shipcheck 對繩梯只記資訊、不報 ✗；桅頂水手直接放到桅頂平台、不經繩梯。⚠ 步驟 14：Blockside game.json 的 reale、fusta、dromon 都設 `crew.top 0`，這艘匯入時也要設，不然三角帆桅沒有平台、會報桅頂水手缺人。
  - 帆裝照遊戲 31_sailing.js sailSetLevel（吃 `+m.set`）：全收不張，收帆、戰鬥帆、滿帆都張 main-lateen。
  - 前端擺到底（14.05°）：帆桁尖在舷外左 1.05 m／右 0.25 m；tack 拉長、偏鉛直約 19°，很高才越過船舷線，穿格 0 ⇒ 只是帆桁尖在舷外，看起來而已（量的是 v1 的 tack 落點）。
  - 鼓度 ÷ 前緣 10.9%（海鷗號 9.6%、越嶺號 10.5%、皇家號 10.3／9.5%、持火號 8.0%）；試 10 個風：最鼓 43.7 格、z ≥ 47.9，離座、走道最近 7.57 格，離槳架（照 plan 推算）22.98 格 ⇒ 不會打到。
- 照實記、不改：
  - 右舷 sheet 在 x 175–180 橫過中央走道，離走道頂 1.2–1.6 m（下垂時 0.8 m）；遊戲裡繩沒有碰撞，只是畫面。
  - 風往右舷吹時帆壓過桅、貼到右舷靜索（三角帆反舷的本性；遊戲帆的碰撞預設關）。
  - 靜索在 hound 下面約 5 格貼著桅面；逆風時長旗有幾個點碰到帆桁；ropecheck 有一個舊的 ⚠：船殼關聯的 pivot 400 對現在的 420（turn 0，沒影響）。
- ⚠ 步驟 14 要看：遊戲在主桅頂自己加的陣營旗往船尾飄（−x），桅頂正後方就是往後上升的帆桁（x 220 時帆桁 z 179 ＝ 桅頂）⇒ 旗可能壓在帆桁上。
- 過程圖：`design/sheet06_rigging_v1.png`（右舷側面：平面帆的三角形、繩的直線）。3D 照舊等有 GPU 的機器。

## 步驟 9 砲（2026-11-24）

- 已讀：Ship_Guns（§4.1–§4.4、§4.2「後座」、§4.2.1 砲身與砲座拆兩件、§2.2 砲只跟同一種砲共用模型）、Ship_Turrets §4.5（mount=turret、arc、rate）。
- **砲照史料**：Tim 11-24 04:41 UTC 在 FAR-92 的問題卡選「照史料：8l ×1 加 pierrier ×2」（FUR p.80：船首中間一門最大的、兩旁各一門後膛小砲）。驗收格同時用 `task op=update` 改成這一套（`op=update` 不發酒館；只改步驟 9 那一行，其他 14 格的勾選不變）。
- 程式：`design/draft_guns.py`（新圖紙 07 ⇒ `guns_placement.json`、`verify_guns.json`、`sheet07_guns_v1.png`；出處海鷗號 draft_guns，8l 的擺法照皇家號）；落格 `tools/build_guns.py`。參數在 `plan.json` 的 `guns_build`（每一項有 src）。
- **做了什麼**（05:33 UTC；模型都掛在船首平台子作品 `claude-galiot-01m-bow`，組裝件路徑 `甲板-main/船首平台/…`）：
  | 模型 | 來源（共用件） | at／rotate | meta |
  |---|---|---|---|
  | `8磅砲-F01` | `ridge-two-centurion-01m-gun-8l`（scale 0.5、pivot 砲架尾底 7.5,0,0） | (328,120.5,26)、−90（砲口朝船頭） | kind=gun, gun=8l, deck=main, id=gun-1, port=bow（固定，不標 mount） |
  | `迴旋砲-F02`＋`迴旋砲-F02座` | `apex-one-reale-01m-gun-pierrier`＋`-mount`（scale 0.5、pivot 叉架插銷底 5.5,18.5,0） | (338.5,130.5,34)、0（右舷砲柱頂） | kind=gun, gun=pierrier, deck=main, id=gun-2, mount=turret, arc=-90,40, rate=45, port=bow；座 kind=gunmount, id=gunmount-2, mount_of=gun-2 |
  | `迴旋砲-F03`＋`迴旋砲-F03座` | 同上 | (338.5,110.5,34)、180（左舷砲柱頂） | 同上，gun-3／gunmount-3，arc=-40,90 |
  | 砲柱 ×2 | stampvox 進船首平台子作品（`masks/guns/posts.vox.txt`） | x 338、y 130／110、z 26–33 | 8 格高、色 132（Ship_Guns §4.1 的砲架色）；16 格 |
  - 遊戲砲種表（Blockside game.json `guns`）有 code `8l`（鍵 long8）、`pierrier` ⇒ 不用新砲種、不用做新部件。
- **8l 怎麼擺**：
  - 從「中央走道末端（x 325）＋ 3 格」往船頭找第一個「格心＋八角零碰撞、底層的輪子 12 格都踩在實心上、砲口出了船首胸牆 ≥ 2 格」的位置 ⇒ x_rear 328。
  - 為什麼留 3 格：遊戲把砲的外框外擴 1 格當走路格的障礙（40_crew.js blocked），走路格每 2 格一點 ⇒ 砲架尾要是貼著走道末端（v1 從胸牆往後退，x 326 就零碰撞），走道上不了平台。
  - 砲口 (357.25,120.5,34.25)：出了船首胸牆 4.25 格；砲膛 z 34.25 比胸牆頂 z 30 高，是**從胸牆上方**打出去（胸牆中線那個砲口沒用到；v1 筆記寫「從砲口出去」不對，verifier9 抓到）；砲膛離平台 0.83 m；砲口往前射線不碰船（越過 spur 與艏柱頭）。
  - 後座（砲管長 × 0.3 ＝ 7.95 格）退到底也零碰撞。
- **pierrier 怎麼擺（v2，插在平台上的砲柱頂）**：
  - v1 插在船首平台兩舷胸牆頂（dy ±16、站面 z 30）。verifier9 照遊戲原始碼量到 **fail**：遊戲照砲的外框排砲手站位（40_crew.js makeCrew：外框 ＝ 砲＋座、[b0−3, y0＋10·sg]、高度 b2−8…b2+3），砲手站在 1 格寬的胸牆頂；迴旋砲轉的時候砲手跟著繞轉軸（21_gunnery.js mountStep），獨立的 mount=turret 不在 svRest 的豁免裡、腳下 3×3 都空就掉（32_hull.js）⇒ 轉過 ±17° 掉下平台、變預備水手（pierrier 砲班 1 人 ⇒ 砲沒人開），朝船頭轉 68° 以上落海。galère 船頭對敵，這會常常發生，匯入檢查不報。
  - ⚠ 插在欄杆、胸牆上的迴旋砲（海鷗號舷頂 3 門、越嶺號船首胸牆、皇家號槳架）很可能有同一個問題 —— 回頭要查；要根治是遊戲那側讓獨立 mount=turret 的砲手比照 mt.up 豁免（給 Tim 決定）。
  - v2：插在平台上的砲柱頂（x 338、dy ±10、柱高 8 格 ⇒ 轉軸 z 34）。柱頂夠高 ⇒ 砲尾最低 z 37，掃過 8l（頂 z 36.5）上方不撞；遊戲把砲手排在平台板上 (333.5,131.5,26)／(333.5,109.5,26)，繞轉軸的圈整個在平台上。砲膛離平台 1.28 m、打得過胸牆。
  - `draft_guns.py` 多一把「遊戲砲手站位」的尺：照 makeCrew 算站位、照 mountStep 繞轉軸轉到每個角度、照 svRest 看腳下 3×3 ⇒ arc 內腳下最少 8 格。
  - arc：從正橫往船頭最多 90°、往船尾最多 45°（v1 ±90 的船尾那一端沿著自己的船上空開，verifier9），再扣掉撞到（含 8l、砲柱）、射線被擋、砲手踩空的角度（每 10° 量）⇒ 右舷 −90～+40、左舷 −40～+90。
  - 反向對照：柱高 0 ⇒ 砲撞 8l、arc 0；放回胸牆頂 dy 16 ⇒ 砲手站在胸牆上、轉 ±90° 腳下 0 格。
- **讀數**（`verify_guns.json`，problems 0）：
  - 走路格（照遊戲 navBuild，每個砲的外框外擴 1 格當障礙；pierrier 的砲＋座合成一個外框，跟遊戲 gmtPair 一樣）：砲之前主群 2,679 點（含砲柱）、之後 2,604（被 8l 擋 75 點；pierrier 外框在 z 31 以上、不擋站面 26），≥ 12 點的群都是 12 個；中央走道中段、走道末端、平台後端中線、8l 兩旁、兩門 pierrier 旁都在主群。
  - 繩離砲（步驟 8 的直線；pierrier 照 arc 每 10° 掃一圈）：tack 1.62 格（步驟 8 v3 落點 (327,114,25)；v1 1.0、v2 在 pierrier 搬到 dy −10 之後 0.38），其他 ≥ 95 格。
  - 反向對照（`--probe`）：`gun8_fixed=326`（貼著走道末端）⇒ 平台、三門砲旁 5 個取樣點掉出主群；`gun8_fixed=320` ⇒ 砲口還在胸牆裡（−3.75 格）；`pier_dy=-7`（回到步驟 3 的 dy 9）⇒ 兩門正橫都撞胸牆、arc 0。
- 落格：v1 05:33 UTC 模型 5 個；v2 05:58 UTC 砲柱 stampvox 16（placed 16）、模型 5 個 overwrite（exit 0）；回讀 models.json 的 work／at／rotate／meta 都 ＝ 設計。引擎印的外框：8l (328.5,116.8,26)–(357.5,124.3,36.5)（＝ 本小姐算的）；F02 (337.3,121.3,37.5)–(339.8,139.8,40)、F02座 (336.3,129.8,34)–(340.8,131.3,39.5)，F03 鏡像。
- 結果帳：船首平台重播 2,026 ＝ 平台 2,010＋砲柱 16，缺 0、多 0、色差 0（反向對照：不加砲柱清單 ⇒ 多 16）；**引擎組出來的組裝件** 73,964 格 ＝ 設計，缺 0、多 0、色差 0、1 元件、空腔 0（`verify_step9_assembly.json`）；ropecheck 12 端 ok、link_overlap 0；ropes_broken 0、sails_broken 0。
- **沒做的**：砲具與砲索（驗收格寫「要的話」）：galère 船首的砲沿中央走道後座、平台沒有舷牆可以綁 breeching；pierrier 插在叉架上、沒有砲車。
- 重跑（v2）：`draft_rigging.py`、`draft_guns.py` 各兩次，8 個輸出 sha256 一樣：`guns_placement.json` 3f869f9e…、`posts.vox.txt` 8e38850c…、`verify_guns.json` e005521e…、`sheet07_guns_v1.png` 84bfbb6b…、`rig_plan.json` 37d364d9…、`rig_meta.tsv` 53efbc5e…、`verify_rigging.json` bbac501c…、`sheet06_rigging_v1.png` 68061ede…。
- 過程圖：`design/sheet07_guns_v1.png`（船首平台平面、三門砲的腳印、pierrier 的 arc）。

### 獨立 verifier（verifier9，唯讀、自己寫尺、照 Blockside 原始碼重寫 makeCrew／mountStep／svRest／mountDrop 模擬，不 import 作者的程式；草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier9/`）
- **第一輪**（05:37–05:49 UTC，v1）：9 條 6 pass、2 minor、1 部分 fail。
  - fail：pierrier 砲手站在胸牆頂、轉過 ±17° 掉、朝船頭 68° 以上落海（見上面「pierrier 怎麼擺」）⇒ 改 v2。
  - minor：8l 是從胸牆上方打出去（筆記用詞改了）；arc ±90 的船尾那一端沿著自己的船上空開 237 格 ⇒ v2 往船尾只到 40°。
  - 其他 pass：8l 幾何、輪子、後座、射線；meta gun= 在砲種表（10_ship.js 照 code 對）；走路格；繩離砲；CLI；不做砲具與砲索不會報錯（匯入檢查沒有那一行）；重跑。
- **複驗**（05:51–05:53 UTC，v2）：(a)～(f) 全部 pass，**沒有 fail**。
  - 砲手：照 makeCrew 站在平台板上 (333.5,131.5,26)／(333.5,109.5,26)；每 1° 轉整個 arc，照 svRest 腳下最少 8 格，不掉、不落海。
  - 撞擊：arc 內每 1°，對組裝件（含砲柱）、8l、對面那門 0 格（一整圈也 0）；砲尾從 8l 上方過時離 8l 頂 1 格。
  - 射線：25 m 不被擋；船頭那一端有 9.5 格飛在自己船首／spur 上方（離實心 0.875 m），船尾那一端只剩 2.25 格。
  - 走路格、8l 三個砲手、8l 的放藥箱都在主群；砲柱只多拿掉 2 個取樣點。
  - 照實記、不改（minor）：
    - pierrier 的放藥箱位置（砲尾後面 7 格）越過中線、落在 8l 另一側，跟著砲轉時會進 8l 的外框或浮在走道上方；這艘沒有會轉的裝甲，遊戲的「走得到」檢查照算通過，只是送藥手的畫面會穿過 8l。
    - tack 用模型格的實際表面量，離左舷那門最近 1.11 格（轉 +66°；本小姐用格心量 1.62）——不會撞。
    - 人會從迴旋砲砲管底下走過（砲管離平台 1.15–1.4 m），穿模；座底 9 格只有 4 格踩在砲柱頂，外觀。

## 步驟 10 彈藥庫與甲板物件（2026-11-24）

- 已讀：Ship_Magazine §8、Ship_Fittings §9.7（門與艙蓋）、§9.13（廚房）、§9.14（被打掉怎麼演：照預設，不用標）。
- Tim 11-24 07:06 UTC 在 FAR-92 的問題卡選「繼續做到完成吧 GO」（步驟 10 一路做到 15）。
- 程式：`design/draft_magazine.py`（新圖紙 08 ⇒ `masks/magazine/room.vox.txt`、`magazine_placement.json`、`verify_magazine.json`、`sheet08_magazine_v1.png`；出處海鷗號 draft_magazine）；落格 `tools/build_magazine.py`；組裝件讀數 `tools/check_asm.py`（步驟 10 起共用）。參數在 `plan.json` 的 `magazine`（有 src）。
- **藥艙放艙底**（甲板排滿划手座、放不下藥箱 ⇒ Ship_Magazine「甲板沒有地方放的找船底的藏藥艙」）：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | `claude-galiot-01m-magazine` 藥艙 | 組裝件關聯 `彈藥庫` meta kind=magazine pos=fore powder_lb=200 id=magazine-1 | 1,036 | 船首那段艙底 x 282–303、中線 ±7；牆銅皮 168、松木地板 177（照每一片船底高度一階一階，z 5–7）、牆頂橡木壓條 136；後牆中線門洞 5 格寬、0.6 m 高；裡面淨高 0.9–1.2 m；固定點 blast (292,120,12)、door (282,120,6) |
  | `桶-001`、`桶-002` | 藥艙子作品裡的外部模型 | — | 憲法號的 powder-barrel（scale 0.2、pivot 11,11,0），meta kind=powder powder_lb=100 |
  | `艉燈` | 艉台子作品的外部模型 | — | 三叉戟號的 lantern（scale 0.5、pivot 8.5,8.5,0，皇家號同一套），meta kind=light；坐在步驟 6 的艉燈桿頂 (24,120,62) |
  | `艙蓋-艙口` | 甲板-main 的外部模型 | — | 莫尼特號的 hatch（kind=door open=up），蓋在步驟 5 的格柵上、坐在緣圍頂 z 23；沿 y 每邊大一格，沿 x 被艉台（x 56）與走道台階（x 62）夾住，只能跟開口一樣長；遊戲認到的開口 21 格 |
- 放船首那段：三門砲都在船首平台，遊戲照藥艙找取用點 ⇒ 送藥路最短（史料沒寫 galiot 的藥艙在哪一段，設計決定）。
- **遊戲的取用點**（照 23_powder.js 重寫；verifier10 抓到 v1 兩個錯：彈藥庫外框要照火藥桶、中線是 120.5 ⇒ 改了）：前 (327,126.5,26) 在船首平台右舷、離 8l 1.6 m；後 (268,126.5,19)。步驟 14 匯進遊戲讀到的一樣。
- 不做（設計決定）：小艇（甲板排滿划手座，槳帆船的小艇拖在船後）、絞盤（三角帆桁用滑車、兩隻四爪錨人力起）、羅經櫃（地中海槳船的 bussola 是放在艉台的小盒）、**廚房**：放得下 1.2 × 1.0 m 灶的只有船首平台兩舷，那裡是砲台、迴旋砲砲手的站位與取用點，不在火藥旁放明火（verifier11 提：槳帆船的灶 fogon 一般佔掉左舷一張座，沒查史料；這艘照史料每舷排滿 20 座，不拿掉座）。
- 讀數（`verify_magazine.json`，problems 0）：藥艙跟船重疊 0、鏡像差 0；藥艙的空氣經門洞→艙底→艙口格柵接到外面，全船封閉空腔 0；兩桶碰撞 0、都站在同一階地板；艉燈、艙蓋碰撞 0。
- 反向對照：藥艙往船尾挪 6 格 ⇒ 桶-002 撞牆；拿掉門洞 ⇒ 藥艙變 2,834 格的封閉空腔。
- 結果帳：藥艙重播 1,036／1,036，缺 0、多 0、色差 0；引擎組出來的組裝件 75,000 格 ＝ 設計、1 元件、空腔 0。
- 重跑兩次 sha256 一樣：`room` 77ddd3ee…、`magazine_placement.json` 12ca22b0…、`verify_magazine.json` 93e1fdf6…、`sheet08` 6232ef3b…。
- verifier10（第 1–5 條 pass；取用點預測、廚房理由兩條 fail ⇒ 改了）、verifier11 複驗三處 pass。草稿在 Paperclip 工作目錄 `.work/FAR-92/scorpion/verifier10/`、`verifier11/`。

## 步驟 11 舵、舵柄、錨（2026-11-24）

- 已讀：Ship_Helm §9.8、§9.8.1（舵 kind=rudder＋hinge／axis＋stock-top、舵柄 kind=tiller、操舵鏈）；Ship_Game §9 anchor 那一列。
- 程式：`design/draft_helm.py`（新圖紙 09 ⇒ `masks/helm/{rudder,tiller,strap,cathead}.vox.txt`、`helm_placement.json`、`verify_helm.json`、`sheet09_helm_v1.png`；出處海鷗號 draft_helm，錨照越嶺號）；落格 `tools/build_helm.py`。參數 `plan.json` 的 `helm`。
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | `claude-galiot-01m-rudder` 舵 | 組裝件模型 `舵`，at ＝ pivot ＝ 鉸鏈點 (44.5,120.5,3) | 265 | 艉柱舵：鉸鏈往後傾 45°（艉柱 z 3–38 每一層都在它後面 ≥ 2 格的支撐直線；艉柱往後凸 ⇒ 縫 2–11 格）；舵葉弦長水線下 0.9 m、往上收到 0.3 m；沿鉸鏈 5.2 m（DAS p.129 galère 的舵 25 pieds）；stock-top (6,120,40) |
  | `claude-galiot-01m-tiller` 舵柄 | 組裝件模型 `舵柄`，同一個 at／pivot | 18 | 從舵頭頂往船頭伸到 x 22（離舵軸 1.55 m、艉柱頭上方、離艉台站面 1.1 m）；tiller-end (22,120,40) |
  | 舵頭鐵箍 | stampvox 進艉台子作品 | 48 | 舵頭在艉柱頭後面約 0.8 m；遊戲照 stock-top 旁 8 格內的船格當舵的「腳」（10_ship.js anchorNear），沒有它找不到 ⇒ 開局舵就掉；黑鐵臂 z 37–38、x 12–19 接艉柱頭 |
  | `錨-S`、`錨-P` | 船首平台子作品的模型 | — | 越嶺號的四爪錨（scale 0.6 ⇒ 1.4 m）×2（FUR p.80：galeotta 兩個錨），掛在 x 332 胸牆外、rotate ±45；錨冠 z 15.9（水線上 0.49 m）；meta kind=anchor anchor=bower |
  | 吊錨木 | stampvox 進船首平台子作品 | 10 | 從胸牆頂外緣伸到錨環正上方，錨環貼在它底下（verifier11 抓到錨看起來懸空） |
  - 船殼固定點 hawse-S (332,138,29)、hawse-P (332,102,29)。
  - 舵 meta：kind=rudder hinge axis (−0.7071,0,0.7071) max_deg 35 turn_axis=hinge spin rudder ±35 lag 0.3；舵柄 kind=tiller、spin 同舵、spin_pivot／spin_axis ＝ 舵的鉸鏈與軸。
- 舵柄只能這麼短：艉台只有 0.9 m 寬、上面有篷，艉燈桿立在 x 24；舵柄 +3 格 ⇒ −15～15° 掃到燈桿（反向對照）。遊戲的舵手站在舵柄端往前 2 格 (25.5,120.5,29)，燈桿夾在中間（照實記；燈桿是步驟 6 放的）。
- 讀數（`verify_helm.json`，problems 0）：舵、舵柄每 5° 從 −35 到 35° 碰船、篷、鐵箍 0，不進艉燈外框；錨碰船 0、離船最近 1.19 格、碰吊錨木 0；stock-top 8 格內找得到鐵箍 (12,120,38)。
- 反向對照：gap 1 ⇒ 舵每個角度碰 8 格（舵葉前緣的格角斜著碰到 45° 的艉柱）；鐵箍末端只離鉸鏈 2 格 ⇒ −30° 以上碰到。
- 結果帳：舵 265、舵柄 18 重播缺 0／多 0／色差 0；艉台 ＝ poop＋鐵箍 1,302、船首平台 ＝ bow＋砲柱＋吊錨木 2,036，都缺 0／多 0／色差 0。
- 重跑兩次 sha256 一樣：`rudder` 46e7535a…、`tiller` 2bd3ec55…、`strap` a7800801…、`cathead` dcde19f9…、`helm_placement.json` 42c6dc89…、`verify_helm.json` e917ff29…、`sheet09` 0b31795d…。
- verifier11（唯讀、照原始碼重寫 anchorNear／helmGripOf）：沒有 fail；minor 已照改（吊錨木、說明）或照實記（鐵箍被打掉舵和舵柄都掉）。

## 步驟 13 動力：槳（2026-11-24）

- 已讀：Ship_Oars §9.10、§9.10.1（皇家號的做法）、§9.10.2-5（跟其他模型也要量）。
- 程式：`design/draft_oars.py`（新圖紙 10 ⇒ `masks/oars/{apostis,oar}.vox.txt`、`oars_placement.json`、`verify_oars.json`、`sheet10_oars_v1.png`；元件照皇家號、擺法照海鷗號；槳架的格子照步驟 3 的 layout.py build_apostis）；落格 `tools/build_oars.py`。參數 `plan.json` 的 `oars_build`。
- **越嶺號的槳（7.2／6.6 m、一人一支）不合 ⇒ 新做一件**：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | `claude-galiot-01m-apostis` 舷外槳架 | 組裝件關聯 `舷外槳架` | 3,508 | 縱樑（dy 30–31）、兩頭 joug、每張座一個托架、每張座一根槳栓（座 −2） |
  | `claude-galiot-01m-oar`、`-oar-aft` 槳元件 | 0.05 m、框 7×166×47、同一份 683 格 | — | 水平投影 8.2 m（舷內 2.6、舷外 5.6；沿軸實長約 8.4 m，verifier13 量）、畫在約 12.6°；槳葉 1.2 × 0.16 m；pivot (3,52,29)、blade (3,164,4)；seat：-oar (3,22,15)、-oar-aft (3,11,12) |
  | `oar-S01…S20`、`oar-P01…P20` | 槳架子作品裡的模型 | — | 槳在座 −4（槳栓在它船頭側 2 格）；at 縱樑頂＋1＋1.0；右舷 rotate x −5.39～−1.90°、左舷反號＋mirror=y；第 1–3 張座的 6 支用 -oar-aft、rowers 2，其他 34 支 rowers 3 |
- 船尾三張座只排 2 人：槳手站的那一排甲板內緣半寬只有 0.9–1.3 m，遊戲從 seat 往船裡每 6 格排一人，第 3 人會站到中央走道上或跑到對舷 ⇒ 設計決定（HAE f16r 寫船尾段常 4 人；遊戲的排法 4 人要 seat 在 dy ≥ 21，這艘全船都排不下）。全船槳手 114 人（步驟 3 寫 120）。
- 讀數（`verify_oars.json`，problems 0）：40 支碰撞（船、槳架、槳栓、舵、舵柄）0；不進其他模型外框；槳跟槳共用格 0；槳葉中心離水面 0.00 m（40／40）；照遊戲 oarCrew 模擬槳手 114／114 都站在甲板上、沒被挪；每支槳 pivot 8 格內有船格（≥ 89 格）；槳架鏡像差 0。
- 反向對照：S05 往下沉 3 格 ⇒ 只有它報 6 格；拿掉 P20 ⇒ 左舷 19 支、槳手 111。
- 引擎印的外框跟自己照「先鏡像再轉」算的一樣（verifier13：最大差 5e-5），左右舷 40／40 互為鏡像。
- 結果帳：槳架 3,508、兩件槳元件 683 重播缺 0／多 0／色差 0；組裝件 links=all 78,566 格 ＝ 設計、1 元件、空腔 0。
- 重跑兩次 sha256 一樣：`apostis` a93394f5…、`oar` 7ce3caed…、`oars_placement.json` 5ab90917…、`verify_oars.json` e7a437bc…、`sheet10` 8d0fef34…。
- 照實記（verifier13）：遊戲的划槳動畫（繞槳座直立軸掃 ±30°、回槳抬 12°）有 7 支會掃過右舷靜索 S2、S3 和兩舷 sheet，S20／P20 往船頭掃到底抬槳時碰到船首平台 —— 只是畫面，遊戲照靜止外框算。

## 步驟 14 給遊戲的 meta 與匯入（2026-11-24；Paperclip FAR-92）

- 已讀：Ship_Game §9／§9.4／§12、Ship_Render。
- meta：船殼關聯 `kind=ship, waterline_z=11`（DWL 那一格 z 10 的頂上）；其他 kind 各步驟標過。`admin.py ids` 發了 9 個 id、寫回作品（63／63 件都有 id）。ropecheck 12 端全 ok。
- render：不標。新做的件（船殼、甲板、桅、帆桁、舵、舵柄、槳、槳架、藥艙）全木頭；桶、砲、錨、燈、艙蓋引用現有元件。
- **匯入**：Blockside worktree `.work/FAR-92/blockside-aqrab`（分支 `feat/ship-aqrab`，從 `dev` 58decd9 開）⇒ `admin.py import --only` ⇒ ids ⇒ build --ship ⇒ showlod、ancbake ⇒ shipcheck、ladcheck。commit **`80d559d`**，用 `blockside-push` 推到 GitHub `tim099/Blockside` 的 `feat/ship-aqrab`（11-24 08:30 UTC）。
  - `.vxk`：78,566 格、**checksum 3935879961**、框 420×241×300、0.1 m／格、繩 6、帆 2、模型 55。
  - 遊戲那側的設定一起填（海鷗號交船時漏了、FAR-87 補的那三項）：`cfg.base` 6.5 節（設計決定，跟越嶺號同一列）、`geo`（水線 z 11、座間甲板 z 19、走道與平台 z 26–27、船中舷頂 z 18、桅頂 z 179；陸戰隊沿舷站 marineY 8、軍官站艉台 qx 25）、`crew`（軍官 1、舵手 1、陸戰隊 12、桅頂水手／航海士／軍需官／船醫 0、handsK 0.05）⇒ 選船卡 66 噸、31.9 m、船員 139。
- **匯入檢查 ✗ 0、⚠ 7**（都看過）：
  - 砲 3 門 0 門缺人；槳 40 支、槳手 114／114；操舵「舵令 ⇒ 舵柄 ⇒ 舵 100%」、兩舷差動；錨兩舷模型＋ring＋hawse；艙蓋 1 扇（開口 21 格）；浮空 0；開場就摔：沒有；甲板連通 1 層都接得到。
  - ⚠ 火藥 ×3：遊戲把前取用點擺在船首平台右舷後角，8l 佔掉平台中間 ⇒ 送藥手站的那一角跟中央走道不連通，照直線走（只有 1.5 m）。遊戲 findSpot 沒量取用點那一角接不接得到；造船這側要改，得在平台上擺東西去擋它的找法，不做。
  - ⚠ 穿模 ×2：後取用點的桶擺進划手座（遊戲那側，23_powder.js makeStations）。
  - ⚠ 漏水 ×2：再多載 139 噸（吃水再深 1.2 m）才從船殼的斜角縫進水。
- 樓梯自檢：沒有梯子，✗ 0。
- 順便量了（Tim 選「請遊戲那側改」迴旋砲砲手掉落）：遊戲那側 11-22 已經修好（Blockside `c6d1523` mountStand，已在 `dev`）；在這個 worktree 跑海鷗號、越嶺號、皇家號的 shipcheck，「開場就摔」都是沒有。
- 遊戲裡 W／S 走過帆裝（無頭 Chrome，`.work/FAR-92/step14/sails/`）：滿帆、收帆、戰鬥帆都張主帆；全收主帆收成一捲留在帆桁上；收帆時船靠槳照樣在走。

## 步驟 15 交船（2026-11-24）

- 已讀：Ship_Game §10。
- **checksum**：`feat/ship-aqrab` 成品裡蠍子號的檔頭，跟 `_cache` 從作品匯出的那份，都是 **checksum 3935879961**、78,566 格、420×241×300、繩 6、帆 2、模型 55（`.work/FAR-92/step14/heads_aqrab.log`）。合不合進 `dev` 由 Tim 決定；合進去之後在 `dev` 再對一次。
- **給遊戲那側填 geo 的高度**（格座標、一格 0.1 m；已照這些填進 `config/ships/aqrab.json`）：
  | 項目 | 高度／位置 | 出處 |
  |---|---|---|
  | 水線 | z 11（吃水 1.1 m） | 步驟 3；匯入檢查讀回 |
  | 甲板（站面） | 座間甲板 z 19–22（跟著舷弧）；中央走道頂 z 25–28；船首平台 z 26；艉台 z 27–29 | 步驟 5、6 |
  | 舷頂 | 船中 z 18；划手座與槳架縱樑頂 z 22–25 | 步驟 3、13 |
  | 砲口 | 8l (358.75,120.5,34.25)；pierrier (349,130.5,38.75)、(349,110.4,38.75) | 遊戲讀回的 muz |
  | 桅頂 | z 179（沒有桅頂平台） | 步驟 7 |
  | 帆頂 | 帆桁 z 98–279（帆的 head 在 jackstay-36） | 步驟 7、8 |
  | 船殼前後端 | 遊戲 hx 12–413（含 spur）；兩柱頂 x 20–371 | 遊戲讀回 |
- **換船檢查表（§10）**：
  | 項目 | 結果 | 讀數／理由 |
  |---|---|---|
  | ropecheck | ✓ | 12 端全 ok，沒有 bind／snap |
  | 組裝件名稱、船殼帶 sub | ✓ | 「蠍子號」；船殼 tags=sub |
  | meters_per_voxel、模型 scale | ✓ | 子作品都記了（槳元件 0.05）；模型都明寫 scale |
  | 開工前查現有元件 | ✓ | 步驟 2 的表；新做的槳元件理由見步驟 13 |
  | 槳帆船 | ✓ | 每張座一支、20／20、碰撞 0；cfg.base 6.5；槳手 114／114 |
  | 撞角 | 不適用 | spur 壓斷槳，不標 kind=ram（步驟 6） |
  | 爐灶 | 不適用 | 不做廚房（步驟 10） |
  | 從船殼伸出去的槳 | 不適用 | 槳靠在舷外槳架上 |
  | 缺的砲種或裝備 | 不適用 | 8l、pierrier 都在砲種表 |
  | 外部模型帶 meta 與固定點 | ✓ | 砲、座、帆桁、桶、燈、艙蓋、錨、舵、舵柄、槳；沒有羅經櫃、絞盤、小艇（步驟 10） |
  | 舵是模型、stock-top | ✓ | 匯入檢查 ✗ 0、浮空 0（開局沒掉） |
  | 舵與舵柄跟著轉 | ✓ | spin ±35°；匯入檢查列出舵、舵柄 |
  | 操舵鏈 | ✓ | 舵令 ⇒ 舵柄 ⇒ 舵 100% |
  | kind=ship、waterline_z、高度 | ✓ | 水線 z 11；上表 |
  | 梯子、樓梯自檢 | 不適用／✓ | 只有一層、沒有梯子；ladcheck ✗ 0 |
  | ratlines | 不適用 | 三角帆沒有 ratlines（步驟 8） |
  | 彈藥庫裡的火藥桶 | ✓ | 藥艙兩桶；取用點 2 個（⚠ 連通，見步驟 14） |
  | 甲板 meta | ✓ | kind=deck、level 0、floor、walk、walk_y、thick 2 |
  | 三角帆桁 | ✓ | yard=gaff＋rig=lateen＋fore |
  | 材質、金屬板、光滑金屬、窗、艙房 | 不適用 | 全船橡木 78,566 格；沒有金屬件、窗、艙房 |
  | 砲零碰撞、砲口在殼外 | ✓ | 步驟 9 |
  | 砲身與砲座 | ✓ | 座 2 件配到 2 門 |
  | 跟著砲轉的裝甲、蒸汽艦 | 不適用 | 沒有 |
  | 迴旋砲每個角度不穿模 | ✓ | 步驟 9（每 1° 量） |
  | 露天的出入口有門 | ✓ | 艙蓋 1 扇、開口 21 格 |
  | 砲門蓋板 | 不適用 | 沒有砲門 |
  | ropes／sails／models_broken | ✓ | 0／0／0（繩 6、帆 2、模型 55） |
  | 帆、旗、帆自己的繩 meta | ✓ | `sub=meta part=sail`：2 面、沒有 meta 0 |
  | 帆裝三段 | ✓ | 表在步驟 8；遊戲裡 W／S 看過（步驟 14） |
  | 組裝件 1 元件、空腔 0、overlap 0、鏡像 | ✓ | stats structure=1 links=all：78,566 格、1 元件、空腔 0、overlap 0、clipped 0 |
  | 產生程式重跑逐位元組相同 | ✓ | 每一步重跑兩次 |
  | 匯出 vxk、對 checksum | ✓ | 3935879961（上面） |
  | 匯入檢查 ✗ 0、⚠ 看過 | ✓ | ✗ 0；⚠ 7 見步驟 14 |
  | spin 列得出來 | ✓ | 舵、舵柄 |

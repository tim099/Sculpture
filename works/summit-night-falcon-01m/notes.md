# 夜隼號（Night Falcon）——《桅頂的賭注》的船（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-13（叮 tavern seq 23130；TASK-0529）：「試著把妳小說中的船造出來吧」。
造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`；大型作品流程見 `Sculpture_Blueprint_Build.md`。

## 規格的本尊（依序）
1. 漫畫船設 `ArtGallery/Comic/summit-masthead-bet/Characters/night-falcon.md`（summit 2026-08-10 寫；TASK-0457 漫畫照它畫）
2. 定稿圖 `references/night_falcon_v1.png`（原檔在 ArtGallery 同一本漫畫的 RawImages）—— ⚠ 圖是**看的**，不是量的；圖上的數量（砲門、帆）都是目測
3. 小說正文 `Books/summit-masthead-bet/`、`Books/summit-masthead-bet-sequel/`

## 第零階段 拍板（2026-10-13，wake #117）

每個數字標一種出處：**原文**（小說／船設）／**參考資料**（附出處）／**設計決定**（我定的，沒有量）。

### 不能動的（原文）
| 項目 | 規格 | 出處 |
|---|---|---|
| 桅數 | 雙桅 | 船設 §一（「三桅大艦進不了退潮礁區」）；正文 001:11「雙桅快船」 |
| 吃水 | 極淺：比圖恩的鴴號只深半尺 | 正文 004:5；船設 |
| 性格 | 小而快、轉向快，靠靈活不靠火力 | 船設；正文 007:41 |
| 舵輪中央 | 俯衝的隼徽記**被剝走、留一塊淺淺的疤**（007 起的狀態） | 正文 002:79、007:41；船設 |
| 船名 | 船身**不寫**船名（這片海靠旗與徽記辨識） | 船設 §二 |
| 人數 | 31 人 | 續篇 000:23 |

⚠ 原文自己有衝突：正文 000:21（「桅杆——三根」）、005:9（「三桅船影」）寫成三桅 ⇒ 照船設與 001:11 造**雙桅**；正文兩處另外更正（TASK-0529 最後一格）。

### 外形（定稿圖，看的）
- 帆裝是 **brigantine**：前桅全橫帆（course／topsail／topgallant）、主桅縱帆（gaff＋boom）＋頂上橫帆；船首斜桅＋三角帆。
- 船首像：張翅的隼。船尾：窗廊。每舷約 6 個砲門（目測）。
- ⚠ 定稿圖桅頂畫的是骷髏旗 —— 原文只說「夜隼號的旗」，沒寫圖案 ⇒ 旗的圖案**未定**，⛔ 不照圖做骷髏。

### 尺寸（參考資料＋設計決定）
參照船：**Oswego 的雙桅橫帆船（1756）** —— 龍骨 60 ft、船寬 21 ft、艙深 7 ft、160 噸（Maritime History of the Great Lakes 對一塊沉船殘片的推定 —— ⚠ 是推定，不是完整紀錄；只讀到搜尋摘要，沒逐頁讀）。
角色參照：皇家格林威治博物館一件約 1820 年的 brigantine 模型（10–12 門砲；館方說明這類小船「快、人手少，用來送急件和偵察」）—— 船身 112 ft 太大，只拿角色不拿尺寸。

| 項目 | 值 | 格 | 出處 |
|---|---|---|---|
| 龍骨長 | 18.3 m（60 ft） | 183 | 參考資料（Oswego） |
| 甲板長 | 約 21 m | 約 210 | **設計決定**：龍骨長 × 1.15 算前後傾斜 —— 1.15 是估的，沒查 |
| 型寬 | 6.4 m（21 ft） | 64 | 參考資料（Oswego） |
| 艙深 | 2.13 m（7 ft） | 21 | 參考資料（Oswego） |
| 吃水（船殼，插板收起） | 1.5 m | 15 | **設計決定** |
| 吃水（插板放下） | 3.0 m | 30 | **設計決定** |
| 砲 | 每舷 6 門、小口徑 | — | 定稿圖目測＋設計決定（口徑等砲的階段再定） |

📌 吃水這格是**設計判斷，不是量的**：照字面「比划槳小艇只深半尺」，一艘 31 人、12 門砲的雙桅船吃水會只剩 0.5 m 上下，船撐不住。
解法（設計決定）：船殼平一點、靠**中插板**（centerboard）抗橫漂 —— 參照兩桅縱帆船 Mercantile 的插板槽（主桅為了讓槽偏離中線；搜尋摘要，沒逐頁讀）。
現代仿古船 SV Black Jack（87 ft、最大吃水 6 ft ≈ 1.8 m）可當「這麼淺的雙桅船真的存在」的旁證 —— ⚠ 鋼殼、有引擎，不是史料。
⇒ 鴴號跟著讀成「比夜隼號淺半尺」的測量艇（約 1.35 m），不是吃水幾公分的小划子。

### 座標與比例（設計決定）
- 比例 **0.1 m／格**（跟憲法號、餘燼號同）—— 理由：同比例才能進 ame《憲法號對轟》同場、造船規格的砲／繩／帆數值可以沿用。`meters_per_voxel 0.1` 已記（work.json 讀回）。
- 空間 **384 × 161 × 320**：X 船長、船頭朝 +X；Y 船寬、**中線 y = 80**；Z 高度、z 0 ＝ 龍骨底面（插板放下時伸出龍骨底，到時候 z 往上整體抬，見 todo）。
- 舷：P（左舷）＝ y < 80、S（右舷）＝ y > 80。鏡像：格 y ↔ 160 − y（80 那一格是自己）；一舷子作品的另一舷關聯 mirror=y、**at.y ＝ 161 − at.y − 高**（憲法號是 321，因為它寬 320）。
- 子作品命名：`summit-night-falcon-01m-<部件>`，建立時帶 `tags=sub`、parent_work ＝ 本件。

## 參考資料
- Royal Museums Greenwich — Service vessel; Brigantine; 10-12 guns：https://www.rmg.co.uk/collections/objects/rmgc-object-66659
- Maritime History of the Great Lakes（Oswego brigantine 殘片）：https://images.maritimehistoryofthegreatlakes.ca/126300/data
- Tall Ships Adventure（SV Black Jack）：https://tallshipsadventure.org/our-fleet
- Mercantile（centerboard schooner）：搜尋摘要引的是 NPS 國家史蹟登錄文件，結果裡有兩份 npgallery 文件（`NRHP/GetAsset/NHLS/82005265_text`、`GetAsset/5152a2f3-…`）—— ⚠ **沒核對哪一份是 Mercantile**，用到插板槽細節前要打開讀

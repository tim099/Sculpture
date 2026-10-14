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

## 階段一 新圖紙 01：線形（2026-10-13，wake #117）
設計 `design/plan.json`（lines 段，每個數字有 provenance）；產生 `design/draft_lines.py` ⇒ `sheet01_lines_v1.png`、`compare01_concept_v1.png`、`masks/hull/shell_preview.vox.txt`、`verify_lines.json`。重跑四個產物逐位元組相同。
- 曲面：半寬 hb(x, z) ＝ 船中剖面 hb_mid(z) × 豐滿度 f(ξ) ＝ (1 − ξ^a)^b；船中剖面 ＝ 斜升 8° 的平底 → 舭部 R 13 → 直舷到 z 24 → 舷頂內收 1.5。龍骨／艏柱／艉柱半寬 1.5。方艉：z ≥ 18 在艉板面截斷。
- 讀數（verify_lines.json）：水線長 19.35 m、水線寬 6.23 m、吃水 1.5 m；排水體積 67.4 m³ ⇒ **69 t**（海水）；Cb 0.372、Cm 0.573、Cp 0.65、Cwp 0.687；L/B 3.1、B/T 4.16；浮心在水線長 51.7%（從船尾量）。
  - ⚠ Cm 低是因為吃水 15 格裡有 4 格是 3 格寬的龍骨（船身本體吃水 11 格），不是剖面瘦。
  - ⚠ 69 t 不能跟 Oswego 的「160 噸」比：那是載重噸位（burthen），不是排水量 —— 兩把尺量的不是同一件事。
- 平順度：七條水線（6、9、12、15、20、25、30）全部單峰；沿 x 的二階差分最大 0.60（舷弧那條）。
- 殼的預覽（厚 4 格）：71,116 格、1 個元件、封閉空腔 0、左右鏡像差 0；貼進**草稿**看 3D（`overlays/stage1_shell_preview_yaw{45,0,-135,135}.png`（檔名照鏡頭 yaw 角；🩸 第一版照角度猜成 q／side／stern／bow，打開看才發現三個名不符實 —— 只記角度，不替畫面下結論）），看完 discard（作品 0 格、events 空）。
- 🩸 v1 的錯：方艉那幾層的後端點在 z 18 直接切換 ⇒ 船尾 0、1 站剖面在翼艉板高度折出台階。改成 smoothstep 漸變（值與斜率都連續）⇒ 台階消失；排水量不變（改的是水線以上）。
- 定稿圖第三方對照（`compare01_concept_v1.png`；龍骨底與船長照**像素量**對齊）：定稿圖龍骨底 y 497（x 94..414 逐欄最低深色像素）、船中欄杆 y≈390（±8）、船長 艉廊外緣 x≈54 → 艏柱頂 x≈545（兩端目測 ±10）⇒ 欄杆高 ÷ 船長 ≈ **0.22**；船尾有後甲板＋船尾樓。本線形到舷弧 0.14、加 1 m 舷牆 0.185 ⇒ **定稿圖的船舷約高兩成**（跟加了舷牆的比）。
  - 🩸 第一版是目測（龍骨 y 545、船長 440 px）⇒ 寫成「0.24、約高三成」，對照圖還標「龍骨底兩邊同一條線」—— 其實差 48 px。做漫畫時看頁圖才發現，改用逐欄掃像素重量。
  ⇒ 拍板（Tim 2026-10-13「都交由妳決定（這是妳的作品）」⇒ summit 定）：水線以下不動，水線以上加後甲板＋舷牆；⛔ 不整體加高（重心）。做在階段二。

## 階段二 新圖紙 01 v2（舷牆、後甲板）＋ 新圖紙 02（骨架與肋骨）—— 落格（2026-10-13 午，wake #117）
**線形 v2**（`draft_lines.py`；plan.json `lines.upper`）⇒ `sheet01_lines_v2.png`、`compare01_concept_v2.png`、`verify_lines_v2.json`。`--v1` 重產階段一四個產物，跟提交時的 md5 逐一相同（v1 不受影響）。
- 舷弧改當主甲板在船邊的高度；船腰舷牆 1 m；後甲板從艉板到 x 138（7.8 m），高 1 m，舷牆 0.9 m；斷口往前 6 格 smoothstep 降回船腰。
- 水線以下：舷牆與後甲板一格沒動到；後來補柱子的根（見下）⇒ 69.0 → **69.1 t**、Cb 0.372 → 0.373。
- 跟定稿圖比（舷牆頂 ÷ 船長；定稿圖是 2 倍放大圖**目測** ±4 px）：船腰 0.181 vs 定稿圖實心舷牆頂 0.183／欄杆頂 0.202；後甲板 0.230 vs 0.287。⇒ 船腰對上了；**後甲板定稿圖仍高約兩成半**，照拍板不追（再抬 1.3 m 是風阻與重心，對淺吃水的船是錯的方向）。
- 定稿圖的後甲板斷在 x≈150、主桅穿過它的前緣；我收到 x 138，讓主桅站在船腰（一般做法）—— 桅位等桅檣階段定。定稿圖船頭那一階（x≈205 起）不做：船頭舷弧本來就抬 1.2 m。

**做法拍板：照真船順序（骨架 → 肋骨 → 外板），不做實心殼。** 理由：① 0.1 m 格子分得出肋骨（2 格）與空檔（3 格）；② 對轟裡打穿外板會露出肋骨，不是一整塊實心；③ 造船記每一階段要有東西可記。

**新圖紙 02**（`design/draft_hull.py`；plan.json `framing`；`sheet02_frames_v1.png`、`verify_hull.json`、`masks/frames/*.vox.txt`）。重跑逐位元組相同。
- 深度 ＝ 格心到最近船外格的距離（EDT，頂面往上複製 ⇒ 不長蓋子）：d ≤ 1 是外板那一層（**留空，階段三鋪**），1 < d ≤ 3 是肋骨那一層。
- 骨架（照順序認領）：龍骨 2,196、艏柱 564、艉柱 545、deadwood 船尾 677／船頭 411（船殼半寬 ≤ 3 格的地方肋骨放不下）。deadwood 的碎片（貼在艏柱內側、艉柱兩旁）歸給那根柱子。
- 肋骨：從 x 175 往兩頭每 5 格一根、2 格寬，40 根 18,333 格；頂離舷牆頂 0.008–0.996 格（每根都到舷牆頂，當舷牆的 stanchion）。
- 艉柱後面（x < 70）不立肋骨，改成橫的 transom：從翼艉板（z 18）起每 5 格一層、2 格厚，繞過船尾、在中線釘上艉柱 —— 7 層 1,580 格；tr+01～+05 在中線被艉柱隔成左右兩半（照設計）。
- 🩸 第一版的兩個錯（都是落格前在讀數上看到的）：
  1. 艉板那一區用 EDT 的「最近船外格」方向判斷 ⇒ **左右差 360 格**：平手時兩舷挑的方向不同。改用座標判斷（兩舷對稱）。
  2. 艉板用直的 counter timber ⇒ **散件 878 格**：船尾在翼艉板那一層只有艉柱那麼寬，counter timber 腳下沒有東西接。改成橫的 transom（真船也是這樣釘在艉柱上）⇒ 散件 0。
- 落格：先打標記 `stage2:begin`（start），試貼龍骨（placed 2,196 ＝ 清單），再照 `verify_hull.json` 的 stamp_order 逐根 stampvox（at 0,0,0、expect_pixels），每刀讀回 placed，對不上就停。53 根全貼，0 → **24,225 格**；`stage2:end` 在第 53 個事件。
  - 🩸 **第三個錯（落格之後才看到）：柱子的根是空的。** 疊圖（作品疊新圖紙 01 v2 側面）上，船頭龍骨前端到艏柱彎曲那一段（x 253–261、z 0–3）圖紙的輪廓線在那裡、作品是空的。追到階段一 `Hull.hb` 的 `keel_zone`：本意「龍骨只在龍骨長度內」，卻把艏柱的根（forefoot）當船外排除了。結果帳照樣全綠 —— 作品＝設計，錯的是設計。
    - 第一版探針只放在肋骨站上，船頭底下一根都沒有 ⇒ 數字量不到，是眼睛看到的。補一組沿艏柱前緣／艉柱後緣的探針（z 0、1、2、3、10、25、40）—— 它馬上量到船尾也有同一個病：艉柱根部 z 2–3 那一欄（x 69）也是空的（stern_gap 0.56、0.78，其他都在半格內）。
    - 修：v2 拿掉 `keel_zone`（前後已經由艏柱面、艉柱面框住）；v1 照舊（`--v1` 重產四個產物 md5 不變）。新清單是舊清單的超集（艏柱 +36、船頭 deadwood +39、艉柱 +6，拿掉 0）⇒ 照補格重貼三份，placed 36／39／6。24,225 → **24,306 格**；`stage2:end` 移到第 56 個事件。
  - 迴圈自己停了兩次，都是我的讀數管道：`grep -P` 在這個 locale 不能用（讀不到 placed）、python 在 Windows 印出的行尾帶 `
`（"539
" ≠ "539"）。兩次那一刀其實都成功，從下一根接著貼。
- 讀數（作品落格之後）：
  - 結果帳：53 份清單的聯集 vs 作品 export list ⇒ 24,306／24,306，缺 0、多 0、顏色不同 0（補格後重跑）。
  - 結構（引擎 `stats structure=1 mirror=y:80`，跟我的 python 不同路）：1 個元件、空腔 0、左右差 0。
  - 圖紙那一邊出發的探針（`design/check_hull.py` ⇒ `verify_hull_post.json`）：x 95／135／175／215／245 五站，肋骨頂離舷牆頂 0.016–0.903 格；DWL 那一層船殼外面到肋骨最外那格的格心 1.30–1.81 格（設計 1–2：外板 1 格＋半格）。
  - 沿柱子的探針：中線那一格離艏柱前緣 −0.41～0.48 格、離艉柱後緣 −0.44～0.33 格（都在半格內 ＝ 格心判斷的量化誤差）。
  - 反向對照：作品清單整份偏 3 格（z、y、x 各一次）⇒ 肋骨站十根、柱子十四根探針全報 3。
  - 🩸 第一版探針在 y 偏 3 時報 **0**：我拿「偏移後的中線」當基準，尺跟著作品一起動。改成圖紙的中線（y 80.5）之後才報 3。
- 過程圖：`overlays/stage2_frames_yaw{45,135,-135,-45}.png`（檔名＝鏡頭 yaw 角）、`overlays/stage2_work_vs_lines.png`（作品疊新圖紙 01 v2 側面）。

## 階段三 新圖紙 03：外板、插板槽、塗裝 —— 落格（2026-10-13 午，wake #117）
設計 plan.json `planking`；產生 `design/draft_planking.py` ⇒ `sheet03_planking_v1.png`、`verify_planking.json`、`masks/planking/*.vox.txt`（9 份）。重跑逐位元組相同。
- **插板槽**：走中線、穿過龍骨，x 158–191（3.4 m），槽頂 z 22（水線上 0.7 m）；放在兩根桅之間（主桅在船腰 x 138–158、前桅 x > 192）⇒ 桅不必挪。槽壁 y 79／81、兩端 headledge、槽頂蓋，104；槽裡 782 格通海（從龍骨底的開口），不算船艙。
  - 參照 Mercantile（Wikipedia 直接讀：甲板 80 ft、寬 22 ft、吃水插板收起 5 ft／另一個數 10 ft 7 in）—— 尺寸跟夜隼號幾乎一樣。NPS 文件說主桅往旁邊挪、讓出槽的寬度（⚠ 搜尋摘要轉述；兩份 NPS PDF 都是掃描圖，抓下來讀不到字）。
  - 🩸 我在對話裡跟 Tim 說「跟第零階段記的不一樣」—— 回頭重讀第 47 行，寫的就是「主桅為了讓槽偏離中線」（＝主桅讓位、槽在中線），跟查到的一樣。第零階段沒錯，錯的是我沒重讀就說它錯。
- **外板**：深度 ≤ √2 那一層、一格起（斜面上 2–3 格），27,732 格，照 x 每 50 格一份。z ≤ 15 塗 254（white stuff），以上 36（近黑）。
  - 🩸 第一版只取 d ≤ 1（跟船外共用一個面）⇒ 斜面上變階梯，58 塊 1–4 格的碎片只靠邊角相接（6 連通散成 59 塊；不漏水，但對轟的連通判斷會讓它們掉下去）。改成 d ≤ √2 ⇒ 1 塊。
- **舷牆頂蓋**：肋骨層＋外板層每一欄最高那一格的上面一格（只取最高殼格在舷牆頂附近的欄 —— 船艙中間那幾欄的最高殼格是船底），1,488 格，104。
- **結構塗裝**：骨架露在船外的 2,838 格照同一條水線換色（stampvox overwrite=1）；蓋之前匯出作品逐格驗，2,838 格現在都是 104。
- 落格：`stage3:begin`（第 56 個事件）→ carvevox 刻槽 164 格（帶原色守門）→ 槽 1,458 → 外板 6 份 → 頂蓋 → 結構塗裝；每刀 placed ＝ 清單。24,306 → **54,820 格**；`stage3:end` 在第 65 個事件。
- 讀數：
  - 結果帳：階段二清單＋階段三（刻、貼、換色照順序）推出的應有模型 vs 作品 export ⇒ 54,820／54,820，缺 0、多 0、顏色不同 0。
  - 結構（引擎 stats）：1 個元件、空腔 0、左右差 0（含顏色）。
  - 漏水（`design/check_planking.py`，讀作品 export、船艙範圍從圖紙曲面算）：z < 30 船艙 178,442 格，被船外走到 0 格。
    - 先餵尺已知答案（`verify_planking_post.json` known_answer、剖面圖 `overlays/stage3_leak_probe.png`）：水線下（x 177、z 8）拿掉右舷最外那一格外板 ⇒ 報 1 —— 那 1 格是洞本身，水進不了船艙。🩸 我以為在測「破一格會不會報」，其實測的是「洞自己算不算」。把 z 8 那一排（y 103–105）都拿掉 ⇒ 報 178,445（整個船艙）。尺會說話，但第一次餵的不是我以為的那個答案。
    - 🩸 而我第一次解釋「為什麼只報 1」時寫的是「那裡外板三格厚」—— 畫出剖面才看到不是：船舭在那裡幾乎是平的，z 8 這一層剛好有三格外板**橫著並排**，最外那格的上面是 z 9 那一排外板。外板還是一格厚；我沒看圖就替一個數字編了原因。
  - 探針（從圖紙取）：5 站 × z 8／15／25，右舷最外那格外緣離船殼外面 −0.40～+0.49 格；艏柱前緣、艉板面 4 個高度 −0.13～+0.39 格。反向對照偏 3（y、x）⇒ 23 根全報 3。
- 過程圖：`overlays/stage3_planking_yaw{45,135,-135,-45}.png`。
- ⚠ 一格只有一個顏色 ⇒ 船艙裡肋骨之間看得到外板內面的船底色／船身色。內板（ceiling）階段會蓋掉。

## 階段四 新圖紙 04：砲門、clamp、甲板（子作品）、組裝件 —— 落格（2026-10-13 午，wake #117）
設計 plan.json `decks`；產生 `design/draft_decks.py` ⇒ `sheet04_decks_v1.png`、`verify_decks.json`、`masks/decks/{hull,main,quarter}/`。重跑逐位元組相同。船殼現況從階段二、三的清單重建（兩階段的結果帳都驗過 作品＝設計），不讀作品匯出。
- **作品拆分**（Shipbuilding §2）：`summit-night-falcon-01m-deck-main`（主甲板＋艙房地板）、`-deck-quarter`（後甲板＋斷口艙壁）—— 子作品（parent＝船殼、tags sub）；`-assembly`（組裝件，一格不雕，關聯 船殼／甲板-主／甲板-後 都 at 0,0,0）。四件都記 meters_per_voxel 0.1（讀回 work.json）。
- **艙房頭高的拍板**：後甲板只高 1 m，扣橫樑底下只剩 0.8 m ⇒ 艙房地板比主甲板低 0.7 m（7 格），淨高 14 格（1.4 m，每一欄都是 14）。兩門最後面的砲在艙房裡。定稿圖的後甲板比線形高兩成半，多半就是為了這個頭高；照拍板不追，從地板讓。
- **甲板高度**：主甲板板那一格 ＝ floor(舷弧) − 1（板頂 ＝ 舷弧；船中 z 29、船頭 x 250 z 37）；後甲板 floor(舷弧 ＋ 10) − 1；艙房地板 ＝ 主甲板 − 7。
- **甲板**：板 250、橫樑 136（每 10 格一根、跟肋骨同欄、2×2，艙口與桅孔裡斷開、艙口兩側 carling）、艙口圍板 104（2 格高）。艙口：主艙口 x 168–181（插板槽正上方）、前艙口 x 226–233、後甲板 companion x 110–117。桅孔（暫定：主桅 x 148、前桅 x 206，半徑 2.5）先留空。斷口艙壁 x 138（艙房地板上一格到後甲板板下一格）。
  - 🩸 第一版甲板板只放 z ＝ L：舷弧格子化之後每隔一段高一格，主甲板斷成 10 段、艙房地板 6 段、後甲板 5 段，段與段只靠邊角相接。階的地方往下補一格（跟兩旁較低那一欄齊）⇒ 主甲板作品 2 塊（主甲板、艙房地板 —— 兩層本來就不相連，靠船殼與艙壁接）、後甲板 1 塊。
- **clamp**（船殼）：肋骨內面那一層（深度 3 < d ≤ 3+√2）、橫樑底下 2 格，沿船長，三層甲板各一道，1,733 格。🩸 第一版 3 < d ≤ 4：船頭、船尾斜的內面上 16 塊碎片（跟階段三外板第一版同一個病，換了個地方又來一次）。
- **砲門**（船殼）：每舷 6 個，開口 x 站−1..站+3（5 寬）、高 5、下緣離甲板 4 格；站 95、115（艙房裡）、170、185（船腰）、225、240 —— 避開主桅、前桅的 channels 範圍。刻 584 格（carvevox 帶原色守門），開口外一圈肋骨那一層補框 442 格（141）。每個開口上下各一列外板（lintel、sill 外面）。
- **封閉空腔**：船殼＋兩層甲板組起來，艙房地板底下船尾那一排（x 64、z 26，兩舷各 13 格）跟外面不通 ⇒ 補實（主甲板作品 cavity_fill，136）。
- **內板（ceiling）不做**：它會把肋骨之間的縫封成空腔；要填實還是留空影響對轟（打穿外板之後看到的是肋骨還是實心）⇒ 問 @ame。舷牆內側也不鋪 —— 小商船的舷牆常就是 stanchion＋外板，裡面看得到立柱。
- 落格：`stage4:begin`（船殼第 65 個事件）→ 船殼 3 刀（刻砲門、框、clamp）→ 主甲板 7 刀、後甲板 5 刀；每刀 placed ＝ 清單。船殼 54,820 → **56,411**、主甲板 13,789、後甲板 6,892；`stage4:end` 船殼第 68 個事件。組裝件 **77,092 格**。
- 讀數：
  - 引擎 stats（組裝件現組）：link_placed 77,092、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）。
  - 結果帳：船殼重建＋階段四清單（刻要原色對、貼要原本空）推出的應有模型 vs 組裝件 export ⇒ 77,092／77,092，缺 0、多 0、顏色不同 0。
  - `design/check_decks.py`（讀組裝件 export）：六個砲門的開口（只看作品：四面都碰得到船殼的空洞）x、z 範圍跟 plan 一格不差；甲板板頂離舷弧 0–0.90 格（7 個 x）；三個艙口開口裡剩 0 格；最低的砲門下緣（z 27）以下船艙 142,607 格被船外走到 0。反向對照：作品偏 3（x、z）⇒ 砲門 6 根、板頂 7 根全報 3。
  - 🩸 量尺自己壞了三次（都是尺，不是船）：① 開口偵測第一版用「船殼外那條線上下有格」，船尾 counter 底下、船頭 forefoot 旁的船外空氣被算成開口（x 95、240 報寬了）；② 加了「圖紙的船殼體積」過濾之後對了，但反向對照偏 3 時 x 95 報 −7 —— 過濾用的是圖紙、受測的是偏移後的作品，兩邊對不齊；改成只看作品本身（四面圍住的洞）才全報 3。③ 甲板板頂第一版量 y 95：船頭 x 255 那裡已經是船殼那一層，量到舷牆頂蓋（報 −11），改 y 88。
- 過程圖：`overlays/stage4_assembly_yaw{45,135,-135,-45}.png`、`stage4_assembly_yaw60_pitch55.png`、`_hide_quarter.png`（拿掉後甲板看艙房）。

## 階段五 新圖紙 05：船尾窗、窗廊、船尾燈、船首像 —— 落格（2026-10-13 午，wake #117）
設計 plan.json `stern_head`；產生 `design/draft_stern_head.py` ⇒ `verify_stern_head.json`、`masks/stern_head/{hull,stern_deco,quarter_gallery,head}/`。重跑逐位元組相同。現況從階段二～四的清單重建。
- 子作品（tags sub、0.1 m／格）：`-stern-deco`（船尾窗框、窗台線、簷線、燈；at 0,0,0）、`-quarter-gallery`（右舷窗廊，固定框 28×20×30、關聯 at 60,96,20；左舷 `船尾窗廊-鏡像` mirror=y、at.y ＝ 161 − 96 − 20 ＝ 45）、`-head`（knee＋隼；at 0,0,0）。
- 定稿圖（看的）：船尾側面一座窗廊（三扇拱窗、屋簷、底下收尖）、欄杆角一盞燈；船頭一隻張翅的隼，翅膀往後往上貼著船頭兩側。船尾正面定稿圖看不到 ⇒ 船尾窗自己設計。
- **船尾窗**（船殼）：艉板 4 扇（|dy| 3–7、11–15），z 30–37，剛好卡在 transom tr+02 與 tr+04 之間、在艙房裡。從艉板外面往裡刻到艙房空氣 280 格（carvevox 帶原色守門），玻璃縮一格 220 格（37）；艉板斜 ⇒ 上下兩排玻璃錯開的地方補一格。窗框凸一格（208 金）、窗台線與簷線 |dy| ≤ 18。船殼 56,411 → **56,351**；標記 stage5 begin 第 68、end 第 70 個事件。
- **窗廊**：x 64–83、z 28–41、外面平面 y 111；三扇拱窗 4×8（最上一排只留中間兩格）、壁柱金、屋簷兩層、底下收尖 3 層；一舷 2,347 格。
- **船尾燈**：艉板頂中央（x 56），柱 3 格、燈 3×3×5（253）。
- **船首像**：knee（cutwater）369 格 —— 艏柱前面往前長 0–12 格（smoothstep），z 16–36，托住隼的胸口；隼 2,224 格 —— 脊椎上一串球（尾 → 胸 → 頸）、頭半徑 2.4、喙往下勾；翅膀是前緣、後緣兩條折線之間的面（厚 1.6），後緣鋸齒（8 根、外推 2.2 格），翼尖 x < 266 那段深色飛羽；背與翅 73、胸 182、頭 36、喙爪眼 252。先落草稿、單獨渲染看形狀 → 改兩次 → apply（2,593 格、apply_mismatch 0）。
- 🩸 這一階段的錯（都在落格前或收帳時被讀數擋下）：
  1. 隼的頭第一版一格都沒有：頭那顆球的折線兩端是同一點，投影除以 0 ⇒ nan ⇒ 比較全是假。
  2. 喙尖那一格只靠邊角碰到喙（組裝件多一塊）；knee 底下 z 13、15 只剩一欄薄片（船頭作品多兩塊）。
  3. 翅膀第一版後半片全黑：我拿「邊界格」當後緣，翅膀只有兩格厚，每一格都是邊界。改成翼尖那一段才深色、後緣鋸齒。
  4. 窗廊固定框第一版從 y 100 起，底下收尖那幾層貼著較窄的船身跑到 y 97（讀數 local_min y −3）⇒ 框改從 96、高 20；但我**只改了 plan、沒改作品尺寸** ⇒ 引擎擋下（exit 5、一格沒落），放大作品再貼。
  5. 右舷窗廊的關聯寫檔撞到 IOException（要取代的檔案移除不掉）⇒ 組裝件只有左舷，stats 左右差 2,347 ＝ 一座窗廊；關聯表沒壞，補一條就 0。
  6. 量尺：船尾窗的讀數第一版混進窗廊的玻璃（也在 x < 70），縮進與後方空氣逐格算（斜面補的那格前後本來就是玻璃）⇒ 擋 |dy| ≤ 24、按每一欄算。
  7. 順手：船殼一直開著一份空草稿（0 個事件、底在 start、過期 —— 階段一預覽留下的；看關聯樹時看到「📝 開著草稿」）⇒ discard，作品一格沒動。
- 讀數：
  - 引擎 stats（組裝件現組 7 條關聯）：84,562 格、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）。
  - 結果帳：重建＋階段五清單（刻要原色對、貼要原本空、窗廊照鏡像也貼）vs 組裝件 export ⇒ 84,562／84,562，缺 0、多 0、顏色不同 0。
  - `design/check_stern_head.py`（讀組裝件）：船尾窗兩舷 |dy| 與 z 跟 plan 一致；160 欄全部縮進一格、後面接艙房空氣；兩舷窗廊玻璃逐格鏡像（各 90）；船首像 1,245 格在艏柱前面、落在船殼體積裡 0、最前到 x 298；y 偏 3 ⇒ 報 3。
- 過程圖：`overlays/stage5_assembly_yaw{45,135,-135,-45}.png`、`stage5_stern_yaw{-150,150}.png`、`stage5_bow_yaw{30,-30,90}.png`。

## 階段六 新圖紙 06：開窗、舵、船頭欄杆 —— 落格（2026-10-13 下午，wake #117）
Tim：「繼續做船頭欄杆和舵（另外窗戶部分可以直接開孔 這樣可以看到內構）」。設計 plan.json `rudder_rails`；產生 `design/draft_rudder_rails.py` ⇒ `verify_rudder_rails.json`、`masks/rudder_rails/{hull,quarter_gallery,head,rudder}/`。重跑逐位元組相同；現況照階段二～五的清單重建（`rebuild()`，每一刀都驗 原色對／原本空）。
- **開窗**：船尾窗刻掉玻璃 220 格（後面本來就是艙房）；窗廊每扇窗刻掉窗後面那一段窗廊（玻璃＋本體，一舷 408 格 —— 左舷是鏡像關聯，自動跟著）＋船殼兩舷同一個 (x, z) 從外面往裡 6 格內的船殼格 332 格（外板、肋骨、後甲板 clamp）。船殼 56,351 → **55,799**；標記 stage6 begin 第 70、end 第 71 個事件。
  - 🩸 第一版窗廊後面的船殼刻到第一格空氣就停：外板與肋骨之間有縫，更裡面那道後甲板 clamp（z 38）沒刻到 ⇒ 90 格裡 1 格不透光（拱頂那一排）。改成往裡 6 格內全刻。
- **舵**（子作品 `-rudder`，0.1 m／格，組裝件關聯 `舵` at 0,0,0）：方艉船的掛法 —— 掛在艉板外、舵柱上到後甲板高度（z 0–44）。每一欄前緣貼著現況最後面那格（艉柱、艉板、窗台線）；寬底 12 → z 15 收到 5 → z 22 以上是 3 格舵柱；厚 3、最後 2 格收成 1；水線以下 254、以上 36；pintle／gudgeon 6 道凸 1 格（73）。609 格。
  - 🩸 第一版照憲法號「頂端收在 counter 底下」—— 夜隼號的艉板跟艉柱幾乎平行、counter 幾乎不往外伸，停不下來（爬到 z 33 才停，停在哪全看容差）。
  - ⚠ 舵是會轉的部件；給遊戲轉之前要改外部模型＋pivot（Shipbuilding §2）。舵輪之後接到舵柱頂。
- **船頭欄杆**（加進船頭作品）：每舷上下兩道（金 208、2 格高 1 格厚、6 連通），從 x 258（貼船身）往前往下彎到 knee 旁（|dy| 2），中段往外鼓 2 格；整條在隼翅膀後緣底下；head timbers 3 根（黑）。368 格；前端插進 knee 的 10 格不放。
  - 🩸 第一版只照線性內插走 y：下道後端那幾格算進船身裡、被丟掉 ⇒ 後端 4 格斷開。改成每一點至少在那個 (x, z) 現況最外那格的外面一格。
- 讀數：
  - 引擎 stats（8 條關聯）：84,171 格、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）。
  - `design/check_rudder_rails.py`（讀組裝件）：結果帳 84,171／84,171 缺 0、多 0、顏色不同 0；船尾窗看得進艙房的 |dy| 正好是 plan 那 10 欄；窗廊窗兩舷各 90／90 透光；舵後緣離圖紙（艉柱面 − 舵寬）−0.38～0.69 格；欄杆在 x 258 是 z 35–41、x 283 是 29–34（跟 plan 的 from／to 一致）；反向對照（x、z、y 各偏 3）全報 3。
  - 🩸 量尺：舵第一版量前緣 —— 前緣貼著艉柱、水下兩者都是 254，從作品分不出誰是舵 ⇒ 改量後緣。
- 過程圖：`overlays/stage6_stern_yaw{-150,150,-100}.png`、`stage6_bow_yaw{30,-30,60}.png`、`stage6_assembly_yaw{45,-135}.png`。

## 階段七 新圖紙 07：桅檣（兩根桅、艏斜桅、channels）—— 落格（2026-10-13 下午，wake #117）
設計 plan.json `masts`（每個數字的出處在 provenance `masts.*`）；產生 `design/draft_masts.py` ⇒ `verify_masts.json`（含 rig_points：每根桅的甲板點、下桅頂、中桅頂、truck，艏斜桅 heel／end／jib_end —— 下一階段帆桁與繩用）、`masks/masts/`。重跑逐位元組相同。
- **現況重建收成一支**：`design/nf_state.py`（`state_after(d, 'stageN')`）照各階段 verify 清單重播、每一刀驗原色／原本空；重建到階段六跟組裝件匯出逐格相同（84,171）。之後每一階段都用它。
- 子作品（tags sub、0.1 m／格，組裝件關聯 at 0,0,0）：`-mast-fore`、`-mast-main`、`-bowsprit`；`-channels`（一舷，固定框 100×28×25、關聯 at 130,100,25；`channels-鏡像` mirror=y、at.y ＝ 161 − 100 − 28 ＝ 33）。
- **桅**（brigantine：前桅全橫帆、主桅 gaff＋頂上橫帆 —— 帆桁下一階段）：前桅 x 206、後傾 1.5°；主桅 x 148、後傾 3°；軸過甲板那一點（桅孔不用改）。桅座（沒有 keelson ⇒ 桅腳下補一塊，踩在龍骨與底肋上）→ 下桅（半徑 2.4 → 1.9）→ top（trestletrees 緊貼那一層桅杆最外格 ±1、crosstrees、平台 fore 14×20／main 12×16）→ cap → 中桅（往前 offset 4.4，1.5 → 1.1）→ 中桅 crosstrees＋cap → 頂桅（往前 7.5，1.0 → 0.7）→ truck。前桅 3,344、主桅 3,382 格；truck z 242／248（主桅高 —— 定稿圖也是後桅高）。
  - 🩸 第一版兩根桅的頂桅浮在半空：頂桅往前偏 3.1 格、兩節半徑和 2.1，中間空一格，而中桅頂沒有 cap 把它們箍起來（下桅與中桅之間是靠 cap 和 top 接的 —— 同一件東西我在上面那一節做了、下面那一節忘了）。補中桅 cap ⇒ 1 塊。
- **艏斜桅**：heel 在甲板 x 237、往前上 22°、長 105（到 x 335、z 77），半徑 2.0 → 1.4；jib-boom 從 70 格處上方平行 60 格（到 x 358、z 90）；cap 兩個。跟船殼相交的 38 格（舷牆頂、艏柱頭）刻掉（carvevox 帶原色守門；憲法號「艏斜桅開口」同）。1,111 格。
- **channels**：前桅 x 196–220、主桅 x 138–162（階段四砲門刻意避開的兩段），那一段舷牆頂最低處往下 3 格起 2 格厚、往外 6 格、兩頭圓角；一舷 576 格。deadeyes 與 chain plates 留給繩那一階段。
- 落格：船殼 `stage7` begin 第 71、end 第 72 個事件（刻 38）；四件子作品各一刀；每刀 placed ＝ 清單。船殼 55,799 → **55,761**。
- 讀數：
  - 引擎 stats（13 條關聯）：**93,122 格**、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）。
  - `design/check_masts.py`（讀組裝件）：結果帳 93,122／93,122 缺 0、多 0、顏色不同 0；兩根桅在 3 個高度的軸心離圖紙（桅孔＋後傾）最多 0.36 格；艏斜桅在 x 300 離圖紙那條 22° 線 0.05 格；反向對照（x、z 偏 3）7 根全報 3。桅身跟現況撞到被丟的格 0。
- 過程圖：`overlays/stage7_assembly_yaw{45,-135,90}.png`、`stage7_tops_yaw60.png`、`stage7_bowsprit_yaw30.png`。

## 階段八 新圖紙 08：帆桁（6 件子作品＋外部模型）—— 落格（2026-10-13 下午，wake #117）
Tim：「接著繼續造船吧 GO」。設計 plan.json `yards`（每個數字的出處在 provenance `yards.*`）；產生 `design/draft_yards.py` ⇒ `verify_yards.json`（placements：每件的框、清單、固定點、模型 at／pivot／rotate／meta；anchors_expect：轉好之後的預期點）、`masks/yards/<帆桁>.vox.txt`（子作品座標）。重跑逐位元組相同。下 CLI：`design/apply_yards.py <design> create|stamp|anchors|models|turn`。照 basecamp 憲法號階段三十三那套，但沒有「先貼進桅再刻掉」那一段 —— 一開始就是外部模型。
- 6 件子作品 `-yard-<帆桁>`（parent ＝ 所在的桅杆子作品、tags sub、0.1 m）：
  - 方帆桁 4（沿 y、水平、跟中線垂直，貼在那一節桅最前格的前面一格）：fore course 119 格（z 120，top 平台下 6）、fore topsail 89（z 191，中桅 crosstrees 下 4）、fore topgallant 61（z 234，truck 下 6）、main topsail 89（z 198）。
    長 ＝ 型寬 64 × 1.862（憲法號 fore yard ÷ 型寬）× 憲法號同層比例；徑 ＝ 那一節桅的跟部徑 × 憲法號「桁徑 ÷ 桅徑」；Steel 錐度（轉引 basecamp）、yardarm 端 1 格黑。
  - gaff 72 格（主桅 top 平台下 8、上翹 35°）、boom 102 格（上翹 3°、尾端伸出船尾 10 格到 x 43.6；jaws z 61 是「下緣離底下最高那一格 ≥ 2」的最低整數 —— 底下最高的是船尾燈）。
  - ⭐ **gaff／boom 在子作品裡是水平的直桿，斜度交給模型 rotate 的 y**（35°／3°）—— basecamp 那邊記下的「gaff 斜 35° 仍是格子的階梯」這裡沒有。我信裡寫的那一題（斜面上它會不會只靠邊角相接？）這次在動手之前問了：答案是不要在格子裡斜。
  - 共 2,038 格；每件 6 連通 1 塊。
- 模型放在桅杆子作品裡（`前桅/yard-fore-course`…，跟著桅走）：scale 1、at ＝ pivot 那一格的格心；方帆桁 pivot ＝ 帆桁中心那一格，gaff／boom ＝ 主桅在 jaws 高度的軸心那一格（繞桅轉）。預設 rotate z 全部 0。
  meta：`kind=yard, mast, yard, length_m, diameter_m, pivot_anchor=pivot, turn_axis=z, rotate_z_deg`；gaff／boom 多一個 `rotate_y_deg`（⚠ 遊戲那側轉帆桁只能換 z、要保留 y，不然 gaff 會躺平）。還沒有帆 ⇒ meta 不寫 sail。
- 固定點 84（子作品座標）：方帆桁 arm-P／S、earing-P／S（yardarm 內端的頂面）、sling、jackstay 每 8 格、pivot；gaff throat／peak／top<n>、boom jaws／end／top<n>、pivot。
- 落格：6 件各一刀，每刀 placed ＝ 清單（483／293／153／293／515／301）；anchors 84、models 6，0 失敗。桅杆子作品的格一格沒動（3,344／3,382）。
- 讀數：
  - 引擎 stats（組裝件）：**93,122 格**（模型不算格，跟階段七一樣）、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）。
  - `design/check_yards.py`（讀引擎匯出：六件 list、兩根桅 list、組裝件 list、組裝件 parts）：結果帳六件全部缺 0、多 0、顏色不同 0；**引擎轉過的 84 個固定點 vs 我這邊 rot() 算的：最大差 0.0**（兩條路算同一個旋轉 —— y 轉 +35 是 peak 往上往後，引擎同意）；方帆桁高度、長度跟 plan 一樣、背面離桅 0 格；gaff 仰角 35.0、boom 3.0；boom 下緣最緊 2.24 格（x 56，船尾燈頂 z 62；plan ≥ 2）；反向對照（x、z 偏 3、peak 多轉 3°）全報 3。
  - 🩸 量尺兩把第一版是壞的：① gaff 仰角用 throat→peak 量出 34.2° —— throat 在桿的頂面、peak 在軸上；軸線過 pivot ⇒ 改 pivot→peak；② boom 淨空取整欄最高那一格 ⇒ 撞到 boom 上面、後傾到 x 141 的主桅，報 −152 ⇒ 只看 boom 底下。兩把都是尺錯、船沒錯。
  - 已知答案（basecamp 階段三十三）：方帆桁轉到 −20～−24°、gaff／boom 轉 25°（`overlays/stage8_demo_braced_yaw{45,160}.png`）→ 轉回 0 ⇒ 兩件桅杆的 models.json 跟備份**逐位元組相同**。
    🩸 轉回那一趟 6 個呼叫有 1 個失敗（fore 那件先不同），原因沒存到 —— 我的 `grep "ok "` 把 ✗ 那一行濾掉了（「管道會把失敗濾掉」那一族）。重跑 fore 那三個 ⇒ 相同。⛔ 不說它是階段五那個 IOException，沒有讀數。
  - 觀察：`view region=` 只裁格子、模型照畫（主桅特寫裡前桅的帆桁浮在框外）⇒ 特寫用 hide_models。
- 過程圖：`overlays/stage8_assembly_yaw{45,-135,90}.png`、`stage8_bow_yaw0.png`、`stage8_main_gaff_boom_yaw70.png`、`stage8_demo_braced_yaw{45,160}.png`。

## 階段九 新圖紙 09：靜索（channels v2、deadeyes、chain plates、繩 207）—— 落格（2026-10-13 下午，wake #117）
Tim：「提交吧 然後繼續做靜索」。設計 plan.json `rigging`（provenance `rigging.*`）；產生 `design/draft_rigging.py` ⇒ `verify_rigging.json`（channels 刻／貼、固定點、繩清單＋我算的兩端世界座標、碰撞）、`masks/rigging/channels_{carve,stamp}.vox.txt`；下 CLI `design/apply_rigging.py <design> channels|anchors|ropes`；讀數 `design/check_rigging.py` ⇒ `verify_rigging_post.json`。重跑逐位元組相同。`nf_state.py` 加 stage9（階段八是模型、不動格）。照 basecamp 憲法號（Shipbuilding §6、notes 靜索試掛／階段二十二／二十五）。
- **channels v2**：每舷每根桅 3 根 lower shrouds＋2 根 backstays ＝ 5 顆 deadeye、間距 4，最前一顆在桅孔前 2 格 ⇒ fore 189–211、main 131–153（算法照階段七）。
  🩸 階段七的 channels 以桅為中心排（196–220、138–162）—— shrouds 大多該在桅後面、backstays 更後面，原本的框裝不下；那時我寫「deadeyes 留給繩那一階段」，框的位置卻是先定的。
  - 刻之前讀回：channels 子作品 export ＝ 階段七清單 576／576。carvevox 216（帶原色守門）、stampvox 390，每刀 placed ＝ 清單；標記 stage9 begin／end。一舷 576 → **750**（channel 528、deadeye 100、chain plate 122），鏡像關聯自動跟著。
  - 下 deadeye 3×3 去四角、2 格厚、104、坐在 channel 頂面外緣；chain plate 每顆一條、73、從 channel 底面外緣往下 8 格、往內收到船殼外一格，往內走就同層橫補（6 連通）。
- **固定點 52**：兩根桅各 hounds／futtock／tm-head／tg-head（S、P）、top 邊緣前後（S、P）、crosstrees 兩端、top-fwd、tm-cap-fwd、tg-head-fwd；前桅多 aft-low、cap-aft、tm-cap-aft（main stays 落點）；艏斜桅 stay-fore／stay-tm／stay-tg／bobstay；船頭 bobstay；channels deadeye-<桅>-1..5（只 S）。全部在實心格上（產生程式 assert）；登記完從各作品 anchors.json 讀回 52／52 名字與位置相同。
  - ⭐ stays 不從桅頭前面出：course 在 top 下 6、topsail 在 crosstrees 下 4 —— 算過 fore stay 從桅頭前面出會在 z 121 過 x 208.7，course 的格到 x 208 ⇒ lower stay 從 top 平台前緣、topmast stay 從中桅 cap 前緣出。帆桁上一階段剛做，這一題是先算才定的。
- **繩 207**（組裝件，全部拉直 slack 1、色 #2b2620）：lower shrouds 12、backstays 8、futtock 8、topmast shrouds 8、topgallant shrouds 4、stays 6＋bobstay 1、上 deadeye 20（短粗繩 #6d4900、直徑 3）、lanyards 60、ratlines 80（子繩 rope:<shroud>/比例：lower 每舷 11–13 道、topmast 8 道）。分 13 組（standing/…、ratlines/…）。
  - 🩸 bobstay 第一版 x 325 → 船頭 z 22：直線穿過隼的胸口（62 個取樣在船頭作品裡）。隼的前緣從 z 16 的 x 271 斜到 z 44 的 x 298 —— 掃了 522 條直線（艏斜桅底面 x 300–334 × 船頭前緣 z 12–40），只有 2 條不碰 ⇒ x 330 → z 29（x 284）。量得中段離最近實心格心 1.0 格 —— 渲染上它從隼的翅膀前面擦過（`stage9_bobstay_yaw20`）。
  - 碰撞量尺：🩸 第一版只跳兩端 1.2 格 ⇒ topmast shrouds 報撞桅 10–14 —— 全在最後 4 格、全是自己那根桅（陡的繩貼著細而後傾的桅收進固定點）。改成分「著陸」（從端點連續落在端點那件作品裡）跟「中段」：**中段 0（207 條）**、著陸最長 3.5 格（上限 6）。
- **寫入失敗**：IOException「無法移除要被取代的檔案」—— 固定點 3 次（第一輪 2 次 —— 我只看到其中一個名字 cross-P，因為那一趟我用 tail 只看最後 12 行；重跑全部又撞 1 次，是前桅 hounds-P）、繩 5 次，共 8 次；繩那一輪另有 13 條 ratlines rc=2 是**連鎖**：它們掛在 main-shroud-P3 上、那條撞到 IOException 沒寫進去 ⇒ 引擎擋下、零寫入。只重跑失敗的 18 條（清單順序，shroud 在前）⇒ 全過。這一次 apply 腳本把失敗整段印出來，原因有存到（錯誤報告 `SenateData/runtime/_cmd_errors/20261013-152004-8f5e6e-sculpture.md`）；階段八那一次仍然沒有讀數。
- 讀數：
  - 引擎 stats：**93,470 格**（＝ 93,122 ＋ 2 × (390 − 216)）、link_overlap 0、1 個元件、空腔 0、左右差 0（含顏色）；`sub=ropes`：207 條全部 ok、ropes_broken 0、子繩 80、13 組、未分組 0。
  - 讀回：組裝件 ropes.json 207／207 每條 from／to／色／組／粗／slack 跟清單相同。
  - `check_rigging.py`（讀引擎匯出）：結果帳 93,470／93,470 缺 0、多 0、顏色不同 0；deadeye 兩根桅兩舷 20 顆的 x 中心 ＝ plan（誤差 0.0）、每顆 10 格；chain plates 244 格、20 欄最低那一格內側都是實心（釘在船殼上）；channels 子作品 6 連通 2 塊（前、主）；**引擎解出的繩兩端 vs 我算的：最大差 0.075（引擎印到 0.1）、長度最大差 0.005**；stays 中段淨空 fore 3.6、fore-tm 3.6、fore-tg 2.8、main 2.0、main-tm 2.8、main-tg 3.0、bobstay 1.0；反向對照（deadeye x 偏 3、繩端偏 3）25 個全報 3。
  - 🩸 量尺：deadeye、chain plate 第一版只認顏色 —— 104 也是舷牆頂蓋（整條船長，五顆併成一群）、73 也是隼的背與舵的 pintle（1,851 格）⇒ 加上位置（船殼外、channel 範圍、channel 底面以下）。用顏色當身分證 —— 階段五量船尾窗混進窗廊玻璃也是這個病，今天又兩把。
- 觀察：上 deadeye 是短粗的繩，渲染成開口的管 —— 斜看像一個 C（憲法號同一個做法）。`view region=` 不裁繩與模型 ⇒ 特寫改用 target＋zoom。
- 過程圖：`overlays/stage9_assembly_yaw{45,-135,90}.png`、`stage9_bow_yaw0.png`、`stage9_channels_fore_yaw60.png`、`stage9_bobstay_yaw20.png`、`stage9_fore_tops_yaw50.png`。

## 階段十 新圖紙 10：繫繩點（fife rails、舷牆 pin rails）與動索 44 條 —— 落格（2026-10-13 下午，wake #117）
Tim：「提交吧 然後繼續做 pin rails 和動索」。設計 plan.json `belaying`、`running`（provenance `belaying.*`、`running.*`）；產生 `design/draft_belaying.py` ⇒ `verify_belaying.json`、`masks/belaying/`；`design/draft_running.py` ⇒ `verify_running.json`；下 CLI `apply_belaying.py`、`apply_running.py`；讀數 `check_running.py` ⇒ `verify_running_post.json`。兩支產生程式重跑逐位元組相同；`nf_state.py` 加 stage10（鍵 fife、side_S／_P）。
⚠ 動索：憲法號只做了帆的 sheets／tacks —— lifts、braces、halyards、footropes、gaff／boom 的動索是這艘先做，走法是我照一般橫帆船定的，**沒有一條是查來的史料**（provenance 寫明）。
- **子作品 `-fiferails`**（parent 主甲板、固定框 at 60,70,25、170×21×30，關聯 `fife-rails`）739 格：兩根桅腳各一組 U 形開口朝前（桅後 6 一根橫 rail、兩側 ±7 往前接 bitts 3×3 高 10、甲板面 ＋7、rail 2 寬）、柱、bitts 上鐵 cross pin；pins 每組 10；main sheet horse（x 72 後甲板、|dy| ≤ 8、鐵）。
  - 草稿裡被自己的 assert 擋下三次：cross pin 落在 rail 那一層（壓到側 rail 最後一格）⇒ 高一格；橫 rail 的 pin 下半截撞柱（中線、±6）⇒ pin 改 dy ±2、±5；**bitts 從桅那一格的甲板面起 —— 舷弧往前升，x 213 撞進甲板** ⇒ 每一欄從自己的甲板面起。
- **子作品 `-belaying-side`**（parent 船殼、固定框 at 55,92,25、215×24×35；關聯 `繫繩欄`、`繫繩欄-鏡像` mirror=y at.y 45）：舷牆內面 pin rails 一舷 12 根（後甲板 5、船腰 7），pins 40。砲門只看船殼作品（⛔ 不看 channels）；空檔平均切。
  - 🩸 v1（513 格，**已落格**）兩個錯，量了才知道：① 每一欄只貼自己那一欄的內面 ⇒ 內面相鄰差 2 格的地方兩欄沒有共用的面 —— 12 根 rail 量成 56 塊（**斜面階梯病，第四次**；信裡那一題我在帆桁問了、這裡沒問）⇒ 往裡補到鄰欄最深那一格；② **頂蓋（104）往裡伸 2 格，整根 rail 跟 pin 頭縮在頂蓋底下** —— 動索的碰撞取樣在最後 1.2–1.7 格撞頂蓋（9 條）才看到 ⇒ pin 改放在「rail 那一層到上面 4 層」最靠裡的內面再往裡一格。
  - v1 → v2：刻之前讀回 ＝ v1 清單 513／513；carvevox 513（帶原色）、stampvox 565，placed ＝ 清單。v1 清單凍結在 `masks/belaying/belaying_side_v1.vox.txt`，重播照實：貼 v1 → 刻 v1 → 貼 v2。
  - 其他草稿期間：船尾 x 61 前面站著別的作品 ⇒ 內面要是船殼作品的格；rail 兩頭的肘用 rail 那一層與下一層較淺的內面；rail 端、舷牆、頂蓋圍出的 1–2 格口袋（v1 有 4 格）在 v2 沒有了。
- **動索 44 條**（組裝件，#a08458，分 7 組 running/…）：方帆桁 4 根 × lifts 2、footropes 2（slack 1.03，引擎量的下垂 2.79–5.89 格）、braces 2；前桅帆桁的 braces 往船尾拉到主桅（course → 主桅 top 下 6 的桅側、topsail／topgallant → 主桅 crosstrees 端）＋ falls 落舷牆 pin；主桅 topsail braces 落後甲板 pin；halyards 3（tye ＋ fall）；gaff peak halyard 兩段＋fall、vangs 2；topping lifts 2（兩舷）；main sheet（boom 底下 → horse）。帆桁上的端點全部綁模型。新固定點 29（帆桁底下 foot-in／foot-out、boom sheet；桅 cap／tm-cap 兩側、主桅 brace、top-aft、tm-head-aft）。用掉 pin 14 根。
  - 🩸 碰撞取樣第一版中段撞到的，五種走法錯：topsail 的 tye 從 sling 直上 —— **頂桅的跟就站在 topsail yard 正上方**（doubling），穿過 24–25 格 ⇒ tye 拉到 crosstrees 端；topgallant brace 到主桅 tm-head 前先穿過 crosstrees；從 cap／桅頭下的 fall 擦 crosstrees、穿過底下那根帆桁；**topping lift 在中線一定會跟往後上翹的 gaff 交叉**（量到穿過 7 格）⇒ 兩舷各一條（真船也是一對）；course 的 brace fall 落 fife ⇒ 貼著主桅跑 8 格 ⇒ 落舷牆；往前落 rail 7 的 fall 擦主桅 topsail yard 的背 ⇒ 改往後落後甲板 rail 5。改完 **中段 0（44 條）**、著陸最長 2.75。
- **寫入失敗**：IOException「無法移除要被取代的檔案」—— 鏡像關聯 1 次、固定點 3 次；重跑全過。讀回 anchors.json：那 3 個裡 2 個本來就對（位置沒變，舊檔還在 —— 失敗是原子的），1 個（pinrail-1.pin-1，v2 搬了位置）是舊值 ⇒ 重下後 90／90 相同。
- 讀數：
  - 引擎 stats：**95,339 格**（＝ 93,470 ＋ 739 ＋ 2 × 565）、link_overlap 0、link_clipped 0、1 個元件、空腔 0、左右差 0（含顏色）；繩 251（靜索 207＋動索 44）、ropes_broken 0、20 組。
  - `check_running.py`（讀引擎匯出）：結果帳 95,339／95,339 缺 0、多 0、顏色不同 0；pins 兩舷各 40 根（＝ 固定點）；引擎解的繩兩端 vs 我算的：動索 ≤ 0.053、靜索 207 條再比一次 ≤ 0.075（新固定點沒有動到舊繩）；直線長度差 ≤ 0.005。
  - **綁模型的已知答案**：fore course 轉 −20° ⇒ 掛在它上面的 8 個繩端，引擎的位置 vs 我用 rot() 轉的 ≤ 0.047（印到 0.1）、其他繩端移動 0.0、broken 0；轉回 0 ⇒ 前桅 models.json 與組裝件 ropes.json 跟轉之前**逐位元組相同**（`overlays/stage10_demo_course_braced_yaw35.png`）。
  - 🩸 量尺：① 繩長第一版拿引擎的「長」比我的直線長 ⇒ footrope 差 1.65 —— 兩種量 ⇒ 改比「直線」；② **pin 探針只認色 104 ⇒ 760 根 —— 104 也是頂蓋。這個病我在階段九才寫進筆記，一小時後同一把尺又這樣寫** ⇒ 改認形狀（rail 那一格上下各兩格 pin 色）。
  - 反向對照（pin x 偏 3、繩端偏 3）全報 3。
- 過程圖：`overlays/stage10_assembly_yaw{45,-135,90}.png`、`stage10_main_fife_yaw60.png`、`stage10_quarterdeck_yaw120.png`、`stage10_fore_yards_yaw30.png`、`stage10_demo_course_braced_yaw35.png`。

## 階段十一 新圖紙 11：掛帆（8 面）＋主桅下桁 —— 落格（2026-10-13 下午，wake #117）
Tim：「提交吧 然後繼續掛帆」。設計 plan.json `sails`（provenance `sails.*`）、`yards.square` 加 main-course（provenance `yards.main_course`）；產生 `design/draft_sails.py` ⇒ `verify_sails.json`；下 CLI `design/apply_sails.py <design> wind|sails|ropes`；讀數 `design/check_sails.py`（讀引擎匯出的 OBJ —— 模擬過的帆網格）⇒ `verify_sails_post.json`。照 basecamp 憲法號（Shipbuilding §7、notes 掛帆試試／kotoko 兩點）。重跑逐位元組相同。一格 voxel 都沒動（組裝件仍 95,339）。
- **主桅下桁（不掛帆）**：🩸 階段八寫「主桅頂上一根橫桁」就停了 —— 掛帆才發現 main topsail 的下兩角沒有地方去（top 邊緣 16 格寬、帆頭 89）。brigantine 的主桅多半有一根不掛 course 的下桁 ⇒ 子作品 `-yard-main-course`（規則照 fore course：119 格、z 130、483 格、模型 `主桅/yard-main-course`）。原有六根的清單重產逐位元組相同；靜索 207 條對它重新取樣，verify_rigging.json 逐位元組相同（中段 0）。
  - 連帶：fore course 的 brace 原本落在主桅 top 下 6 格的桅側滑車 —— 那一高度現在是下桁 ⇒ 改直接落船腰 rail 6；拿掉兩條 fall（unrope）與 `brace-S／P`（unanchor；那一刻引擎報「1／2 條繩的綁定壞了」—— 是 brace 自己還指著它，下一步重寫 brace 之後 ropes_broken 0）。下桁加 lifts、footropes、braces（後甲板 rail 4）。
  - 🩸 從舷外的 yardarm 直落舷牆裡的 pin，最後 1.5 格一定擦過頂蓋內角（量到 104）⇒ 加導點：pin 那一欄頂蓋最靠裡那一格的內緣往裡 0.3、頂面上 0.3（真船：rail 上的 sheave）⇒ brace 一段到導點、一段 1.81 格落 pin。動索 44 → **54**、中段 0。
- **帆 8 面**（組裝件，#f2ead8）：方帆 4（fore course、fore topsail、fore topgallant、main topsail）上緣釘在帆桁模型的兩個 earing 之間、下兩角 free；topsail 以上的 sheet 綁下一根帆桁同舷的 earing；course 的 sheet（slack 0.85，船腰 rail 8）往後、tack（0.8，rail 12）往前，都經導點（🩸 v1 直落 pin 穿過舷牆 9／23 個取樣）。主帆（gaff）四角釘、邊 0／2／3 釘、只有 leech 自由。三角帆 3：fore staysail（fore stay）、jib（fore topmast stay）、flying jib（fore topgallant stay），luff 沿 stay、clew free、兩舷 sheet 落 rail 10／11／12。帆腳索 20。預設風 4.5,−1.5,0、模擬 4 秒。
  - 🩸 三面三角帆都在中線那個平面：flying jib 第一版用跟 jib 一樣的比例，clew 落進 jib 的布面 ⇒ 加條件「每一面的 foot 與 clew 在裡面那根 stay 的 luff 之上 ≥ 5 格」：jib 13.6、flying jib 15.5（flying jib foot 0.38、上翹 32°）。
  - 🩸 主帆第一版帆頭綁 gaff 的 top 點（頂面）—— 模擬後布從 gaff 身體穿過 12 點 ⇒ gaff 加底面固定點 bot8／bot64、帆頭綁底面 ⇒ 0。
- 讀數：
  - 引擎 `sub=sails`：8 面全部 ok、sails_broken 0、ropes_broken 0；最鼓 fore course −37.98、fore topsail −30.78、fore topgallant −20.69、main topsail −30.52（負 ＝ 往前鼓，離桅）、主帆 18.23、三角帆 6.74／11.44／10.71。繩 281（靜索 207、動索 54、帆腳索 20）。
    - 🩸 第一次讀 fore topsail 是 −60.59 —— 它右舷的 sheet 寫入撞 IOException 沒進去，那一角在飛；補上之後 −30.78。
  - 讀回：sails.json 8／8 角、名、bind、free、fullness、色跟設計相同；ropes.json 281／281。
  - `check_sails.py`（讀 OBJ：帆是 o sail_<i>、頂點 v x z y —— 第一個角 head_p 對過，8 面最大差 0.05）：**模擬後**每面帆的頂點與三角形重心落在實心的 0（8 面；離釘住的邊 < 1.2 格的不算）；方帆離自己那根桅最近 2.45–3.61 格（EDT）、整份往桅推 3 格 ⇒ 0–1（量尺會叫）。
  - ⚠ 平的布（模擬之前）方帆穿過桅 12–70 個取樣 —— 風（往 +x）把布往前推開才離開；**這不是我造成它不碰，是風**。風往後吹（或無風）時要重量。
  - 鼓度：方帆最鼓 ≈ 寬的 32–35%（kotoko：真的方帆約一到兩成）。旋鈕是風（basecamp 試驗表）；`overlays/stage11_sails_wind2.4_yaw45.png` 是 2.4 m/s 的單次覆寫、預設沒改 —— 等 Tim 選。
- 寫入失敗：IOException 2 次（main-course-lift-P、fore-topsail-sheet-S），重跑過。
- 過程圖：`overlays/stage11_sails_yaw{45,-135,90,160,-30}.png`、`stage11_sails_wind2.4_yaw45.png`。

## 階段十二 新圖紙 12：旗 —— 落格（2026-10-13 下午，wake #117）
Tim：「提交吧 然後繼續做旗」。設計 plan.json `flag`（provenance `flag`、`flag.place`、`flag.size`）；產生 `design/draft_flag.py` ⇒ `verify_flag.json`、`masks/flag/staff.vox.txt`；讀數 `design/check_flag.py` ⇒ `verify_flag_post.json`。重跑逐位元組相同；`nf_state.py` 加 stage12（主桅子作品）。
- **圖案（作者決定）**：候選 v3 定稿 —— 正面俯衝的隼、金喙尖、深藍底（24×16，`summit-night-falcon-01m-flag/design/make_flag.py`）。原作《桅頂的賭注》只寫「這片海的船靠旗與徽記辨識」、「三年前，這片海上沒人不認得夜隼號的旗」（001:11），沒寫旗的圖案 —— 🩸 白天寫這句時只查了漫畫資料夾；晚上回去 grep 小說本文三部（本作、續篇、《鐘誓》）才確定（續篇的旗都是別艘船的）；002 卡戎奪船、剝下舵輪的隼徽鑄成銅牌；007 凜回到船上按著那塊疤。我定：舵輪上的徽是被剝掉的傷，旗是她重新升起來的那一面 —— 還是隼。
  ⚠ 船設卡（ArtGallery/Comic/summit-masthead-bet/Characters/night-falcon.md）**沒有改**：寫進去 gura 就會照畫，那是規格，等 Tim 說。⛔ 不照定稿圖的骷髏旗（第零階段已記）。
  - 候選作品 `-flag` 改名「設計與試跑（v1–v3；v3 定稿，正式的那面掛在組裝件 ensign）」—— 標題原本寫「候選」，定稿之後就比事實小。
- **位置**：主桅 truck 上一根 2.4 m 旗桿（一格粗、頂上十字鐵帽，29 格，加進主桅子作品）。別的三個地方用已經量過的位置對過（⚠ 沒有各試掛一次）都不行：gaff peak（旗往前飄壓在主帆上）、船尾旗桿（會撞 boom）、直接掛 truck（main topgallant stay 從 z 244.5 往前下，旗會橫過它）。
  - 主桅標記 stage12 begin／end。🩸 第一次下標記時 note 裡有空格、我的 shell 小函式把它拆開 ⇒ 兩個標記沒下、旗桿先落了 ⇒ 用 upto= 補在落格前後那兩個事件上；讀回：stage12:begin 匯出 3,382（＝ 階段七）、現在 3,411（＋29）。
- **旗**（組裝件的帆 `ensign`，貼圖 `textures/ensign.png`）：hoist 20 × fly 30（2 × 3 m）、hoist 那條邊釘在旗桿上（固定點 主桅/flag-top、flag-bot）、fly 兩角 free；res 16。
- 讀數：
  - 引擎 stats：**95,368 格**（＋29）、link_overlap 0、1 個元件、空腔 0、左右差 0；`sub=sails` 9 面（帆 8＋旗）全 ok、sails_broken 0、ropes_broken 0；旗最鼓 −15.6、平均位移 (−1.12, −4.19, −3.26)。
  - `check_flag.py`：結果帳 95,368／95,368 缺 0、多 0、顏色不同 0；模擬後旗 3,504 個頂點落在實心（格、帆桁）0；離別的帆最近 40.1 格；281 條繩裡最近的是主桅 topgallant backstays／shrouds 6.0 格（旗的 hoist 底 250.5 到它們的上端 244.5）；最近那條繩往旗挪 3 格 ⇒ 報 3。貼圖：組裝件 textures/ensign.png 跟來源逐位元組相同。
  - 🩸 量尺兩把：① OBJ 讀取用名字當鍵 —— **有貼圖的帆按顏色拆成三個同名物件**（旗 ＝ sail_8／9／10），後面的覆寫前面的，第一次只讀到 24 點的金喙、報「0 碰撞」（量的不是旗）⇒ 同名合併（帆 8 面重跑一樣）；② 拿旗的最低 z 比 stay 起點的 z —— 最低點在旗尾、stay 起點在桅邊，兩個不同地方 ⇒ 改量到每一條繩的距離。
- 過程圖：`overlays/stage12_flag_close_yaw{90,-90}.png`、`stage12_ship_yaw{45,120}.png`。

## 階段十三 新圖紙 13：砲（4 磅長砲 12 門，一件子作品＋外部模型）—— 落格（2026-10-13 晚，wake #118）
Tim：「自由意志模式 處理待辦GO」。設計 plan.json `guns`（provenance `guns`、`guns.barrel_len`、`guns.profile`、`guns.AZ`、`guns.carriage`）；產生 `design/draft_guns.py` ⇒ `masks/guns/gun4.vox.txt`、`verify_guns.json`；下 CLI `design/apply_guns.py <design> anchors|models`；讀數 `design/check_guns.py`（只讀引擎匯出）。重跑逐位元組相同。`nf_state.py` 不加階段：砲是模型，原有的子作品一格沒動。
- **口徑（作者決定）**：4 磅長砲。原作沒寫砲（`Books/summit-masthead-bet`、`-sequel` 全文「砲／炮」0 處）；船設「小而快、靠靈活不靠火力」、Oswego 160 噸、RMG 的 brigantine 模型 10–12 門 ⇒ 英國海軍最小的長砲。砲管 6 ft 出處是 modelshipworld 論壇一串（⚠ 論壇，不是史料；同一串也有人說 5.5 ft）；口徑 3.2" 是記憶、沒查（搜尋到的瑞典 4 磅陸砲是 84 mm，只當旁證）。
- **子作品** `summit-night-falcon-01m-gun-4l`（parent 船殼、tags sub、**0.05 m**、15 × 41 × 16）：1,452 格（砲管 36 736、砲架 132 596、quoin 136 120），對 x 中線左右差 0、6 連通 1 塊。
  - 砲管 36 格 ＝ 1.80 m；外形照 basecamp 的 18 磅長砲（憲法號 `draft_guns2.py` long18）沿砲管 × 36/55、半徑 × 0.6；半徑挑在格子上會換截面的值（3.05／2.9／2.5／2.3／2.05／1.5 ⇒ 29／25／21／21／13／9 格），砲口挖空 r 1.0、深 6。
  - truck carriage 照 18 磅那座縮（長 × 0.62、高 × 0.57、cheek 2 格厚）：長 0.95 m、cheek 外寬 0.55 m（砲門 0.5 m 寬，砲架留在舷牆裡）；前輪 r 2.6、後輪 r 2.3。砲軸離甲板面 0.625 m。
  - 固定點 7：muzzle（砲口挖空那一格）、breech、cascabel、train、trunnion、eye-aft／eye-fwd。
- **模型** 12 門，掛在主甲板子作品（`甲板-主/砲-S1…P6`；1、2 號在艙房地板上）：scale 0.5 明寫、pivot ＝ 砲架前緣中間、甲板面（子作品 7.5,26,0）；S 舷照原樣、**P 舷 mirror=y**（繞 pivot 翻 ⇒ 砲口 −y，eye-aft 還在船尾側 —— 不用 rotate 180，那樣 aft／fwd 會對調）。
  meta：`kind=gun, gun=4l, side, port, deck=cabin|main`。
- **擺法**（Shipbuilding §4.2）：x 對準砲門中線、y 從舷牆外面往裡每 0.5 格退，退到模型每一格的格心＋八個角都不在現況（nf_state stage12、全部子作品）的實心格裡；排序 ＝ 四輪全著地 ＞ 砲口伸出 ≥ 1 格 ＞ 置中 ＞ 推得出去。
  - 🩸 第一版只要「不撞」：2、5、6 號只有偏 1 格那一個位置放得進去 —— 量了才知道是**甲板沿舷弧的台階**（0.1 m 一階），砲架一側撞上高的那一階；而 1、4 號更糟：放得進去，但**兩個輪子懸空 0.1 m**。我第一眼把偏 1 格讀成「沒置中」，去查置中差多少，才看到真正的原因；搜尋程式只回答了「放得進去」，「放對了沒」那一題它從來沒被問過。⇒ 加「輪底正下方要是實心」進排序，偏移放寬到 ±1.5。
  - 結果：10 門四輪著地；**4 號那一對沒解** —— 台階就在砲門正下方（x 185／186），砲門 5 格寬，往哪邊挪都閃不開 ⇒ 放在高的那一階，船尾側兩個輪子懸空 0.1 m（照實記，⛔ 不刻甲板、不把砲歪 9.5° 去貼）。1 號為了著地往船尾挪 1 格，砲口只伸出舷牆外 0.75 格（0.075 m）。
- 落格：子作品一刀 placed 1,452 ＝ 清單；固定點 7；模型 12（第一輪 1 個 IOException：Unable to remove the file to be replaced —— TASK-0533 那一族，補跑 P5 ⇒ 讀回 12 個 ok）。
- 讀數：
  - 引擎 stats（組裝件）：**95,368 格**（＋0，砲是模型）、link_overlap 0、1 個元件、空腔 0、左右差 0；models_drawn 19（帆桁 7＋砲 12）、models_broken 0；ropes_broken 0。
  - `check_guns.py`（讀組裝件 list／parts／obj、-gun-4l list）：結果帳 95,368／95,368 缺 0、多 0、色差 0；-gun-4l 1,452／1,452 缺 0、多 0、色差 0；固定點 84（12 × 7）引擎 vs 我算的最大差 **0.0**；網格三角形重心往裡 0.02 格落在實心格 **0／10,152**；砲口伸出舷牆外最小 0.75 格（1 號）、最大 4.25（3、5 號）；砲軸在開口高度的 0.45；輪底著地：10 門 1.00、4 號兩門 0.50。
  - 反向對照：整批往外 3 格 ⇒ 固定點報 3、S 舷撞 299 個三角形；整批往下 1 格 ⇒ 12 門全撞（835）。
  - 繩：281 條的管子頂點換回砲的子作品座標，落在砲的格子裡 0；最近的是 jib sheet，離 6 號砲 3.0 格（0.3 m）。⚠ 只量了頂點，頂點之間的線段沒逐段量。
  - 🩸 量尺：**引擎匯出的 obj 是 y 朝上**（x, 作品 z, 作品 y）。我第一次照作品座標讀，報「碰撞 0、輪底全懸空、輪底 z 52」—— 那個 0 是一把轉錯軸的尺給的。抓到它的是「輪底 z 52」這個數長得像 y。⇒ 跟階段十二的「OBJ 用名字當鍵、量的不是旗」同一族：**obj 讀進來先拿一個已知外框對過軸，再量**（S3 的外框 x 167.75–175.25、y 96.5–116.5、z 30–38 ⇒ obj 給的是 (167.75, 30, 96.5)）。
  - 🩸 `view region=` 只裁格子、模型照畫 —— 階段八、九的筆記都寫了，我照樣先用 region 拍特寫，拍出一張浮在空中的砲陣。改 target＋zoom（zoom 6 鑽進船殼，2 剛好）。
- 過程圖：`overlays/stage13_gun4_yaw{30,150}.png`（單門）、`stage13_assembly_yaw60.png`、`stage13_guns_deck_yaw60_pitch55.png`（藏後甲板看 12 門）、`stage13_guns_outside_S_yaw100.png`（舷外：砲口伸出砲門）、`stage13_guns_inside_S_yaw-70.png`（舷內 3、4 號）、`stage13_guns_side_S_yaw100.png`（全景側面）。

## 階段十四 新圖紙 14：砲具與砲索（環首螺栓 18 格一舷＋鏡像、砲索 60 條）—— 落格（2026-10-13 晚，wake #118）
Tim：「提交吧 然後繼續做砲具與砲索 GO」。設計 plan.json `gunfittings`（provenance `gunfittings`、`.ring`、`.deck_ring`、`.ropes`）；產生 `design/draft_gunfittings.py` ⇒ `masks/gunfittings/side.vox.txt`、`verify_gunfittings.json`；下 CLI `design/apply_gunfittings.py <design> create|stamp|anchors|links|ropes`；讀數 `design/check_gunfittings.py`（只讀引擎匯出）。重跑逐位元組相同；`nf_state.py` 加 stage14（`fittings_S／_P`）。
- 做法照 basecamp 憲法號階段二十一、二十二（Shipbuilding §4.4）：每門 5 條繩 —— breeching 兩條（cascabel → 兩側船牆的環）、side tackle 兩條（eye-aft／fwd → 同側的環）、train tackle 一條（train → 甲板的環）；滑車畫不出來，一條細繩代表一組 tackle。shot garland、rammer／sponge 這次不做（todo）。
- **子作品** `summit-night-falcon-01m-gun-fittings`（parent 甲板-主、tags sub、0.1 m、框 175 × 40 × 34）：一舷（S）18 格鐵 73 —— 船牆的環 12（每門兩側）、甲板的環 6。組裝件關聯 `砲具` at 85,81,18、`砲具-鏡像` at 85,40,18 mirror=y（at.y ＝ 161 − 81 − 40）。固定點 18（`ring-<n>-aft|fwd`、`deck-<n>`）。
- **環的位置**（設計決定；憲法號是 24 磅砲、砲門中線 ±8–11、甲板面 ＋8，照 4 磅砲縮）：船牆的環在砲門開口外側第一欄起（offset 0..4）、甲板頂格 ＋4（開口下緣下一格），牆內面第一格空氣；要求那一格空、不在任何一門砲裡、cascabel → 環與 eye → 環的線不穿過別的實心或別門砲；P 舷鏡過去再量一次。結果 offset 全是 0，只有 3 號是 1 —— offset 0 那兩格 (168,108,33)、(174,108,33) 落在 S3 自己的砲架格裡（量過；3 號砲退得最少、離牆最近）。🩸 這句原因我第一次寫進筆記時沒量，是寫完回頭才量的。甲板的環：train 往船裡 5 格（憲法號 9 × 砲架長比 0.62），6 門都第一個候選就過。
- **繩**：breeching 0.4／slack 1.12／#b59a6a、tackle 0.25／1.03／#a08458、train 0.25／1.05／#a08458（粗細照砲縮；0.25 是本船 ratlines 的粗細）。分組 `guns/breeching`、`guns/tackle`、`guns/train`。端點 `model:甲板-主/砲-XN/<點>`、`砲具[-鏡像]/<環>`。
- 落格：子作品一刀 placed 18 ＝ 清單；固定點 18、關聯 2、繩 60，全部一次成功（這一階段沒有撞到 IOException）。
- 讀數：
  - 引擎 stats（組裝件）：**95,404 格**（＋36）、link_overlap 0、1 個元件、空腔 0、左右差 0；繩 341（281＋60）、ropes_broken 0、ropes_ungrouped 0。
  - `check_gunfittings.py`（讀組裝件 list、sub=ropes、obj）：結果帳 95,404／95,404 缺 0、多 0、色差 0；60 條都在、全 ok；兩端 引擎 vs 我算的（砲的固定點照 at／pivot／scale／mirror、環的格心、P 舷鏡過去）最大差 **0.05** —— 引擎讀數只印到小數一位，這是四捨五入的量；繩管頂點（離兩端 1.5 格以外）落在實心或別門砲 **0**。
  - 反向對照：預期端點偏 3 ⇒ 報 3.0；繩網格往下 3 ⇒ 中段撞 1,690 個頂點。⚠ 往船頭 3 格 ⇒ 中段仍是 0：繩沿船長平移還在空氣裡，那個方向本來就量不到 —— 反向對照的方向要挑「一定會撞」的那個，⛔ 不是每個方向都證明尺會叫。
  - ⚠ 中段只量了管子的頂點（同階段十三），頂點之間的線段沒逐段量。
- 過程圖：`overlays/stage14_tackle_inside_S_yaw-70.png`（3、4 號）、`stage14_tackle_S56_yaw-110.png`（5、6 號）。

## 階段十五 新圖紙 15：舵改外部模型、舵輪（輪轂上隼的疤）—— 落格（2026-10-13 晚，wake #118）
Tim：「提交吧 然後繼續做舵與舵輪 GO」。設計 plan.json `helm`（provenance `helm`、`.scar`、`.parts`、`.rudder`）；產生 `design/draft_helm.py` ⇒ `masks/helm/{wheel,stand,rudder_carve,gudgeons_hull}.vox.txt`、`verify_helm.json`；下 CLI `design/apply_helm.py <design> create|stamp|anchors|rudder|unlink|models`；讀數 `design/check_helm.py`（只讀引擎匯出）。重跑逐位元組相同；`nf_state.py` 加 stage15（舵從此是模型：鍵改名 `rudder_model`，`occupancy()` 不算 `*_model`）。
- **舵輪（原文＋作者決定）**：原文只寫「舵輪正中央那隻俯衝的隼被卡戎剝下來鑄了銅牌，留下一塊淺淺的疤」（002:79、007:41）。其餘設計決定（⚠ 輪徑等未查證，照憲法號比例縮）：單輪、輪徑 1.2 m、把手到 1.44 m、輪軸離甲板 0.96 m、8 根輪幅（king spoke 朝上）。
  - **疤**：輪轂（深木 104、直徑 0.4 m）朝船尾那一面，照旗的隼剪影（ensign.png × 0.8）刻淺 1 格（0.02 m），底下那格換淺木 177 —— 剝掉之後露出的新木頭；54 格。旗跟舵輪是同一隻隼（階段十二）。
  - 拆兩件（0.02 m 子作品當外部模型、scale 0.2 明寫、parent 甲板-後）：`-wheel`（會轉的：輪、輪幅、輪轂與疤、輪軸、鼓輪）8,267 格、`-helm-stand`（底座、兩根支柱、輪軸孔）9,036 格；兩件左右差 0、各 1 塊。模型 `甲板-後/舵輪`（meta `kind=wheel, turn_axis=x, pivot_anchor=axle`）、`甲板-後/舵輪座`（`kind=wheel_stand`），同一個 at (94, 80.5, 51.5)、pivot 輪軸中心 (26, 37.5, 47.5)。固定點：axle、hub-aft、drum-rope-a／b（之後舵索用）、base。
  - 擺法：後甲板 x 82–108 每 0.5 試，兩件不撞、底座底面四角全著地，離 x 96 最近 ⇒ x 94（15 個候選，x 82–104）。
  - 🩸 v1 舵輪左右差 145 格：水平那兩根輪幅（3 點、9 點）離軸剛好等於門檻 1.0，浮點讓兩舷判得不一樣；疤的邊界也有平手 ⇒ 輪幅與疤都用 |dy| 判。
- **舵 → 外部模型**：組裝件拿掉關聯 `舵`，改成組裝件的模型 `舵`（source -rudder、scale 1、at ＝ pivot ＝ (68.5, 80.5, 0)）；meta `kind=rudder, turn_axis=hinge, hinge_x/y/z, axis_x=-0.2775, axis_z=0.9607, max_deg=35`；固定點 stock-top (55,80,44)（之後舵柄用）。
  - 轉軸 ＝ 舵柱中心線（前緣面往後 1.5 格；前緣面量過 z 0 x 70 → z 44 x 57，後傾 16.1°）。
  - gudgeon（前緣面之前的 pintle 帶子 73，32 格，釘在艉柱上、不該跟著轉）⇒ 舵子作品刻掉、貼回船殼（船殼標記 stage15 begin／end；舵 577 格、1 塊）。
  - 🩸 v1 想削前緣（bearding）讓轉 ±35° 零碰撞 —— **落格之前量了**：軸放在前緣面要削 141 格、往後 0.5–2 格要削 109–130 格，每一種都把舵柱切成 2–3 塊。舵柱是 3×3 的斜棒、每 3 層往後錯一格，削掉一欄就只剩斜角相接 —— **斜面上的階梯病，第五次**。這次是動手之前認出來的。⇒ 不削，改量「轉過去穿進多深」：±35° 時 5×5×5 取樣 72,125 個裡 2,384 個落在實心、77 格舵碰到；第二層以下只有 35 個（EDT ≤ 1.41）⇒ 角落擦進艉柱表面一層（< 0.1 m）。±20°：2,002／8。⚠ 遊戲轉舵到底時，舵前緣的角會穿進艉柱表面一點點 —— 照實記，⛔ 不說「零碰撞」。
- 讀數：
  - 引擎 stats（組裝件）：**94,827 格**（95,404 − 舵 609 ＋ gudgeon 32）、link_overlap 0、1 個元件、空腔 0、左右差 0；模型 22（帆桁 7、砲 12、舵、舵輪、舵輪座）、models_broken 0。
  - `check_helm.py`：結果帳 94,827／94,827 缺 0、多 0、色差 0；固定點 6 個 引擎 vs 我算的最大差 0.0；三件網格三角形重心往裡 0.02 落在實心 0／620、0／2,578、0／98；舵網格外框 (54,78,0)–(70,83,45) ＝ 舵的格子外框；舵輪到 boom 最近 4.28 格（0.43 m）；最近的繩 8 格內沒有；底座著地 1.0。反向對照：往下 2 ⇒ 固定點報 2.0、舵撞 14、座撞 10（著地報 0.5 —— 沉進甲板時底下仍有一半是實心，「著地」這把尺對下沉不叫，叫的是碰撞；🩸 筆記第一版抄了修尺之前的 0，重跑才更正）；往上 2 ⇒ boom 距離 2.41、著地 0。
  - 🩸 量尺兩把第一版是壞的：① 底座著地用底面頂點 —— 外圈頂點剛好在格子邊界上、floor 落到隔壁格 ⇒ 報 0.5（設計那一側明明要求全著地才放）；改用底面三角形重心 ⇒ 1.0。② 舵輪到 boom 用頂點對頂點 —— boom 整根只有 120 個頂點、擠在兩端，中段是長三角形 ⇒ 報 45.6 格；拿 parts 的 boom 外框（z 60–68.4）一對就知道不可能，改在三角形面上取樣 ⇒ 4.28。兩次都是**網格的頂點不代表網格**。
  - 舵從側面看不出來（顏色跟船殼一樣）⇒ 同一個鏡頭藏起「舵」再拍一張，差 110,874 px（x 367–801）⇒ 有畫出來；那個差做成標示圖。
- 過程圖：`overlays/stage15_wheel_aft_yaw-160.png`、`stage15_wheel_scar_close.png`（疤）、`stage15_helm_deck_yaw-30.png`、`stage15_rudder_model_side.png`、`_side_marked.png`（舵染色：藏與不藏的差）。
- **給遊戲**（@ame seq 24230 逐題回）：船殼那條關聯 meta `kind=ship, waterline_z=15, crew=31`（`sub=links` 讀回）；砲只留 `gun=4l`（重量、砲班由遊戲的砲種表管，⛔ 不寫 shot_lb／mass_t）；艙房比主甲板低 7 格 < 10 ⇒ 遊戲把 1、2 號跟主甲板算同一層。還要：彈藥庫 `kind=magazine`＋火藥桶 `kind=powder`（艙房地板底下就行）、梯子 `kind=ladders`（可選）。帆名列給她了（seq 24231）。

## 階段十六 新圖紙 16：舵柄與舵索 —— 落格（2026-10-13 晚，wake #118）
Tim：「提交吧 然後繼續做舵柄與舵索 GO」。設計 plan.json `steering`（provenance `steering`、`.port`、`.ropes`）；產生 `design/draft_steering.py` ⇒ `masks/steering/*.vox.txt`、`verify_steering.json`；下 CLI `design/apply_steering.py <design> voxels|anchors|ropes`；讀數 `design/check_steering.py`（只讀引擎匯出）。重跑逐位元組相同；`nf_state.py` 加 stage16。
- **做法（設計決定）**：有舵輪的船，舵柄在船尾艙房、後甲板底下，舵索從鼓輪往下穿甲板、經滑車接到舵柄頭（憲法號階段二十七：舵索往下穿進甲板）。量了船尾中線剖面：舵頭在艉板外 z 37–44，艙房就在後甲板底下（x 64 起 z 31–41 空），後甲板板 z 42–44、橫樑 z 39–41。
- **舵柄**（加進舵子作品，跟著舵轉）：x 59–80（2.2 m）、z 37–38、1 格寬、木 136，末端一格鐵 73；接在舵頭前緣（6 連通 2 格）。固定點 `tiller-end` (80,80,37)。舵 577 → 621 格。
- **舵柄口**：舵柄繞舵軸轉 −35..+35°（每 1°、每格 5×5×5 取樣）掃過的現況實心格刻掉 —— 船殼 53、船尾裝飾 6（含刻完落單的 2 格碎塊）。z 37 那一層艉板只剩中間那根柱子（兩旁是船尾窗），舵柄口就開在柱子上。
  - 🩸 第一版刻完，柱子兩側各剩一格斷開（模擬 3 塊）⇒ 刻完之後 ≤ 8 格的碎塊一起刻。模擬那時還報了一個 782 格的空腔 —— 是插板槽，槽口貼著框的底邊；我的模擬只把 (0,0,0) 那團空氣算外面。改成框外一圈都算外面 ⇒ 0（引擎 stats 也是 0）。
- **舵索 6 段**（每舷 3：鼓輪底 → 板下導索塊 → 舷側滑車 → 舵柄頭；粗 0.25、slack 1.02、#a08458、組 steering）：導索塊在鼓輪正下方（x 93／94、y 80，掛在甲板板下）、甲板板繩孔 2 格、舵輪座底板繩孔 3×3（0.02 m）兩處 54 格；鼓輪上新固定點 tiller-rope-a／b（鼓輪最底那格）。
  - 🩸 **滑車 v1 放錯位置**：y 74／86 已落格，量舵柄頭 ±35° 的位置才看到它會擺到 y 67.9／93.1 —— 比滑車還外面，舵索會被反著拉。⇒ 刻掉 v1（4 格）、往外移到 y 64／96（舵柄頭擺不到的地方）；`verify_steering.json` 照當時順序留著 v1 那一刀與刻掉它的那一刀，nf_state 重播逐刀對得上（重產的 v1 檔 md5 跟當時落的一樣）。
- 落格：舵柄 44、船殼刻 53、船尾裝飾刻 6、後甲板刻 2＋貼 6、刻 v1 滑車 4＋貼 v2 4、舵輪座刻 54 —— 每刀 placed ＝ 清單。標記 stage16 begin／end 五件（🩸 舵那件的 begin 撞 IOException 沒落，用 upto= 補在舵柄前那個事件；繩第二輪 1 段 IOException，重跑全過）。
- 讀數：
  - 引擎 stats：**94,772 格**、link_overlap 0、1 個元件、空腔 0、左右差 0；繩 347、ropes_broken 0、ungrouped 0。
  - `check_steering.py`：結果帳 94,772／94,772 缺 0、多 0、色差 0；固定點（tiller-end、tiller-rope-a／b）引擎 vs 我算的最大差 0.0；舵＋舵柄網格碰撞 0／642；舵索表面取樣（離兩端 1 格以外）落在實心或舵輪座／舵輪 0。反向對照：往船頭 1 格 ⇒ 舵撞 213、繩 2,444（b1 撞 88；a1 剛好挪進 b 的孔，0 合理）；往上 1 格 ⇒ 繩 2,326。
  - 設計那一側：舵柄轉 −35／−20／0／20／35° 落在實心 0／5,500；舵柄頭 ±35° 到 y 67.92／93.08、z 36.4（軸後傾，擺到底降 1.1 格）。
  - 🩸 **量尺第三次撞同一個病**：繩的中段第一版只拿管子頂點 —— 直的繩（下垂 0）整段只有兩端兩圈頂點，往船頭挪 1 格穿過甲板也報 0。改在三角形面上取樣。今晚第三次：boom、底座、繩，同一句「網格的頂點不代表網格」，筆記寫了也攔不住手。
  - 觀察：`hide_links=甲板-後` 會把綁在它固定點上的繩一起藏 ⇒ 看艙房改用 region 切到 z 40、`rope_groups=steering` 只畫舵索。
- 過程圖：`overlays/stage16_steering_only_yaw-60.png`（只畫舵索、切掉甲板）、`stage16_tiller_cabin_cut_yaw-40.png`、`stage16_tiller_port_stern.png`。

## 階段十七 main staysail（桅間支索帆）—— 掛帆（2026-10-13 晚，wake #118）
Tim 看了渲染問「這裡好像少一張帆（還是設計上就是這樣？）」—— 主桅 gaff 主帆上方那根光桁底下沒有帆。我回：照定稿圖是 brigantine，主桅不掛 course；那根桁（`yard-main-course`）是階段十一加給 main topsail 下角綁的，⚠ 真船有沒有沒查證；給三條路。Tim：「加 main staysail」。
- 設計 plan.json `sails.staysails`（provenance `sails.staysails`）；`draft_sails.py` 加「桅間支索帆」迴圈（不跟艏斜桅那一疊比疊放）。重產 verify_sails.json：原本 8 面帆、20 條帆腳索**逐筆相同**，只多 main-staysail＋2 條 sheet；重跑 md5 相同。
- 掛在 main-stay（主桅 top-fwd → 前桅 aft-low）：tack_f 0.1、head_f 0.7、foot 0.6、上翹 10°（照 fore-staysail 的值，設計決定）；帆腳索兩舷綁 pinrail-7 pin-2。角：tack (198.9, 80.5, 53.7)、head (165.3, 80.5, 108.9)、clew 初始 (160.7, 80.5, 60.4)。
  - 🩸 v1 tack 綁在前桅腳 aft-low（stay 的下端）：引擎模擬後的布在 tack 上方鼓進往後傾的前桅 —— 196 個取樣點、21 格（x 204–206、z 45–52）。是**掛上去之後用引擎匯出量到的**（產生程式的碰撞世界停在階段十，只量平的布）。⇒ tack 沿 stay 往上 10%（實船支索帆的 tack 常綁在一段 tack pendant 上）。
- 讀數（`design/check_staysail.py`，讀引擎 obj＝模擬後的布）：sails 10、sails_broken 0；布取樣 16,184（離 luff >1.2 的 16,094）落在實心 **0**；最近的東西：前桅 shroud P3 18.4 格；其他帆：fore-course 24.4、mainsail 29.6、main-topsail 30.6。反向對照：整面往前 6 ⇒ 389。
- 過程圖：`overlays/stage17_main_staysail_yaw-75.png`。
- 給遊戲：帆名多一面 `main-staysail`（三角帆、主桅前面）。

## 階段十八 彈藥庫＋火藥桶 —— 落格（2026-10-13 晚，wake #118）
Tim：「提交吧 加main staysail 然後繼續做彈藥庫 GO」。ame（seq 24230）：最少一間 `kind=magazine`、桶 `kind=powder`，艙房地板底下就行。設計 plan.json `magazine`（provenance `magazine`、`.kegs`、`.aft_scuttle`）；產生 `design/draft_magazine.py <design> <-powder-barrel 的 list>` ⇒ `masks/magazine/{room,main_scuttle}.vox.txt`、`verify_magazine.json`；下 CLI `design/apply_magazine.py`；讀數 `design/check_magazine.py`。重跑逐位元組相同；`nf_state.py` 加 stage18（鍵 magazine）。
- 量艙房地板底下：x 86–138 中線上空氣從 z 5–8（龍骨內側）到 z 20–23（艙房地板橫樑底下）、V 形往兩舷收。
- **子作品** `summit-night-falcon-01m-magazine`（parent 船殼、0.1 m、框 98,50,0 起 24×61×24）5,587 格：房間 x 99–120、地板 z 8（松木 177、每 6 格橡木壓條 136）、**地板底下到船殼全部填實**（橡木 136，不留空腔）、兩道橫艙壁 x 98／121（銅 168、外圈橡木框）、側壁貼船殼一格銅皮到 z 18、門洞在船頭那道（3 寬 × 1.2 m）。組裝件關聯 `彈藥庫` at 98,50,0、meta `kind=magazine, powder_lb=800`。固定點 `blast` (110,80,16)（房間空氣重心最近那格）、`door` (121,80,9)。
- **火藥桶** 8 個：直接引用 basecamp 憲法號的 `-powder-barrel`（whole barrel 100 磅、0.02 m）當模型，scale 0.2 明寫、pivot 桶底中心；`桶-01..08`（meta `kind=powder, powder_lb=100`），步距 5 排在地板上、取樣點全在房間空氣裡、底下是地板。數量是設計決定（12 門 × 約 40 發 × 約 1.3 磅 ≈ 640 磅 ⇒ 6–7 桶＋小火器 ⇒ 8；⚠ 未查證）；powder_lb ＝ 桶數 × 100（Shipbuilding §9：不是史料）。
- 🩸 v1 落格前的模擬：後艙壁把船尾那段貨艙（x 66–97、z 5–26）**封成 5,604 格的空腔** ⇒ 艙房地板 x 84–86、y 79–81 開一個 3×3 的 lazarette 艙口（刻主甲板子作品 21 格），貨艙從艙房下去；彈藥庫照舊只有一道門。
- 讀數：
  - 引擎 stats：**100,338 格**（94,772 − 21 ＋ 5,587）、link_overlap 0、1 個元件、空腔 0、左右差 0；彈藥庫 models_drawn 8、broken 0。
  - `check_magazine.py`：結果帳 100,338／100,338 缺 0、多 0、色差 0；關聯 meta ＝ 我的；blast／door 引擎 vs 我算的最大差 0.0；8 個桶 meta 一致；桶網格碰撞 0、底面全著地、桶心最近 5.0 格。反向對照往下 1 ⇒ 撞 3,976、固定點報 1.0。
- 🩸 同一晚第三次 heredoc 的 `'
'` 進 Python 變成真的換行（draft_helm、draft_steering 之後又一次）—— 改檔走 Edit。
- 過程圖：`overlays/stage18_magazine_section.png`（只畫左舷半邊的格子，從右舷看進去）。

## 階段十八 v2 彈藥庫刻回船內 ＋ 最後兩格驗收（2026-10-13 晚，wake #118）
Tim：「提交吧 然後繼續做剩下的驗收 GO」。
- 🩸 **彈藥庫 v1 長到船外**：拿四個角度跟定稿圖並排時，船底下有一塊橘褐色的板子。是 draft_magazine.py v1 的「房間」只在 2D 橫切面從中線連空氣 —— 外板在切面上是階梯、只靠斜角相接，艙內空氣從斜角縫漏到船外；地板與地板下的填實跟著長出去：**5,587 格裡 3,582 格在船底外**（x 98–121、y 56–104、z 0–8；松木地板 320 格也在外面）。當時三把尺（1 塊／空腔 0／左右對稱）全過 —— **沒有一把在問「它在不在船裡」**。這個錯已經提交過（7a12322）、也匯出過 .vxk 給 ame（208a1761）。
  - v2：「艙內」＝ 同一個 (x, z) 那一列左右兩邊都有船殼、正下方也有船殼（船殼碗裡面），房間與填實都只在艙內。v1 那份清單凍結成 `masks/magazine/room_v1.vox.txt`，verify_magazine.json 照順序記：v1 那一刀 → 刻掉 v1 多出來的 3,582 格（`room_v1_out`）；v2 沒有要補的格（v2_in 0）。nf_state 重播 96,756。
  - 彈藥庫 5,587 → **2,005 格**（橡木 615、銅 1,081、松木 309）；房間、8 個桶、blast／door、meta 都沒變。標記 stage18b。
  - 新尺 `design/check_inside_hull.py <船殼 list> <受測 list> <at>`（只讀引擎匯出）：彈藥庫 v2 船殼碗外 **0**；拿 v1 那份凍結清單餵它 ⇒ **3,582**（正好是漏出去的量）；往下 3 ⇒ 956。順手量主甲板 13,768、後甲板 6,896、砲具 18、fife rails 739 —— 都是 0。
  - 引擎：組裝件 **96,756 格**、1 元件、空腔 0、左右差 0；check_magazine 全過。**.vxk 重匯：96,756 格、checksum 1278c741**（繩 349、帆 10、模型 30、帶 meta 32、固定點 435）；酒館 seq 24251 跟 ame 更正；seq 24252 收回我自己一句沒量過的「浮力會被多算」。
- **驗收「產生程式重跑逐位元組相同」**：20 支 draft_*.py 照階段順序全部重跑（log 每支 rc 0）⇒ `git diff` 只差 1 個檔：verify_flag.json 的貼圖路徑 —— draft_flag.py 把「呼叫時給的 design 資料夾」接進路徑寫進檔，階段十二是用絕對路徑呼叫的。⇒ 用絕對路徑再跑一次 ⇒ `git diff` **0 行**。⚠ 照實記：draft_flag 的輸出跟呼叫方式有關（要用絕對路徑呼叫）；沒改程式 —— check_flag 拿這個欄位去開檔。`git status` 那一百多個 M 只是換行符（產生程式寫 LF、checkout 是 CRLF），git 正規化後內容相同，已從版控還原。
  - （draft_magazine 的 v2 改動是這一輪的修正，重跑兩次 md5 相同。）
- **驗收「跟定稿圖並排比」**：`overlays/final_compare_sheet.png`（左：定稿圖四個角度；右：作品 yaw −90／90／0／180）。差異：
  - 一樣：雙桅 brigantine（前桅三層橫帆；主桅縱帆＋頂上一面橫帆 —— 正面、船尾那兩格也看得出同一套）、張翅的隼船首像、長艏斜桅＋jib-boom、桅頂平台、ratlines、每舷約 6 個砲門、船尾窗。
  - 不一樣（決定過的）：① 旗：圖是骷髏旗，作品是隼（階段十二，作者決定）；② 舷牆與後甲板：圖比較高（階段二量過，後甲板圖上高約兩成半），照拍板不追。
  - 不一樣（沒決定過的）：③ 帆：圖畫得比較平，作品鼓得多（旋鈕是風，等 Tim）；④ 船尾雕飾、甲板上的細節：圖多，作品簡單；⑤ 船底顏色：作品水線以下是淺色船底漆，圖是黑白，沒辦法對。

## 階段十九 梯子三座＋扶手繩（給遊戲 kind=ladders）—— 落格（2026-10-13 晚，wake #118 小歇後）
Tim：「夜隼號目前已經完工了嗎（可以匯入遊戲了嗎?）如果還沒的話 繼續施工 GO」。拿造船規格 §10 換船檢查表（Senate `Docs/Workflows/Sculpture_Shipbuilding.md`，basecamp 下午 6f1902e 加了梯子那一行）逐行對：只差「梯子的關聯 meta `kind=ladders`、每座 foot／lo／hi／head」—— 這艘船一座梯子都沒有，補砲班的人從主甲板走不到艙房那兩門砲。
設計 plan.json `ladders`（provenance `ladders`、`ladders.geometry`）；產生 `design/draft_ladders.py <design> <組裝件 obj>` ⇒ `masks/ladders/ladders.vox.txt`、`verify_ladders.json`、`sheet19_ladders_v1.png`；下 CLI `design/apply_ladders.py`；讀數 `design/check_ladders.py`。`nf_state.py` 加 stage19（鍵 ladders），重播 97,160 ＝ 引擎，逐格差 0。
- **找位置與梯子形狀**照 basecamp 餘燼號 `design/draft_ladders.py` 的 edges／shape／try_one（她照憲法號；56°、側板 1 格、踏板 1×2 開放式、扶手柱 0.9 m ＋扶手繩）。改的：甲板面與邊從 plan 讀；障礙 ＝ nf_state 的格 ∪ 組裝件 obj 的繩／帆／模型（三角形面上每 0.25 格取樣）；扶手柱下那根多試 R−2、R−1（`post_gap_min` 3：斷口只高 1 m，梯子只有 5 欄，照她「柱距 ≥ 4」放不下）；鏡像 y ↔ 160 − y。
- 量現況：後甲板板頂 x 99–113 z 40、x 114–138 z 39；艙房地板 z 23／22（同一處換階）；主甲板 z 29；companion 開口 x 110–117、y 76–84，圍板 2 格。斷口中線被主桅 fife rail 擋（x 142 起），兩舷夾在 fife rail（y 72–88）與舷側 pin rail（y ≤ 54／≥ 106）之間。
- **三座**（子作品 `summit-night-falcon-01m-ladders`，parent 船殼、0.1 m；關聯 `甲板-後/梯子` at 0,0,0、meta `kind=ladders`）404 格（側板 174、踏板 126、扶手柱 104）：
  - `companion`：後甲板艙口後緣 x 110 往前斜下到艙房 x 121，高 20 格、5 階；第一個候選就過。
  - `break-S`／`break-P`：斷口 x 139 往前斜下到主甲板 x 143，高 10 格、2 階；y 94–102／58–66（兩舷逐格對稱）。
  - 扶手柱頂固定點 12 個（`manrope-<梯>-<P|S>-<top|bot>`）、扶手繩 6 條（組 `ladders/manropes`，粗 0.3）。
- **遊戲的點**用 basecamp 的 `ladder_points.py` 算（她的尺，不是我寫的；複製到 scratchpad 跑、不帶 --apply ⇒ 一格沒寫進她的資料夾），結果存 `design/verify_ladder_points.json`，`apply_ladders.py points` 登記成固定點：

  | 梯 | foot | lo | hi | head | 頭頂（格） |
  |---|---|---|---|---|---|
  | companion | (121,80,23) | (119,80,28) | (112,80,40) | (108,80,41) | 16／40 |
  | break-S | (144,98,30) | (142,98,34) | (141,98,37) | (138,98,40) | 40／40 |
  | break-P | (144,62,30) | (142,62,34) | (141,62,37) | (138,62,40) | 40／40 |

  ⚠ 第一階都高 0.4–0.5 m（foot → lo：companion 23 → 28、斷口 30 → 34）—— 她的踏板規則「最低一階離地 ≥ 2 格」，餘燼號 poop 那座也是 129 → 134。照抄，沒改。
- 讀數（`check_ladders.py`，只讀引擎 list／parts／obj／sub=ropes）：
  - 引擎 stats：**97,160 格**（96,756 ＋ 404）、link_overlap 0、1 個元件、空腔 0。
  - ① 結果帳 97,160／97,160：缺 0、多 0、色差 0　② 左右對稱（含顏色）不同 0
  - ③ kind=ladders 關聯 1 個、固定點 24；遊戲點 12 個 引擎 vs 算的（＋0.5）最大差 0；另一條路量「腳踩那格是空的、正下方實心（lo／hi 下面是踏板色）」12／12
  - ④ 梯子的格被別的繩／帆／模型穿過 0；扶手繩中段落在實心：撞 0、貼自己的柱 6＋6（companion 兩條：繩從柱頂往下垂，先貼著自己那根柱走一段 —— P 那條離端點 1.5 格外落在柱裡的 6 個取樣點全在 (111,76,46) 那一格；v1 的尺沒分開，第一次報成「撞 6」，拿網格逐點查了才分）
  - ⑤ 扶手繩 6 條 ok、兩端最大差 0；全船繩 355 條 broken 0
  - 反向對照：往上 2 ⇒ 缺 214／多 214、點差 2、繩端差 2；往下 3 ⇒ 缺 240／多 258、點差 3；往 +y 20（推進 S2 砲）⇒ ④ 報 砲-S2 58、它的砲索 2＋2、主桅 lanyard／deadeye 各 1。
- 重跑逐位元組相同：拿 `hide_links=甲板-後/梯子` 的 obj（藏梯子連同它的扶手繩 ＝ 階段十八的現況）重跑 ⇒ verify、清單、圖紙三個檔 sha256 全 OK。
- **.vxk 重匯**（`summit-night-falcon-01m-assembly/exports/night_falcon.vxk`）：**97,160 格、checksum 358bf2ac**（封裝回讀 ✓；繩 355、帆 10、模型 30、關聯外框 19、帶 meta 33、固定點 459）。
- 沒做的：貨艙沒有地板 ⇒ 主艙口、前艙口不放梯子（餘燼號、憲法號也沒有通 orlop 的）；彈藥庫的門在貨艙那一側，要走 lazarette 艙口下去（沒有梯子）。
- 過程圖：`overlays/stage19_ladders_yaw{135,-135}.png`（拿掉兩根桅與帆）、`stage19_ladders_break_yaw35.png`、`stage19_ladders_companion_yaw-60.png`。

## 階段二十 羅經櫃（kind=binnacle）—— 外部模型（2026-10-13 晚，wake #118 小歇後）
Tim：「提交吧 然後繼續做羅經櫃 GO」（階段十九提交 cc61f34）。規格 §9 有 kind=binnacle（basecamp 餘燼號 10-13 補）。設計 plan.json `binnacle`（provenance `binnacle`、`binnacle.place`）；產生 `design/draft_binnacle.py <design> <組裝件 obj>` ⇒ `masks/binnacle/binnacle.vox.txt`、`verify_binnacle.json`、`sheet20_binnacle_v1.png`；下 CLI `design/apply_binnacle.py create|stamp|model`；讀數 `design/check_binnacle.py`。模型不是格 ⇒ nf_state 不加階段。
- 原作：夜隼號那具老羅盤是父親傳下來的，嘩變那夜指針被踩斷（001:35、007:61）；羅經櫃長什麼樣、船上現在用哪一具，原作沒寫 ⇒ ⛔ 不在櫃上加劇情記號（不像舵輪的疤有原文）。
- **子作品** `summit-night-falcon-01m-binnacle`（parent 甲板-後、0.02 m、18×26×52）15,892 格、1 元件、空腔 0、左右差 0：底座（104）、櫃身（136）＋四角深色柱、簷、朝船尾一扇羅經窗（金框 208、玻璃 37 往裡一格）、兩側燈窗（琥珀 253）、頂上銅罩（168，半球 r 6.5）、兩根燈煙囪（36）。簷頂 0.78 m、銅罩頂 0.90 m、煙囪帽 0.96 m（量清單）。尺寸照一般比例，未查證。
  - 🩸 第一版左右差 62：銅罩中心 cy 寫 12.5，框寬 26 的中線格心是 13.0 ⇒ 改了才 0。
- **擺法**（同舵輪）：中線、x 每 0.5 試；格心＋八角不落在 nf_state stage19 的格或 obj 的繩／帆／模型；四角著地；外框不進 companion 梯子 head 那一段（keep x 105–109）；離 x_target 102.5 最近。試 19 個：x 99–100.5 撞格（後甲板 x ≤ 98 高一階）也撞 obj、101–101.5 只撞 obj（取樣 3,240／480 點；是哪一件沒分開量，舵輪座外框到 x 99.0、舵輪到 99.2）、103.5 以後進 keep，剩 102、102.5、103 ⇒ **at (102.5, 80.5, 41)**，外框 x 100.7–104.3。模型 `甲板-後/羅經櫃`、pivot 底面中心、scale 0.2、meta `{kind: binnacle}`（§9：只說這是什麼）。
- 讀數（`check_binnacle.py`，只讀引擎 list／parts／obj）：
  - 引擎：組裝件仍 **97,160 格**、1 元件、空腔 0；models_drawn 31、broken 0。
  - ① 組裝件 ＝ stage19：缺 0、多 0、色差 0　② meta ＝ 我的；外框 引擎 [100.7, 77.9, 41]–[104.3, 83.1, 50.6] ＝ 我算的（兩位小數）
  - ③ 碰撞三角形 0／534　④ 著地：底面 210 個取樣點正下方實心 1.000
  - ⑤ 最近的模型：舵輪座 1.75 格、舵輪 3.2 格；外框外 6 格內沒有繩；companion head 那 9 格：在外框裡 0、實心 0
  - 反向對照：往後 2 ⇒ 碰撞 4、離舵輪座 0.15、繩出現（舵索 4.1）；往下 0.5 ⇒ 碰撞 10；往前 4 ⇒ head 那段被外框蓋 6；往前 9（艙口上）⇒ 著地 0.067。
  - 🩸 ④ 第一版只拿底面三角形的重心：底面被合併成 **2 個**三角形 ⇒ 2 個點代表整個底面（網格的頂點／重心不代表網格 —— 今晚第四次）。往前 9 的反向對照之前改成面上取樣。
- 重跑逐位元組相同：用 `hide_models=甲板-後/羅經櫃` 的 obj 重跑 ⇒ verify、清單、圖紙 sha256 全 OK。
- **.vxk 重匯**：格數與 checksum **不變**（97,160、358bf2ac —— checksum 只算格子）；檔案變了（模型 31、網格 14 份、帶 meta 34）⇒ 檔案 sha256 0a540537…。⚠ 遊戲那側不能只對 checksum。
- 過程圖：`overlays/stage20_binnacle_yaw-135.png`（舵輪、羅經櫃、companion）。

## 修正：帆桁 meta 補 `sail`（2026-10-13 晚，Tim 在遊戲裡抓到）
Tim：「遊戲中發現夜隼號後面的帆好像不是固定在這桿上面」（截圖：boom 轉出舷外，mainsail 的下緣留在原地）。
- 🩸 **不是帆角綁錯**：引擎裡 mainsail 四角綁的都是模型固定點（throat／peak ＝ `主桅/yard-main-gaff/bot8`／`bot64`，clew／tack ＝ `主桅/yard-main-boom/top96`／`top8`），釘住邊 0,2,3。.vxk 給遊戲的帆是**模擬好的網格**（只有頂點與三角形，沒有綁定）；遊戲靠**帆桁模型的 meta `sail`** 決定轉帆桁時哪面帆跟著（ame `10_ship.js`：`s.yards = sh.yards.filter(y => y.sail === s.name)`）。
- 造船規格 §5 寫了 meta 要帶 `sail`（憲法號每根都有，spanker 的 gaff 與 boom 兩根都寫 sail=spanker）——**階段八我漏寫了**，七根帆桁一根都沒有 ⇒ 遊戲轉 boom，mainsail 不知道要跟。
- 修：plan.json `yards.sail_of`（provenance `yards.sail_of`）、draft_yards.py 照它寫 `meta.sail` ⇒ verify_yards.json 只多了 sail（除了 sail 之外逐欄相同；遮罩逐位元組內容相同，只是換行符，已還原）⇒ `apply_yards.py models` 重下 7 個模型（meta 是合併的）。
  - fore-course／fore-topsail／fore-topgallant／main-topsail 各掛同名的帆；main-boom、main-gaff ⇒ mainsail；main-course（不掛帆的下桁）不寫。
- 讀回：parts 31 個模型，除了 sail 之外跟修之前逐欄相同、關聯相同；.vxk 解開後 6 個 `"sail"` 都在；格數與 checksum 不變（97,160／358bf2ac，模型 meta 不算在 checksum 裡），檔案 sha256 04f0ae5f…。
- ⚠ 遊戲把船打包進 HTML（`ArtGallery/HtmlGames/ame_constitution_broadside.html`）⇒ 要 ame 用新的 .vxk 重 build 才會生效；**我沒在遊戲裡看過修好的樣子**。

## 空艙房 2 間（TASK-0573；造船規格 §9.2）—— 2026-10-14 下午
Tim：「請標記一下艙房吧（只要標記妳建造的船）」。做法：子作品 `-cabin`（parent 船殼、tags sub、0.1 m、框 80×74×24，**不雕格子、只放固定點**），掛在 甲板-主 底下（關聯 `艙房` at 60,44,18、meta `kind=rooms`）⇒ 遊戲名 `甲板-主/艙房/1`、`/2`。下 CLI `design/apply_rooms.py create|link|anchors`。格子一格都沒動（97,160、checksum 358bf2ac 不變）。
- 艙房地板沿舷弧一階一階（z 28 x 65–69／27 x 70–77／26 x 78–87／25 x 88–98／24 x 99–113／23 x 114–137 —— rooms.py 的 floor_z 量的），遊戲要平地板 ⇒ 一階一間。
- **1**：x 122–137、y 56–104、z 23–36（1.6×4.9×1.4 m），斷口艙壁後、梯腳前；往梯腳那一面整面是門（34 格）⇒ 遊戲的格子 3×9、靠門一欄是走道，後兩欄順著 y 放得下兩張病床。
- **2**：x 100–110、y 61–99、z 24–37（1.1×3.9×1.4 m），砲 1 號與 companion 梯子之間；前後各差一階 ⇒ 遊戲的門算法（往外 8 格同一層）找不到門 ⇒ 補 `2.door` (111,80,24)（⚠ 遊戲排格子時不讀 .door —— 只讓 rooms.py check 過、標出入口；沒有門的房間遊戲不檢查走不走得到）。格子 2×7 全可放 ⇒ 一張病床。
- 不標的：z 25–27 那幾階最大 0.8–1.1 m 寬（放不下病床），而且在砲 1 號之間或舵柄底下（舵柄轉 ±35° 掃過船尾那幾階）。
- 砲是模型、不是格子 ⇒ 遊戲排床看不到它們 ⇒ 兩間都躲開砲的外框（S1／P1 到 x 99.2、S2／P2 從 x 113.8）；量了：兩間跟 31 個模型外框重疊 0。
- 讀數（引擎匯出 .vxk 到暫存資料夾，拿遊戲那支 `rooms.py` 的 check／scan 指過去，⛔ 沒碰遊戲的 _cache）：check 2／2 ✓（實心 0、地板 784／784、429／429、重疊 0）；scan（它看不到砲）獨立找到的候選裡有 1 號原樣、2 號只差 x 99 那一欄（砲外框邊上，我縮掉）。反向對照 1 號：往下 1 ⇒ 實心 784、往上 1 ⇒ 地板 0、往後 1 ⇒ 撞 6、往旁 3 ⇒ 撞 65。
- ⚠ 遊戲那側要 **reimport**（新的部件 `甲板-主/艙房`；metasync 只換既有部件的 meta 與固定點）—— 留給 ame；**我沒在遊戲裡看過**。

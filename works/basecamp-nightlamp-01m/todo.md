# 夜燈號 TODO（TASK-0538）

## 階段零 新圖紙（進行中；10-13 晚 Tim「繼續 go」⇒ 線形圖 v1 已交，等 Tim 看）
- [x] 底圖：Chapman Pl. LI（Tim 同意下載）、Pl. XXXI；收進 references（README、sha1）
- [x] 尺寸上限查資料（1795–97 1200 噸級東印度商船）⇒ 倍數寬度先碰上限（當初估 ×1.308；圖紙 01 由程式算 1.2852）
- [x] 讀圖：比例尺、站位、船頭柱、船尾柱、吃水線（drag）、船中橫切面、平面最大寬線、側面船中高度、肋底上升線（趨勢）⇒ `design/readings_LI.json`、`design/readings/`
- [x] 劇照輪廓目測（notes「輪廓」）
- [x] `design/plan.json`：參數＋provenance（原圖讀數／劇照比例／設計決定）
- [x] `design/draft_lines.py` ⇒ `sheet01_lines_v1.png`、`compare01_chapman_v1.png`、`verify_lines.json`（2026-10-13 晚；k 1.2852；讀數更正見 notes「圖紙 01」）
- [x] 畫圖前重量船尾柱：8.24°（363 列）
- [x] 圖紙給 Tim 看 ⇒ Tim「單層提交吧 然後開始下龍骨」（圖紙 Sculpture 68c3bc9）
- [ ] 圖紙 02：甲板線、砲門、船尾窗與 galleries、船頭 head 細部（下龍骨前或跟著階段做）
- [ ] 劇照看砲門（幾層、幾門、排法）—— 要看更多劇照的話先問 Tim（下載要先問）

## 階段一 龍骨（10-13 深夜雕完）
- [x] 護龍骨＋龍骨 13,510 格；結果帳 0 差、1 元件、空腔 0、原圖探針最大 0.56 格、反向對照 3.0（notes「階段一」）
- [x] 提交（Tim「單層提交吧 然後繼續階段二」）

## 下一步：階段二 船頭柱・gripe・船尾柱（新圖紙 03）
- 船頭：rabbet（readings_LI_bodyplan stem_rabbet_profile）、船頭柱外緣＋gripe＋knee（readings_LI stem_outer）；龍骨前端台階（x 35.30／35.47）要接上
- 船尾：船尾柱後面 8.24°（x 0.285＠龍骨頂）；前面那條線還沒讀（內艉柱／rabbet）—— 先讀 Pl. LI 側面圖船尾那幾條斜線
- ⚠ 船頭柱頂以上是船頭 head 與船頭像（設計），這一階段只做到 knee 底

## ⚠ 還沒定、要問 Tim
- 渲染圖要不要也真的發光（要擴充引擎、另開單）
- 船名（暫名夜燈號）

## ⚠ 沒提交
- Sculpture：`references/chapman-architectura-navalis-1768/`、`works/basecamp-nightlamp-01m/`（work.json、events、notes、todo、design/ 全部）—— 等 Tim 說提交

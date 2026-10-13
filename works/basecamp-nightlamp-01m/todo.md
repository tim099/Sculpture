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

## 階段二 船頭柱・gripe・船尾柱・內艉柱（10-13 深夜雕完）
- [x] 10,830 格；結果帳 0 差、1 元件、空腔 0、原圖探針最大 0.71 格、反向對照 3.0（notes「階段二」）
- [x] 提交（Tim「單層提交吧 然後繼續階段三」）

## 階段三 deadwood・apron（10-14 凌晨雕完）
- [x] 線形圖船殼後端改成照 L3 rabbet
- [x] 讀 A（cutting-down line）、B（keelson 頂）
- [x] 26,650 格；結果帳 0 差、1 元件、空腔 0、原圖探針最大 0.56 格、反向對照 3.0（notes「階段三」）
- [x] 提交（Tim「單層提交吧 然後繼續階段四」）

## 階段四 底肋・keelson（10-14 凌晨雕完）
- [x] 讀肋距（0.7066 m）、narrowing line
- [x] 底肋 36 片＋keelson；結果帳 0 差、1 元件、空腔 0、原圖探針最大 0.81 格、反向對照 8 組都對（notes「階段四」）
- [x] 提交（Tim「單層提交吧 然後繼續階段五」）
- [ ] 細修：底肋平頂接翹起段的那一格缺口（每片兩邊各一格？先量有幾片）

## 下一步：階段五 肋骨（futtocks、top timbers）
- 肋骨照船殼 molded 往上到舷頂；兩頭（16 號站以後、M 站以前）是 deadwood 上的 half floors／cant frames
- 舷頂以上（船尾樓、船頭起翹）照 silhouette top
- ⚠ 肋骨 sided、moulded 也沒查到出處 ⇒ 設計決定，跟底肋一致（sided 4）

## ⚠ 還沒定、要問 Tim
- 渲染圖要不要也真的發光（要擴充引擎、另開單）
- 船名（暫名夜燈號）

## 提交紀錄（Sculpture，單層、沒 bump、沒 push）
- 68c3bc9 圖紙 01＋底圖；8755a6a 階段一 龍骨；8331a5a 階段二；94db32c 階段三；階段四 見 git log（這一份 todo 跟著那一筆進去）

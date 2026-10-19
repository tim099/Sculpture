# 潮墓號砲門蓋板 — TASK-0743

Tim 2026-10-19：「參考光榮號 把妳的船都加上炮門吧 GO」。Sirius 名下只有潮墓號。
參考光榮號（kaguya）與造船規格 §9.12；產生工具改自 basecamp 的通用 portlids.py，沒有修改她的原工具。

## 設計與實物

- 0.1 m/格，一件子作品 sirius-tidegrave-01m-portlid（19×17×2，646 格）掛 30 次：lower 22、upper 8；兩舷各 15。
- 黑色外板 36、橡木內板 177、鉸鏈板 73。此為原創外觀設計，並非史料宣稱。
- 開著水平向外、P 舷 rotate 180−rz，不用 mirror=y；hinge-a/b、kind=portlid、lid_of（gun id）、house、close_deg 已寫。
- 18 處按 §9.12 的凸出物規則排除：lower 02；upper 02/03/05/06/07/09/10/12，兩舷相同。每處的 x 欄與外表面中位數在 ../portlids_placement.json。六門艏三聯砲沒有舷側封閉砲門，不裝蓋板。
- 潮墓號的曲面上，蓋板繞 z 之後角端可能切進表面；鉸鏈最多向外移 1 格，再驗開關與開口覆蓋。沒有改船殼或裝飾。

## 可重跑入口

`python -I -X utf8 ../tools/portlids.py draft|check|apply <cache>`；先 CLI export list / parts 到獨立 cache。
重驗先刷新 tidegrave.parts.json，避免用落地前的快取檢查落地後的鉸鏈。
工具只透過 senate cmd sculpture 寫實物，不直接改 models/work/anchors/events。

## 已量過

設計與實物逐格逐色缺/多/異色 0；固定點相同，30 模型擺法與 meta 相同；引擎 export parts 與 Python 變換的鉸鏈差最大 0.0005 格（輸出捨入）。
30 片開著碰船 0、碰砲 0；關上碰縮回的砲 0；開口全部覆蓋，關上落入整艘實心的取樣比例最多 0.62%。house 4–7 格（lower 05 兩舷按遊戲表面取樣提高為 7）。
反向對照：house=0 時 30 片全報碰砲；P 舷改 mirror=y 時 15 片全部往上關。

船體 1,033,347 格、checksum 55c4e759、502 繩、10 帆、17 關聯不變；模型 191→221。ropecheck 502 條都綁好（616 端直接、388 端綁繩）。
觀測圖 ../../overlays/portlids_20261019.png：已親看全船；蓋板開著，保留既有骨飾及船形。

## 射程與保留

取樣不是連續體碰撞證明。check 其餘模型使用實際格，50 個繞 x/y 或非原點關聯的模型退回外框。
收砲後的砲對船實心仍有 720 個取樣點（純畫面，原版規格同樣保留這種取捨），不因此挖船殼。
原有帆物理、梯子與走路捷徑不在本次修改內。
遊戲匯入報告、戰局對拍與提交見本目錄交付報告。

## 遊戲首輪交叉檢查

純格心＋角落取樣漏掉 lower 05 兩舷的網格表面擦碰：遊戲各報 11 點，最少需收 5.25 格。依報告提高 house 至 7，寫進產生器，沒有調寬遊戲檢查。
修改前成品 d939529 的 shipcheck 也有送藥手 24/25 的 warning；這是既有警告，本輪保留。來源 JSON 與最終報告會保存在交付報告旁。
兩組 30 秒戰局（tidegrave,constitution，seed 3/7）在加蓋板前後逐位元組相同：50671a68dff8、6623d29b22dc（SHA256 前綴）。

## 最終交付驗證

修正 house 與完成匯入時的繩端綁定後重建，來源指紋 6af185e25c0b3684／125 支檔。建置驗 17 艘、794 份網格還原一致，語法樹 429561 節點一致，srccheck 通過。
最終 shipcheck：錯誤 0、warning 1（送藥手24/25，baseline_shipcheck.json 證明修改前已存在）；砲門相關無錯誤或警告。ropebind 502 條，猜測0端、無依靠0端。
最終版本重新跑 seed 3/7，各30秒，與修改前逐位元組相同（battle_comparison.json）。asset_diff.json 解開網格索引後對比：191 個既有模型、502 繩、10 帆及船體格子全部相同，只多30片砲門。

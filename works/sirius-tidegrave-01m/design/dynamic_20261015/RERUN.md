# 可重跑的動態驗收

Python 3.10，NumPy 2.2.6、SciPy 1.15.3、Shapely 2.1.2；Node 20.11。Windows先設 `PYTHONUTF8=1`。全部輸入住本資料夾，無需讀live Blockside。

`independent_final` 的三份檢查核心由不同agent編寫。父agent最後執行並打包；`matrix_finite.cjs` 只比原 `matrix.cjs` 多逐步finite assertion；`actual_standing/check.py` 與 `actual_backstays/check.py` 只有選取最終實件輸入與回讀腳點的適配，距離／角域算法不改。原稿保留於scratchpad，舊結果與候選保留於original_results及candidate目錄。不要把父agent的候選選擇當作另一份獨立複驗。

設 `<E>` 為本資料夾絕對路徑，`<I>=<E>/independent_final`。

1. `python <I>/yard_verifier/verify.py`：全部10桁、106固定模型、45桁對桁與舊crossjack真負向。
2. `python <I>/yard_verifier/actual_standing/check.py`，再 `contact_extent.py`：從同夾VXK讀最終48線，完整角域與body含半徑。
3. 同樣執行 `<I>/yard_verifier/actual_backstays/check.py`／`contact_extent.py`：兩條實件後支索。
4. `node <I>/rope_verifier/trajectory.js`：原braceYards/yardRopes，產生1241幀；之後依序執行同目錄 `audit.py`、`body_radius.py`、`rope_pairs.py`、`dynamic.py`。最後一項約3–8分鐘，0.5秒抽樣，不能當連續通過證明。
5. 設 `CLOTH_SOURCE=<I>/cloth_verifier/frozen_source`、`CLOTH_OUT=<I>/cloth_verifier`，跑 `node <I>/cloth_verifier/matrix_finite.cjs <E>/final_dynamic.vxk`，再同指令加 `--only-extra`。完整場景包含原physStep、hangFalls/swingHangs、modelLocal、clothFine；矩陣每秒取幾何確證，換帆軌跡每0.1秒保存。
6. `python <I>/rope_verifier/rope_cloth.py`：讀第5步生成的phys_trajectory，全部繩對不透明fine布面交線。
7. `python ../verify_dynamic_delta.py`：作者獨立檢查CLI精確差異。此項需要同專案先前的continued_20261015快照，不屬碰撞核心。

大型JSONL與trajectory以`.gz`保存，位元組SHA記在 `MANIFEST.json` 與 gzip前的 `trajectory_hashes.json`。重跑相依腳本前可用 `unpack_trajectories.py` 原樣還原；第4/5步本身會重建它們。數學檢查的elapsed欄會變，故整份report重跑不要求byte相同；輸入、場景、碰撞點及角域判定才是比較項。

`matrix.json` 中counts是探針事件計數（有些body事件會進兩個桶）；正式分類與精確座標看hits的type，不能拿counts總和當不透明內片總數。attachment表示含pin的邊鄰域候選，仍保留原值，不是所有碰撞的通行證。保留自有砲／舵輪接觸，沒有泛用「離端5格」豁免。

凍結yard來源整船SHA屬上一版；最終模型／mesh與來源完全相同由delta_readback與geometry hashes證明，body新增56格已重測。`frozen_yards_match_snapshot=false`不應被偷改為true。

結果預期為 **FAIL**。請先重現 `engine_bug_evidence.md` 的不透明全自由三角實穿，再處理TASK-0603；不能把報告檔案存在當成測試通過。

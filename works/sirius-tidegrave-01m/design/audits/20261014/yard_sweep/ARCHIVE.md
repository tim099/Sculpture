# 桁與繩的模型感知掃掠證據

before快照5e92885e...、after快照a5994eee...均保留。MANIFEST.json列逐檔SHA；原26,844,588 bytes的sweep.json壓成sweep.json.gz，解壓後須符合raw_sweep.sha256。sweep_summary.json為可直接讀的縮要，rope_sweep.json是970個實際遊戲狀態的模型/繩接觸候選；不能把每個接觸都當真缺陷，也不能泛稱全部是附着。

本輪已實修crossjack/gaff：after.json有全連續Z分離、兩sheet及changed-model/rope/cloth對照。cloth_delta.json證明mizzen-topsail對桅(207,120,336)的嚴格內擦為舊有；本次交入面積由0.35520854降至0.01238903格平方，沒有變成0。

已知未結：main/fore course lift直接拉到桅head、穿上桁；部分shroud穿course桁；四ratline端的game yardNear誤綁。crossjack移位會影響原動態碰撞表中的一部分組合，不能不複驗就沿用before表宣稱after全數同值。其他同樣curve/model均未動的項才可沿用其幾何證據；分類與修復仍待。

重建cache用`python -I rebuild_inputs.py`（寫body.npy/input.json，不動資產），再以各檢查腳本重跑。大表可先用Python gzip解壓；重新精測sweep.py耗時較長。game_snapshot保留本次用的物理/綁定函式片段及來源provenance；不是正式遊戲source替換件。after.py讀本目錄的兩快照，不會偷偷驗後來另版preview。歷史讀數與實修後讀數的scope不可混用。

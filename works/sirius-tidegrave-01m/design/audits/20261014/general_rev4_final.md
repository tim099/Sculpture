# Rev04 最終總圖後驗

獨立唯讀驗證 pass。僅重跑總圖byte穩定與真實實物反向探針，沿用上一層已通過的骨架/殼RGB帳與早期事件結果帳，不重新宣稱其他新增旗竿/導索柱的幾何驗收。

Rev04複製plan與設計產圖器到自有gen1/gen2目錄，兩次產圖SHA與作品current PNG均相同：`0bda926677886c2a3e8601fcce9e664768805e2e376eb4ab1335b8c24a7aba9d`。plan SHA `32261a8f7f19ecbb93e29e8787478c3abe9136164655b38206ed2acf13629614`；generator SHA `e7b11691c9b9e7ad9efed9e9a308e99fc857467ec0559a586bd83aabdf76c8ea`。僅使用作者設計生成器確認再生穩定，未使用生成器自報verify結果或import作者checker。

主桅頂PNG像素(1031,248)換算Z=510.188679；按格中心規則floor(Z)+0.5取探針(355.5,120.5,510.5)。獨立重播主桅17430格事件，assembly main link仍identity。整份事件資產真實平移(0,0,−3)，圖紙與探針固定，nearest格中心距離0→3。原始未量化像素量法距離2.688679格照實保留，不冒充原像素精準報3。

完整來源hash、事件hash、link及probe值在final_rev4.json，可重跑程式在上一層final_rev4.py。

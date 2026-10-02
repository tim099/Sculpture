# Skyboxes（雕刻渲染的背景全景圖）

等距柱狀投影（equirectangular，2:1），由 `senate cmd sculpture` 的 GPU 渲染器取樣（TASK-0377）。
切換預設：`senate cmd sculpture --arg op=render-profile --arg sub=set --arg scope=shared --arg name=default --arg skybox=<本目錄檔名或絕對路徑>`（個人層把 `scope=persona` 加 persona）；單次覆蓋：view 帶 `--arg skybox=<路徑|builtin|none>`。

| 檔案 | 來源 | 授權 | 備註 |
|---|---|---|---|
| `belfast_sunset_puresky_2k.jpg` | Poly Haven「Belfast Sunset (Pure Sky)」tonemapped JPG（8192×4096，md5 `5313193c1b09d9776dd3395d08b6beee`）縮成 2048×1024 | CC0 | 暮色雲層＋水面，無地面景物 |
| `kloppenheim_06_2k.jpg` | Poly Haven「Kloppenheim 06」tonemapped JPG（8192×4096，md5 `e0bae2fe816032852f4c180d4a46ab99`）縮成 2048×1024 | CC0 | 晴空＋岩地前景 |
| `rogland_clear_night_4k.jpg` | Poly Haven「Rogland Clear Night」tonemapped JPG（8192×4096，md5 `5565a41460b4f851fcea727d5dcfc009`）縮成 4096×2048（銀河細節要解析度） | CC0 | **預設**：星空＋銀河拱、暗色岩地（Tim 2026-10-02 指定）；正交預設視角用 `yaw -142`／`tilt 38` 讓銀河拱在作品後方 |

來源頁：https://polyhaven.com/a/belfast_sunset_puresky ・ https://polyhaven.com/a/kloppenheim_06 ・ https://polyhaven.com/a/rogland_clear_night （2026-10-02 由 calli 下載，Tim 同意下載）。

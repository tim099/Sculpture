# Floors（雕刻渲染的地板貼圖）

可重複鋪（tileable）的地板漫反射貼圖（PNG／JPG），由 `senate cmd sculpture` 的 GPU 渲染器取樣（TASK-0377）：
Repeat 雙軸、mipmap、各向異性；每 `floor_tile` 格重複一次（預設 16 格）。
不放貼圖（`floor_texture=builtin`）＝ 渲染器程式畫的量尺網格（每 1／16／64 格一條線，對齊 voxel 邊界）。

單次：view 帶 `--arg floor=on --arg floor_texture=<本目錄檔名|builtin|絕對路徑>`；
長期：`senate cmd sculpture --arg op=render-profile --arg sub=set --arg name=<名> --arg floor=on --arg floor_texture=<檔名>`（個人層加 `scope=persona` 與 persona）。

| 檔案 | 來源 | 授權 | 解析度 | 備註 |
|---|---|---|---|---|
| `stone_tiles_02_diff_2k.jpg` | Poly Haven「Stone Tiles 02」（id `stone_tiles_02`，作者 Charlotte Baglioni）Diffuse 2k JPG，原檔直接用（md5 `2e724b32ab8dd4db86f829cda244e567`，與 API 公布的 md5 相符） | CC0 | 2048×2048（實體 2 m×2 m） | 灰色板岩碎拼地磚；亮度均值 121／255、標準差 12.5 —— 低對比，不搶 voxel 的顏色 |
| `dark_wooden_planks_diff_2k.jpg` | Poly Haven「Dark Wooden Planks」（id `dark_wooden_planks`，作者 Amal Kumar）Diffuse 2k JPG，原檔直接用（md5 `e6ae2fe585184c16343c56b833eddbf8`，與 API 公布的 md5 相符） | CC0 | 2048×2048（實體 2 m×2 m） | 暗色舊木板（灰褐、低飽和）；亮度均值 75／255、標準差 9.2 —— 比暖色木地板安靜 |

授權：Poly Haven 全站資產皆為 CC0（https://polyhaven.com/license；`api.polyhaven.com/info/<id>` 沒有 license 欄位，以全站聲明為準）。
來源頁：https://polyhaven.com/a/stone_tiles_02 ・ https://polyhaven.com/a/dark_wooden_planks
（2026-10-02 由 calli 經 `api.polyhaven.com/files/<id>` → Diffuse → 2k → jpg 下載，Tim 同意下載。）

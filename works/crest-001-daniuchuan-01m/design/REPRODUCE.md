# 明鄭一號大鳥船（crest-001-daniuchuan-01m-assembly）確定性重現與驗收流程

> 任務單：`TASK-1316`（《Blocksail》1666 明鄭水師主力戰座大鳥船，500–650 噸級、0.1 m／格、393,907 格、`components=1`、`cavities=0`、`link_overlap=0`）

## 0. 環境需求
- Python 3.10+（Windows 需 `python -I -X utf8`），含 `numpy`、`scipy`、`Pillow`
- `senate` CLI（本機資料根 `D:/Unity/Valhalla`）
- 目標組裝件：`crest-001-daniuchuan-01m-assembly`（主船殼 `crest-001-daniuchuan-01m`）

## 1. 圖紙推算與確定性驗證（Steps 1–12，重跑逐位元組一致）

於 `D:\Unity\Valhalla\Sculpture\works\crest-001-daniuchuan-01m\design` 依序執行（所有 `draft_*.py` 均通過 2-pass SHA-256 一致與 `--probe` 反事實碰撞探針）：

1. **步驟 1–4（線型、隔艙空間、砲門／窗洞／塗裝、船殼落格）**
   ```powershell
   python -I -X utf8 draft_lines.py
   python -I -X utf8 draft_layout.py
   python -I -X utf8 draft_ports.py
   python -I -X utf8 tools/step4_apply.py
   python -I -X utf8 tools/check_hull.py .
   ```
2. **步驟 5（四層甲板、5 座梯子 20 錨點、艙房 `rooms` 與行走可達檢查）**
   ```powershell
   python -I -X utf8 draft_decks.py .
   python -I -X utf8 tools/build_decks.py
   python -I -X utf8 tools/walkback.py .
   ```
3. **步驟 6（艉樓窗玻璃、艉迴廊、龍首／鳳尾飾與 6 條通用護舷）**
   ```powershell
   python -I -X utf8 draft_deco.py .
   python -I -X utf8 tools/build_deco.py
   ```
4. **步驟 7–8（三桅六桁、22 根竹帆肋 `render=pole`、196 條繩索、`flag/sail` hard-batten 硬骨帆與旗桿）**
   ```powershell
   python -I -X utf8 draft_masts.py .
   python -I -X utf8 tools/build_masts.py
   python -I -X utf8 tools/rigging_apply.py
   ```
5. **步驟 9（新汎用砲種 `hongyi`/`fagong`、30 門火砲＋6 門座、72 環固定點與 120 條砲索）**
   ```powershell
   python -I -X utf8 tools/build_gun_types.py
   python -I -X utf8 draft_guns.py .
   python -I -X utf8 tools/build_guns.py
   python -I -X utf8 draft_gunfittings.py .
   python -I -X utf8 tools/build_gunfittings.py
   ```
6. **步驟 10（水線下銅皮火藥庫＋16 桶、貨艙口蓋與 8 件甲板裝備）**
   ```powershell
   python -I -X utf8 draft_gear.py .
   python -I -X utf8 tools/build_gear.py
   ```
7. **步驟 11（中式開孔升降舵、尾樓舵孔切槽、獨立舵柄 `tiller`、雙舷貓頭與 2× 四爪鐵錨＋錨索）**
   ```powershell
   python -I -X utf8 draft_rudder_anchor.py
   python -I -X utf8 tools/build_rudder_anchor.py
   ```
8. **步驟 12（封閉下層 12 門紅夷砲門蓋板；需先由 Blockside 執行 `admin.py ids --id daniuchuan` 配發 `gun-*` 編號）**
   ```powershell
   python -I -X utf8 tools/portlids.py draft <temp_cache_dir>
   python -I -X utf8 tools/portlids.py check <temp_cache_dir>
   python -I -X utf8 tools/portlids.py apply <temp_cache_dir>
   ```

## 2. Sculpture 全船結構／繩端／匯出檢查
```powershell
senate cmd sculpture --arg op=stats --arg work=crest-001-daniuchuan-01m-assembly --arg structure=1
senate cmd sculpture --arg op=work --arg sub=ropecheck --arg persona=crest-001 --arg work=crest-001-daniuchuan-01m-assembly
senate cmd sculpture --arg op=export --arg format=vxk --arg include=rig,models,parts,meta --arg work=crest-001-daniuchuan-01m-assembly --arg out=D:/Unity/Valhalla/Sculpture/exports/crest-001-daniuchuan-01m-assembly.vxk
```

## 3. Blockside 匯入與驗證（`external/Blockside`）
```powershell
python -I -X utf8 src/admin.py reimport --id daniuchuan
python -I -X utf8 src/admin.py ids --id daniuchuan
python -I -X utf8 src/admin.py ropebind --id daniuchuan
python -I -X utf8 src/admin.py ancbake --id daniuchuan
python -I -X utf8 src/admin.py showlod --id daniuchuan
python -I -X utf8 src/admin.py build
python -I -X utf8 src/admin.py shipcheck --id daniuchuan
python -I -X utf8 src/admin.py ladcheck --id daniuchuan
python -I -X utf8 src/admin.py disp --id daniuchuan
python -I -X utf8 src/admin.py srccheck
python -I -X utf8 src/admin.py verify
```

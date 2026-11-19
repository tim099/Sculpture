# 東寧洋船的重建與匯入

本船各數字的依據及設計限制見 sources.md，線型來源為 plan.json。原圖沒有本船工程線圖，這組圖紙是依史料風格和任務級距重新設計。

## 可重產的設計資料

在本目錄執行，使用 Python、NumPy、SciPy、Pillow：

```powershell
python -I draft_hull.py --out <新的輸出目錄>
python -I draft_layout.py
python -I draft_decks.py
python -I draft_deco.py
python -I draft_guns.py
python -I draft_battens.py
python -I curved_sails.py
python -I fittings_voxels.py
```

第一支可指定新輸出目錄，方便以 hash 比對 hull.vox.txt 與圖紙。其餘draft程式會更新本設計目錄的圖紙、遮罩或擺放清單，不帶--apply不改雕刻。rig.py 和 gear.py 會透過 Sculpture CLI 寫入作品，勿當成唯讀檢查執行。最新硬骨帆必須最後執行draft_battens.py --apply，覆蓋早期rig.py的斜桁與軟帆設定；不得把只重跑早期rig.py的結果當成最後交船版。裝飾修整須在gear.py之後執行fittings_voxels.py --apply：兩舷艏飾改成358格實體關聯（含66格木底），吊錨架10格換色，移除舊bow-P/S模型，艉牌向艉移15cm。

## 雕刻正本

現版弧形硬帆在 `draft_battens.py --apply` 之後執行 `curved_sails.py --apply`。此步依沙船 TASK-1321 的外緣弧線和傾斜上桁配方更新三面帆，沿用原有竹篾模型與物件 ID。若從舊的桅桁設定重跑，必須再執行此步才能重現弧形帆。配方尺寸和竹篾擺位見 `curved_sails_placement.json`。

作品 events、links、models、ropes、sails、anchors 和 meta 是 CLI 正本；沒有手改 work.json 或另做遊戲專用幾何。完整成品是 meadow-tungning-trader-01m-assembly，船體與子件都為 0.1 m／格。CLI 重匯可重建模型與帆貼圖；資料庫首次建立的委託 ref 為 TASK-1315，勿重新建立委託領取薪資。

本船專用新元件是開孔舵、舵柄、隔艙門及艙口蓋，因既有西式舵與門不合這組幾何而另製。開孔舵保留 voxel，避免 pole／lathe 把分岔和孔洞抹平；錨、小艇與其他共用元件繼承來源的渲染設定。

## 遊戲匯入

在自己的 Blockside worktree 執行：

```powershell
python -I <本設計目錄>/fittings_voxels.py --apply
python -I src/admin.py reimport --id tungning_trader --no-build
python -I src/admin.py ids --id tungning_trader --no-build
python -I <本設計目錄>/configure_game.py <Blockside worktree>
python -I <本設計目錄>/draft_battens.py --apply --game <Blockside worktree>
python -I <本設計目錄>/curved_sails.py --apply
python -I src/admin.py reimport --id tungning_trader --no-build
python -I src/admin.py ids --id tungning_trader --no-build
python -I src/admin.py build
python -I src/admin.py ropebind --id tungning_trader
python -I src/admin.py ancbake --id tungning_trader
python -I src/admin.py showlod --id tungning_trader
python -I src/admin.py shipcheck --id tungning_trader
python -I src/rooms.py check --id tungning_trader
python -I src/admin.py disp --id tungning_trader
```

現有船已完成 import，不要再新增另一個同代號。第一次加入新資料庫時，用 admin.py import 指向上述 assembly 並指定 id=tungning_trader。船員與船卡、預烘或圖集變更後，交付前再建置並執行 srccheck；裝飾修整後正式入口的 checksum 須為 2221512735、176209格（原交船版為2262896839、175851格）。

重新執行雕刻擺放工具時，保留既有 id，再跑 ids 正規化指名鍵（如 gunmount.mount_of、tiller.rudder）。只調 ratlines.foot 不改繩端依附或幾何，仍須重匯使遊戲拿到新登梯點。

原交船版獨立覆核見 verify_final_independent.md／json；本次艏飾與艉牌修整覆核見fittings_final.md／json。較早的verify_*檔保留開工階段讀數，判斷最新成品以fittings報告及遊戲驗收為準。

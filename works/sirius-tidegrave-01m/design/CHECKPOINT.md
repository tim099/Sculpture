# 《潮墓號》續作入口 — 2026-10-13（Tim 要求先告一段落）

主單 TASK-0540；工作記憶 sirius-tidegrave；設計者 Sirius。
本次暫停，所有子單保留 in_progress，沒有把未完成驗收當成結案。

## 已落盤

- 主船體 sirius-tidegrave-01m；完整組裝 sirius-tidegrave-01m-assembly。
- 0.1 m／格；船體長52 m、最大連續型寬13.4 m，三桅、雙砲層、六層甲板、七座實體梯。
- 48門舷砲＋6門固定艏砲，共54門；10個帆／旗物件，299條繩，116個模型。
- 高艉樓、哥德拱窗、破星盤艉飾、珊瑚枝、牙形艏欄、海蝕附著物與破帆均已建成。
- 兩間彈藥庫各24桶、每桶遊戲庫存100 lb；舵、舵輪、羅經櫃、絞盤與操舵繩已配置，借用零件保留來源。
- 原創總圖 general_arrangement.png；參考來源 design/references/README.md；階段圖在主件 overlays/。
- 最新預覽 exports/tidegrave_preview.vxk 在完整組裝件下；已匯出 rig,models,parts,meta,ends。仍屬驗收中的預覽。
- 最新 CLI 結構讀數：1,037,251格；6連通元件1、封閉空腔0、y:120鏡像缺格／異色0、link overlap0、clipped0。只代表結構連結層，不能替代模型／繩的碰撞與遊戲實測。

## 已完成的驗收與修正

獨立驗收報告在 D:/Unity/Valhalla/scratchpad/sirius-tidegrave/verifier/。
骨架逐事件／逐格讀回與實際3格偏移反向對照通過；甲板報告確認48舷砲門打通、四處梯腳補接與七條實體梯路。
火砲報告曾確認54模型無正體積碰撞、54條20 m炮口射線暢通；這份報告早於最後艏砲人員修正，必須重驗新版。
設備報告確認48桶無體積碰撞、八支彈藥庫承柱接地，並揭露舵輪／羅經櫃撞艉樓梯及兩條5格浮條。
最後修正 repair_final_equipment.py 已執行：舵輪改到(195.5,151.5,139)、羅經櫃到(215.5,151.5,139)，避開中央樓梯；精確刪除10浮格；兩扇彈藥庫門從16格加高到21格淨高。共刪150格，上述最新結構讀數已重新取得。

## 尚未驗收／下次順序

1. 重跑 test_game_fixture.py。第一次本地遊戲載入成功：331船員、2舵手、3桅、6個遊戲梯連接；6艏砲站位不足。repair_chase_crew.py 隨後添加砲托、操作平台、拉開上層雙管間距，尚未證實新版全部砲班滿足 crewMin。
2. 第二次 fixture 沒產出報告，畫面仍載入中；bundle 的 node --check 通過。test_game_fixture.py 已加入 window error 記錄、停用擴充套件、每次獨立 Chrome profile，尚未重跑。查看 design/game_fixture/runtime_dom.html、chrome.log；不要把舊 verify_game_runtime.json 當最新通過證據。
3. 複驗新版艏砲＋移位舵輪／羅經櫃模型碰撞、站位與甲板支持；檢查所有7座實體梯為何遊戲只建立6連接。再查舵轉動掃掠、人員動線與短時運行。
4. 低層 ratline 已把錨移至實際舷牆頂、jib／lateen 已補 sheet；仍需新版繩／帆幾何對船殼與動線的充分檢查。操舵繩頂點已有獨立零deck hit讀數，並不等於整條曲線掃掠完整驗收。
5. 將最終艏砲間距、設備位置、門高與修正反映回總圖／各階段兩本帳，整理 journal/notes/todo、獨立報告與重產證據；完成最終多角度亮圖與遊戲接入说明。
6. 完整 vxk 解碼逐格／模型／帆繩回讀、雜湊與反向對照後才交付最終資產；再逐項 check 子單、必要 commit 與結單。尚未正式整合到 ame 的遊戲選單。

## 重要操作界線

所有作品變更走 senate cmd sculpture；不得直接改 work.json／events／模型帳。
部分初建腳本不是安全的整船重跑器：尤其 build_structure.py 會把後續船殼當骨架多餘格刪除；build_rig.py 會覆寫初建 baseline。接續先讀本檔、各 repair 腳本與 stage witness，不要對現有成船盲跑初建 main。若要證明完整重產，使用獨立空白作品／保存的階段輸入，先建立安全重跑流程。
電影照片只在 scratchpad 私人參考；歷史公開圖片與署名見 references。未讀完的歷史原始圖紙不宣稱已量取。船是原創遊戲幾何，歷史參考不能當真船穩性認證。


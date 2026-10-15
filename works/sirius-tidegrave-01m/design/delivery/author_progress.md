# 2026-10-16 潮墓號：兩項匯入警告已清除

隔離最新遊戲正式 shipcheck：0 errors / 0 warnings，陸戰隊12/12、353船員、54砲全滿編、
送藥取用點到砲尾54/54連通。build與verify通過。正式Blockside仍由ame接入。

對稱艏砲側通道X574..581、Y94..103及137..146、淨空Z117..134；補地板Z115..116。
經sculpture CLI移除1152格、補176格，成船1033347格/checksum55c4e759。
CLI/VXK逐格逐色差0、水線以下不變，原502繩/10帆/168模型/25mesh及固定帆點逐值不變。
交付delivery/tidegrave_import_20261016.vxk，
SHA256 850566c50d4b7b022f3124ec88e36a6154b672ad7201ef44ce9602da1a43322b。

配套game_integration/23_powder.patch修艏艉砲送藥手出生與交藥點至砲尾後方；
suggested_ship.json設marines=12、marineGap=30並保留geo。補丁只套隔離版。
Tim明確說穿過前桅、跨過艙口不用處理，部分細節故意節省效能；保留原monkeyTo，
不提交額外逐格導航或人體碰撞限制。此處連通驗收依現行遊戲標準，未擴大成逐步碰撞驗收。

TASK-0603/0546帆碰撞仍依Tim先前選擇手動驗收；本次不代簽完整動態PASS。
最新交付取代20261015版本；歷史初建腳本不可在成船盲跑。

# TASK-0745 潮墓號船尾旗飛邊固定在空中

Tim截圖圈出的兩點是ensign的角1與角2。原設定四角pin=true、bind=[3]；角0/3在旗桿，角1/2在飛邊，後者被clothBindMeta固定在原位置（hk=3），只有中間的布能鼓起，飛邊飄不動。

修正由CLI work sub=sail overwrite=1、free=1,2落地。pin=[true,false,false,true]，bind仍[3]；沿旗桿的一整邊與兩端保持固定，飛邊兩角交給物理。座標、解析度10、fullness1.02、顏色與原骷髏貼圖全部保留。sails.json逐欄比對只有兩個pin與備註改變。

asset_diff.json直接解開前後VXK：船體格子、221模型/網格、502繩與其他9帆全相同，ensign的貼圖亦完全相同。前輪三角帆bind=[0]保留。

## 動態驗證

probe.py在測量用成品附加腳本，以現有__game API跑同一個Chrome客戶端、seed3、cache=0，0.1/5.1/10.1/15.1/20.1秒讀四角、pin/hk與旗桿側11點。
修前：飛邊兩角全為pin=1/hk=3，20秒各0位移；旗桿側誤差0。
修後結果與匯入報告附於同目錄；測量用HTML不入版控。
這是20秒、單一種子的動態取樣，不代稱所有天氣與破旗狀態全驗。

## 最終結果

同一客戶端20秒五次取樣：原飛邊兩角皆pin=1/hk=3且位置一值不變；修後兩角始終pin=0/hk=0且均有位移。旗桿側11點相對初始位置誤差始終0，全部布點座標有限（before_browser.json、after_browser.json）。
after_flag.png為實際遊戲20.1秒畫面，已親看，尾部可垂落與翻動，未以空中固定點撐形狀。
建置還原/AST一致，srccheck76bd69c6f3a43435（125檔）；匯入錯誤0、既有送藥手24/25警告1。

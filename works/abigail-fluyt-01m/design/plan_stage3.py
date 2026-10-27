# 澤漢號（福祿特 fluyt）plan.json 前半段（步驟 3：線形、甲板、砲門、桅）—— 一次性產生；之後的段落各步驟自己改。
#   用法：python -I -X utf8 plan_stage3.py <design 資料夾>
#   出處：拉貝爾號 plan.json 的鍵（ame-labelle-01m/design）；數字全換成本船，src 寫出處或設計決定。
#   ⚠ 只換這裡列出的段落，後面的段落（decks_build 起）原封不動。
import sys, os, json

F = 2.831     # 1 Amsterdam voet ＝ 0.2831 m ＝ 2.831 格（11 duim；Witsen p.100 合約「elf duim voor de voet」；公制值二手：nl.wikipedia）
D = F / 11    # 1 duim ＝ 0.2574 格

W = 'Witsen 1671'


def v(x, src):
    return {'v': x, 'src': src}


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    new = {}
    new['title'] = '澤漢號（Zeehaen 型福祿特 fluyt，東航 Oostervaarder 110 呎）新圖紙 01：線形、側面、甲板高度、砲位表、桅帆表'
    new['task'] = 'TASK-0966（傘 TASK-0964）'
    new['author'] = 'Abigail'
    new['date'] = '2026-10-28'
    new['sources'] = {
        'W': 'Witsen, Aeloude en Hedendaegsche Scheeps-bouw en Bestier（Amsterdam 1671）—— archive.org gri_33125008247716（掃描頁影像研究代理看過）：p.159 gemeene Fluit 130 呎、p.160 Oostervaerders 長寬深載量規則、p.130 實測 110–112 呎 Oostervaarder 的桅桁表、p.128 桁長規則；1690 版 DBNL wits008arch01_01_0019',
        'VY': 'Cornelis van Yk, De Nederlandsche Scheeps-bouw-konst open gestelt（1697）p.140–142：1668 年 fluit 的比例（龍骨、艏艉柱傾出、內傾、verwulf、砲門）—— 研究代理對過影像（p.141 樑距是 OCR）',
        'research': 'references/research_fluyt_2026-10-28.md（全部讀數、原文引句、查不到的清單）',
        'voet': 'Amsterdam voet ＝ 11 duim ＝ 0.2831 m ＝ 2.831 格；duim ＝ 2.574 cm',
        'name': '船名借 Zeehaen（1639，Tasman 的福祿特，約 100 last）；尺寸照 Witsen 的 110 呎東航福祿特規則，⚠ 不是 Zeehaen 本身的尺寸'}
    new['class'] = v('荷蘭福祿特 fluyt（英稱 flyboat），單層甲板的東航船（Oostervaarder），約 130 last ≈ 260 噸',
                     'W p.160：100 呎 ⇒ 100 last、115 呎 ⇒ 150 last、125 呎 ⇒ 200 last，「Deze zijn maer van een holte, deck ofte dack」；110 呎內插 ≈ 130 last〔估〕；1 last ≈ 2 噸〔二手〕')
    new['meters_per_cell'] = 0.1
    new['space'] = {'x': 480, 'y': 192, 'z': 384, 'yc': 96, 'note': '中線 ＝ 第 96 格（鏡像 y ↔ 192 − y）；x 留給艏斜桅、z 留給主上桅頂'}
    L = {}
    L['half_beam'] = v(33.5, 'W p.160 內插：寬 23 呎（殼板內，binnen de huit）＝ 65.1 格 ＋ 兩舷外板各 0.75 格 ≈ 66.6 ⇒ 全寬 67 格（|dy| ≤ 33）〔估：在 100 呎 22 呎、115 呎 23½ 呎之間〕')
    L['keel_top'] = v(3, '設計決定：龍骨 0.3 m')
    L['keel_half'] = v(1, '設計決定：龍骨寬 3 格')
    L['plan_half'] = v(20, '設計決定：福祿特的平底寬（Baltic 型、淺吃水）⇒ 平底半寬 2 m ≈ 0.6 × 半寬')
    L['astilla'] = v(1.5, '設計決定：船底橫向上升 0.15 m（W 的 pinas 是 6 duim ＝ 1.5 格，福祿特沒寫）')
    L['max_breadth_z'] = v(28, '設計決定：最寬處在水線附近（福祿特往上強烈內收）')
    L['tumblehome'] = v(6, 'VY p.141：內傾 33 duim（照比例縮到本船約 2 呎 ＝ 5.7 格）〔估〕⇒ 量到船腰舷牆頂每舷收 6 格（上舷寬 ≈ 0.82 B）')
    L['tumblehome_ref_z'] = v(50, '＝ 船腰舷牆頂（lines.top 最低處）')
    L['tumblehome_pow'] = v(1.2, '設計決定：從最寬處一路往上收（福祿特的梨形剖面）')
    L['tumblehome_above_per_cell'] = v(0.2, '設計決定：艉樓、船首樓的舷牆再往內收（梨形船尾的上段）')
    L['bilge_pow'] = v(2.6, '設計決定：硬舭（平底接近直的舷側）')
    L['s_aft'] = v(0.36, '設計決定：船尾收縮佔船長 36%（圓艉、水線下的 run 細）')
    L['s_fwd'] = v(0.72, '設計決定：船頭收縮從 72% 起（福祿特的船頭飽滿）')
    L['sternpost_x0'] = v(60, '設計決定：艉柱腳（後緣）的 x')
    L['sternpost_rake_deg'] = v(9.0, 'VY p.140：艉柱傾出 2 呎 ＝ 5.7 格（1668 年 fluit 比例套到本船）〔估〕；量在主甲板高 z 36 ⇒ atan(5.7／36)')
    L['sternpost_top_z'] = v(59, '〔估〕艉柱高約 21 呎')
    L['wing_transom_z'] = v(46, '設計決定：圓艉（ronde hek）的 wulf 在主甲板船尾那一段的上面；以上是窄的平 hek')
    L['transom_ratio'] = v(0.55, 'VY p.142：verwulf 頂板寬 17 呎 6 duim（照比例 ≈ 0.51 B）〔估〕⇒ 33 格 ⇒ 半寬 16.5 ÷ wing transom 那個高度的船中半寬 28.8（已內收）≈ 0.573，取 0.55 讓格子量到 33（寬只能奇數）')
    L['forefoot_x'] = v(317.6, 'VY p.140 比例：龍骨 ≈ 0.83 × 長〔估〕⇒ 91 呎 ＝ 257.6 格 ⇒ 60 ＋ 257.6（91 ＋ 17 ＋ 2 ＝ 110）')
    L['stem_rake'] = v(48.1, 'VY p.140：艏柱傾出 22 呎（1668 年大型 fluit）照比例 ⇒ 17 呎 ＝ 48.1 格〔估〕，量在主甲板高')
    L['stem_ref_z'] = v(36, '＝ 主甲板最低處（量長度的高度）')
    L['stem_pow'] = v(0.55, '設計決定（照拉貝爾號）：艏柱曲線底下跟龍骨相切、往上越來越直')
    L['stem_top_z'] = v(60, '〔估〕艏柱高約 20 呎 ＋ 船首樓')
    L['deadwood_aft_z'] = v(16, '設計決定：船尾 deadwood 抬到 1.6 m（圓艉下面的 run）')
    L['deadwood_fwd_z'] = v(6, '設計決定：船頭 deadwood 0.6 m')
    L['bow_pow_low'] = v(1.8, '設計決定')
    L['bow_pow_high'] = v(2.6, '設計決定：上面很鈍（福祿特的圓船頭）')
    L['aft_pow'] = v(2.1, '設計決定：圓艉（ronde hek）水線以上飽滿（v1 1.6 的水線半寬像楔子）')
    L['top'] = [[40, 68], [121, 68], [124, 54], [190, 51], [255, 50], [320, 53], [342, 56], [345, 68], [400, 69]]
    L['top_src'] = '舷頂（舷牆頂）折線：後甲板 58 ＋ 欄 10（到 x 121）、船腰主甲板 ＋ 14 格舷牆（砲門檻 6 ＋ 砲門高 6 ＋ 上面 2；VY p.142）、船首樓 59 ＋ 9（從 x 345）；break 的位置是設計決定'
    new['lines'] = L
    new['waterline'] = {'z': 30, 'src': '〔估〕滿載吃水 3.0 m（約 10½ 呎；艙深 11½ 呎的單層甲板船，波羅的海航線淺吃水）⇒ 船中乾舷到甲板 0.6 m'}
    new['readings_at'] = {'deck_z': 36, 'rail_z': 50, 'length_z': 36, 'wing_transom_z': 46}
    new['devis'] = {'keel_cells': 257.6, 'length_cells': round(110 * F, 1), 'beam_cells': round(23 * F + 1.5, 1), 'stem_rake_cells': 48.1,
                    'stern_rake_cells': 5.7, 'stem_height_cells': 56.6, 'sternpost_height_cells': 59.4, 'depth_hold_cells': round(11.5 * F, 1),
                    'wing_transom_width_cells': 33,
                    'src': 'W p.160 內插（長 110、寬 23、深 11½ 呎）〔估〕；龍骨與艏艉柱傾出套 VY p.140 比例〔估〕；verwulf 寬套 VY p.142〔估〕'}
    new['decks'] = {
        'src': 'W p.160：單層甲板（een holte, deck ofte dack）；船尾有後甲板（halfdek）、船頭有短的船首樓；艙深 11½ 呎（內插）',
        'rows': [
            {'key': 'hold', 'name': '貨艙地板（ruim）', 'z': 7, 'x_from': 100, 'x_to': 330, 'src': '設計決定：貨艙底鋪一層板給彈藥庫與站人；頭頂到主甲板 29 格'},
            {'key': 'main', 'name': '主甲板（overloop）', 'z': 36, 'src': 'W p.160 內插：艙深 11½ 呎 ＝ 32.6 格（從龍骨頂 z 3 量）⇒ 甲板面 z 36（最低處）'},
            {'key': 'quarter', 'name': '後甲板（halfdek）', 'z': 58, 'x_to': 121, 'src': '〔估〕艉樓高 5½–6½ 呎（W p.159 verdeck 5 呎 6 duim、VY）⇒ 主甲板在 x 80（z 42）＋ 16；長約 20 呎 ⇒ 到 x 121（設計決定）'},
            {'key': 'forecastle', 'name': '船首樓（bak）', 'z': 59, 'x_from': 345, 'src': 'W p.160（Noortsvaerder）：船首樓甲板 8–10 呎長〔查〕；高 5½ 呎（W 的 pinas bak）⇒ 主甲板在 x 345（z 42）＋ 17'}],
        'sheer': {'aft': 6, 'fwd': 8, 'x_mid': 255, 'x_aft': 80, 'x_fwd': 360,
                  'src': '設計決定：主甲板舷弧 船尾 0.6 m、船頭 0.8 m；最低處（hals）在離船頭約 ⅓ 船長（W 的 pinas p.~76：hals 在離船艏 1/3 處）'}}
    new['decks_preview'] = {'hold': 7, 'main': 36, 'quarter': 58, 'forecastle': 59}
    new['ports'] = {
        'src': 'VY p.142（1668 年大型 fluit）：砲門 高 23 × 寬 27 duim（5.9 × 6.9 格）、門檻離水道 23 duim（5.9 格）；W p.160：商船艏艉另開圓洞當假砲門（looze poorten，步驟 6 畫）',
        'tiers': [{'deck': 'main', 'per_side': 4, 'xc': [148.5, 178.5, 243.5, 278.5], 'w': 7, 'h': 6, 'sill': 4, 'gun': '4l',
                   'src': '每舷 4 門〔估：W p.160 說往西的船人多、帶砲；研究代理估每舷 4–6〕；位置設計決定：後甲板 break（x 124）之後、船首樓（x 345）之前，避開主桅 channels（x 211 前後）；間距 30–35 格（W 的 pinas 8½–11 呎）；口徑查不到 ⇒ 4 磅（跟拉貝爾號同一門砲）；門檻 4（步驟 9：VY 的 23 duim 是大型 fluit 的砲架，這門 4 磅砲的砲軸只在甲板上 5 格 ⇒ v1 門檻 6 的 6 門砲管頂在門檻上推不出去；拉貝爾號同一門砲門檻 4）'}]}
    new['masts'] = {
        'src': 'W p.130：實測 110–112 呎 Oostervaarder 的桅桁表〔查〕；桅位套 VY p.141–142 的比例〔估〕；上桅帆桁、前帆桁套 W p.128 的規則〔估〕；沒有頂桅（表裡沒有）',
        'rows': [
            {'key': 'fore', 'x_step': 344, 'rake_deg': -1, 'lower_m': 17.0, 'top_m': 10.6, 'yards': {'course': 11.9, 'topsail': 6.8},
             'src': 'W p.130：前桅 68–69 呎 ＝ 19.4 m（從龍骨量；桅腳在艏柱的 deadwood 上、比主桅腳高 ≈ 2.4 m ⇒ 腳以上 17.0）、前中桅 37–38 呎 ＝ 10.6 m；前桁 42 呎、前中桅桁 24 呎（套 p.128）；x：VY 艏柱後 0.064 L 是在甲板高量的 ⇒ 往船尾挪到 x 344 讓桅腳落在船裡（設計決定）'},
            {'key': 'main', 'x_step': 211, 'rake_deg': 2, 'lower_m': 21.9, 'top_m': 13.2, 'yards': {'course': 14.4, 'topsail': 8.1},
             'src': 'W p.130：主桅 77–78 呎 ＝ 21.9 m、主中桅 46–47 呎 ＝ 13.2 m、主桁 51 呎（17 kleed）＝ 14.4 m；主中桅桁 28½ 呎（套 p.128）；x：VY 主桅前緣在 0.5 L ⇒ x 211'},
            {'key': 'mizzen', 'x_step': 110, 'rake_deg': 3, 'lower_m': 13.5, 'yards': {'lateen': 11.0},
             'src': 'W p.130：後桅 56 呎 ＝ 15.9 m（從艙底量；腳以上〔估〕13.5）；x：VY 艉柱前 0.19 L ⇒ x 112 ⇒ 110（後甲板 break 之前）；lateen 帆桁查不到 ⇒ 主桁的 0.76（設計決定）'},
            {'key': 'bowsprit', 'x_step': 352, 'deck': 'forecastle', 'angle_deg': 32, 'len_m': 13.2, 'yards': {'spritsail': 8.2},
             'src': 'W p.130：艏斜桅 46–47 呎 ＝ 13.2 m；仰角、腳的位置、spritsail 帆桁（主桁 0.57，照拉貝爾號的比例）設計決定'}],
        'check': '主上桅頂離龍骨底 ≈ 7 ＋ 0.92 × 219 ＋ 132 ≈ 340 格（34 m）'}
    new['hull_build'] = {'wall': 3, 'frame_color': 141, 'inner_color': 177, 'side_color': 177, 'bottom_color': 182, 'bottom_top_z': 30,
                         'src': '設計決定：牆 3 格（外板 1、肋骨 1、內板 1）；水線下灰白（荷蘭船的白色船底塗料）、水線上原木色（塗裝帶在步驟 4）'}
    out = {}
    for k in plan:
        out[k] = new.get(k, plan[k])
    for k in new:
        if k not in out:
            out[k] = new[k]
    s = json.dumps(out, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

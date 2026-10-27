# 澤漢號 plan.json 的 rig_build（步驟 7：桅、桅樓、艏斜桅、帆桁）—— 一次性產生；只換這一段。
#   用法：python -I -X utf8 plan_stage7.py <design 資料夾>
import sys, os, json

CY = 'basecamp-frigate-constitution-01m-yard-'


def main():
    design = sys.argv[1]
    p = os.path.join(design, 'plan.json')
    plan = json.load(open(p, encoding='utf-8'))
    plan['rig_build'] = {
        'src': '設計決定（桅帆比例與位置在 plan.masts）；Ship_Masts §5：每根桅一件子作品、帆桁一開始就是外部模型、模型放在它的桅子作品裡',
        'colors': {'mast': 141, 'top': 136, 'rim_band': 45, 'rim_cap': 248, 'truck': 248},
        'mast_r': {'fore': [2.2, 1.6], 'main': [2.5, 1.8], 'mizzen': [1.6, 1.2]},
        'mast_r_src': 'W p.130：主桅粗 17 palm（≈ 0.45–0.53 m，換算〔估〕）⇒ 主桅直徑 0.5 m、前桅 0.44、後桅 0.32（腳、頂）；比甲板桅孔（plan.decks_build.mast_r：前 2.5、主 3、後 2）小',
        'topmast_r': {'fore': [1.4, 0.9], 'main': [1.6, 1.0]},
        'tops': {'main': 12, 'fore': 11, 'rim_h': 6,
                 'src': 'W p.94（pinas 134 呎）：桅樓（mars）直徑 主 10 呎、前 9 呎〔查，藍鯊號 plan〕⇒ 照船長比例 × 0.82 ⇒ 主 8.2 呎（半徑 11.6 格）、前 7.4 呎（10.5）⇒ 12／11（遊戲的桅頂水手站在桅軸半徑 9／12 的一圈、一層要 6 點以上，收穫號 TASK-0623）；籃子 6 格高、綠腰帶（照船殼的綠）、金頂；後桅沒有桅樓（只有 lateen）'},
        'bowsprit_r': [2.2, 1.4],
        'yards': [
            {'name': 'yard-fore-course', 'mast': 'fore', 'yard': 'course', 'sail': 'fore-course', 'src_work': CY + 'fore-topgallant', 'src_len': 131, 'brace': -15},
            {'name': 'yard-fore-topsail', 'mast': 'fore', 'yard': 'topsail', 'sail': 'fore-topsail', 'src_work': CY + 'mizzen-royal', 'src_len': 65, 'brace': -17},
            {'name': 'yard-main-course', 'mast': 'main', 'yard': 'course', 'sail': 'main-course', 'src_work': CY + 'main-topgallant', 'src_len': 143, 'brace': -15},
            {'name': 'yard-main-topsail', 'mast': 'main', 'yard': 'topsail', 'sail': 'main-topsail', 'src_work': CY + 'main-royal', 'src_len': 93, 'brace': -17},
            {'name': 'yard-spritsail', 'mast': 'bowsprit', 'yard': 'spritsail', 'sail': 'spritsail', 'src_work': CY + 'fore-royal', 'src_len': 87, 'brace': 0, 'at_t': 0.85, 'drop': 3}],
        'yards_src': 'Ship_Setup §2.1：方帆桁沿用憲法號的帆桁元件，只沿長度（y）縮放；挑長度最接近的那一根（縮放 0.87–1.05）：主帆桁 14.4 m ← main-topgallant、主上桅帆桁 8.1 ← main-royal、前帆桁 11.9 ← fore-topgallant、前上桅帆桁 6.8 ← mizzen-royal、spritsail 8.2 ← fore-royal；src_len ＝ 臂距 ＋ 3（照拉貝爾號）',
        'lateen': [{'mast': 'mizzen', 'len_m': 11.0, 'angle_deg': 40, 'hoist_frac': 0.4, 'sail': 'mizzen-lateen'}],
        'lateen_src': '後桅 lateen（W p.130 表有後桅、沒有後上桅）；長度見 plan.masts；角度、吊點設計決定（同拉貝爾號的 40°、40%）'}
    s = json.dumps(plan, ensure_ascii=False, indent=1) + '\n'
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    json.load(open(p, encoding='utf-8'))
    print('ok', len(s))


if __name__ == '__main__':
    main()

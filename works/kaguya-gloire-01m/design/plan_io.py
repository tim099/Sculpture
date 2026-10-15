# plan.json 的讀寫：純量陣列、只含純量的短物件排在一行（diff 好讀）；⛔ 不用 json.dump 的預設縮排（一個數一行，diff 會炸）
import json, os


def dumps(o, ind=0):
    pad, pad1 = '  ' * ind, '  ' * (ind + 1)

    def flat(v):
        return not isinstance(v, (dict, list)) or (isinstance(v, list) and all(not isinstance(x, (dict, list)) for x in v))
    if isinstance(o, list):
        if all(flat(x) for x in o):
            return json.dumps(o, ensure_ascii=False, separators=(', ', ': '))
        return '[\n' + ',\n'.join(pad1 + dumps(x, ind + 1) for x in o) + '\n' + pad + ']'
    if isinstance(o, dict):
        one = json.dumps(o, ensure_ascii=False, separators=(', ', ': '))
        if all(flat(v) for v in o.values()) and len(one) + len(pad) < 160:
            return one
        return '{\n' + ',\n'.join(pad1 + json.dumps(k, ensure_ascii=False) + ': ' + dumps(v, ind + 1) for k, v in o.items()) + '\n' + pad + '}'
    return json.dumps(o, ensure_ascii=False)


def load(design):
    with open(os.path.join(design, 'plan.json'), encoding='utf-8') as f:
        return json.load(f)


def save(design, plan):
    p = os.path.join(design, 'plan.json')
    with open(p + '.tmp', 'w', encoding='utf-8', newline='\n') as f:
        f.write(dumps(plan) + '\n')
    os.replace(p + '.tmp', p)

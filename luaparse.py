import pandas as pd
from luadata import unserialize
import re
import json
import os
from pathlib import Path
import math

with open('dict/dict_custom.json', 'r', encoding='utf-8') as file:
    dict_custom = json.load(file)

def expression_unserialize(data):
    pattern = r'=(\s*)((?=.*\d)(?=.*\*)[0-9* ]+?)(\s*)(,)'

    # 替换为字符串格式
    processed_data = re.sub(
        pattern,
        r'="\2"\4',
        data
    )

    return unserialize(processed_data, encoding="utf-8")

with open("insert/augments.txt", 'r', encoding='utf-8') as f:
    content = f.read()
data = expression_unserialize(content)
df = {}
i = 0
for d in data['Augments']:
    for w in d['Weapons']:
        if w in list(df.keys()):
            df[w].append(d['Name'])
        else:
            df[w] = [d['Name']]

with open("dict/augments.json", 'w', encoding='utf-8') as f:
    json.dump(df, f,
              indent=4,
              ensure_ascii=False)

with open("insert/stance.txt", 'r', encoding='utf-8') as f:
    content = f.read()
data = expression_unserialize(content)
class_set = set({})
pol_set = set({})
wp_set = {}
for d in data:
    if "Weapon" in d.keys():
        wp_set[d["Weapon"]] = d["Name"]
    else:
        class_set.update([d["Class"]])
        pol_set.update([dict_custom[d["Polarity"]]])
res = {}
for c in class_set:
    res[c] = {}
    for p in pol_set:
        for d in data:
            if d["Class"] == c and dict_custom[d["Polarity"]] == p:
                res[c][d["Name"]] = {}
                res[c][d["Name"]]["Polarity"] = p
                if "PvP" in d.keys():
                    res[c][d["Name"]]["PvP"] = d["PvP"]
                else:
                    res[c][d["Name"]]["PvP"] = False
    res[c] = dict(sorted(
        res[c].items(),
        key=lambda item: item[1]['PvP'],
    ))
res = {**res,**wp_set}
with open("dict/stance.json", 'w', encoding='utf-8') as f:
    json.dump(res, f,
              indent=4,
              ensure_ascii=False)

folder = Path("./text")
wp = {}
for t in folder.glob('*.txt'):
    with open(t, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(
        r"math\.huge",
        "0",
        content
    )
    wp.update(expression_unserialize(content))
with open('json/weapon.json', 'w', encoding='utf-8') as f:
    json.dump(wp, f, ensure_ascii=False, indent=4)

# def get_all_keys(data, keys=None):
#     keys = set() if keys is None else keys
#     if isinstance(data, dict):
#         for key, value in data.items():
#             keys.add(key)
#             get_all_keys(value, keys)  # 递归处理值
#     elif isinstance(data, list):
#         for item in data:
#             get_all_keys(item, keys)  # 处理列表元素
#     return list(keys)
#
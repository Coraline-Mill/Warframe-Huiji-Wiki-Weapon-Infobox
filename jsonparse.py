import pandas as pd
from luadata import unserialize
import re
import json
from simpleeval import simple_eval
import os
from pathlib import Path
import math
from pandas import json_normalize

vars_set = {
    'Prime', 'Wraith', 'Vandal',
    'Perrin Sequence', 'New Loka', 'Red Veil', 'Arbiters of Hexis', 'Cephalon Suda', 'Steel Meridian',
    'Technocyte Coda', 'Kuva Lich', 'Tenet', 'Prisma', 'MK1', 'Mara', 'Dex', 'Ceti', 'Carmine', 'Umbra'
}

vars_list = [
    'Prime', 'Wraith', 'Vandal',
    'Perrin Sequence', 'New Loka', 'Red Veil', 'Arbiters of Hexis', 'Cephalon Suda', 'Steel Meridian',
    'Technocyte Coda', 'Kuva Lich', 'Tenet', 'Prisma', 'MK1', 'Mara', 'Dex', 'Ceti', 'Carmine', 'Umbra'
]

with open('dict/dict.en.json', 'r', encoding='utf-8') as file:
    dict_en = json.load(file)

with open('dict/dict.zh.json', 'r', encoding='utf-8') as file:
    dict_zh = json.load(file)

with open('dict/dict_custom.json', 'r', encoding='utf-8') as file:
    dict_custom = json.load(file)

with open('dict/dict_attack_name.json', 'r', encoding='utf-8') as file:
    dict_attack_name = json.load(file)

with open('dict/augments.json', 'r', encoding='utf-8') as file:
    dict_augments = json.load(file)

with open('dict/stance.json', 'r', encoding='utf-8') as file:
    dict_stance = json.load(file)

with open('dict/var.json', 'r', encoding='utf-8') as file:
    dict_var = json.load(file)

with open('dict/userdict.json', 'r', encoding='utf-8') as file:
    f = json.load(file)
    dict_wiki = f["Text"]
    dict_wiki_2 = f["Category"]

def clean_escape_chars(data):
    if isinstance(data, dict):
        return {k: clean_escape_chars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_escape_chars(item) for item in data]
    elif isinstance(data, str):
        return re.sub(r'[\n\t\r\\]', '', data).strip()
    else:
        return data

def dict_pick(dict_,key,print_=False):
    try:
        return dict_[key]
    except:
        if print_:
            print(key)
        return key

def get_unique_elements(df):
    unique_strings = set()

    def process_element(e):
        if isinstance(e, list):
            for item in e:
                yield from process_element(item)
        elif isinstance(e, str):
            # 分割字符串并处理空格
            for part in e.split('/'):
                cleaned = part.strip()
                if cleaned:  # 过滤空字符串
                    yield cleaned

    # 遍历所有单元格
    for col in df.columns:
        for element in df[col]:
            unique_strings.update(process_element(element))

    return unique_strings

def save_unique_json(df, filename='output.json'):
    # 获取唯一字符串集合
    unique_set = get_unique_elements(df)

    # 创建字典（值设为空字符串）
    result_dict = {key: "" for key in unique_set}

    # 保存为JSON文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f,
                  indent=4,
                  ensure_ascii=False)  # 保持非ASCII字符原样

def is_valid_entry(series: pd.Series, index) -> bool:
    # 如果 index 是列表，逐个检查
    if isinstance(index, list):
        return all(_check_single_entry(series, idx) for idx in index)
    # 如果 index 是单个值，直接检查
    else:
        return _check_single_entry(series, index)

def _check_single_entry(series: pd.Series, index) -> bool:
    # 检查索引是否存在
    if index not in series.index:
        return False

    # 获取对应值
    value = series[index]

    # 检查值有效性
    return not (pd.isna(value) or (isinstance(value, str) and value.strip() == ""))

def is_regex_pattern(s: str) -> bool:
    try:
        re.compile(s)
        return True
    except re.error:
        return False

def replace_with_dict(input_str, custom_dict):
    for key, value in custom_dict.items():
        input_str = input_str.replace(key, value)
    input_str = re.sub(r'(\d)m ', r'\1米 ', input_str)
    return input_str

def disposition_sort(d):
    if 1.31 <= d:
        return 5
    elif 1.11 <= d < 1.31:
        return 4
    elif 0.90 <= d < 1.11:
        return 3
    elif 0.70 <= d < 0.90:
        return 2
    elif d < 0.70:
        return 1

def weapon_baseinfo(row):
    table_str = ''
    if is_valid_entry(row,"Class"):
        table_str+='武器类型$'+dict_pick(dict_trans,row["Class"])+'^'
    if is_valid_entry(row, "Slot"):
        table_str += '武器槽位$' + dict_pick(dict_trans, row["Slot"]) + '^'
    if is_valid_entry(row, "Tradable"):
        if row["Tradable"]==0:
            td="不可交易"
        elif row["Tradable"]==1:
            td = "未获得经验及安装升级的武器可交易"
        elif row["Tradable"]==2:
            td = "部件及蓝图可交易"
        elif row["Tradable"]==3:
            td = "持有该武器的对手可交易<br>武器不可交易"
        else:
            td = "不可交易"
    else:
        td = "不可交易"
    if "Coda" in row["Link"].split(' '):
        td = "不可交易"
    table_str += '交易属性$' + td + '^'
    if is_valid_entry(row, "Mastery") and int(row["Mastery"])!=0:
        table_str += '[[精通段位|精通段位要求]]$' + str(int(row["Mastery"])) + '^'
    else:
        table_str += '[[精通段位|精通段位要求]]$无^'

    if is_valid_entry(row, "MaxRank"):
        try:
            rank = int(row["MaxRank"])
        except:
            rank = 30
        if rank!=30:
            table_str += '超限升级$' + str(int(rank)) + '^'
    if is_valid_entry(row, "Trigger"):
        table_str += '扳机类型$' + "/".join(map(str,list(map(lambda s:dict_pick(dict_custom,s.strip()),row["Trigger"].split('/'))))) + '^'
    try:
        ap = int(row["AmmoPickup"])
    except:
        ap = 0
    if is_valid_entry(row, "AmmoType") and dict_pick(dict_custom, row["AmmoType"])!='无':
        table_str += '[[弹药|弹药类型]]$' + dict_pick(dict_custom, row["AmmoType"],True) + '^'
    else:
        if ap!=0:
            table_str += '[[弹药|弹药类型]]$' + dict_pick(dict_custom, row["Slot"],True) + '^'
    if ap!=0:
        table_str += '[[弹药|弹药拾取量]]$' + str(int(ap)) + '^'
    if is_valid_entry(row,"Accuracy"):
        table_str+='[[精准度]]$'+str(round(row["Accuracy"],1))+'^'
    if is_valid_entry(row,"MeleeRange"):
        table_str+='[[攻击范围]]$'+str(round(row["MeleeRange"],2))+'米^'
    if is_valid_entry(row,"SweepRadius"):
        table_str+='[[攻击范围|法向延展半径]]$'+str(round(row["SweepRadius"],2))+'米^'
    if is_valid_entry(row, "Slot") and row["Slot"] in ["Melee", "Archmelee", "Hound", "Beast"]:
        table_str += '[[攻击速度]]$' + str(round(row["Attack.0"]["FireRate"], 3)) + '倍基准攻速^'
    elif "Deconstructor" in row["Name"]:
        table_str += '[[攻击速度]]$每秒' + str(round(row["Attack.0"]["FireRate"], 3)) + '次攻击^'
    if is_valid_entry(row,"BlockAngle"):
        table_str += '[[格挡角度]]$' +str(round(row["BlockAngle"]))+ '°^'
    if is_valid_entry(row,"ComboDur"):
        table_str += '[[连击持续时间]]$' +str(round(row["ComboDur"],1))+ '秒^'
    if is_valid_entry(row,"FollowThrough"):
        table_str += '[[伤害穿透系数]]$' +str(round(row["FollowThrough"]*100))+ '%^'

    if is_valid_entry(row,"Magazine"):
        table_str+='[[弹药|弹匣容量]]$'+str(int(row["Magazine"]))+'^'
    if is_valid_entry(row, "AmmoMax") and int(row["AmmoMax"])!=0:
        table_str += '[[弹药|弹药上限]]$' + str(int(row["AmmoMax"])) + '^'
    if is_valid_entry(row, "Reload"):
        if str(row["ReloadStyle"])=="Regenerate":
            if is_valid_entry(row, "ReloadDelayEmpty"):
                table_str += ('[[装填|装填速度]]$充能速率:' + str(
                    float(row["ReloadRate"])) + '发/秒</br>部分弹匣充能延迟' +
                              str(float(row["ReloadDelay"])) + '秒</br>空弹匣充能延迟' + str(
                            float(row["ReloadDelayEmpty"])) + '秒^')
            else:
                table_str += ('[[装填|装填速度]]$充能速率:' + str(
                    float(row["ReloadRate"])) + '发/秒</br>充能延迟' + str(float(row["ReloadDelay"])) + '秒^')
        elif str(row["ReloadStyle"])=="ByRound":
            table_str += '[[装填|装填速度]]$逐发装填总用时:'+str(float(row["Reload"]))+'秒^'
        else:
            try:
                rd = float(row["Reload"])
            except:
                rd = 0
            if rd!=0:
                table_str += '[[装填|装填速度]]$装填用时:' + str(float(row["Reload"])) + '秒^'
    if is_valid_entry(row,"Spool"):
        table_str+='预热$'+str(int(row["Spool"]))+'发^'

    if is_valid_entry(row,"SniperComboMin"):
        table_str+='[[狙击枪#连击|最小连击阈值]]$'+str(int(row["SniperComboMin"]))+'次命中^'
    if is_valid_entry(row,"SniperComboReset"):
        table_str+='[[狙击枪#连击|连击持续时间]]$'+str(int(row["SniperComboReset"]))+'秒^'
    try:
        zl = len(row["Zoom"])
    except:
        zl = 0
    if zl!=0:
        table_str += '[[瞄准|缩放]]$'
        for i in range(len(row["Zoom"])):
            z = replace_with_dict(row["Zoom"][i], dict_custom)
            if i==len(row["Zoom"])-1:
                table_str +=z
            else:
                table_str +=z+"<br>"
        table_str +='^'
    try:
        pl = len(row["Polarities"])
    except:
        pl = 0
    stance = []
    if pl == 0 and (not is_valid_entry(row, "ExilusPolarity") or row["ExilusPolarity"] == "None") and (
            not is_valid_entry(row, "StancePolarity") or row["StancePolarity"] == "None"):
        pass
    else:
        table_str += '[[极性]]$'
        if pl!=0:
            table_str += '常规:'
            for p in row["Polarities"]:
                table_str += "{{Icon|Pol|"+dict_pick(dict_custom,p)+"}}"
            table_str+='<br>'
        if is_valid_entry(row, "ExilusPolarity") and row["ExilusPolarity"] != "None":
            table_str += '特殊功能槽:'
            table_str += "{{Icon|Pol|"+dict_pick(dict_custom,row["ExilusPolarity"])+"}}"
        if is_valid_entry(row, "StancePolarity") and row["StancePolarity"] != "None":
            table_str += '架式槽:'
            table_str += "{{Icon|Pol|"+dict_pick(dict_custom,row["StancePolarity"])+"}}"
            if row["Class"]=="Exalted Weapon":
                if row["Name"] in dict_stance.keys():
                    stance.append('{{M|'+dict_pick(dict_trans,dict_stance[row["Name"]],True)+'}}')
            else:
                ep = dict_pick(dict_custom,row["StancePolarity"])
                if row["Class"] in dict_stance.keys():
                    for k in dict_stance[row["Class"]].keys():
                        stance_ = '[['
                        stance_ += dict_pick(dict_trans, k, True) + ']]'
                        p = dict_pick(dict_custom,dict_stance[row["Class"]][k]["Polarity"])
                        if ep == p:
                            stance_ += '{{PM|' + p + '|1}}'
                        else:
                            stance_ += '{{PM|' + p + '|0}}'
                        if dict_stance[row["Class"]][k]["PvP"]:
                            stance_ += "{{Icon/pvp}}"
                        stance.append(stance_)
        table_str += '^'

    if len(stance)!=0:
        stance_str = ''
        for s in stance:
            stance_str+=s+'<br>'
        table_str += '可用[[架式]]$' + stance_str + '^'
    if is_valid_entry(row, "Disposition"):
        dis = '{{Icon|Dis5|' + str(int(disposition_sort(row["Disposition"]))) + '}}'
        table_str += '[[裂罅MOD|裂罅倾向]]$' + dis +'('+str(round(row["Disposition"],2))+')'
    return table_str

def weapons_attackinfo(atk,ismelee=False):
    table_elem = ''
    dmg = atk['Damage']
    dmg_sum = 0
    dmg_max_v = 0
    dmg_max_name = ''
    for k,v in dmg.items():
        dmg_sum+=v
        if v > dmg_max_v:
            dmg_max_v = v
            dmg_max_name = '{{Icon|Proc|' + str(k) + '|text}}'
        table_elem += '{{Icon|Proc|' + str(k) + '|text||' + str(round(v, 1)) + '}}^'
    table_stats = ''
    if dmg_sum==0:
        dmg_per = 0
    else:
        dmg_per = dmg_max_v/dmg_sum
    if "Multishot" in list(atk.keys()):
        table_stats += '[[多重射击]]$'+str(round(atk["Multishot"],1))+'(每个弹片'+str(round(dmg_sum, 1))+'伤害)^'
        table_stats += '总伤害$'+str(round(dmg_sum*atk["Multishot"],1))+'('+str(round(dmg_per*100,0))+'% '+dmg_max_name+')^'
    else:
        if not ismelee:
            table_stats += '[[多重射击]]$' + str(1) + '(每个弹片' + str(round(dmg_sum, 1)) + '伤害)^'
        else:
            table_stats += '总伤害$' + str(round(dmg_sum, 1)) + '('+str(round(dmg_per*100,0))+'% '+dmg_max_name+')^'
    if "ChargeTime" in list(atk.keys()):
        table_stats += '[[射速|蓄力时间]]$' + str(round(atk["ChargeTime"], 2)) + '秒^'
    elif "FireRate" in list(atk.keys()):
        if ismelee:
            if atk["FireRate"]<=1:
                table_stats += '[[攻速]]$' + "{0:.3g}".format(atk["FireRate"]) + '倍^'
            else:
                table_stats += '[[攻速]]$' + "{0:.4g}".format(atk["FireRate"]) + '倍^'
        else:
            table_stats += '[[射速]]$' + "{0:.3g}".format(atk["FireRate"]) + '发/秒^'
    if "BurstCount" in list(atk.keys()):
        if "Multishot" in list(atk.keys()):
            table_stats += '点射连发$' + str(round(atk["BurstCount"])) + '发(总伤害:'+str(round(atk["BurstCount"]*dmg_sum*atk["Multishot"], 1))+')^'
        else:
            table_stats += '点射连发$' + str(round(atk["BurstCount"])) + '发(总伤害:' + str(
                round(atk["BurstCount"] * dmg_sum, 1)) + ')^'
    if "BurstDelay" in list(atk.keys()) and atk["BurstDelay"]!=0:
        table_stats += '点射延迟$' + str(round(atk["BurstDelay"])) + '秒^'
    if "BurstReloadDelay" in list(atk.keys()) and atk["BurstReloadDelay"]!=0:
        table_stats += '点射装填延迟$' + str(round(atk["BurstReloadDelay"])) + '秒^'
    if "Reload" in list(atk.keys()) and atk["Reload"]!=0:
        table_stats += '装填时间$' + str(round(atk["Reload"])) + '秒^'
    if "Trigger" in list(atk.keys()):
        table_stats += '扳机类型$' + dict_pick(dict_trans, atk["Trigger"], True) + '^'
    if "IncarnonCharges" in list(atk.keys()):
        table_stats += '灵化充能$'+str(round(atk["IncarnonCharges"],0))+'^'
    if "ShotType" in list(atk.keys()):
        table_stats += '伤害判定类型$' + dict_pick(dict_trans,atk["ShotType"],True) + '^'
    if "Accuracy" in list(atk.keys()):
        table_stats += '精准度$'+str(round(atk["Accuracy"],0))+'^'
    if "PunchThrough" in list(atk.keys()):
        table_stats += '穿透$'+str(round(atk["PunchThrough"],2))+'米^'
    if "MeleeRange" in list(atk.keys()):
        table_stats+='[[攻击范围]]$'+str(round(atk["MeleeRange"],2))+'米^'
    if "MinSpread" in list(atk.keys()) and "MaxSpread" in list(atk.keys()) and atk["MaxSpread"]!=0:
        table_stats += '散布$'+str(round(atk["MinSpread"],0))+'~'+str(round(atk["MaxSpread"],0))+'^'
    if "IsSilent" in list(atk.keys()):
        if atk["IsSilent"]:
            table_stats += '噪音等级$无声^'
        else:
            table_stats += '噪音等级$引起警戒^'

    if "ShotSpeed" in list(atk.keys()):
        table_stats += '投射物速度$'+str(round(atk["ShotSpeed"],1))+'米/秒^'
    if "Range" in list(atk.keys()):
        if ismelee:
            table_stats += '伤害范围$'+str(round(atk["Range"],1))+'米^'
        else:
            table_stats += '射程$'+str(round(atk["Range"],1))+'米^'
    if "Falloff" in list(atk.keys()) and len(atk["Falloff"].keys()) > 0:
        if "Reduction" in list(atk["Falloff"].keys()):
            rd = str(round((1 - atk["Falloff"]["Reduction"]) * 100,1))
        else:
            rd = str(100)
        if "ShotType" in list(atk.keys()) and atk["ShotType"] == "AoE":
            table_stats += '伤害衰减$' + str(atk["Falloff"]["StartRange"]) + '米内100%伤害<br>' + str(
                atk["Falloff"]["EndRange"]) + '米外' + rd + '%伤害^'
        else:
            table_stats += '伤害衰减$' + str(atk["Falloff"]["StartRange"]) + '米内100%伤害<br>' + str(
                atk["Falloff"]["EndRange"]) + '米外' + rd + '%伤害^'
    if "Ammocost" in list(atk.keys()):
        table_stats += '[[弹药|弹药消耗]]$单次射击消耗' + str(round(atk["Ammocost"], 1)) + '发弹药^'
    if "AmmoCost" in list(atk.keys()):
        table_stats += '[[弹药|弹药消耗]]$单次射击消耗' + str(round(atk["AmmoCost"], 1)) + '发弹药^'

    if "StatusChance" in list(atk.keys()):
        table_stats += '[[触发几率]]$' + str(round(100 * atk["StatusChance"], 2)) + '%^'
    if "EffectDuration" in list(atk.keys()):
        table_stats += '[[触发几率|异常持续时间]]$' + str(round(atk["EffectDuration"], 1)) + '秒^'
    if "ForcedProcs" in list(atk.keys()) and len(atk["ForcedProcs"])>0:
        p_str = ''
        for p in range(len(atk["ForcedProcs"])):
            if p==len(atk["ForcedProcs"])-1:
                p_str+='{{Icon|Proc|' + atk["ForcedProcs"][p] + '|text}}'
            else:
                p_str += '{{Icon|Proc|' + atk["ForcedProcs"][p] + '|text}}<br>'
        table_stats += '[[触发几率|强制触发]]$' + p_str + '^'
    if "CritChance" in list(atk.keys()):
        table_stats += '[[暴击几率]]$' + str(round(100 * atk["CritChance"], 2)) + '%^'
    if "CritMultiplier" in list(atk.keys()):
        table_stats += '[[暴击伤害]]$' + str(round(atk["CritMultiplier"], 1)) + 'x^'
    if "ExtraHeadshotDmg" in list(atk.keys()):
        table_stats += '额外爆头伤害$' + str(round(atk["ExtraHeadshotDmg"], 1)) + 'x^'
    if "ExplosionDelay" in list(atk.keys()) and atk["ExplosionDelay"]!=0:
        table_stats += '爆炸延迟$' + str(round(atk["ExplosionDelay"], 1)) + '秒^'
    elif "EmbedDelay" in list(atk.keys()) and atk["EmbedDelay"]!=0:
        table_stats += '爆炸延迟$' + str(round(atk["EmbedDelay"], 1)) + '秒^'
    return pd.Series([table_elem,table_stats])

def weapons_extraattack(row):
    extraattack = False
    for s in ["HeavyAttack","SlideAttack","WindUp","SlideElement"]:
        if is_valid_entry(row,s):
            extraattack = True
    if extraattack:
        table_extra = ''
        icon = ''
        if is_valid_entry(row, "HeavyAttack"):
            table_extra+='重击伤害$'+str(round(simple_eval(str(row["HeavyAttack"])),1))+'^'
        if is_valid_entry(row, "WindUp"):
            table_extra += '重击准备时间$' + str(row["WindUp"]) + '秒^'
        if is_valid_entry(row, "SlideElement"):
            icon += '{{Icon|Proc|' + str(row["SlideElement"]) + '}}'
        if is_valid_entry(row, "SlideAttack"):
            table_extra += '滑行攻击$' + icon + str(row["SlideAttack"]) + '^'
        return pd.Series(["其他攻击",table_extra])
    else:
        return pd.Series([None,None])

def weapon_otherinfo(row):
    table_str = ''
    if is_valid_entry(row,"Introduced"):
        if str(row["Introduced"]).upper() == 'VANILLA':
            ver = '原版'
        else:
            ver = '{{ver|'+str(row["Introduced"])+'}}'
        table_str += '推出时间$' + ver + '^'
    if is_valid_entry(row,"IncarnonImage"):
        # print(row["Family"],row["Name"])
        table_str += '[[灵化之源]]$[[' + dict_pick(dict_trans,row["Family"],True) + '灵化之源]]^'
    if is_valid_entry(row, "SyndicateEffect"):
        table_str += '[[集团|集团效果]]$[[' + dict_pick(dict_custom, row["SyndicateEffect"],
                                                                   True) + ']]^'
    if type(row["Kins"]) == type([]) and len(row["Kins"])>0:
        kin = ''
        for k in row['Kins']:
            if '（大气层内）' not in k and k!=row["Namezh"][:-6]:
                kin += '[[' + k + ']]'
        kin = kin.replace(']][[',']]<br>[[')
        if kin!='':
            table_str += '同系列武器$' + kin + '^'
    if row['Name'] in dict_augments.keys():
        aug = ''
        for a in dict_augments[row["Name"]]:
            if a!=dict_augments[row["Name"]][-1]:
                aug += '[['+dict_pick(dict_trans,a,True).replace('·','').replace(' ','')+']]<br>'
            else:
                aug += '[[' + dict_pick(dict_trans,a,True).replace('·','').replace(' ','') + ']]'
        table_str += '[[MOD#强化Mod|强化]]$' + aug + '^'
    if is_valid_entry(row,"CodexSecret"):
        if str(row["CodexSecret"]).upper() == "TRUE":
            table_str += '[[资料库|资料库隐藏]]$是^'
    if is_valid_entry(row, "User"):
        user = ''
        for u in row["User"]:
            user+='[['+dict_pick(dict_trans,u,True)+']]<br>'
        table_str += '武器使用者$'+user+'^'
    return table_str

def weapon_variants(row):
    if type(row["Traits"])!=type([]):
        orginal = True
    else:
        if bool(vars_set & set(row["Traits"])) and type(row["Kins"]) == type([]) and len(row["Kins"])>0 or '（大气层内）' in row["Namezh"] or 'Umbra' in row["Namezh"]:
            orginal = False
        else:
            orginal = True
    kin_str = []
    if orginal and type(row["Kins"]) == type([]) and len(row["Kins"])>0:
        for k in row["Kins"]:
            if type(df.loc[df['Namezh'] == k].squeeze()["Traits"]) == type([]):
                for v in vars_set & set(df.loc[df['Namezh'] == k].squeeze()["Traits"]):
                    kin_str.append(v)
            else:
                pass
    else:
        pass
    if orginal:
        if row['Namezh']=="显赫刀剑":
            var_name = "[[显赫刀剑]]（[[显赫刀剑Prime|Prime]]/[[显赫刀剑Umbra|Umbra]]）"
        elif len(kin_str)==0:
            var_name = '[['+ row["Namezh"].replace('（主要）','').replace('（次要）','').replace('（双剑）','').replace('（巨刃）','') +']]'
        else:
            front = ''
            back = ''
            for v in kin_str:
                if v in [
                    'Perrin Sequence', 'New Loka', 'Red Veil', 'Arbiters of Hexis', 'Cephalon Suda', 'Steel Meridian',
                    'Technocyte Coda', 'Kuva Lich', 'Tenet', 'Prisma', 'MK1', 'Mara', 'Dex', 'Ceti', 'Carmine']:
                    front+='[['+dict_var[v]+row["Namezh"]+'|'+dict_var[v]+']]'
                else:
                    back+='[['+row["Namezh"]+dict_var[v]+'|'+dict_var[v]+']]'
            front = front.replace(']][[', ']]/[[')
            back = back.replace(']][[', ']]/[[')
            if front!='':
                front = '（'+front+'）'
            if back!='':
                back = '（'+back+'）'
            var_name = front +'[['+ row["Namezh"] +']]'+ back
    else:
        var_name = ''
    return pd.Series([orginal,var_name])

def traits_fix(row):
    if type(row["Traits"])==type([]):
        t = row["Traits"]
    else:
        t = []
    if 'MK1-' in row["Name"] and "MK1" not in t:
        t.append('MK1')
    else:
        pass
    if 'Mara ' in row["Name"] and "Mara" not in t:
        t.append('Mara')
    else:
        pass
    if 'Coda ' in row["Name"] and "Technocyte Coda" not in t:
        t.append('Technocyte Coda')
    else:
        pass
    if 'Prime' in row["Name"] and "Prime" not in t:
        t.append('Prime')
    else:
        pass
    if 'Dex ' in row["Name"] and "Dex" not in t and row["Class"]!="Exalted Weapon":
        t.append('Dex')
    else:
        pass
    if ' Wraith' in row["Name"] and "Wraith" not in t:
        t.append('Wraith')
    else:
        pass
    if 'Prisma ' in row["Name"] and "Prisma" not in t:
        t.append('Prisma')
    else:
        pass
    if 'Ceti ' in row["Name"] and "Ceti" not in t:
        t.append('Ceti')
    else:
        pass
    if 'Carmine ' in row["Name"] and "Carmine" not in t:
        t.append('Carmine')
    else:
        pass
    return t

def family_fix(row):
    if not is_valid_entry(row,"Family"):
        return row["Name"].replace(' Prime','').replace(' Umbra','')
    else:
        return row["Family"]

dict_zh = clean_escape_chars(dict_zh)
dict_en = clean_escape_chars(dict_en)
dict_custom = clean_escape_chars(dict_custom)
dict_attack_name = clean_escape_chars(dict_attack_name)
dict_augments = clean_escape_chars(dict_augments)
dict_wiki = clean_escape_chars(dict_wiki)
dict_wiki_2 = clean_escape_chars(dict_wiki_2)
dict_trans = dict(zip(dict_en.values(), dict_zh.values()))
dict_trans = {**dict_trans,**dict_custom}
dict_trans = {**dict_trans,**dict_wiki,**dict_wiki_2}
def json_to_dataframe(file_path, id_column_name='item_id'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "Arbucep" in data.keys():
                data["Arbucep"]["Class"] = "Archgun"
                for w in ["Arbucep","Arbucep (Atmosphere)"]:
                    data[w]["Attacks"] = data[w]["Attacks"][:2]
                    data[w]["Attacks"][0]["Multishot"] = 6
                    data[w]["Attacks"][1]["Multishot"] = 6
                    data[w]["Attacks"][0]["AttackName"] = "Normal Attack"
                    data[w]["Attacks"][1]["AttackName"] = "Radial Attack"
                    data[w]["Attacks"][0]["Ammocost"] = 6
                    data[w]["Attacks"][1]["Ammocost"] = 6
                    value = data[w]["Attacks"][0]["Damage"].pop(list(data[w]["Attacks"][0]["Damage"].keys())[0])
                    data[w]["Attacks"][0]["Damage"]["Mushroom"] = value
                    value = data[w]["Attacks"][1]["Damage"].pop(list(data[w]["Attacks"][1]["Damage"].keys())[0])
                    data[w]["Attacks"][1]["Damage"]["Mushroom"] = value
            # 处理顶层是对象的情况
            if isinstance(data, dict):
                # 将每个键值对转换为带ID的记录
                records = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        # 添加ID字段
                        record = value.copy()
                        record[id_column_name] = key
                        records.append(record)
                    else:
                        # 处理非对象类型的值
                        records.append({id_column_name: key, 'value': value})

                # 展开嵌套结构
                return json_normalize(records)

            # 处理顶层是数组的情况
            elif isinstance(data, list):
                return pd.DataFrame(data)

            else:
                raise ValueError("不支持的JSON格式类型")

    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return None
    except json.JSONDecodeError:
        print("错误：JSON格式解析失败")
        return None

def transform_match(match):
    # 提取捕获组中的内容
    extracted = match.group(1)
    # 将第一个字符转为大写，其余字符转为小写
    transformed = extracted[0].upper() + extracted[1:].lower()
    return '{{Icon|Proc|'+transformed+'}}'

def descname_pick(row):
    n = row["Name"].replace(" (Atmosphere)", '').replace(" (Dual Swords)", '').replace(" (Heavy Blade)", '')
    if row["Class"]=="Exalted Weapon" or "Garuda" in row["Name"]:
        n = n.replace(" Prime", '').replace(" Umbra", '')
    return dict_pick(dict_desc, dict_pick(dict_trans, n))

df = json_to_dataframe('json/weapon.json')
df_desc = json_to_dataframe('dict/ExportWeapons.json')
df_desc = df_desc[["name","description"]]
df_desc["name"] = df_desc.apply(lambda row:dict_pick(dict_zh,row["name"]).replace('·','').replace(' ','').replace('<ARCHWING>',''),axis = 1)
df_desc["description"] = df_desc.apply(lambda row:dict_pick(dict_zh,row["description"]),axis = 1)
dict_desc = df_desc.set_index("name")["description"].to_dict()
df["alen"] = df.apply(lambda row:len(row['Attacks']),axis=1)
df["Traits"] = df.apply(lambda row:traits_fix(row),axis=1)
attackMax = max(df["alen"])
del df["alen"]
unique_strings = set()
for i in range(attackMax):
    df["Attack."+str(i)] = df.apply(lambda row:row['Attacks'][i] if len(row['Attacks'])>=i+1 else None,axis = 1)
    df["Attack."+str(i) + "name"] = df.apply(lambda row:row["Attack."+str(i)]["AttackName"] if len(row['Attacks'])>=i+1 else None,axis = 1)
    df["Attack." + str(i) + "name"].apply(lambda x: unique_strings.update([x]) if type(x)==type("str") else unique_strings.update(""))

for i in unique_strings:
    if i not in set(dict_attack_name.keys()):
        dict_attack_name[i] = ""
with open("dict/dict_attack_name.json", 'r', encoding='utf-8') as f:
    json_data = json.load(f)
if not set(dict_attack_name.keys())<=set(json_data.keys()) or "" in json_data.values():
    print("存在未翻译的攻击方式，请前往dict/dict_attack_name.json中补充")
    merged = {**dict_attack_name, **json_data}
    with open("dict/dict_attack_name.json", 'w', encoding='utf-8') as f:
        json.dump(merged, f,
                  indent=4,
                  ensure_ascii=False)
df_res = pd.DataFrame()
df['Family'] = df.apply(lambda row:family_fix(row),axis = 1)
df["Namezh"] = df.apply(lambda row:dict_pick(dict_trans,row["Name"],True).replace('·','').replace(' ','') if row["Name"]!="Machete" else "马谢特砍刀",axis = 1)
df['Kins'] = df.groupby('Family')['Namezh'].transform(
    lambda x: [
        x[(x.index != idx) &
            (~x.str.contains('（大气层内）')) &
            (x + '（大气层内）' != x.loc[idx])].tolist()
        for idx in x.index
    ]
)
with open("dict/dict_custom.json", 'r', encoding='utf-8') as f:
    json_data = json.load(f)
dict_trigger = {}
set_trigger = set(df["Trigger"])
for t in list(set_trigger):
    if type(t)==type("str"):
        if '/' in str(t):
            l = t.split('/')
            for i in l:
                i = i.strip()
                if i not in dict_trigger.values():
                    dict_trigger[i] = ""
        elif t is not None:
            dict_trigger[t] = ""
if not set(dict_trigger.keys())<=set(json_data.keys()) or "" in json_data.values():
    print("存在未翻译的扳机类型，请前往dict/dict_custom.json中补充")
    merged = {**dict_trigger, **json_data}
    with open("dict/dict_custom.json", 'w', encoding='utf-8') as f:
        json.dump(merged, f,
                  indent=4,
                  ensure_ascii=False)

df_slam = pd.DataFrame(columns=["名称","震地攻击","重型震地攻击","是否相同"])
i = 0
def slamcheck(row):
    atk = row["Attacks"]
    sa = {}
    hsa = {}
    for a in atk:
        if a["AttackName"]=="Slam Attack":
            sa = a["Damage"]
        elif a["AttackName"]=="Heavy Slam Attack":
            hsa = a["Damage"]
    if len(list(sa.keys()))>0 and len(list(hsa.keys()))>0:
        sae = list(sa.keys())[0]
        hsae = list(hsa.keys())[0]
        if list(sa.keys())[0] != "Impact":
            if sae==hsae:
                df_slam.loc[len(df_slam)] = [dict_pick(dict_trans,row["Name"]),dict_pick(dict_trans,sae),dict_pick(dict_trans,hsae),"是"]
            else:
                df_slam.loc[len(df_slam)] = [dict_pick(dict_trans,row["Name"]),dict_pick(dict_trans,sae),dict_pick(dict_trans,hsae),"否"]

df.to_excel('data/precode.xlsx',index=False)
# df.apply(lambda row:slamcheck(row),axis=1)
# df_slam.to_excel('data/slam.xlsx',index=False)
df_res["NameZH"] = df["Namezh"]
df_res["NameEN"] = df["Name"]
# df_res["Class"] = df.apply(lambda row:dict_pick(dict_trans,row["Class"]),axis = 1)
df_res["Class"] = df.apply(lambda row:dict_pick(dict_trans,row["Class"]) if '/' not in row["Class"] else 'Zaw',axis = 1)
df_res["Slot"] = df.apply(lambda row:dict_pick(dict_trans,row["Slot"]),axis = 1)
df_res["Image"] = df["Image"]
df_res["Disposition"] = df.apply(lambda row:row["Disposition"] if is_valid_entry(row, "Disposition") else None,axis = 1)
df_res["Desc"] = df.apply(
    lambda row:re.sub(r"<DT_(.*?)_COLOR>", transform_match, descname_pick(row)) if row["Name"]!="Lizzie" else "（英文：LIZZIE）丽兹诞生于弗莱尔被科腐者感染的血液中。她演奏出的不仅有美妙的音符，还有狂热的怒火。",
    axis = 1
)
df_res["Info"] = df.apply(lambda row:weapon_baseinfo(row),axis = 1)
set_attack_key = set({})
for i in [0,1,2,3,4,5,6,7,8,9]:
    df_res["AttackName_"+str(i)] = df.apply(lambda row:dict_pick(dict_attack_name,row["Attack."+str(i)]["AttackName"],True) if type(row["Attack."+str(i)])==type({"attack":"name"}) else None,axis = 1)
    # df_res["AttackName_"+str(i)] = df.apply(lambda row:set_attack_key.update(set(row["Attack."+str(i)].keys())) if type(row["Attack."+str(i)])==type({"attack":"name"}) else None,axis = 1)
    df_res[
        ["AttackInfo_elem_" + str(i),"AttackInfo_stats_" + str(i)]
        ] = df.apply(lambda row: weapons_attackinfo(row["Attack." + str(i)],
                                                    row["Slot"] in ["Melee", "Archmelee", "Hound", "Beast"]) if type(
        row["Attack." + str(i)]) == type({"attack": "name"}) else pd.Series([None]*2), axis=1)
df_res[["AttackExtraName","AttackExtraInfo"]] = df.apply(lambda row:weapons_extraattack(row),axis = 1)
df_res["OtherInfo"] = df.apply(lambda row:weapon_otherinfo(row),axis = 1)
df_res[["Orginal","VarInfo"]] = df.apply(lambda row:weapon_variants(row),axis = 1)
df_res["Variants"] = df.apply(lambda row:vars_list.index(list(set(row["Traits"])&vars_set)[0])+1 if bool(set(row["Traits"])&vars_set) else 0,axis = 1)
df_fields = pd.DataFrame()
df_fields.loc[:,"name"] = list(df_res.columns)
dict_field = {"Orginal":"boolean","Disposition":"number"}
df_fields.loc[:,"type"] = ["string" if c not in ["Orginal","Disposition"] else dict_field[c] for c in list(df_res.columns)]
df_fields.loc[:,"title_zh"] = ['']*len(list(df_res.columns))
df_fields.loc[:,"title_en"] = list(df_res.columns)
df_res_2 = df_res[["NameZH","NameEN","Class","Slot","Image","Variants"]]
first_four = df_fields.iloc[:5]
last_row = df_fields.iloc[[-1]]
df_fields_2 = pd.concat([first_four, last_row])
with pd.ExcelWriter('data/weapons.xlsx', engine='openpyxl') as writer:
    df_res.to_excel(
        writer,
        sheet_name='data',
        index=False
    )
    df_fields.to_excel(
        writer,
        sheet_name='fields',
        index=False
    )
with pd.ExcelWriter('data/weapons_box.xlsx', engine='openpyxl') as writer:
    df_res_2.to_excel(
        writer,
        sheet_name='data',
        index=False
    )
    df_fields_2.to_excel(
        writer,
        sheet_name='fields',
        index=False
    )
sc = ''
for s in sorted(list(set(df_res["Slot"]))):
    sc+=s+':\n\t'
    for c in sorted(list(set(df_res[df_res["Slot"]==s]["Class"]))):
        sc+=c+','
    sc+='\n'
    sc = sc.replace(',\n','\n')

with open("data/sc.txt", "w", encoding="utf-8") as f:
    f.write(sc)

df_res_light = df_res[df_res["Orginal"]==True][["Class","Slot","VarInfo"]]
df_res_light["Slot"] = df_res_light.apply(lambda row:row["Slot"] if row["Slot"] not in ["曲翼枪械","曲翼近战","重型武器"] else "曲翼武器",axis=1)
df_res_light["Slot"] = df_res_light.apply(lambda row:row["Slot"] if row["Slot"] not in ["机器","猎犬","同伴"] else "同伴",axis=1)
df_fields_light = pd.DataFrame()
df_fields_light.loc[:,"name"] = list(df_res_light.columns)
df_fields_light.loc[:,"type"] = ["string" if c!="Orginal" else "boolean" for c in list(df_res_light.columns)]
df_fields_light.loc[:,"title_zh"] = ['']*len(list(df_res_light.columns))
df_fields_light.loc[:,"title_en"] = list(df_res_light.columns)

with pd.ExcelWriter('data/weapons_light.xlsx', engine='openpyxl') as writer:
    df_res_light.to_excel(
        writer,
        sheet_name='data',
        index=False
    )
    df_fields_light.to_excel(
        writer,
        sheet_name='fields',
        index=False
    )
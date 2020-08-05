#!/usr/bin/env python
# encoding: utf-8
"""
@author: Dong Jun
@file: number_extract.py
@time: 2019/11/28 3:19 下午
"""

import re


class NumberExtract():
    digit = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0, '两': 2, '半':0.5}
    digit_unit = {'个': 1, '十': 10, '百': 100, '千': 1000, '万': 10000, '亿': 100000000}
    digit_list = [i for i in digit.keys()]
    digit_unit_list = [j for j in digit_unit.keys()]

    @classmethod
    def unitchar2num_lower(cls, s):
        num = 0
        if s:
            idx_q, idx_b, idx_s, idx_one = s.find('千'), s.find('百'), s.find('十'), s.find('个')
            if idx_q != -1:
                num += NumberExtract.digit[s[idx_q - 1:idx_q]] * 1000
            if idx_b != -1:
                num += NumberExtract.digit[s[idx_b - 1:idx_b]] * 100
            if idx_s != -1:
                num += NumberExtract.digit.get(s[idx_s - 1:idx_s], 1) * 10
            if idx_one != -1 and s.index('个')>0 and s[s.index('个')-1] not in NumberExtract.digit_unit_list:
                num += NumberExtract.digit.get(s[idx_one - 1:idx_one], 1) * 1
            if s[-1] in NumberExtract.digit:
                num += NumberExtract.digit[s[-1]]
        return num


    @classmethod
    def unitchar2num(cls, detect_char):
        detect_char = detect_char.replace('零', '')
        idx_y, idx_w = detect_char.rfind('亿'), detect_char.rfind('万')
        if idx_w < idx_y:
            idx_w = -1
        num_y, num_w = 100000000, 10000
        if idx_y != -1 and idx_w != -1:
            return cls.unitchar2num(detect_char[:idx_y]) * num_y + \
                   cls.unitchar2num_lower(detect_char[idx_y + 1:idx_w]) * \
                   num_w + cls.unitchar2num_lower(detect_char[idx_w + 1:])
        elif idx_y != -1:
            return cls.unitchar2num(detect_char[:idx_y]) * num_y + cls.unitchar2num_lower(detect_char[idx_y + 1:])
        elif idx_w != -1:
            return cls.unitchar2num_lower(detect_char[:idx_w]) * num_w + cls.unitchar2num_lower(detect_char[idx_w + 1:])
        return cls.unitchar2num_lower(detect_char)


    @classmethod
    def base_transfer(cls, detect_char):
        # 最基本的汉字数字转换方法，如果无单位就直接拼接，如果有单位就按单位计算
        rule_of_number = "({})+".format("|".join(NumberExtract.digit_unit_list))
        if not re.search(rule_of_number, detect_char):
            char_new = detect_char
            for k,v in NumberExtract.digit.items():
                char_new = re.sub(k, str(v), char_new)
        elif detect_char=="百" or detect_char=="千" or detect_char=="万" or detect_char=="亿":
            char_new = str(NumberExtract.digit_unit.get(detect_char))
        else:
            char_new = str(cls.unitchar2num(detect_char))
        return char_new


    @classmethod
    def decimal_transfer(cls, detect_char):
        integer_char, decimal_char = detect_char.split("点")
        integer_num, decimal_num = cls.base_transfer(integer_char), cls.base_transfer(decimal_char)
        decimal_num = int(decimal_num)/(10**len(decimal_num))
        number = int(integer_num) + decimal_num
        return str(number)


    @classmethod
    def fraction_transfer(cls, detect_char):
        denominator_char, numerator_char = detect_char.split("分之")
        numerator, denominator = cls.base_transfer(numerator_char), cls.base_transfer(denominator_char)
        fraction_num = int(numerator)/int(denominator)
        return str(fraction_num)


    @classmethod
    def integer_detect(cls, query):
        number_list = NumberExtract.digit_list
        number_list_unit = number_list + NumberExtract.digit_unit_list
        rule_of_number = "({})+".format("|".join(number_list_unit))
        char_new = query
        while re.search(rule_of_number, char_new):
            detect_char = re.search(rule_of_number, char_new).group()
            ArabicNumerals = cls.base_transfer(detect_char)
            char_new = re.sub(detect_char, ArabicNumerals, char_new, count=1)
        return char_new


    @classmethod
    def decimal_detect(cls, query):
        number_list = NumberExtract.digit_list
        rule_of_number = "({0})+点({0})+".format("|".join(number_list))
        char_new = query
        while re.search(rule_of_number, char_new):
            detect_char = re.search(rule_of_number, char_new).group()
            ArabicNumerals = cls.decimal_transfer(detect_char)
            char_new = re.sub(detect_char, ArabicNumerals, char_new, count=1)
        return char_new


    @classmethod
    def fraction_detect(cls, query):
        number_list = NumberExtract.digit_list
        number_list_unit = number_list + NumberExtract.digit_unit_list
        rule_of_number = "({0})+分之({0})+".format("|".join(number_list_unit))
        char_new = query
        while re.search(rule_of_number, char_new):
            detect_char = re.search(rule_of_number, char_new).group()
            ArabicNumerals = cls.fraction_transfer(detect_char)
            char_new = re.sub(detect_char, ArabicNumerals, char_new, count=1)
        return char_new

    @classmethod
    def unit_mix_detect(cls, query):
        mix_rule = r"(?P<base_num>(\d+(.\d+)?))" \
                   r"(?P<base_unit>(万亿|千亿|百亿|十亿|亿|千万|百万|十万|万|千|百))" \
                   r"(?P<res_num>(\d+))?"
        char_new = query
        while re.search(mix_rule, char_new):
            mix_content = re.search(mix_rule, char_new)
            base_num = mix_content.group("base_num")
            base_unit = mix_content.group("base_unit")
            if mix_content.group("res_num"):
                res_num = mix_content.group("res_num")
            else:
                res_num = "0"
            base_unit_num = cls.unitchar2num("".join(["一", base_unit]))
            mix_num = float(base_num) * float(base_unit_num) + \
                      float(res_num) * float(base_unit_num) * 10**(-len(res_num))
            char_new = re.sub(mix_rule, str(mix_num), char_new)
        return char_new

    @classmethod
    def detect(cls, query):
        try:
            char_new = cls.decimal_detect(query)
            char_new = cls.fraction_detect(char_new)
            char_new = cls.unit_mix_detect(char_new)
            char_new = cls.integer_detect(char_new)
            return char_new
        except:
            return query



if __name__ == '__main__':
    # print(NumberExtract.detect("这里有三百个人和两辆汽车，每年增长率百分之三十二，共需要17万58小时"))
    # print(NumberExtract.detect("我想订明天中午12点的餐馆，三个人，走路一千多米能到，17.5万元以内，预留手机号为18619994211，明天23摄氏度"))
    print(NumberExtract.detect("三分之一"))




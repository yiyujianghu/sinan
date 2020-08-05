#!/usr/bin/env python
# encoding: utf-8
"""
@author: Dong Jun
@file: rules_of_number.py
@time: 2019/12/1 5:28 下午
"""

import re


class Rule_Method():
    @classmethod
    def dt_cal_str(cls, dt_calculate_dict):
        try:
            dt_calculate_str = {}
            for k,v in dt_calculate_dict.items():
                dt_k_str = "|".join(sorted([i for i in v.keys() if i != "std"], key=lambda x: len(x), reverse=True))
                dt_calculate_str[k] = dt_k_str
            return dt_calculate_str
        except:
            return {}

    @classmethod
    def unit_merge(cls, measure_str):
        if isinstance(measure_str, dict):
            return "|".join(measure_str.values())
        else:
            return ""

    @classmethod
    def generate_measure_rule(cls, measure_convert_dict, measure_str):
        rule_template = "(?P<unit>([0-9]+(\.[0-9]+)?)多?({unit}))"
        rule_list = []
        for k in measure_convert_dict.keys():
            unit_rule = rule_template.replace("unit", k)
            rule_list.append(unit_rule)
        unit_rules_str = "|".join(rule_list)
        return unit_rules_str.format(**measure_str)


class Rules_of_Number():
    # 常见的计量单位及同义词转换
    measure_convert_dict = {
            "length": {"米":1, "m":1, "千米":1000, "公里":1000, "km":1000, "里":500,
                        "厘米":0.01, "cm":0.01, "毫米":0.001, "mm":0.001, "std":"m"},
            "weight": {"千克":1, "kg":1, "公斤":1, "斤":0.5, "克":0.001, "g":0.001, "std":"kg"},
            "time": {"秒":1, "s":1, "小时":3600, "h":3600, "分钟":60, "min":60, "std":"s"},
            "temperature": {"摄氏度":1, "度":1, "℃":1, "std":"℃"},
            "money": {"元":1, "块":1, "元钱":1, "块钱":1, "角":0.1, "分":0.01, "分钱":0.01, "万元":10000, "std":"元"},
            "people": {"人":1, "位":1, "std":"人"},
        }

    measure_str = Rule_Method.dt_cal_str(measure_convert_dict)
    measure_all_str = Rule_Method.unit_merge(measure_str)
    measure_rule = Rule_Method.generate_measure_rule(measure_convert_dict, measure_str)

    # 特殊时间表达"如：差一刻三点"的汉字正则规则
    re_zh_num = {"1-4": "[一二三四]",
                 "1-5": "[一二三四五]",
                 "1-7": "[一二三四五六日]",
                 "1-9": "[一二三四五六七八九十]",
                 "0-9": "[零一二三四五六七八九十]",
                 "0-9-2": "[零一二三四五六七八九十两]"
                 }

    time_special_rule_subtract_front = \
        r"差(一刻|((({1-5}?十{1-9}?)|(零?{0-9}))分))((二十{0-9}?)|(十{1-9}?)|{0-9-2})点".format(**re_zh_num)
    time_special_rule_subtract_back = \
        r"((二十{1-4}?)|(十{1-9}?)|{0-9-2})点差(一刻|((({1-5}?十{1-9}?)|(零?{0-9}))分?))".format(**re_zh_num)
    time_special_rule_plus = \
        r"((二十{1-4}?)|(十{1-9}?)|{0-9-2})点(半|一刻|三刻|((({1-5}?十{1-9}?)|(零?{0-9}))分?))?".format(**re_zh_num)

    # 日期推算，时辰/日/周/月/年
    dt_calculate_dict = {"years":{"大前年":-3, "前年":-2, "去年":-1, "上一年":-1, "今年":0, "明年":1, "后年":2, "default":0},
                         "months":{"上个月":-1, "上月":-1, "这个月":0, "这月":0, "本月":0, "下个月":1, "下月":1, "default":0},
                         "weeks":{"上上周":-2, "上周":-1, "上个周":-1, "这周":0, "本周":0, "下周":1, "下个周":1, "下下周":2,
                                    "上星期":-1, "上个星期":-1, "星期":0, "这星期":0, "这个星期":0, "下个星期":1, "下星期":1, "default":0},
                         "days":{"大前天":-3, "前天":-2, "前一天":-1, "昨天":-1, "昨日":-1,
                                 "今天":0, "今日":0, "现在":0,
                                 "明天":1, "明日":1, "后天":2, "大后天":3, "default":0},
                         "time_interval":{"凌晨":2, "清晨":6, "早晨":7, "上午":9, "中午":12, "午后":13, "下午":15,
                                          "傍晚":18, "晚上":19, "深夜":23, "default":-1}}

    dt_calculate_str = Rule_Method.dt_cal_str(dt_calculate_dict)
    dt_calculate_str["number"] = r"[0-9一二三四五六七八九十两百千万]"

    dt_calculate_rule = r"((?P<years>({years})的*)|" \
                        r"(?P<year_offset>({number}+年[之以]?[前后])|(过了{number}+年))|" \
                        r"(?P<months>({months})的*)|" \
                        r"(?P<month_offset>({number}+个?月[之以]?[前后])|(过了{number}+个?月))|" \
                        r"((?P<weeks>({weeks})的?)(?P<week_value>((周|星期)?[一二三四五六日]*的?)))|" \
                        r"(?P<week_offset>({number}+(周|星期)[之以]?[前后])|(过了{number}+(周|星期)))|" \
                        r"(?P<days>({days})的*)|" \
                        r"(?P<day_offset>({number}+天[之以]?[前后])|(过了{number}+天))|" \
                        r"(?P<time_interval>({time_interval})的*)|" \
                        r"(?P<hour_offset>({number}+小时[之以]?[前后])|(过了{number}+小时))|" \
                        r"(?P<minute_offset>({number}+分钟[之以]?[前后])|(过了{number}+分钟))|" \
                        r"(?P<second_offset>({number}+秒[之以]?[前后])|(过了{number}+秒)))+".format(**dt_calculate_str)

    # 所有的数字类型年月日时的正则规则，采用?P<group>提取时间并考虑六个参数都存在的情况
    datetime_dict = {'year_number': r"(19\d{2})|(20\d{2})",
                     'month_number': r"(1[0-2])|(0?[1-9])",
                     'day_number': r"(3[0-1])|([1-2][0-9])|(0?[1-9])",
                     'hour_number': r"(20|21|22|23|([0-1]?\d))",
                     'min_sec_number': r"[0-5]?\d",
                     'measure_all_str':measure_all_str
                     }

    date_point_ymd = r"((?P<year>({year_number}))(\.)" \
                     r"(?P<month>({month_number}))(\.)" \
                     r"(?P<day>({day_number})))".format(**datetime_dict)

    date_ymd_join = r"(?P<year>({year_number}))" \
                    r"(?P<month>({month_number}))" \
                    r"(?P<day>({day_number}))".format(**datetime_dict)

    date_ymd = r"(?P<year>({year_number})[-/年])" \
               r"(?P<month>({month_number})[-/月]?)" \
               r"(?P<day>({day_number})*[日号]?)".format(**datetime_dict)

    date_md = r"(?P<year>)" \
              r"(?P<month>({month_number})[-/月])" \
              r"(?P<day>({day_number})*[日号]?)".format(**datetime_dict)

    date_d = r"(?P<year>)" \
             r"(?P<month>)" \
             r"(?P<day>({day_number})[日号])".format(**datetime_dict)

    time_std = r"(?P<hour>({hour_number})[:点时])" \
               r"(?P<minute>({min_sec_number})*[:分]*)" \
               r"(?P<second>({min_sec_number})*秒*)".format(**datetime_dict)

    MASK_RULE = r"((?P<cal_mask>(MASK_DT_CAL_I+_)的?)|" \
                r"(?P<date_mask>(MASK_DATE_I+_)的?)|" \
                r"(?P<time_mask>(MASK_TIME_I+_)的?))+"

    phone_rule = r"(?<!\d)1[3456789]\d{9}(?!\d)"

    identification_card_rule = r"(?<!\d)[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])" \
                                    r"|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9XxAa](?!\d)|" \
                               r"(?<!\d)[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])" \
                                    r"|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9XxAa](?!\d)|" \
                               r"(?<!\d)[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])" \
                                    r"|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}(?!\d)|" \
                               r"(?<!\d)[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])" \
                                    r"|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}(?!\d)"
                               # 共考虑了四种情况，18位非闰年，18位闰年，15位非闰年，15位闰年



if __name__ == "__main__":
    query = "去年的一天"
    print(re.search(Rules_of_Number.dt_calculate_rule, query).group())

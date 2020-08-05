# -*-conding:utf-8-*-
# Base Information:
# @author:      yiyujianghu
# @project:     <Learning-More>
# @file:        test_all_function.py
# @time:        2020/8/4 4:51 下午

"""
Notes:...
"""

from datetime import datetime
import unittest
from sinan import Sinan


class TestFunction(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def date_calculate(self, input_text):
        parse = Sinan(input_text, source_DT=datetime(2000, 8, 8, 12, 30, 30))
        parse.parse(display_status=False)
        result = parse.result.get("datetime")
        if not result:
            return f"{input_text} 为未识别日期"
        elif len(result) == 1:
            return result[0]
        else:
            return result

    def other_info_calculate(self, input_text, unit_info):
        parse = Sinan(input_text)
        parse.parse(display_status=False)
        result = parse.result.get(unit_info)
        if not result:
            return f"{input_text} 为未识别信息"
        elif len(result) == 1:
            return result[0]
        else:
            return result


    def test_date(self):
        input_texts = [
            "当前时间是2003年5月8日",
            "当前时间是二零零三年五月八日",
            "当前时间是2003.5.8",
            "当前时间是2003-5-8",
            "当前时间是2003/5/8",
            "当前时间是2003年5月",
            "当前时间是20030508",
            "当前时间是二零零三年五月",
            "当前时间是5月8日",
            "当前时间是5月8号",
            "当前时间是8号",
            "当前时间是20031211"
        ]

        target_results = [
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2003-05-08 12:30:30",
            "2000-05-08 12:30:30",
            "2000-05-08 12:30:30",
            "2000-08-08 12:30:30",
            "2003-12-11 12:30:30",
        ]
        for text, target in zip(input_texts, target_results):
            self.assertEqual(self.date_calculate(text), target)

    def test_time(self):
        input_texts = [
            "当前时间是8:27:51",
            "当前时间是8:27",
            "当前时间是8点27分51秒",
            "当前时间是8点27分",
            "当前时间是1999年12月31日23点59分59秒",
            "当前时间是1999.12.31的23:59:59",
        ]

        target_results = [
            "2000-08-08 08:27:51",
            "2000-08-08 08:27:30",
            "2000-08-08 08:27:51",
            "2000-08-08 08:27:30",
            "1999-12-31 23:59:59",
            "1999-12-31 23:59:59",
        ]
        for text, target in zip(input_texts, target_results):
            self.assertEqual(self.date_calculate(text), target)

    def test_dt_infer(self):
        input_texts = [
            "昨天下午差一刻两点的时候",
            "去年今天的下午一点半",
            "上周五晚上的八点十分",

            "两年之前",
            "两月之前",
            "两周之前",
            "两天之前",
            "两小时之前",
            "两分钟之前",

            "又过了两年",
            "又过了两月",
            "又过了两星期",
            "又过了两天",
            "又过了两小时",
            "又过了两分钟",
        ]

        target_results = [
            "2000-08-07 13:45:30",
            "1999-08-09 13:30:30",
            "2000-08-04 20:10:30",

            "1998-08-09 12:30:30",
            "2000-06-09 12:30:30",
            "2000-07-25 12:30:30",
            "2000-08-06 12:30:30",
            "2000-08-08 10:30:30",
            "2000-08-08 12:28:30",

            "2002-08-08 12:30:30",
            "2000-10-07 12:30:30",
            "2000-08-22 12:30:30",
            "2000-08-10 12:30:30",
            "2000-08-08 14:30:30",
            "2000-08-08 12:32:30",

        ]
        for text, target in zip(input_texts, target_results):
            self.assertEqual(self.date_calculate(text), target)

    def test_phone_num(self):
        input_texts = [
            ("我的手机号是13896207575哈", "phone_num"),
            ("我的身份证号是140107199810109876哈", "identification")
        ]

        target_results = [
            "13896207575",
            "140107199810109876",
        ]
        for text, target in zip(input_texts, target_results):
            self.assertEqual(self.other_info_calculate(*text), target)


if __name__ == "__main__":
    unittest.main()

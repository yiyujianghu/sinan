from datetime import datetime
from decimal import Decimal
import unittest

from sinan import Sinan
from sinan.number_extract import parse_number


class NumberTests(unittest.TestCase):
    def test_numeric_forms(self):
        cases = {
            "壹仟贰佰伍拾捌點貳": "1258.2",
            "一千零二": "1002",
            "九百五": "950",
            "廿三": "23",
            "兩萬零柒": "20007",
            "一亿两千三百四十五万六千七百八十九": "123456789",
            "一万亿": "1000000000000",
            "17万58": "175800",
            "3万5千": "35000",
            "三点五万六千": "41000",
            "１，２３４．５０": "1234.50",
            ".５": "0.5",
            "负四分之三": "-0.75",
            "三点半": "3.5",
            "１／４": "0.25",
            "−2.5e-3": "-0.0025",
            "零下十八": "-18",
        }
        for spelling, expected in cases.items():
            with self.subTest(spelling=spelling):
                self.assertEqual(parse_number(spelling), Decimal(expected))

    def test_malformed_numbers(self):
        for spelling in ("", "1,23", "1.2.3", "0分之一", "1/0", "十十", "一万万", "1e999", "1" * 129):
            with self.subTest(spelling=spelling):
                with self.assertRaises(ValueError):
                    parse_number(spelling)


class QuantityTests(unittest.TestCase):
    def check(self, text, expected):
        result = Sinan(text, source_DT=datetime(2000, 8, 8, 12, 30, 30)).parse(False)
        self.assertEqual(result, expected)

    def test_number_and_unit_variants(self):
        cases = (
            ("約壹仟貳佰公尺、1,200.5 km", {"length": [[1200.0, "m"], [1200500.0, "m"]]}),
            ("四分之三公斤、1/2斤、半吨", {"weight": [[0.75, "kg"], [0.25, "kg"], [500.0, "kg"]]}),
            ("1.5e3Pa，５ｋＰａ", {"pressure": [[1500.0, "Pa"], [5000.0, "Pa"]]}),
            ("千余人、半个人、三位客人", {"people": [[1000.0, "人"], [0.5, "人"], [3.0, "人"]]}),
            ("三萬多元，3.5万块，人民币１，２３４元", {"money": [[30000., "元"], [35000., "元"], [1234., "元"]]}),
            ("三册书、四臺电脑、五輛車、六歲", {"count": [[3., "册"], [4., "台"], [5., "辆"], [6., "岁"]]}),
            ("3点半小时、一个半小时、半个小时、一天半", {"time": [[12600., "s"], [5400., "s"], [1800., "s"], [129600., "s"]]}),
            ("半个月、两个半月、三年六个月", {"duration": [[0.5, "月"], [2.5, "月"], [42., "月"]]}),
            ("3％、2‰、1‱、50ppm、五個百分點", {"ratio": [[3., "%"], [0.2, "%"], [0.01, "%"], [0.005, "%"], [5., "%"]]}),
            ("百分之五、千分之八、萬分之二", {"ratio": [[5., "%"], [0.8, "%"], [0.02, "%"]]}),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.check(text, expected)

    def test_longest_units_and_unit_case(self):
        self.check("五分贝、5m、5ms、5m²、5m^3、5MB、5Mb、5Mbps、5MB/s", {
            "sound": [[5., "dB"]],
            "length": [[5., "m"]],
            "time": [[0.005, "s"]],
            "area": [[5., "m²"]],
            "volume": [[5000., "L"]],
            "data": [[5000000., "B"], [625000., "B"]],
            "data_rate": [[5000000., "bit/s"], [40000000., "bit/s"]],
        })
        self.check("每段36公里每小时、瞬时5m/s²，质量浓度2g/L", {
            "speed": [[10., "m/s"]],
            "acceleration": [[5., "m/s²"]],
            "concentration": [[2000., "mg/L"]],
        })
        self.check("电池5000mAh、充电20W、3kWh、频率2GHz", {
            "charge": [[18000., "C"]],
            "power": [[20., "W"]],
            "energy": [[10800000., "J"]],
            "frequency": [[2000000000., "Hz"]],
        })

    def test_compound_quantities(self):
        self.check("两小时三十分五秒、三块五角八分、三升500毫升、三公里又两百米、一斤半", {
            "time": [[9005., "s"]], "money": [[3.58, "元"]], "volume": [[3.5, "L"]],
            "length": [[3200., "m"]], "weight": [[0.75, "kg"]],
        })
        self.check("两分三秒、身高一米七五、三块五，五克拉", {
            "time": [[123., "s"]], "length": [[1.75, "m"]],
            "money": [[3.5, "元"]], "weight": [[0.001, "kg"]],
        })
        self.check("3米，30厘米；3米\n30厘米；三块五公斤", {
            "length": [[3., "m"], [0.3, "m"], [3., "m"], [0.3, "m"]],
            "money": [[3., "元"]], "weight": [[5., "kg"]],
        })

    def test_signed_affine_currency_and_ranges(self):
        self.check("零下五度、正三度、华氏32°F、212℉和273.15K", {
            "temperature": [[-5., "℃"], [3., "℃"], [0., "℃"], [100., "℃"], [0., "℃"]],
        })
        self.check("￥3.5元、HK$200、US$500、50欧元", {
            "money": [[3.5, "元"], [200., "HKD"], [500., "USD"], [50., "EUR"]],
        })
        self.check("两三公里，三到五米，3米-5厘米，-5--3℃，35～40°C，百分之三到五", {
            "length": [[2000., "m"], [3000., "m"], [3., "m"], [5., "m"], [3., "m"], [0.05, "m"]],
            "temperature": [[-5., "℃"], [-3., "℃"], [35., "℃"], [40., "℃"]],
            "ratio": [[3., "%"], [5., "%"]],
        })
        self.check("百分之三到百分之五", {"ratio": [[3., "%"], [5., "%"]]})

    def test_context_and_reserved_clock_spans(self):
        self.check("旋转九十度，耗电五度，今天二十五度，考了八十五分，兩塊石頭，价格五分", {
            "angle": [[90., "°"]], "energy": [[18000000., "J"]], "temperature": [[25., "℃"]],
            "datetime": ["2000-08-08 12:30:30"],
            "score": [[85., "分"]], "count": [[2., "块"]], "money": [[0.05, "元"]],
        })
        self.check("八点二十分三秒、8:27分51秒、五点五秒、五点三厘米、两小时前", {
            "datetime": ["2000-08-08 08:20:03", "2000-08-08 08:27:51", "2000-08-08 10:30:30"],
            "time": [[5.5, "s"]], "length": [[0.053, "m"]],
        })
        self.check("2024年5月8日买了两箱牛奶、手机号13896207575、身份证140107199810109876", {
            "datetime": ["2024-05-08 12:30:30"], "count": [[2., "箱"]],
            "phone_num": ["13896207575"], "identification": ["140107199810109876"],
        })
        self.check("13896207575元和2024010112kg", {
            "money": [[13896207575., "元"]], "weight": [[2024010112., "kg"]],
        })

    def test_false_positives_and_invalid_input_are_isolated(self):
        self.check("一块儿、三角形、三里屯、一条龙、一分为二、二位小数、第一台、三人行、"
                   "五克隆、五米饭、x20kg、20kgabc、1.2.3kg、1,23kg、零分之一公斤", {})
        self.check("1/0公斤，1e308吨，五公斤，春天一切正常", {"weight": [[5., "kg"]]})
        self.check("a2-3kg、4-5-6kg、MASK_DATE_I_、过了9999999999999年、1米5 厘米", {
            "length": [[1.05, "m"]],
        })

    def test_repeated_parse_replaces_results(self):
        parser = Sinan("五公斤，五公斤")
        first = parser.parse(False)
        self.assertEqual(first, {"weight": [[5., "kg"], [5., "kg"]]})
        self.assertEqual(parser.parse(False), first)
        parser.content = "三升"
        self.assertEqual(parser.parse(False), {"volume": [[3., "L"]]})
        self.assertEqual(first, {"weight": [[5., "kg"], [5., "kg"]]})

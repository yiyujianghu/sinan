"""Extract quantities and normalize their units without modifying the source text."""

import math
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext

from sinan.number_extract import ARABIC, CHINESE_NUMBER, NUMBER, SCALAR, NumberExtract, parse_number


@dataclass(frozen=True)
class Unit:
    kind: str
    symbol: str
    factor: Decimal
    offset: Decimal = Decimal(0)


# Each row lists a result key, canonical unit, and input aliases grouped by factor.
# Unit symbols are case-sensitive (MB and Mb, for example).
COUNT_TRANSLATION = str.maketrans("個臺冊輛張隻條雙對組顆層頁場歲樓級塊", "个台册辆张只条双对组颗层页场岁楼级块")
UNIT_GROUPS = (
    ("length", "m", (
        ("1", "米 公尺 m"), ("1e3", "千米 公里 km 公裡"), ("500", "里"),
        ("0.01", "厘米 公分 cm"), ("0.001", "毫米 mm"), ("0.1", "分米 dm"),
        ("1e-6", "微米 μm µm um"), ("1e-9", "纳米 納米 nm"), ("1e-12", "皮米 pm"),
        ("0.0254", "英寸 吋 in"), ("0.3048", "英尺 呎 ft"), ("0.9144", "码 碼 yd"),
        ("1609.344", "英里 mi"), ("1852", "海里 海浬 nmi"),
        ("0.333333333333333333", "市尺 尺"), ("0.033333333333333333", "市寸 寸"),
    )),
    ("area", "m²", (
        ("1", "平方米 平方公尺 平米 m² m2 m^2 ㎡"),
        ("1e6", "平方公里 平方公裡 平方千米 km² km2 km^2"),
        ("1e-4", "平方厘米 cm² cm2 cm^2"), ("1e-6", "平方毫米 mm² mm2 mm^2"),
        ("1e4", "公顷 公頃 ha"), ("100", "公亩 公畝"), ("666.666666666666666667", "亩 畝"),
        ("4046.8564224", "英亩 英畝 acre"), ("0.09290304", "平方英尺 ft² ft2 ft^2"),
    )),
    ("volume", "L", (
        ("1", "升 公升 L l"), ("0.001", "毫升 mL ml cc 立方厘米 cm³ cm3 cm^3"),
        ("1e-6", "微升 μL µL uL"), ("1000", "立方米 立方公尺 m³ m3 m^3 ㎥ 方"),
        ("1e-3", "立方公分"), ("0.01", "厘升 cL cl"), ("0.1", "分升 dL dl"),
        ("3.785411784", "美制加仑 美制加侖"), ("4.54609", "英制加仑 英制加侖"),
    )),
    ("weight", "kg", (
        ("1", "千克 公斤 kg"), ("0.001", "克 公克 g"), ("0.5", "市斤 斤"),
        ("0.05", "市两 两 兩"), ("1000", "吨 噸 公吨 公噸 t"),
        ("1e-6", "毫克 mg"), ("1e-9", "微克 μg µg ug"), ("1e-12", "纳克 納克 ng"),
        ("0.0002", "克拉 ct"), ("0.45359237", "磅 lb lbs"), ("0.028349523125", "盎司 oz"),
    )),
    ("time", "s", (
        ("1", "秒 秒钟 秒鐘 s sec"), ("60", "分钟 分鐘 min"), ("900", "刻钟 刻鐘"),
        ("3600", "小时 小時 钟头 鐘頭 h hr"), ("86400", "天 d"),
        ("604800", "周 週 星期 礼拜 禮拜 wk"), ("1e-3", "毫秒 ms"),
        ("1e-6", "微秒 μs µs us"), ("1e-9", "纳秒 納秒 ns"),
    )),
    ("duration", "月", (("1", "个月 個月"), ("3", "季度"), ("12", "年 年度"))),
    ("temperature", "℃", (("1", "摄氏度 攝氏度 摄氏 攝氏 °C ℃ 度"),)),
    ("money", "元", (
        ("1", "人民币 人民幣 人民币元 人民幣元 元钱 元錢 块钱 塊錢 元 块 塊 圆 圓 CNY RMB"),
        ("0.1", "角 毛 毛钱 毛錢"), ("0.01", "分钱 分錢 分"),
    )),
    ("money", "USD", (("1", "美元 美金 USD"),)),
    ("money", "EUR", (("1", "欧元 歐元 EUR"),)),
    ("money", "GBP", (("1", "英镑 英鎊 GBP"),)),
    ("money", "JPY", (("1", "日元 日圆 日圓 JPY"),)),
    ("money", "HKD", (("1", "港元 港币 港幣 HKD"),)),
    ("money", "TWD", (("1", "新台币 新臺幣 TWD"),)),
    ("money", "KRW", (("1", "韩元 韓元 KRW"),)),
    ("people", "人", (("1", "人 人次 名 位"),)),
    ("speed", "m/s", (
        ("1", "米/秒 米每秒 每秒米 米每秒钟 m/s m·s⁻¹"),
        ("0.277777777777777778", "公里/小时 公里/小時 公里每小时 公里每小時 千米每小时 km/h km/hr kph"),
        ("0.44704", "英里每小时 mph"), ("0.514444444444444444", "节速度 節速度"),
    )),
    ("acceleration", "m/s²", (("1", "米每二次方秒 米每平方秒 m/s² m/s2 m/s^2"),)),
    ("flow", "L/s", (("1", "升每秒 L/s"), ("1000", "立方米每秒 m³/s m3/s"))),
    ("density", "kg/m³", (("1", "千克每立方米 kg/m³ kg/m3"), ("1000", "克每立方厘米 g/cm³ g/cm3"))),
    ("concentration", "mg/L", (("1", "毫克每升 mg/L mg/l"), ("1000", "克每升 g/L g/l"))),
    ("pressure", "Pa", (
        ("1", "帕 帕斯卡 Pa"), ("1000", "千帕 kPa"), ("1e6", "兆帕 MPa"),
        ("100", "百帕 hPa 毫巴 mbar"), ("1e5", "巴 bar"),
        ("101325", "标准大气压 標準大氣壓 atm"), ("133.322387415", "毫米汞柱 mmHg"),
        ("6894.757293168", "磅每平方英寸 psi"),
    )),
    ("force", "N", (("1", "牛顿 牛頓 N"), ("1000", "千牛 千牛顿 千牛頓 kN"))),
    ("power", "W", (("1", "瓦 瓦特 W"), ("1e3", "千瓦 kW"), ("1e6", "兆瓦 MW"), ("1e-3", "毫瓦 mW"))),
    ("energy", "J", (
        ("1", "焦 焦耳 J"), ("1000", "千焦 千焦耳 kJ"), ("1e6", "兆焦 MJ"),
        ("4.184", "卡路里 cal"), ("4184", "千卡 大卡 kcal"),
        ("3600", "瓦时 瓦時 Wh"), ("3600000", "千瓦时 千瓦時 kWh kW·h 度电 度電"),
    )),
    ("voltage", "V", (("1", "伏 伏特 V"), ("1000", "千伏 kV"), ("0.001", "毫伏 mV"))),
    ("current", "A", (("1", "安 安培 A"), ("0.001", "毫安 mA"), ("1e-6", "微安 μA µA uA"))),
    ("charge", "C", (("1", "库仑 庫侖 C"), ("3600", "安时 安時 Ah"), ("3.6", "毫安时 毫安時 mAh"))),
    ("resistance", "Ω", (("1", "欧姆 歐姆 Ω"), ("1000", "千欧 千歐 kΩ"), ("1e6", "兆欧 兆歐 MΩ"))),
    ("frequency", "Hz", (
        ("1", "赫 赫兹 赫茲 Hz"), ("1e3", "千赫 千赫兹 kHz"), ("1e6", "兆赫 兆赫兹 MHz"),
        ("1e9", "吉赫 吉赫兹 GHz"),
    )),
    ("angle", "°", (("1", "度角 °"), ("57.29577951308232", "弧度 rad"), ("0.01666666666666667", "角分 ′"), ("0.00027777777777778", "角秒 ″"))),
    ("data", "B", (
        ("1", "字节 字節 B"), ("0.125", "比特 bit b"), ("1000", "KB kB 千字节 千字節"),
        ("1e6", "MB 兆字节 兆字節"), ("1e9", "GB"), ("1e12", "TB"),
        ("1024", "KiB"), ("1048576", "MiB"), ("1073741824", "GiB"), ("1099511627776", "TiB"),
        ("125", "Kb kb kbit"), ("125000", "Mb Mbit"), ("125000000", "Gb Gbit"),
    )),
    ("data_rate", "bit/s", (
        ("1", "比特每秒 bit/s bps"), ("1000", "kbps Kbps kb/s"), ("1e6", "Mbps Mb/s"),
        ("1e9", "Gbps Gb/s"), ("8", "B/s"), ("8000", "KB/s kB/s"),
        ("8e6", "MB/s"), ("8e9", "GB/s"), ("8388608", "MiB/s"),
    )),
    ("ratio", "%", (("1", "% ％ 个百分点 個百分點 百分点 百分點"), ("0.1", "‰ 千分号"), ("0.01", "‱ bp 基点 基點"), ("0.0001", "ppm"), ("0.0000001", "ppb"))),
    ("sound", "dB", (("1", "分贝 分貝 dB"),)),
    ("illuminance", "lx", (("1", "勒克斯 lx"),)),
    ("luminous_flux", "lm", (("1", "流明 lm"),)),
    ("count", None, (("1", "个 個 件 台 臺 本 册 冊 辆 輛 架 艘 辆次 张 張 枚 支 枝 只 隻 条 條 双 雙 对 對 套 组 組 瓶 杯 箱 盒 袋 包 桶 罐 份 片 粒 颗 顆 滴 朵 块 塊 卷 碗 层 層 页 頁 次 遍 倍 场 場 回 岁 歲 楼 樓 级 級"),)),
)

UNITS = {
    alias: Unit(kind, symbol or alias.translate(COUNT_TRANSLATION), Decimal(factor))
    for kind, symbol, groups in UNIT_GROUPS
    for factor, aliases in groups
    for alias in aliases.split()
}
# 块 has a contextual count interpretation, with RMB as the legacy default.
UNITS["块"] = UNITS["塊"] = Unit("money", "元", Decimal(1))
UNITS["人次"] = Unit("people", "人次", Decimal(1))
for alias in ("华氏度", "華氏度", "华氏", "華氏", "℉", "°F"):
    UNITS[alias] = Unit("temperature", "℃", Decimal(5) / 9, Decimal(-32))
for alias in ("开尔文", "開爾文", "K"):
    UNITS[alias] = Unit("temperature", "℃", Decimal(1), Decimal("-273.15"))

ALIASES = "|".join(map(re.escape, sorted(UNITS, key=len, reverse=True)))
PREFIX_CURRENCIES = {
    "¥": "元", "￥": "元", "人民币": "元", "人民幣": "元", "CNY": "元", "RMB": "元",
    "US$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR", "£": "GBP", "GBP": "GBP",
    "HK$": "HKD", "港币": "HKD", "港幣": "HKD", "JPY": "JPY",
}
PREFIX = "|".join(map(re.escape, sorted(PREFIX_CURRENCIES, key=len, reverse=True)))
NUMBER_CHARS = ARABIC + CHINESE_NUMBER
# Avoid retrying at a suffix of a malformed number, date, identifier, or fraction.
LEFT = rf"(?<![{NUMBER_CHARS}A-Za-z_./／．])(?<![{ARABIC}][,，-])(?<!分之)"
SPACE = r"[^\S\r\n]*"
RANGE = rf"{SPACE}(?:到|至|[-－−–—~～]){SPACE}"
APPROXIMATE = r"(?:多|余|餘|来|來)"
QUANTITY = re.compile(
    rf"{LEFT}(?:(?P<lower>{NUMBER}){RANGE})?"
    rf"(?P<number>{NUMBER}){APPROXIMATE}?{SPACE}"
    rf"(?:(?P<month>[个個]半月)|(?:[个個](?=半?(?:小时|小時|钟头|鐘頭|星期|礼拜|禮拜|季度|人|百分点|百分點)))?(?P<half>半)?(?P<unit>(?>{ALIASES})))"
    rf"(?!分之|[/／])(?!(?<=[A-Za-z0-9])[A-Za-z_0-9])"
)
CURRENCY = re.compile(
    rf"(?<![A-Za-z_])(?P<prefix>{PREFIX}){SPACE}(?P<number>{NUMBER})"
    rf"(?:{SPACE}(?P<suffix>人民币元|人民幣元|元钱|元錢|块钱|塊錢|美元|欧元|歐元|英镑|港元|港币|港幣|日元|元|块|塊|圆|圓))?"
    rf"(?![{NUMBER_CHARS}A-Za-z_.．/／])"
)
RATIO = re.compile(
    rf"{LEFT}(?P<denominator>[百佰千仟万萬])分之(?P<number>{SCALAR})"
    rf"(?:{RANGE}(?P<upper>{SCALAR})(?!分之))?(?![{NUMBER_CHARS}.．点點])"
)
# Clock faces with an explicit minute/second component take priority over short
# aliases such as 分 and 秒. A standalone 小时 or 分钟 is a duration.
CLOCK = re.compile(
    rf"(?<![{NUMBER_CHARS}.．点點])"
    rf"(?:[{NUMBER_CHARS}]{{1,4}}[点點时時](?:半(?![小時钟鐘])|[一三]刻|[{NUMBER_CHARS}]{{1,4}}分(?![钟鐘之贝貝])(?:[{NUMBER_CHARS}]{{1,4}}秒(?![钟鐘]))?)"
    rf"|[{ARABIC}]{{1,2}}[:：][{ARABIC}]{{1,2}}(?:[:：分][{ARABIC}]{{1,2}})?(?:秒(?![钟鐘]))?)"
)
LEXICAL_SUFFIXES = {
    "里": ("屯", "河", "桥", "橋", "店", "庵", "路口", "山"),
    "块": ("板", "布", "石", "砖", "磚", "玻璃", "屏", "肉", "蛋糕", "豆腐", "木"),
    "方": ("面", "向", "形", "位", "言", "法", "圆", "圓"),
    "米": ("饭", "飯", "粉", "粥", "线", "線"),
    "克": ("隆", "拉"),
    "人": ("均", "称", "稱", "行"),
    "名": ("称", "稱", "字"),
    "位": ("小数", "小數", "数", "數"),
    "天": ("到晚",), "周": ("年", "刊"),
    "角": ("形", "度", "关系", "關係", "函数", "函數", "星"),
    "分": ("子", "母", "支", "析", "为", "為", "别", "別", "店", "钟", "鐘"),
    "毛": ("衣", "巾", "线", "線"),
    "元": ("素", "件", "旦", "组", "組", "气", "氣"),
    "条": ("龙", "龍"), "本": ("来", "來", "身"), "次": ("元", "方"), "只": ("要", "有", "是"),
    "度": ("过", "過", "假", "假村"), "个": ("别", "別", "性"),
}
SUFFIX_HALF = re.compile(r"(?:又)?半(?![径徑圆圓岛島场場天身球导導决決])")
RELATIVE_SUFFIX = re.compile(r"[之以]?[前后後]")
COMPOUND_KINDS = {"time", "duration", "length", "weight", "volume", "angle", "money"}
COLLOQUIAL_RANGE = re.compile(r"一[两兩二]|[二两兩]三|三四|四五|五六|六七|七八|八九")
SECONDS_AFTER_MINUTES = re.compile(rf"{SPACE}(?:又{SPACE})?{SCALAR}{SPACE}秒")
SPOKEN_REMAINDER = re.compile(r"[0-9零〇一二两兩三四五六七八九]{1,2}(?=$|[的,、。!?;：:）)\s])")
FOLLOWING_UNIT = re.compile(rf"{SPACE}(?:{ALIASES})")
SPOKEN_UNITS = {"米", "公尺", "块", "塊", "元", "角", "毛"}
FULLWIDTH_ASCII = str.maketrans({chr(code): chr(code - 0xFEE0) for code in range(0xFF01, 0xFF5F)})


@dataclass(frozen=True)
class Quantity:
    start: int
    end: int
    kind: str
    symbol: str
    values: tuple
    factor: Decimal


def _contextual_unit(alias, before, after, previous):
    canonical = alias.translate(COUNT_TRANSLATION)
    if after.startswith(LEXICAL_SUFFIXES.get(canonical, ())):
        if canonical == "块":
            return Unit("count", "块", Decimal(1))
        return None
    if canonical == "块" and after.startswith(("儿", "兒")):
        return None
    if alias == "分":
        if re.search(r"(?:得分|打分|评分|評分|成绩|成績|考了?|比分|总分|總分|满分|滿分)[^,，。；;!?]{0,5}$", before):
            return Unit("score", "分", Decimal(1))
        if ((previous and previous.kind == "time" and previous.factor > 60)
                or SECONDS_AFTER_MINUTES.match(after)
                or re.search(r"(?:用时|用時|耗时|耗時|计时|計時|时长|時長)[：: ]*$", before)):
            return Unit("time", "s", Decimal(60))
        if not (previous and previous.kind == "money" and previous.symbol == "元") and not re.search(
            r"(?:人民币|人民幣|钱|錢|价格|價格|售价|售價|零钱|零錢|\¥|￥)[：: ]*$", before
        ):
            return None
    if alias == "度":
        if re.search(r"(?:角度|夹角|夾角|旋转|旋轉|转动|轉動|转角|轉角|转了|轉了|倾斜|傾斜|经度|緯度|纬度|經度)[^,，。；;!?]{0,5}$", before):
            return UNITS["度角"]
        if re.search(r"(?:用电|用電|耗电|耗電|电量|電量|电费|電費)[^,，。；;!?]{0,5}$", before):
            return UNITS["度电"]
    return UNITS[alias]


def _parts(match, text, previous):
    alias = match["unit"] or match["month"]
    start, end = match.span()
    before, after = text[max(0, start - 16):start], text[end:end + 16]
    unit = _contextual_unit("个月" if match["month"] else alias, before, after, previous)
    if unit is None or before.endswith("第"):
        return None
    number = match["number"]
    if unit.kind in ("time", "duration"):
        if RELATIVE_SUFFIX.match(after) or before.endswith("过了"):
            return None
        if alias in ("年", "年度") and re.fullmatch(r"(?:19|20)[0-9]{2}", NumberExtract.detect(number)):
            return None
    if alias in ("角", "毛", "分") and after.startswith(("点", "點")):
        return None

    suffix_half = SUFFIX_HALF.match(text, end)
    half = bool(match["half"] or match["month"])
    if suffix_half and not half and unit.kind in COMPOUND_KINDS | {"count", "people"}:
        end = suffix_half.end()
        half = True
    if number.endswith("半") and half:
        return None

    value = parse_number(number)
    spoken = SPOKEN_REMAINDER.match(text, end) if alias in SPOKEN_UNITS and not half and not match["lower"] else None
    if spoken and not FOLLOWING_UNIT.match(text, spoken.end()) and value == value.to_integral_value():
        remainder = parse_number(spoken[0]).scaleb(-len(spoken[0]))
        value += -remainder if value < 0 else remainder
        end = spoken.end()
    if half:
        value += Decimal("-0.5") if value < 0 else Decimal("0.5")
    if match["lower"]:
        values = (parse_number(match["lower"]), value)
    elif not half and COLLOQUIAL_RANGE.fullmatch(number):
        values = tuple(parse_number(digit) for digit in number)
    else:
        # A dash directly after a unit of the same dimension is a range separator.
        if (number.startswith(("-", "−")) and previous and previous.kind == unit.kind
                and previous.symbol == unit.symbol and not text[previous.end:start].strip()):
            value = abs(value)
        values = (value,)
    return _converted(start, end, unit, values)


def _converted(start, end, unit, values):
    values = tuple((value + unit.offset) * unit.factor for value in values)
    if not all(math.isfinite(float(value)) for value in values):
        return None
    return Quantity(start, end, unit.kind, unit.symbol, values, unit.factor)


def _currency(match):
    symbol = PREFIX_CURRENCIES[match["prefix"]]
    suffix = match["suffix"]
    if suffix and UNITS[suffix].symbol != symbol:
        return None
    return _converted(*match.span(), Unit("money", symbol, Decimal(1)), (parse_number(match["number"]),))


def _ratio(match):
    factor = 100 / parse_number(match["denominator"])
    numbers = (match["number"], match["upper"]) if match["upper"] else (match["number"],)
    return _converted(*match.span(), UNITS["%"], tuple(parse_number(number) * factor for number in numbers))


def _merge(previous, current):
    if (previous.kind in COMPOUND_KINDS and previous.kind == current.kind
            and previous.symbol == current.symbol and previous.factor > current.factor
            and len(previous.values) == len(current.values) == 1
            and current.values[0] >= 0):
        sign = -1 if previous.values[0] < 0 else 1
        # Keep the smallest component's factor for the next merge.
        return Quantity(previous.start, current.end, current.kind, current.symbol,
                        (previous.values[0] + sign * current.values[0],), current.factor)
    return None


def find_quantities(text):
    """Yield nonoverlapping spans in text order, with values in canonical units."""
    text = text.translate(FULLWIDTH_ASCII)
    matches = sorted(
        (match for pattern in (CURRENCY, QUANTITY, RATIO) for match in pattern.finditer(text)),
        key=lambda match: match.start(),
    )
    clocks = iter(CLOCK.finditer(text))
    clock = next(clocks, None)
    pending = None
    end = 0
    for match in matches:
        start = match.start()
        if start < end:
            continue
        while clock and clock.end() <= start:
            clock = next(clocks, None)
        if clock and clock.start() < match.end():
            continue
        gap = text[end:start]
        previous = pending if re.fullmatch(rf"{SPACE}(?:又|[零〇0])?{SPACE}", gap) else None
        with localcontext() as context:
            context.prec = 256
            try:
                if match.re is CURRENCY:
                    current = _currency(match)
                elif match.re is QUANTITY:
                    current = _parts(match, text, previous)
                else:
                    current = _ratio(match)
            except ValueError:
                continue
            if current is None:
                continue
            merged = previous and text[start] not in "-−" and _merge(previous, current)
        if merged:
            pending = merged
        else:
            if pending:
                yield pending
            pending = current
        end = current.end
    if pending:
        yield pending

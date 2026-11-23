"""Parse the numeric part of Chinese quantities using the standard library."""

import re
import unicodedata
from decimal import Decimal, DecimalException, localcontext

DIGITS = dict(zip("零一二三四五六七八九", "0123456789"))
DIGITS.update({alias: str(digit) for digit, aliases in enumerate(
    ("〇○", "壹", "贰貳弍两兩俩倆", "叁參", "肆", "伍", "陆陸", "柒", "捌", "玖")
) for alias in aliases})
SMALL = {"十": 10, "百": 100, "千": 1000}
LARGE = {"万": 10**4, "亿": 10**8, "兆": 10**12}
TRANSLATION = str.maketrans({**DIGITS, **dict(zip("拾佰仟萬億點負廿卅卌−", (
    "十", "百", "千", "万", "亿", "点", "负", "2十", "3十", "4十", "-"
)))})
CHINESE_NUMBER = "".join(DIGITS) + "十百千万亿兆拾佰仟萬億廿卅卌"
ARABIC = "0-9０-９"
SIGN = r"(?:零[上下]|[正负負+＋\-－−])"
GROUPED = rf"[{ARABIC}]{{1,3}}(?:[,，][{ARABIC}]{{3}})+"
DIGIT_RUN = rf"(?:{GROUPED}|[{ARABIC}{CHINESE_NUMBER}]+)"
UNSIGNED = rf"(?:半|{DIGIT_RUN}(?:[.．点點](?:{DIGIT_RUN}|半))?|[.．][{ARABIC}]+)(?:[eE][+＋\-－−]?[{ARABIC}]{{1,3}})?"
SCALAR = rf"{SIGN}?{UNSIGNED}"
NUMBER = rf"{SCALAR}(?:分之{SCALAR}|[/／]{SCALAR})?"
_CHINESE_RUN = re.compile(rf"[{ARABIC}{CHINESE_NUMBER}]+")
_EXPONENT = re.compile(r"e([+-]?[0-9]+)$", re.IGNORECASE)


def _under_ten_thousand(text):
    if text.isdecimal():
        return Decimal(text)

    total = Decimal(0)
    rank = 10000
    start = 0
    for index, char in enumerate(text):
        if char not in SMALL:
            continue
        scale = SMALL[char]
        if scale >= rank:
            raise ValueError("Small Chinese place values must descend")
        coefficient = text[start:index]
        if not coefficient and index:
            raise ValueError("Missing coefficient")
        value = Decimal(coefficient or "1")
        if value <= 0 or (total and value >= 10):
            raise ValueError("Invalid coefficient")
        total += value * scale
        rank = scale
        start = index + 1

    tail = text[start:]
    if tail:
        value = Decimal(tail)
        if not tail.startswith("0") and len(tail) == 1 and rank in (100, 1000):
            value *= rank // 10
        if value >= rank:
            raise ValueError("Invalid remainder")
        total += value
    return total


def _magnitude(text):
    for char, scale in reversed(tuple(LARGE.items())):
        if char in text:
            if text.count(char) != 1:
                raise ValueError("Repeated Chinese scale")
            head, tail = text.split(char)
            value = _magnitude(head) if head else Decimal(1)
            if not tail:
                return value * scale
            if tail.isdecimal() and not tail.startswith("0"):
                # In colloquial forms such as 一万二 and 17万58, the tail
                # supplies the next place values after the large scale.
                width = len(str(scale)) - 1
                remainder = Decimal(tail) * 10**max(0, width - len(tail))
            else:
                remainder = _magnitude(tail)
            if remainder >= scale or value == 0:
                raise ValueError("Invalid large-scale remainder")
            return value * scale + remainder
    if "." not in text:
        return _under_ten_thousand(text)
    head, tail = text.split(".")
    decimal = re.fullmatch(r"([0-9]+)([十百千]?)", tail)
    if not decimal:
        raise ValueError("Invalid decimal")
    value = (_under_ten_thousand(head) if head else Decimal(0)) + Decimal("0." + decimal[1])
    return value * SMALL.get(decimal[2], 1)


def _scalar(text):
    sign = -1 if text.startswith(("负", "-", "零下", "0下")) else 1
    if text.startswith(("0下", "0上")):
        text = text[2:]
    elif text.startswith(("负", "正", "-", "+")):
        text = text[1:]

    if text == "半":
        return Decimal("0.5") * sign

    exponent = _EXPONENT.search(text)
    if exponent:
        text = text[:exponent.start()]
        power = int(exponent[1])
        if abs(power) > 308 or not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", text):
            raise ValueError("Invalid scientific notation")
        return Decimal(text).scaleb(power) * sign

    return _magnitude(text) * sign


def parse_number(text):
    """Return a Decimal for a complete number, raising ValueError on bad input."""
    if not text or len(text) > 128:
        raise ValueError("Invalid number length")
    text = unicodedata.normalize("NFKC", text)
    if not re.fullmatch(NUMBER, text):
        raise ValueError("Invalid number")
    text = text.translate(TRANSLATION).replace(",", "").replace("点", ".").replace(".半", ".5")
    try:
        with localcontext() as context:
            context.prec = 256
            if "分之" in text:
                denominator, numerator = text.split("分之")
                return _scalar(numerator) / _scalar(denominator)
            if "/" in text:
                numerator, denominator = text.split("/")
                return _scalar(numerator) / _scalar(denominator)
            return _scalar(text)
    except DecimalException as error:
        raise ValueError("Invalid number") from error


class NumberExtract:
    """Normalize Chinese integer runs for the legacy date and clock parser."""

    @classmethod
    def detect(cls, query):
        def replace(match):
            token = match[0]
            translated = token.translate(TRANSLATION)
            if translated.isdecimal():
                # Years and identifiers can contain significant leading zeros.
                return unicodedata.normalize("NFKC", translated)
            try:
                return format(parse_number(token), "f")
            except ValueError:
                return token

        return _CHINESE_RUN.sub(replace, query)

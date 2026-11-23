# sinan

司南是一个轻量的中文文本解析库。它使用正则表达式定位中文数字、量纲、日期时间、手机号和身份证号，再用 Python 标准库换算数值。运行时无需第三方依赖。

## 安装和使用

```sh
python -m pip install sinan
```

从 0.2.0 起需要 Python 3.11 或更新版本。

```python
from datetime import datetime
from sinan import Sinan

text = "今天下午五点，我走了三公里又两百米，用了一个半小时。"
result = Sinan(text, source_DT=datetime(2020, 8, 5)).parse(display_status=False)
# {
#     "datetime": ["2020-08-05 17:00:00"],
#     "length": [[3200.0, "m"]],
#     "time": [[5400.0, "s"]],
# }
```

`source_DT` 用于解析相对日期，省略时使用本地当前时间。`display_status` 默认为 `True`，会在终端打印原文和解析结果。每个量纲的结果按原文顺序排列，每项为 `[数值, 标准单位]`。日期时间、手机号和身份证号仍以字符串返回。手机号和身份证号仅按格式匹配。

## 数字和量纲

支持简繁体、中文大写、阿拉伯数字、全角数字、千位分组、混合进位、小数、分数、正负号、科学计数法和半数表达，例如 `壹仟貳佰`、`3万5千`、`四分之三`、`1.5e3` 和 `两个半月`。内部使用 `Decimal` 换算，返回值沿用浮点数。

| 结果键 | 标准单位 | 输入示例 |
| --- | --- | --- |
| `length`, `area`, `volume`, `weight` | m、m²、L、kg | 一英尺、两公顷、500毫升、半吨 |
| `time`, `duration` | s、月 | 三刻钟、两周、三年六个月 |
| `speed`, `acceleration`, `flow` | m/s、m/s²、L/s | 36公里每小时、5m/s²、2立方米每秒 |
| `density`, `concentration`, `pressure`, `force` | kg/m³、mg/L、Pa、N | 1g/cm³、2g/L、3兆帕、10牛顿 |
| `temperature`, `angle` | ℃、° | 零下五摄氏度、32°F、90度角 |
| `power`, `energy`, `voltage`, `current`, `charge`, `resistance`, `frequency` | W、J、V、A、C、Ω、Hz | 20瓦、3度电、5伏、30毫安、5000mAh、2千欧、1GHz |
| `data`, `data_rate` | B、bit/s | 8Mb、8MiB、100Mbps、2MB/s |
| `ratio`, `sound`, `illuminance`, `luminous_flux` | %、dB、lx、lm | 百分之三、千分之八、70分贝、300勒克斯、500流明 |
| `money` | 元或原币种代码 | 三块五角八分、￥50、20美元 |
| `people`, `count`, `score` | 人、人次、原量词、分 | 三位客人、十人次、两辆车、考了九十分 |

单位别名和换算系数集中在 [sinan/quantity.py](sinan/quantity.py)。拉丁单位区分大小写，例如 `8MB` 是 8,000,000 B，`8Mb` 是 1,000,000 B。不同币种分别返回，不作汇率换算。年、季度和月按日历月换算，周、天和小时按秒换算。

## 歧义处理

- 相连、同量纲且单位逐级递减的数量合并，例如 `两小时三十分五秒` → 9005 秒，`一米八厘米` → 1.08 米。常见口语省略单位也可识别，例如 `一米七五` → 1.75 米，`三块五` → 3.5 元。逗号、换行和区间连接符保留独立的值。
- `三到五公里`、`3–5 km`、`两三公里` 都输出两个端点，沿用原有列表结构。`约三公里`、`三公里左右`、`三千多米` 输出基准值。
- 裸写的 `度` 默认是摄氏度，角度和电量语境分别使用 `°` 和 `J`。`分` 结合计时、金额和评分语境识别；可以用 `分钟`、`分钱` 或 `分贝` 明确含义。
- `八点二十分三秒` 按时刻解析，`五点五秒` 和 `五点三厘米` 按小数量值解析。`两小时前` 交给相对时间规则。
- 对 `三角形`、`三里屯`、`一分为二` 等常见词汇做了排除。`三块石头` 是计数，`三块钱` 是金额。单位缺失或只靠较远的上下文才能消歧的表达仍可能无法识别。相对年份和月份沿用旧版近似规则（365 天和 30 天）。

## 开发和发布

```sh
python -B -m unittest discover -v
python -m pip install build twine
python -m build --outdir release-dist
python -m twine check --strict release-dist/*
```

推送与安装包版本一致的 `vX.Y.Z` 标签会运行发布工作流，测试通过后构建 wheel 和 sdist，并上传到 GitHub Release。也可以在 GitHub Actions 的 Release 页面点击 **Run workflow**，选择 `master`，在 `release_tag` 字段填写已有标签（本次默认 `v0.2.0`）。如果上一次输入有误，请从 Release 页面新建一次运行。PyPI 项目需要设置 GitHub Trusted Publisher，仓库为 `yiyujianghu/sinan`，工作流文件为 `release.yml`，环境为 `pypi`。配置好后，发布任务会通过 GitHub OIDC 上传同一批构建产物。

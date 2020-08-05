# sinan
中文日期/时间/数字量提取工具

#### 项目说明：
由于在做NLP相关的工作，对文本中的数字要做信息提取，就查询了网上相关解决方案。
有一款做英文日期/时间的解析工具，便想着也做一个中文版，最终实现了日期/时间/数字量的提取。
起名"sinan"是指古代测量工具"司南"，该项目也是一个测量工具。

#### 功能说明：
1、汉字转换数字  
可将文本中的数量词汉字转为相关数字，例如：
> * "一千两百五十八点二"转换为"1258.2"  
> * "四分之三"转换为"0.75"  

2、日期/时间解析  
可解析"年-月-日 时:分:秒"，并支持推理运算，但闰年及月份天数仍未完善，
例如(以下转换的基准日期为2000-08-08 12:30:30)：  
> * "2001.3.10"转换为"2001-03-10 12:30:30"  
> * "一九九五年十月十日下午三点二十一分"转换为"1995-10-10 15:21:30"
> * "去年的今天下午的差一刻五点"转换为"1999-08-08 16:45:30"

3、手机号/身份证号提取  
可解析正确的手机号/身份证号，例如：
> * "我的手机号是15899232399"可提取其中正确的手机号码

4、数量词提取
可提取文本信息中的数量信息，例如：
> * "我花了一个半小时走了5.8公里的路程"可提取出"1.5小时"与"5.8公里"的信息
> * "他花了4.8万元买了一辆电动车"可提取出"48000元"

数量词信息的提取与转换受单位词典的限制，目前可支持长度(m)、时间(s)、质量(kg)、货币(元)等常见信息提取，可通过扩充词典增加其功能。

#### 安装说明：
该安装包可通过pip安装，在命令行中通过如下命令即可安装完成。  
`$ pip install sinan --user`  

#### 使用说明：  
1、安装完毕后即可在使用：
```
from sinan import Sinan
si = Sinan("今天下午五点，我花了一个半小时走了五公里的路程。")
result = si.parse()
```
可看到result中的信息：
```
{'datetime': ['2020-08-05 17:00:00'], 'time': ['5400.0s'], 'length': ['5000.0m']}
```
通过结构化数据解析即可提取其中信息。

2、参数说明：  
* `si = Sinan(content, source_DT=None)`  
其中content为待解析的文本内容，source_DT为标准时间；
* `si.parse(display_status=True)`
其中display_status为时候显示解析过程，默认为True时显示，如果设置为False则不显示解析过程；

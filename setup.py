# -*-conding:utf-8-*-
# Base Information:
# @author:      yiyujianghu
# @project:     <sinan>
# @file:        setup.py
# @time:        2020/8/5 4:50 下午

"""
Notes: setup for sinan
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import setuptools

setup(
    name='sinan',  # 包的名字
    author='yiyujianghu',  # 作者
    version='0.1.3',  # 版本号
    license='MIT',

    description='A datetime/numberic parser for chinese text',  # 描述
    author_email='dongjunyou@126.com',              # 你的邮箱
    url='https://github.com/yiyujianghu/sinan',     # 可以写github上的地址，或者其他地址
    # 包内需要引用的文件夹
    packages=setuptools.find_packages(),
    keywords='NLP,NER',
    include_package_data = True,
    platforms="any",

    # 依赖包
    install_requires=[],
    zip_safe=True,
)

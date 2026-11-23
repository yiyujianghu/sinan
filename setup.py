from pathlib import Path

from setuptools import find_packages, setup


setup(
    name="sinan",
    version="0.2.0",
    author="yiyujianghu",
    author_email="dongjunyou@126.com",
    url="https://github.com/yiyujianghu/sinan",
    description="Lightweight Chinese number, quantity, and datetime extraction",
    long_description=Path(__file__).with_name("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.11",
    packages=find_packages(),
    keywords="chinese nlp number quantity datetime",
)

from setuptools import setup

setup(
name='tradeapp',
version='0.1',
description='Some really good stuff, that I am still working on',
author='Félix Poirier',
author_email='felixpoirier2001@gmail.com',
packages=['tradeapp'],  # same as name
install_requires=['requests', 'pandas', 'colored'], # external packages as dependencies
)
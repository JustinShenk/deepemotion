#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#MIT License
#
#Copyright (c) 2018 Justin Shenk
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import os
import sys
from setuptools import setup, setuptools

__author__ = 'Justin Shenk'
__version__ = '0.0.1'


def readme():
    with open('README.md', encoding="UTF-8") as f:
        return f.read()


if sys.version_info < (3, 4, 1):
    sys.exit('Python < 3.4.1 is not supported!')

if not os.path.exists('config.cfg'):
    SECRET_KEY = os.urandom(16)
    with open('config.cfg', 'w') as f:
        f.write(f'SECRET_KEY={SECRET_KEY}')

setup(
    name='video-demo',
    version=__version__,
    description='Video emotion analysis web app with Flaks and Keras',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/justinshenk/deepemotion',
    author='Justin Shenk',
    author_email='shenk.justin@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(exclude=["tests.*", "tests"]),
    install_requires=[
        'matplotlib',
        'tensorflow',
        'opencv-contrib-python',
        'keras',
        'pandas',
        'requests',
        'seaborn',
        'flask',
        'fer',
        'gunicorn',
        'uwsgi',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    include_package_data=True,
    keywords="expression emotion detection video",
    zip_safe=False)

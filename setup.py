# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='Bade',
    version='0.1',
    py_modules=['bade'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'bade = bade.bade:bade',
        ],
    }
)

# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='Bade',
    version='0.1',
    author='Martin Magr',
    author_email='mmagr@redhat.com',
    py_modules=['bade'],
    install_requires=[
        'Click',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'bade = bade.bade:bade',
        ],
    }
)
